"""Create a PRIVATE 50-frame H.264 clip locally. No network or Meta dependencies.

Run: .venv/Scripts/python.exe scripts/prepare_sam_clip.py --video PATH --start 150
Does not overwrite an existing clip. This is a future test input, not SAM evidence.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--start', type=int, default=150)
    parser.add_argument('--output', type=Path, default=Path('output/sam-local/eitech-50-frames.mp4'))
    args = parser.parse_args()
    source = args.video.resolve(strict=True)
    cap = cv2.VideoCapture(str(source))
    fps, frames = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps <= 0 or args.start < 0 or args.start+50 > frames:
        raise SystemExit('Input does not contain the requested 50-frame interval')
    if args.output.exists():
        raise SystemExit('Output exists; refusing to overwrite it')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-n',
                    '-i', str(source), '-vf',
                    f'trim=start_frame={args.start}:end_frame={args.start+50},setpts=N/({fps}*TB),scale=960:-2',
                    '-frames:v', '50', '-r', str(fps), '-fps_mode', 'cfr', '-an', '-c:v', 'libx264',
                    '-bf', '0', '-crf', '18', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(args.output)], check=True, capture_output=True)
    cap = cv2.VideoCapture(str(args.output))
    count, width, height = 0, int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    while cap.read()[0]: count += 1
    cap.release()
    if count != 50: raise SystemExit(f'Decoded {count} frames, expected 50; do not use this clip')
    manifest = {'purpose':'PRIVATE future authorized SAM test; no inference performed',
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'source_frame_interval_inclusive':[args.start,args.start+49],
                'clip_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                'frames':count,'fps':fps,'width':width,'height':height,
                'transformation':'H.264 re-encode without B frames, downscale to 960 wide, audio removed, constant-rate timestamps start at zero',
                'uploaded_to_meta':False}
    args.output.with_suffix('.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Local clip verified: {count} frames, {width}x{height}, {count/fps:.2f} seconds. No network calls.')


if __name__ == '__main__': main()
