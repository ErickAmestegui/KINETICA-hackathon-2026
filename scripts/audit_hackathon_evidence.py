"""Audit the preserved private hackathon evidence offline, without provider transport.

Run from the repository root with .venv/Scripts/python.exe. Private source files
are read only; the report is content-addressed under output/final-audit/.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.kinematics import Parameters
from backend.mask_motion import audit_masks
from backend.reality_lab import freeze, reveal

EXPORT_SHA256 = "f4e09b06aa2323348e79b182c598a1f34f57816f65b3eb91b44184d645eff65a"
ORIGINAL_VIDEO_SHA256 = "a80d4fc0c85b1d4ec747fe2049349cf656579c3e0d02894c4ae437a412665e66"
CLIP_SHA256 = "4e179551a3dde38da847c9392e277331bc93fd1ac28d3524da8a6ca4872a1677"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT / "output/kinetica-project.json")
    args = parser.parse_args()
    project_path = args.project.resolve()
    raw = project_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPORT_SHA256, "Original export hash changed")
    project = json.loads(raw)
    result, video = project["samResult"], project["video"]
    require(not result.get("simulated"), "Synthetic export cannot establish real evidence")
    require(result.get("outcome", {}).get("status") == "completed", "Incomplete original SAM response")
    identity = video["id"]
    require(bool(re.fullmatch(r"[0-9a-f]{32}", identity)), "Invalid source identity")
    folder = ROOT / "data" / identity
    metadata = json.loads((folder / "metadata.json").read_text("utf-8"))
    require(metadata["extension"] == ".mp4", "Expected preserved MP4 source")
    source = folder / "source.mp4"
    original_hashes = {project_path: digest(project_path), source: digest(source)}
    require(original_hashes[source] == CLIP_SHA256, "Preserved source clip hash changed")
    require(all(video[k] == metadata[k] for k in ("frames", "width", "height")), "Source metadata mismatch")
    capture = cv2.VideoCapture(str(source))
    require(capture.isOpened(), "Cannot decode source video")
    decoded_fps = capture.get(cv2.CAP_PROP_FPS)
    decoded = 0
    dimensions = set()
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            decoded += 1
            dimensions.add((frame.shape[1], frame.shape[0]))
    finally:
        capture.release()
    require(decoded == 50 and dimensions == {(960, 540)}, "Source decode differs from saved 50-frame clip")
    require(decoded_fps == metadata["fps"] == 25 and len(metadata["timestamps"]) == decoded, "Timing metadata mismatch")
    audit = audit_masks(result, metadata, "e14d21bb8f3c")
    require(audit["counts"] == dict(records=300, objects=3, boxes=150, masks=150, frames_with_geometry=50, source_frames=50), "SAM counts changed")
    require(not audit["issues"] and not audit["missing_geometry_frames"], "Malformed or missing original geometry")
    require(audit["evidence"]["parser_diagnostics"] == 0, "Original parser diagnostics found")
    require({obj["object_id"] for obj in audit["objects"]} == {"0", "1", "2"}, "SAM IDs changed")
    require(all(obj["valid_masks"] == obj["boxes"] == 50 and not obj["missing_mask_frames"] and not obj["missing_box_frames"] for obj in audit["objects"]), "Missing or invalid object observations")
    expected_geometry = Counter({(frame, kind): 1 for frame in range(50) for kind in ("box", "mask")})
    for object_id in ("0", "1", "2"):
        geometry = Counter((row["frame"], row["kind"]) for row in result["records"] if row["object_id"] == object_id)
        require(geometry == expected_geometry, "Duplicate SAM geometry")
    original_video = None
    for candidate in sorted((ROOT / "data").glob("*/metadata.json")):
        entry = json.loads(candidate.read_text("utf-8"))
        if entry.get("frames") != 442 or entry.get("extension") != ".mp4":
            continue
        candidate_source = candidate.parent / "source.mp4"
        if candidate_source.is_file() and digest(candidate_source) == ORIGINAL_VIDEO_SHA256:
            original_video = candidate_source
            original_hashes[original_video] = ORIGINAL_VIDEO_SHA256
            break
    require(original_video is not None, "Preserved original 442-frame video hash not found locally")
    replay = {}
    for horizon in (8, 20):
        prediction = freeze(result, metadata, Parameters(**project["parameters"]), "2", True, 29, horizon)
        require("metrics" not in prediction and "rows" not in prediction, "Freeze exposed hidden evaluation")
        require(prediction["protocol"]["training_frames"] == list(range(30)), "Training split changed")
        report = reveal(prediction["token"])
        require(report["n"] == horizon, "Missing replay observations")
        if horizon == 8:
            require(report["evaluation_valid"], "Eight-frame replay unexpectedly invalid")
            expected = dict(model_rmse_px=9.1046, constant_rmse_px=23.9297, linear_rmse_px=75.5859)
            require(all(math.isclose(report["metrics"][key], value, abs_tol=.0001) for key, value in expected.items()), "Replay metrics changed")
        else:
            require(not report["evaluation_valid"] and all(value is None for value in report["metrics"].values()), "Known source cut did not invalidate every score")
        replay[str(horizon)] = report
    incident_folder = ROOT / "output/muse-incident-d25cbc08d7c2"
    assessment = json.loads((incident_folder / "assessment.json").read_text("utf-8"))
    log_hashes = {}
    for name, expected_hash in assessment["preserved_logs"].items():
        require(name in ("server.stdout.log", "server.stderr.log"), "Unexpected incident log path")
        path = incident_folder / name
        log_hashes[name] = digest(path)
        original_hashes[path] = log_hashes[name]
        require(log_hashes[name] == expected_hash, "Preserved Muse incident log changed")
    stdout = (incident_folder / "server.stdout.log").read_text("utf-8")
    quote_200 = len(re.findall(r'"POST /api/lab/muse/quote HTTP/1\.1" 200\b', stdout))
    run_502 = len(re.findall(r'"POST /api/lab/muse/run HTTP/1\.1" 502\b', stdout))
    require(quote_200 == run_502 == 1, "Saved Muse local attempt differs")
    require(all(digest(path) == before for path, before in original_hashes.items()), "Input evidence changed during audit")
    report = dict(schema="kinetica-final-evidence-audit/1", inference_performed=False,
                  export_sha256=EXPORT_SHA256, source_clip_sha256=original_hashes[source],
                  original_video_sha256=ORIGINAL_VIDEO_SHA256, decoded_source_frames=decoded,
                  source_dimensions=sorted(dimensions), source_fps=metadata["fps"],
                  sam_audit=audit, replay=replay,
                  muse_incident=dict(diagnostic_id="d25cbc08d7c2", local_quote_200=quote_200,
                                     local_run_502=run_502, preserved_log_sha256=log_hashes,
                                     root_cause="undetermined", provider_receipt_confirmed=None,
                                     external_http_status=None, usage=None,
                                     explanation="Original failure retained no provider response or phase telemetry; local 502 is not billing evidence"),
                  input_hashes_unchanged=True,
                  limits=["Local hashes establish integrity, not provider authentication",
                          "300 geometry records represent 150 boxes plus 150 contours, not 300 independent objects",
                          "Slider #2 is a manual interpretation; mask centroids are not joint labels",
                          "Replay uses previously inspected data and full-video SAM context; independent prospective validation is absent"])
    encoded = json.dumps(report, indent=2, allow_nan=False)
    out = ROOT / "output/final-audit"
    out.mkdir(exist_ok=True, parents=True)
    path = out / ("evidence-" + hashlib.sha256(encoded.encode()).hexdigest()[:16] + ".json")
    if not path.exists():
        path.write_text(encoded, "utf-8")
    print(json.dumps(dict(report=str(path), checks_passed=True, counts=audit["counts"],
                          replay_8_metrics=replay["8"]["metrics"], replay_20_valid=replay["20"]["evaluation_valid"],
                          muse_cause="undetermined", muse_usage=None, input_hashes_unchanged=True,
                          inference_performed=False), indent=2))


if __name__ == "__main__":
    main()
