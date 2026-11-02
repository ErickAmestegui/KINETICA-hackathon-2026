"""Seal the original real Meta SAM 3.1 result with its one and only source clip.

Copies (never moves or edits) the saved project and its input clip into a separate,
read-only evidence folder with hashes and lineage. The detections belong exclusively
to that Eitech excerpt; any other media must never be paired with them. No inference.
"""
import hashlib
import json
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_submission_package import CLIP_ID, CLIP_SHA, DIAGNOSTIC, PROJECT_SHA  # noqa: E402

OUT = ROOT / 'output/sam-evidence-preserved'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    project_path = ROOT / 'output/kinetica-project.json'
    clip_path = ROOT / 'data' / CLIP_ID / 'source.mp4'
    if digest(project_path) != PROJECT_SHA or digest(clip_path) != CLIP_SHA:
        raise ValueError('Original evidence changed; refusing to seal')
    project = json.loads(project_path.read_text('utf-8'))
    result = project['samResult']
    records = result['records']
    if result.get('simulated') or result['diagnostic']['id'] != DIAGNOSTIC or len(records) != 300 or project['video']['id'] != CLIP_ID:
        raise ValueError('Not the original completed real SAM result')
    lineage = json.loads((ROOT / 'docs/evidence/media-lineage.json').read_text('utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    copies = {'kinetica-project.original.json': project_path, 'eitech-sam-input-50.mp4': clip_path}
    for name, source in copies.items():
        target = OUT / name
        if target.exists():
            if digest(target) != digest(source):
                raise ValueError('Sealed copy differs from original: ' + name)
            continue
        shutil.copyfile(source, target)
    kinds = {kind: sum(1 for r in records if r['kind'] == kind) for kind in ('box', 'mask')}
    provenance = dict(
        schema='kinetica-sealed-sam-evidence/1',
        statement='These 300 geometry records were produced by Meta SAM 3.1 from this exact clip only. '
                  'They must never be attributed to, overlaid on or replayed against any other recording.',
        model='Meta sam-3.1 via Meta Model API; parsed by meta-sam-parser 0.1.0', diagnostic_id=DIAGNOSTIC,
        records=len(records), boxes=kinds['box'], contours=kinds['mask'],
        objects=sorted({str(r['object_id']) for r in records}), frames=project['video']['frames'],
        records_sha256=hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest(),
        original_project_sha256=PROJECT_SHA, source_clip_sha256=CLIP_SHA, source_video_id=CLIP_ID,
        source=dict(title='Schubkurbelgetriebe (Eitech)', author='Rhetos', license='CC BY-SA 4.0',
                    page=lineage['source_page'], download=lineage['original_download_url'],
                    original_sha256=lineage['original_sha256'], original_bytes=lineage['original_bytes'],
                    original_frames_used_inclusive=lineage['clip_original_frame_interval_inclusive'],
                    transform=lineage['clip_transform']),
        reconstruction_verified=False, new_inference_performed=False,
        files={name: digest(OUT / name) for name in copies})
    manifest = OUT / 'PROVENANCE.json'
    for path in (manifest, OUT / 'SHA256SUMS'):
        if path.exists():
            path.chmod(stat.S_IREAD | stat.S_IWRITE)
    manifest.write_text(json.dumps(provenance, indent=2) + '\n', 'utf-8')
    (OUT / 'SHA256SUMS').write_text(''.join(f'{digest(OUT / n)}  {n}\n' for n in [*copies, 'PROVENANCE.json']), 'utf-8')
    for path in OUT.iterdir():
        path.chmod(stat.S_IREAD)
    print(json.dumps({'sealed': str(OUT.relative_to(ROOT)), 'records': len(records), **kinds, 'diagnostic': DIAGNOSTIC}))


if __name__ == '__main__':
    main()
