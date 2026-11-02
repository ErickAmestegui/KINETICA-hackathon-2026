"""Restore the packaged saved-SAM demo and optionally run KINETICA without Meta I/O.

This is release tooling, not an inference adapter. No network, credentials or
original workspace inputs are needed by --prepare-only. Existing data is never
overwritten. Run it only from an extracted submission-review kit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    demo = ROOT / 'demo'
    inventory = json.loads((demo / 'PROVENANCE.json').read_text('utf-8'))
    names = [inventory.get('project_file', 'kinetica-review-project.json'), inventory.get('media_file', 'eitech-sam-input-50.mp4')]
    if not all(re.fullmatch(r'[A-Za-z0-9._-]+', name) for name in names):
        raise ValueError('Invalid packaged demo file name')
    project_path = demo / names[0]
    project = json.loads(project_path.read_text('utf-8'))
    video = project['video']
    identity = video['id']
    if not re.fullmatch(r'[0-9a-f]{32}', identity) or video['extension'] != '.mp4':
        raise ValueError('Invalid packaged video identity')
    media = demo / names[1]
    metadata = demo / 'metadata.json'
    if digest(media) != inventory['source_clip_sha256']:
        raise ValueError('Packaged media hash differs from provenance')
    if digest(project_path) != inventory['sanitized_project_sha256']:
        raise ValueError('Packaged project hash differs from provenance')
    if digest(metadata) != inventory['metadata_sha256']:
        raise ValueError('Packaged metadata hash differs from provenance')
    destination = ROOT / 'data' / identity
    destination.mkdir(parents=True, exist_ok=True)
    for source, name in ((media, 'source.mp4'), (metadata, 'metadata.json')):
        target = destination / name
        if target.exists():
            if digest(target) != digest(source):
                raise ValueError('Existing data differs; refusing to overwrite: ' + name)
        else:
            # Exclusive creation prevents an unnoticed concurrent overwrite.
            with target.open('xb') as output, source.open('rb') as incoming:
                shutil.copyfileobj(incoming, output)
    (ROOT / 'output').mkdir(exist_ok=True)
    print(inventory.get('restore_message', 'Saved real SAM demo restored. 300 records = 150 boxes + 150 contours; Ask remains mock; no new inference.'), flush=True)
    return project_path.relative_to(ROOT).as_posix()


def prepare_tests():
    """Generate visibly synthetic browser fixtures only inside the extracted tree."""
    environment = dict(os.environ, MODEL_API_KEY='', META_ALLOW_PAID='false')
    subprocess.run([sys.executable, '-m', 'scripts.make_synthetic_fixture'], cwd=ROOT, env=environment, check=True)
    from backend.vision import inspect_video
    media = ROOT / 'output/synthetic-slider-crank.mp4'
    identity = digest(media)[:32]
    folder = ROOT / 'data' / identity
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / 'source.mp4'
    if target.exists() and digest(target) != digest(media):
        raise ValueError('Existing synthetic fixture differs; refusing to overwrite')
    if not target.exists():
        with target.open('xb') as output, media.open('rb') as incoming:
            shutil.copyfileobj(incoming, output)
    metadata = inspect_video(media)
    metadata.update(id=identity, name='synthetic-slider-crank.mp4', extension='.mp4', bytes=media.stat().st_size)
    metadata_path = folder / 'metadata.json'
    if metadata_path.exists():
        if json.loads(metadata_path.read_text('utf-8')) != metadata:
            raise ValueError('Existing synthetic metadata differs; refusing to overwrite')
    else:
        metadata_path.write_text(json.dumps(metadata), encoding='utf-8')
    subprocess.run([sys.executable, 'scripts/prepare_mask_motion_test.py'], cwd=ROOT, env=environment, check=True)
    print('SYNTHETIC TEST fixtures prepared; they are not Meta or real-video evidence.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--prepare-tests', action='store_true', help='Generate explicitly synthetic E2E fixtures locally')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise ValueError('Use an unprivileged local port')
    project = prepare()
    if args.prepare_tests:
        prepare_tests()
    print('Open project JSON: ' + project, flush=True)
    if args.prepare_only:
        return
    if not (ROOT / 'frontend/dist/index.html').is_file():
        raise ValueError('Build frontend before launching this source-only package')
    environment = dict(os.environ)
    # Nonempty dotenv values cannot replace these process settings.
    environment['MODEL_API_KEY'] = ''
    environment['META_ALLOW_PAID'] = 'false'
    print(f'Local review: http://127.0.0.1:{args.port}; paid inference disabled.', flush=True)
    subprocess.run([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host',
                    '127.0.0.1', '--port', str(args.port)], cwd=ROOT, env=environment, check=True)


if __name__ == '__main__':
    main()
