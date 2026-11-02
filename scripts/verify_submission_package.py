"""Smoke-test an extracted local review kit without touching original studies.

Uses the current Python dependency environment, but imports application code from
the newly extracted archive. The temporary local server has no key and paid=false.
No external provider request is made. All outputs stay inside this workspace.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_submission_package import verify


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--report', type=Path, default=ROOT / 'output/submission-package/extracted-validation.json')
    args = parser.parse_args()
    archive = args.archive.resolve()
    archive.relative_to((ROOT / 'output').resolve())
    report_path = args.report.resolve()
    report_path.relative_to(ROOT.resolve())
    if not 1024 <= args.port <= 65535:
        raise ValueError('Use an unprivileged local port')
    checked = verify(archive)
    if checked['package_kind'] != 'submission-review-kit':
        raise ValueError('Select the review kit with built frontend, not the source-only candidate')
    stage_root = ROOT / 'output/submission-package'
    stage_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='extracted-review-', dir=stage_root))
    protected = [ROOT / 'output/kinetica-project.json', ROOT / 'data/3e4c5e12f8b84af0996f02a9dfa89989/source.mp4']
    original_hashes = {path.relative_to(ROOT).as_posix(): digest(path) for path in protected if path.is_file()}
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(stage)
    subprocess.run([sys.executable, 'scripts/prepare_review_demo.py', '--prepare-only'], cwd=stage,
                   check=True, capture_output=True)
    replays = {}
    for horizon in (8, 20):
        result = subprocess.run([sys.executable, 'scripts/replay_reality_lab.py', '--project', 'demo/kinetica-review-project.json',
                                 '--object-id', '2', '--confirm-slider', '--freeze-frame', '29', '--horizon', str(horizon)],
                                cwd=stage, check=True, capture_output=True, text=True)
        replay = json.loads(result.stdout)
        if replay['inference_performed'] is not False:
            raise ValueError('Replay must not perform inference')
        if horizon == 8:
            expected = dict(model_rmse_px=9.1046, constant_rmse_px=23.9297, linear_rmse_px=75.5859)
            if replay['n'] != 8 or not all(math.isclose(replay['metrics'][key], value, abs_tol=.0001) for key, value in expected.items()):
                raise ValueError('Extracted replay metrics differ')
        elif not all(value is None for value in replay['metrics'].values()):
            raise ValueError('Known-cut replay must withhold every score')
        replay.pop('report', None)
        replays[str(horizon)] = replay
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            raise ValueError('Requested port is in use; existing process was not modified')
    environment = dict(os.environ, MODEL_API_KEY='', META_ALLOW_PAID='false')
    imported = subprocess.check_output([sys.executable, '-c', 'import backend.main;print(backend.main.__file__)'],
                                       cwd=stage, env=environment, text=True).strip()
    if not Path(imported).resolve().is_relative_to(stage.resolve()):
        raise ValueError('Interpreter did not import the extracted backend')
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    origin = f'http://127.0.0.1:{args.port}'
    with (stage_root / 'extracted-server.log').open('w') as logs:
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', str(args.port)],
                                  cwd=stage, env=environment, stdout=logs, stderr=logs, creationflags=flags)
        try:
            deadline = time.monotonic() + 45
            while True:
                try:
                    health = json.load(urlopen(origin + '/api/health', timeout=2))
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.2)
            if health['status'] != 'ok' or health['meta']['paid_enabled'] or health['meta']['key_configured']:
                raise ValueError('Extracted health/spending configuration differs')
            if b'<html' not in urlopen(origin, timeout=5).read().lower():
                raise ValueError('Extracted built frontend unavailable')
            video_id = '3e4c5e12f8b84af0996f02a9dfa89989'
            metadata = json.load(urlopen(origin + '/api/videos/' + video_id, timeout=5))
            if (metadata['frames'], metadata['width'], metadata['height']) != (50, 960, 540):
                raise ValueError('Extracted source metadata differs')
            thumbnail = urlopen(origin + '/api/videos/' + video_id + '/thumbnail/0', timeout=5).read()
            if thumbnail[:2] != b'\xff\xd8':
                raise ValueError('Extracted source did not decode')
        finally:
            server.terminate()
            server.wait(timeout=15)
    if any(digest(ROOT / name) != before for name, before in original_hashes.items()):
        raise ValueError('Original source/project changed during extraction check')
    report = dict(schema='kinetica-extracted-package-check/1', candidate=archive.name,
                  candidate_sha256=digest(archive), archive_manifest_verified=True,
                  extracted_source_used=True, backend_source='backend/main.py',
                  dependencies='existing Python environment; dependency binaries not bundled',
                  server_port=args.port, server_stopped_after_test=True,
                  key_configured=False, paid_enabled=False, root_html_served=True,
                  clip_metadata_valid=True, actual_thumbnail_decoded=True,
                  replays=replays, original_input_hashes_unchanged=True,
                  original_input_hashes=original_hashes, new_meta_requests=0)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
