"""Render an ORIGINAL, explicitly synthetic slider-crank clip for the rights-clean demo variant.

Everything here is authored by this repository: the footage, its ground truth and the
saved geometry derived from that ground truth. Nothing is real footage, nothing comes
from SAM, and no inference is performed. The true motion contains a motor speed ripple
and measurement noise so the constant-speed replay has a non-trivial error to report.
"""
import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.kinematics import Calibration, Parameters, project, solve  # noqa: E402

OUT = ROOT / 'output' / 'original-demo'
W, H, FPS, FRAMES = 1280, 720, 25, 125
P = Parameters(r=32, L=128, rpm=36, e=0)
CAL = Calibration(ox=380, oy=410, scale=3.0)
RIPPLE_RAD, RIPPLE_PERIOD_S = 0.16, 2.3
MASK_NOISE_PX, SEED = 0.8, 20261102
LABEL = 'ORIGINAL SYNTHETIC CLIP - rendered by KINETICA code - not real footage'
DIAGNOSTIC = 'SYNTHETIC-ORIGINAL-CLIP'
SLIDER_W, SLIDER_H = 92, 58


def true_theta(t):
    return t * P.rpm * math.tau / 60 + RIPPLE_RAD * math.sin(math.tau * t / RIPPLE_PERIOD_S)


def state(t):
    return solve(P.model_copy(update={'rpm': 0.0, 'phase': true_theta(t)}), 0.0)


def background():
    rows = np.linspace(0, 1, H)[:, None]
    top, bottom = np.array([58, 52, 46]), np.array([30, 27, 24])
    image = (top * (1 - rows) + bottom * rows)[:, None, :].repeat(W, 1).reshape(H, W, 3)
    image = image.astype(np.uint8)
    cv2.rectangle(image, (0, 560), (W, H), (40, 44, 48), -1)
    cv2.line(image, (0, 560), (W, 560), (70, 76, 82), 2, cv2.LINE_AA)
    for x in range(0, W, 64):
        cv2.line(image, (x, 560), (x - 120, H), (46, 50, 54), 1, cv2.LINE_AA)
    return image


def shadowed(draw, image, offset=(10, 14)):
    shadow = np.zeros_like(image)
    draw(shadow, shift=offset, shadow=True)
    blur = cv2.GaussianBlur(shadow, (0, 0), 7)
    image[:] = np.clip(image.astype(np.int16) - blur.astype(np.int16) // 2, 0, 255).astype(np.uint8)
    draw(image, shift=(0, 0), shadow=False)


def pt(v, shift=(0, 0)):
    return int(round((v[0] + shift[0]) * 16)), int(round((v[1] + shift[1]) * 16))


def render(t):
    s = state(t)
    o = project(s['O'], CAL); a = project(s['A'], CAL); b = project(s['B'], CAL)
    image = background()
    rail_y = CAL.oy
    for dy in (-SLIDER_H / 2 - 5, SLIDER_H / 2 + 5):
        cv2.line(image, pt((560, rail_y + dy)), pt((1060, rail_y + dy)), (120, 128, 134), 6, cv2.LINE_AA, 4)
    for x in (600, 1020):
        cv2.rectangle(image, (x - 14, int(rail_y + SLIDER_H / 2 + 8)), (x + 14, 560), (74, 80, 86), -1)
    cv2.rectangle(image, (int(o[0]) - 70, int(o[1]) + 40), (int(o[0]) + 70, 560), (66, 72, 78), -1)

    def mechanism(canvas, shift, shadow):
        dark = (255, 255, 255) if shadow else None
        cv2.circle(canvas, pt(o, shift), 120 * 16, dark or (92, 104, 112), -1, cv2.LINE_AA, 4)
        if not shadow:
            cv2.circle(canvas, pt(o), 120 * 16, (150, 160, 166), 3, cv2.LINE_AA, 4)
            for k in range(6):
                angle = s['theta'] + k * math.tau / 6
                end = (o[0] + 108 * math.cos(angle), o[1] - 108 * math.sin(angle))
                cv2.line(canvas, pt(o), pt(end), (70, 80, 88), 10, cv2.LINE_AA, 4)
            cv2.circle(canvas, pt(o), 26 * 16, (54, 60, 66), -1, cv2.LINE_AA, 4)
        cv2.line(canvas, pt(a, shift), pt(b, shift), dark or (176, 186, 192), 18, cv2.LINE_AA, 4)
        corners = np.array([[b[0] - SLIDER_W / 2, b[1] - SLIDER_H / 2], [b[0] + SLIDER_W / 2, b[1] + SLIDER_H / 2]])
        p0, p1 = pt(corners[0], shift), pt(corners[1], shift)
        cv2.rectangle(canvas, p0, p1, dark or (150, 132, 36), -1, cv2.LINE_AA, 4)
        if not shadow:
            cv2.rectangle(canvas, p0, p1, (200, 186, 90), 3, cv2.LINE_AA, 4)
            for joint in (a, b):
                cv2.circle(canvas, pt(joint), 13 * 16, (60, 150, 196), -1, cv2.LINE_AA, 4)
                cv2.circle(canvas, pt(joint), 5 * 16, (36, 64, 84), -1, cv2.LINE_AA, 4)
            cv2.circle(canvas, pt(o), 9 * 16, (40, 120, 160), -1, cv2.LINE_AA, 4)

    shadowed(mechanism, image)
    cv2.rectangle(image, (0, 0), (W, 44), (18, 18, 20), -1)
    cv2.putText(image, LABEL, (24, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (120, 220, 240), 2, cv2.LINE_AA)
    cv2.putText(image, 'SYNTHETIC', (W - 196, H - 26), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (120, 220, 240), 2, cv2.LINE_AA)
    return image, o, a, b


def encode(path):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
           '-crf', '16', '-movflags', '+faststart', '-map_metadata', '-1', str(path)]
    rng = np.random.default_rng(SEED)
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    truth, records = [], []
    for frame in range(FRAMES):
        t = frame / FPS
        image, o, a, b = render(t)
        grain = rng.normal(0, 2.0, image.shape)
        process.stdin.write(np.clip(image + grain, 0, 255).astype(np.uint8).tobytes())
        truth.append(dict(frame=frame, t=t, theta=true_theta(t), crank_x=a[0], crank_y=a[1], slider_x=b[0], slider_y=b[1]))
        noisy = b + rng.normal(0, MASK_NOISE_PX, 2)
        for identity, cx, cy, w, h in [('SYNTHETIC-SLIDER', noisy[0], noisy[1], SLIDER_W, SLIDER_H),
                                       ('SYNTHETIC-FLYWHEEL', o[0], o[1], 240, 240)]:
            bounds = dict(left=cx - w / 2, top=cy - h / 2, right=cx + w / 2, bottom=cy + h / 2)
            records.append(dict(kind='box', object_id=identity, frame=frame, **bounds))
            records.append(dict(kind='mask', object_id=identity, frame=frame, bounds=bounds, width=w, height=h,
                                path=f'M0 0L{w} 0L{w} {h}L0 {h}Z'))
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError('FFmpeg encoding failed')
    return truth, records


def register(clip):
    """Store the clip exactly as POST /api/videos would, without needing a running server."""
    from backend.main import DATA, inspect_video
    identity = uuid.uuid4().hex
    folder = DATA / identity; folder.mkdir(parents=True)
    target = folder / 'source.mp4'; shutil.copyfile(clip, target)
    info = inspect_video(target)
    info.update(id=identity, name=clip.name, extension='.mp4', bytes=target.stat().st_size)
    (folder / 'metadata.json').write_text(json.dumps(info), 'utf-8')
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', action='store_true', help='also store the clip in data/ and write the project JSON')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    clip = OUT / 'kinetica-original-synthetic-slider-crank.mp4'
    truth, records = encode(clip)
    with (OUT / 'ground-truth.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(truth[0])); writer.writeheader(); writer.writerows(truth)
    digest = hashlib.sha256(clip.read_bytes()).hexdigest()
    provenance = dict(label='SYNTHETIC - ORIGINAL WORK OF THIS REPOSITORY', generator='scripts/make_original_demo_clip.py',
                      seed=SEED, frames=FRAMES, fps=FPS, size=[W, H], parameters=P.model_dump(), calibration=CAL.model_dump(),
                      true_motion=f'theta(t) = 2*pi*{P.rpm}/60*t + {RIPPLE_RAD}*sin(2*pi*t/{RIPPLE_PERIOD_S})',
                      saved_geometry=f'Boxes/contours derived from ground truth plus Gaussian noise sigma={MASK_NOISE_PX}px; not SAM output',
                      inference_performed=False, third_party_material=False, clip_sha256=digest)
    (OUT / 'provenance.json').write_text(json.dumps(provenance, indent=2), 'utf-8')
    print('Rendered', clip.relative_to(ROOT), digest, '- SYNTHETIC, no inference performed.')
    if not args.register:
        return
    info = register(clip)
    result = dict(records=records, outcome=dict(status='completed'), diagnostic=dict(id=DIAGNOSTIC), simulated=True,
                  diagnostics=[], remote_file_cleanup='not_needed')
    project_json = {'schema': 'kinetica/1', 'name': 'SYNTHETIC - original rendered slider-crank (no SAM, no third-party footage)',
                    'parameters': P.model_dump(), 'calibration': CAL.model_dump(), 'observations': [],
                    'video': {**info, 'provenance': 'synthetic'}, 'sam': records, 'samResult': result, 'regions': [], 'aiEvidence': []}
    target = OUT / 'SYNTHETIC-original-demo-project.json'
    target.write_text(json.dumps(project_json), 'utf-8')
    print('Registered video', info['id'], 'and wrote', target.relative_to(ROOT), 'records:', len(records))


if __name__ == '__main__':
    main()
