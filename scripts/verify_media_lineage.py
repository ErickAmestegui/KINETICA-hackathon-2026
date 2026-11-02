"""Verify preserved Eitech media lineage offline without provider transport.

Download the public original separately from the URL in RELEASE_RIGHTS.md first.
This script never downloads, edits source media, or sends data to a provider.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = 'a80d4fc0c85b1d4ec747fe2049349cf656579c3e0d02894c4ae437a412665e66'
CLIP_SHA = '4e179551a3dde38da847c9392e277331bc93fd1ac28d3524da8a6ca4872a1677'
ORIGINAL_URL = 'https://upload.wikimedia.org/wikipedia/commons/2/25/Schubkurbelgetriebe_%28Eitech%29.webm'
SOURCE_PAGE = 'https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, default=ROOT / 'output/submission-rights/Schubkurbelgetriebe-Eitech-original.webm')
    parser.add_argument('--clip', type=Path, default=ROOT / 'output/sam-local/eitech-50-cfr.mp4')
    args = parser.parse_args()
    original, clip = args.original.resolve(strict=True), args.clip.resolve(strict=True)
    require(digest(original) == ORIGINAL_SHA, 'Downloaded original differs from preserved Eitech SHA-256')
    require(digest(clip) == CLIP_SHA, 'SAM source clip hash differs')
    # The earlier local .mp4 filename did not identify the true container.
    original_header = original.read_bytes()[:16]
    require(original_header[:4] == bytes.fromhex('1a45dfa3'), 'Expected EBML/WebM container header')
    original_capture = cv2.VideoCapture(str(original))
    clip_capture = cv2.VideoCapture(str(clip))
    require(original_capture.isOpened() and clip_capture.isOpened(), 'Source decoder unavailable')
    original_metadata = dict(reported_frames=int(original_capture.get(cv2.CAP_PROP_FRAME_COUNT)),
                             fps=original_capture.get(cv2.CAP_PROP_FPS),
                             width=int(original_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                             height=int(original_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    require(original_metadata['fps'] == 25.0 and original_metadata['width'] == 1920 and original_metadata['height'] == 1080,
            'Original dimensions/fps changed')
    observations = []
    try:
        index = 0
        while True:
            ok, frame = original_capture.read()
            if not ok:
                break
            if 150 <= index <= 199:
                ok_clip, clip_frame = clip_capture.read()
                require(ok_clip and clip_frame.shape[:2] == (540, 960), 'Missing or mismatched clip frame')
                resized = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
                diff = resized.astype(np.float64) - clip_frame.astype(np.float64)
                mse = float(np.mean(diff ** 2))
                psnr = 10 * math.log10(255 ** 2 / mse) if mse else 100.0
                observations.append(dict(clip_frame=index-150, original_frame=index,
                                         psnr_db=psnr, mean_absolute_difference=float(np.mean(np.abs(diff)))))
            index += 1
        require(index == 442 and len(observations) == 50, 'Unexpected decoded frame count')
        original_metadata['decoded_frames'] = index
        require(not clip_capture.read()[0], 'Unexpected additional clip frames')
        require(min(row['psnr_db'] for row in observations) > 35, 'Clip/source frame correspondence failed')
    finally:
        original_capture.release()
        clip_capture.release()
    require(digest(original) == ORIGINAL_SHA and digest(clip) == CLIP_SHA, 'Original evidence changed during verification')
    report = dict(schema='kinetica-media-lineage/1', verified_date='2026-11-02',
                  original_download_url=ORIGINAL_URL, source_page=SOURCE_PAGE,
                  author='Rhetos', declared_license='CC BY-SA 4.0',
                  license_url='https://creativecommons.org/licenses/by-sa/4.0/',
                  original_sha256=ORIGINAL_SHA, original_bytes=original.stat().st_size,
                  clip_sha256=CLIP_SHA, clip_bytes=clip.stat().st_size,
                  exact_binary_match_to_preserved_original=True,
                  original_container='EBML/WebM (earlier local filename used .mp4 extension)',
                  original_metadata=original_metadata,
                  clip_original_frame_interval_inclusive=[150, 199],
                  clip_transform='Excerpt, resize 1920x1080 to 960x540, H.264 encoding, audio removed, CFR25',
                  comparison='All50 corresponding decoded frames, OpenCV INTER_AREA half-size reference; encoding/resampler differences expected',
                  minimum_psnr_db=min(row['psnr_db'] for row in observations),
                  mean_psnr_db=float(np.mean([row['psnr_db'] for row in observations])),
                  frames=observations, originals_unchanged=True, inference_performed=False,
                  limits=['Binary identity establishes local/public file identity; Commons uploader licensing declaration is not a title warranty',
                          'PSNR establishes image correspondence, not model accuracy or prospective validation',
                          'Public release and competition license declarations still need entrant review/authorization'])
    encoded = json.dumps(report, indent=2, allow_nan=False).encode('utf-8')
    target = ROOT / 'output/submission-rights' / ('lineage-' + hashlib.sha256(encoded).hexdigest()[:16] + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(encoded)
    print(json.dumps(dict(report=str(target), exact_original_identity=True, compared_frames=len(observations),
                          minimum_psnr_db=report['minimum_psnr_db'], mean_psnr_db=report['mean_psnr_db'],
                          inference_performed=False), indent=2))


if __name__ == '__main__':
    main()
