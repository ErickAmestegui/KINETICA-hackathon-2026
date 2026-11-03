"""Build local public-repository and review candidates from an explicit allowlist.

No upload, publication, installation, inference or credential configuration is
performed. Packaging source does not establish participant eligibility or submit
the official form. Zip inputs are content-addressed; original evidence is read only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CLIP_ID = '3e4c5e12f8b84af0996f02a9dfa89989'
CLIP_SHA = '4e179551a3dde38da847c9392e277331bc93fd1ac28d3524da8a6ca4872a1677'
PROJECT_SHA = 'f4e09b06aa2323348e79b182c598a1f34f57816f65b3eb91b44184d645eff65a'
DIAGNOSTIC = 'e14d21bb8f3c'
TEXT_SUFFIXES = {'.py', '.md', '.txt', '.json', '.ts', '.tsx', '.css', '.html', '.svg', '.cjs', '.mjs', '.ps1', '.srt', '.vtt'}
ROOT_FILES = {'.env.example', '.gitattributes', '.gitignore', 'LICENSE', 'README.md', 'ATTRIBUTIONS.md'}
SOURCE_TREES = {'backend', 'docs', 'sample-data', 'scripts', 'assets'}
BANNED_PARTS = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.playwright-cli', '.playwright-mcp', 'test-results'}
SECRET_PATTERNS = {
    'private-key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github-token': re.compile(rb'gh[pousr]_[A-Za-z0-9]{24,}'),
    'aws-key': re.compile(rb'AKIA[0-9A-Z]{16}'),
    'google-key': re.compile(rb'AIza[0-9A-Za-z_-]{30,}'),
    'jwt-token': re.compile(rb'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{15,}'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False, ensure_ascii=False) + '\n').encode('utf-8')


def known_secrets():
    """Compare exact configured secret bytes without reporting or retaining them."""
    candidates = [os.environ.get('MODEL_API_KEY', '')]
    dotenv = ROOT / '.env'
    if dotenv.is_file():
        for line in dotenv.read_text('utf-8').splitlines():
            match = re.match(r'^\s*(?:export\s+)?MODEL_API_KEY\s*=\s*(.*?)\s*$', line)
            if match:
                candidates.append(match[1].strip('"\''))
    return [value.encode() for value in candidates if len(value) >= 8]


def source_allowed(name):
    path = PurePosixPath(name)
    if any(part in BANNED_PARTS for part in path.parts) or (path.name.startswith('.env') and path.name != '.env.example'):
        return False
    if name in ROOT_FILES:
        return True
    # Entrant-private form drafts and proposed survey answers are not repository content.
    if path.parts[:2] == ('docs', 'submission'):
        return False
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    if path.parts[0] in SOURCE_TREES:
        return True
    if path.parts[0] == 'tests':
        return path.suffix in {'.py', '.json'}
    if path.parts[0] == 'frontend':
        return len(path.parts) == 2 or path.parts[1] in {'src', 'e2e', 'public'}
    return False


def export_text(raw):
    """Remove user-home paths from exported copies only; code behavior unchanged."""
    text = raw.decode('utf-8-sig')
    home = str(Path.home())
    for prefix in {home, home.replace('\\', '/'), home.replace('\\', '\\\\')}:
        text = text.replace(prefix, '<USER_HOME>')
    # Historical documents can contain the original workstation path.
    text = re.sub(r'[A-Z]:[/\\]+Users[/\\]+[^/\\\s`\'"<>]+(?=[/\\])', '<USER_HOME>', text, flags=re.IGNORECASE)
    return text.replace('\r\n', '\n').encode('utf-8')


def scan(entries):
    issues = []
    secrets = known_secrets()
    for name, raw in entries.items():
        path = PurePosixPath(name)
        reserved = {'con', 'prn', 'aux', 'nul'} | {prefix + str(number) for prefix in ('com', 'lpt') for number in range(1, 10)}
        if (not name or path.is_absolute() or '\\' in name or ':' in name or '..' in path.parts
                or any(part in BANNED_PARTS for part in path.parts)
                or any(part.endswith((' ', '.')) or part.split('.')[0].lower() in reserved for part in path.parts)):
            issues.append({'file': name, 'category': 'forbidden-path'})
        if path.name.startswith('.env') and path.name != '.env.example':
            issues.append({'file': name, 'category': 'dotenv-file'})
        if any(secret in raw for secret in secrets):
            issues.append({'file': name, 'category': 'configured-secret'})
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in ROOT_FILES:
            for category, pattern in SECRET_PATTERNS.items():
                if pattern.search(raw):
                    issues.append({'file': name, 'category': category})
            if re.search(rb'[A-Z]:[\\/]+Users[\\/]+[^\\/\s]+', raw, re.IGNORECASE):
                issues.append({'file': name, 'category': 'private-user-path'})
    if issues:
        # Deliberately omit matching contents and exception text from the report.
        raise ValueError(json.dumps({'scan_failed': issues}))


def source_entries():
    output = subprocess.check_output(['git', 'ls-files', '-c', '-o', '--exclude-standard', '-z'], cwd=ROOT)
    names = sorted(set(output.decode('utf-8').split('\0')) - {''})
    entries = {}
    for name in names:
        if source_allowed(name):
            path = ROOT / name
            if not path.is_file() or path.is_symlink():
                raise ValueError('Source entry must be a regular file: ' + name)
            path.resolve().relative_to(ROOT.resolve())
            entries[name] = export_text(path.read_bytes())
    required = ['backend/main.py', 'backend/requirements-lock.txt', 'frontend/package-lock.json',
                'frontend/src/RealityLab.tsx', 'LICENSE', 'README.md', 'docs/licenses/SAM-LICENSE.txt']
    if not all(name in entries for name in required):
        raise ValueError('Required source/lock/license file missing')
    return entries


def saved_demo():
    project_path = ROOT / 'output/kinetica-project.json'
    original = project_path.read_bytes()
    if sha(original) != PROJECT_SHA:
        raise ValueError('Original saved project changed')
    project = json.loads(original)
    video = project['video']
    if video['id'] != CLIP_ID:
        raise ValueError('Original SAM source identity changed')
    media_path = ROOT / 'data' / CLIP_ID / 'source.mp4'
    media = media_path.read_bytes()
    if sha(media) != CLIP_SHA:
        raise ValueError('Original SAM input media changed')
    result = project['samResult']
    if result.get('simulated') or result['outcome']['status'] != 'completed' or result['diagnostic']['id'] != DIAGNOSTIC:
        raise ValueError('Only original completed real SAM evidence is permitted')
    records = result['records']
    if len(records) != 300:
        raise ValueError('Original SAM geometry count changed')
    allowed_fields = {'kind', 'object_id', 'frame', 'confidence', 'left', 'top', 'right', 'bottom', 'path', 'bounds', 'width', 'height'}
    if any(set(record) - allowed_fields for record in records):
        raise ValueError('Unexpected geometry fields require manual review')
    clean_result = dict(records=records, simulated=False, outcome={'status': 'completed'}, diagnostics=[],
                        provenance='Saved real Meta sam-3.1 geometry; parsed by meta-sam-parser 0.1.0',
                        reconstruction_verified=False, diagnostic={'id': DIAGNOSTIC},
                        remote_file_cleanup='deleted', retry_performed=False)
    metadata_keys = ('fps', 'frames', 'width', 'height', 'duration', 'timestamps', 'timing', 'id', 'extension', 'bytes')
    metadata = {key: video[key] for key in metadata_keys}
    metadata['name'] = 'eitech-sam-input-50.mp4'
    clean = dict(schema='kinetica/1', name='KINETICA — saved real SAM review', parameters=project['parameters'],
                 calibration=project['calibration'], observations=[], regions=[], sam=records, samResult=clean_result,
                 video={**metadata, 'provenance': 'real'}, proposal=None,
                 aiEvidence=[dict(action='sam', result=clean_result)],
                 fitNote='Declared geometry; no physical calibration. Retrospective saved-data replay.',
                 lost=[], trainedFrames=[], labPreferences={'freezeFrame': 29, 'horizon': 20, 'alternate': None})
    clean_bytes = json_bytes(clean)
    metadata_bytes = json_bytes(metadata)
    provenance = dict(schema='kinetica-review-evidence/1', original_export_sha256=PROJECT_SHA,
                      source_clip_sha256=CLIP_SHA, sanitized_project_sha256=sha(clean_bytes),
                      metadata_sha256=sha(metadata_bytes),
                      records_sha256=sha(json.dumps(records, sort_keys=True).encode()),
                      records_unchanged=True, records=300, boxes=150, contours=150, objects=3, frames=50,
                      diagnostic_id=DIAGNOSTIC, new_inference_performed=False,
                      removed=['provider usage', 'provider/file identifiers', 'raw diagnostics/events',
                               'original project name/timestamp', 'duplicated private operation telemetry'],
                      changed=['sanitized portable project title', 'explicit real-source provenance',
                               'public media filename; original local video identity retained'],
                      methods={'SAM': 'saved_real_Meta_sam-3.1', 'Predict': 'retrospective local fit/replay',
                               'Break': 'counterfactual solver simulation', 'Ask': 'deterministic_mock',
                               'Muse': 'failed d25cbc08d7c2; live unverified; cause/usage unknown'},
                      credit='Schubkurbelgetriebe (Eitech), Rhetos, CC BY-SA 4.0, Wikimedia Commons; converted/cropped and annotated.',
                      source_url='https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm',
                      license_url='https://creativecommons.org/licenses/by-sa/4.0/',
                      limits=['segmentation is not joint-center detection', 'full-video SAM context',
                              'previously inspected dataset', 'no independent physical/prospective validation'])
    demo_readme = '''# Saved real SAM demonstration

This versionable demonstration contains authentic saved SAM geometry and its known-hash
licensed input clip. It is not synthetic and makes no new Meta request. See PROVENANCE.json
for source hashes, retained fields, sanitization and explicit scientific limits.

Media: Schubkurbelgetriebe (Eitech), Rhetos, CC BY-SA4.0, via Wikimedia Commons.
https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm
https://creativecommons.org/licenses/by-sa/4.0/
Changes: source frames150–199, scaling to960x540, H264 conversion; SAM overlays/annotations
are derived presentation. Retain credit/source/license and mark changes. The full media
license is in ../docs/licenses/CC-BY-SA-4.0.txt. Original application code has a separate MIT
license. Parser code/documentation fixtures retain the separate SAM License.

Run python scripts/prepare_review_demo.py --prepare-only before opening the project JSON.
The helper restores source.mp4/metadata under data/ without overwriting different files.
Then build the frontend if needed and run python scripts/prepare_review_demo.py --port 8001.
The child server disables paid inference.

Publication still requires user approval. Official entrant ownership/license declarations
need participant review; a verified CC license is not a claim of unrestricted ownership.
'''
    return {'demo/kinetica-review-project.json': clean_bytes, 'demo/metadata.json': metadata_bytes,
            'demo/eitech-sam-input-50.mp4': media, 'demo/PROVENANCE.json': json_bytes(provenance),
            'demo/README.md': demo_readme.encode('utf-8')}


ORIGINAL_DIR = ROOT / 'output/original-demo'
ORIGINAL_MEDIA = 'kinetica-original-synthetic-slider-crank.mp4'
ORIGINAL_PROJECT = 'SYNTHETIC-original-demo-project.json'


def original_demo():
    """Rights-clean variant: only footage and geometry generated by this repository."""
    project = json.loads((ORIGINAL_DIR / ORIGINAL_PROJECT).read_text('utf-8'))
    generated = json.loads((ORIGINAL_DIR / 'provenance.json').read_text('utf-8'))
    media = (ORIGINAL_DIR / ORIGINAL_MEDIA).read_bytes()
    video = project['video']
    if sha(media) != generated['clip_sha256'] or sha((ROOT / 'data' / video['id'] / 'source.mp4').read_bytes()) != generated['clip_sha256']:
        raise ValueError('Original synthetic clip differs from its generation record')
    result = project['samResult']
    if not result.get('simulated') or video.get('provenance') != 'synthetic' or generated['third_party_material'] or generated['inference_performed']:
        raise ValueError('Original variant must contain only labeled synthetic material')
    metadata_keys = ('fps', 'frames', 'width', 'height', 'duration', 'timestamps', 'timing', 'id', 'extension', 'bytes', 'name')
    metadata = {key: video[key] for key in metadata_keys if key in video}
    clean = {**project, 'video': {**metadata, 'provenance': 'synthetic'},
             'labPreferences': {'freezeFrame': 74, 'horizon': 20, 'alternate': None}}
    clean_bytes = json_bytes(clean)
    metadata_bytes = json_bytes(metadata)
    records = result['records']
    provenance = dict(schema='kinetica-review-evidence/1', variant='original-media',
                      media_file=ORIGINAL_MEDIA, project_file=ORIGINAL_PROJECT,
                      source_clip_sha256=generated['clip_sha256'], sanitized_project_sha256=sha(clean_bytes),
                      metadata_sha256=sha(metadata_bytes), records_sha256=sha(json.dumps(records, sort_keys=True).encode()),
                      records=len(records), synthetic=True, sam_output=False, third_party_material=False,
                      new_inference_performed=False, generator=generated,
                      restore_message='SYNTHETIC original demo restored: rendered by scripts/make_original_demo_clip.py; geometry derived from known motion, not SAM.',
                      separate_real_evidence='The real Meta SAM 3.1 run (diagnostic e14d21bb8f3c, 300 records) used third-party footage that this variant does not distribute; see docs/RELEASE_RIGHTS.md.',
                      limits=['synthetic footage, not a real recording', 'geometry derived from known ground truth plus noise, not segmentation',
                              'replay checks the pipeline; it is not evidence about real mechanisms'])
    demo_readme = f'''# Original synthetic demonstration

Everything in this folder was generated by this repository: the clip is rendered by
scripts/make_original_demo_clip.py and every frame is labeled "ORIGINAL SYNTHETIC CLIP".
The saved geometry is derived from the clip's known motion plus measurement noise. It is
NOT Meta SAM output and is marked simulated/synthetic in the project JSON. No third-party
footage is included and no inference was performed. See PROVENANCE.json for hashes.

Meta SAM 3.1 really ran on separate third-party footage, Schubkurbelgetriebe (Eitech) by
Rhetos (Wikimedia Commons, CC BY-SA 4.0): diagnostic e14d21bb8f3c, 300 records. That footage
and its geometry are kept as separate historical evidence and are not distributed here.
Synthetic metrics are not validation on real footage. Live Muse Spark remains unverified.

Run python scripts/prepare_review_demo.py --port 8001, open {ORIGINAL_PROJECT},
pick SYNTHETIC-SLIDER, freeze after frame 74 with horizon 20, then reveal.
'''
    return {f'demo/{ORIGINAL_PROJECT}': clean_bytes, 'demo/metadata.json': metadata_bytes,
            f'demo/{ORIGINAL_MEDIA}': media, 'demo/PROVENANCE.json': json_bytes(provenance),
            'demo/README.md': demo_readme.encode('utf-8')}


ORIGINAL_README_RUN = f'''## Run the Reality Lab demo (about 10 minutes, no API key)

> **Media variant: original material only.** This repository ships no third-party footage. The demo clip is an original synthetic rendering generated by `scripts/make_original_demo_clip.py`, labeled on every frame. Its saved geometry is derived from the known motion plus noise and is **not** Meta SAM output.

Windows PowerShell, Python 3.12 and Node.js 22.12+/24, from the repository root:

```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r backend/requirements-lock.txt
Set-Location frontend; npm.cmd ci; npm.cmd run build; Set-Location ..
.\\.venv\\Scripts\\python.exe scripts/prepare_review_demo.py --port 8001
```

Open http://127.0.0.1:8001, then **My machines → Open project JSON → `demo/{ORIGINAL_PROJECT}`** and the **Reality Lab** tab:

1. **Observe** — the original synthetic clip and its synthetic geometry (the Reality Lab badge reads **SYNTHETIC TEST**; the Compare overlay's generic "SAM #" box prefix does not make this geometry SAM output). Pick **SYNTHETIC-SLIDER** and confirm it.
2. **Predict** — freeze after frame **74**, horizon **20**. The model assumes constant motor speed; the hidden truth contains a speed ripple.
3. **Reveal** — model **7.67 px** vs constant **52.05 px** and linear **129.82 px** RMSE on the same twenty saved observations. Freezing at frame **49** is refused: timing is not identifiable from fewer than 1.25 observed cycles.
4. **Break Reality** — change geometry; both 3D machines are driven by the constraint solver, impossible strokes are rejected.
5. **Ask the Machine** — **Interpret locally (mock)**: a deterministic, visibly labeled mock proposes a change you must confirm. It is not Muse inference.

**Evidence status — read this first.**

- **Meta SAM 3.1 really ran** on a 2-second excerpt of third-party footage, *Schubkurbelgetriebe (Eitech)* by Rhetos ([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm), CC BY-SA 4.0): diagnostic e14d21bb8f3c, 300 geometry records = 150 boxes + 150 contours, three object IDs over 50 frames. That footage and its geometry are kept as separate historical evidence and are **not distributed** in this repository; the results are documented in `docs/` (for example [MASK_MOTION.md](docs/MASK_MOTION.md) and [REALITY_LAB.md](docs/REALITY_LAB.md)), not reproducible from it.
- **The demo clip and demo video are synthetic**, rendered by KINETICA's own code (`scripts/make_original_demo_clip.py`), and labeled on every frame. Their saved geometry is derived from the known motion plus noise; it is not SAM output.
- **Synthetic metrics are not validation on real footage.** The 7.67 px replay checks the pipeline against a known ground truth; it says nothing about accuracy on real recordings.
- **Live Muse Spark remains unverified.** The one real trial (d25cbc08d7c2) failed; Ask the Machine is a deterministic, labeled mock.

'''


def original_readme(raw):
    text = raw.decode('utf-8')
    start = text.index('## Run the Reality Lab demo')
    end = text.index('## Current evidence')
    text = text[:start] + ORIGINAL_README_RUN + text[end:]
    if '**Prepared release packages:**' in text:
        packaged = text.index('**Prepared release packages:**')
        text = text[:packaged] + ('**Original-media variant:** this repository does not include the third-party clip or its saved SAM geometry, '
                                  'so the workspace-only steps below cannot be reproduced from it. Use the synthetic demo above.') + text[text.index('\n', packaged):]
    elif '**Original-media variant:**' not in text:
        raise ValueError('README has neither the release-package note nor the original-media note')
    return text.encode('utf-8')


def status_file(kind):
    text = licensed_status(kind)
    if not kind.endswith('-original-media'):
        return text
    raw = text.decode('utf-8')
    start = raw.index('Open http://127.0.0.1:8001')
    end = raw.index('but omit the production build/final video.')
    replacement = f'''Open http://127.0.0.1:8001, My machines → Open project JSON → demo/{ORIGINAL_PROJECT}.
This variant contains ONLY original synthetic media generated by this repository; every frame
is labeled synthetic and its geometry is derived from known motion, not SAM. Pick
SYNTHETIC-SLIDER, freeze 74 / horizon 20: model 7.67 px vs constant 52.05 px and linear
129.82 px. Break Reality is calculated simulation; Ask the Machine is deterministic_mock.
The real SAM 3.1 run (e14d21bb8f3c) used third-party footage not distributed here.

Public-repository candidates include the original synthetic clip and its labeled geometry,
'''
    return (raw[:start] + replacement + raw[end:]).encode('utf-8')


def licensed_status(kind):
    return f'''# KINETICA — {kind}

This is a LOCAL REVIEW CANDIDATE, not a submitted entry or an authorized public release.
The old KINETICA-final-audit-dcc27fd.zip is an audit-only collection, not this project.

Official form requires a public GitHub repository URL and a three-minute demo video URL.
Those publication URLs and final submission require the user's separate authorization.
Participant identity, eligibility and required form opinions/consents must be reviewed.

## Run locally

Source and lockfiles are included; dependency binaries are intentionally not bundled.
Use Python 3.12 and the existing environment, or install the exact backend lockfile in a
new virtualenv. That first dependency installation needs a local wheel cache or network;
the package does NOT claim a zero-install offline bootstrap on a clean computer.
Node is required only to rebuild the frontend; the review kit already has a built frontend.
Do not copy any operator .env into the candidate. Inference is not needed for the demo.

PowerShell, from the extracted review-kit root with dependencies available:

    python scripts/prepare_review_demo.py --port 8001

The launcher restores only the packaged known-hash clip/metadata, refuses to overwrite
different existing data, clears the child process API key, forces META_ALLOW_PAID=false,
    and binds uvicorn to 127.0.0.1. It never makes provider calls or modifies .env.
Open http://127.0.0.1:8001, My machines → Open project JSON → demo/kinetica-review-project.json.
Inspect #2 and confirm slider identity. Cutoff29/horizon20 correctly invalidates scores;
reset to horizon8 for9.1046/23.9297/75.5859px on the same eight observed frames.
Break Reality is calculated simulation. Ask the Machine is explicitly deterministic_mock.
Muse real remains unverified after a failed attempt; no new inference was made.

For CLI replay: python scripts/prepare_review_demo.py --prepare-only, then:
python scripts/replay_reality_lab.py --project demo/kinetica-review-project.json --object-id 2 --confirm-slider --freeze-frame 29 --horizon 8

Public-repository candidates include the licensed demo clip and sanitized saved geometry,
but omit the production build/final video. Build and test instructions are in README;
tests with synthetic data remain explicitly synthetic.
The original strict forensic audit command expects private originals and is documented
as workspace-only; use the portable replay and packaged provenance for this review kit.

## Rights and safeguards

Review ATTRIBUTIONS.md, docs/RELEASE_RIGHTS.md and docs/licenses before redistribution.
Media keeps CC BY-SA4.0 separately from MIT original application code. No credentials,
raw provider responses, private operation logs, browser/account snapshots, dependency
binaries or Git history are included. Package scan is best-effort, not a substitute for
visual review of recorded video or participant contract review.

PACKAGE_MANIFEST.json lists every file hash, source checkpoint and known release gates.
Verify the archive with: python scripts/build_submission_package.py --verify PATH_TO_ZIP
'''.encode('utf-8')


def archive(entries, kind, head, dirty, destination):
    scan(entries)
    files = {name: {'sha256': sha(raw), 'bytes': len(raw)} for name, raw in sorted(entries.items())}
    manifest = dict(schema='kinetica-submission-package/1', package_kind=kind,
                    source_head=head, source_worktree_dirty=dirty, publication_authorized=False,
                    entry_submitted=False, new_inference_performed=False,
                    contains_credentials=False, contains_raw_provider_responses=False,
                    contains_dependency_binaries=False, files=files,
                    official_public_urls_pending=True, final_entrant_review_pending=True)
    manifest_bytes = json_bytes(manifest)
    fingerprint = sha(manifest_bytes)[:12]
    path = destination / f'KINETICA-{kind}-{head[:7]}-{fingerprint}.zip'
    if path.exists():
        verify(path)
        return path
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, raw in sorted({**entries, 'PACKAGE_MANIFEST.json': manifest_bytes}.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, raw)
    verify(path)
    return path


def verify(path):
    with zipfile.ZipFile(path) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('Zip CRC check failed')
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive path')
        manifest_raw = bundle.read('PACKAGE_MANIFEST.json')
        manifest = json.loads(manifest_raw)
        expected = set(manifest['files']) | {'PACKAGE_MANIFEST.json'}
        if set(names) != expected:
            raise ValueError('Archive inventory differs from manifest')
        entries = {}
        for name, entry in manifest['files'].items():
            raw = bundle.read(name)
            if sha(raw) != entry['sha256'] or len(raw) != entry['bytes']:
                raise ValueError('Archive file hash mismatch: ' + name)
            entries[name] = raw
        scan({**entries, 'PACKAGE_MANIFEST.json': manifest_raw})
    return {'path': path.name, 'sha256': sha(path.read_bytes()),
            'bytes': path.stat().st_size, 'files': len(names), 'verified': True,
            'package_kind': manifest['package_kind']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--video', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, default=ROOT / 'output/submission-package')
    parser.add_argument('--variant', choices=('licensed', 'original'), default='licensed',
                        help='original: ship only repository-generated synthetic media, no third-party footage')
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify.resolve()), indent=2))
        return
    output = args.output.resolve()
    output.relative_to((ROOT / 'output').resolve())
    output.mkdir(exist_ok=True, parents=True)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    entries = source_entries()
    suffix = '' if args.variant == 'licensed' else '-original-media'
    if args.variant == 'licensed':
        entries.update(saved_demo())
        # The reviewable public candidate must retain its explicitly licensed demo clip
        # when a future authorized publication imports this tree into Git.
        entries['.gitignore'] += b'\n# Explicit licensed release-demo media; publication still needs approval.\n!demo/eitech-sam-input-50.mp4\n'
    else:
        entries.update(original_demo())
        entries['README.md'] = original_readme(entries['README.md'])
        entries['.gitignore'] += f'\n# Original synthetic release-demo media.\n!demo/{ORIGINAL_MEDIA}\n'.encode()
    entries['PACKAGE_STATUS.md'] = status_file('public-repository-candidate' + suffix)
    public = archive(entries, 'public-repository-candidate' + suffix, head, dirty, output)
    review = dict(entries)
    review['PACKAGE_STATUS.md'] = status_file('submission-review-kit' + suffix)
    notices = ROOT / 'docs/licenses/THIRD_PARTY_FRONTEND.txt'
    if not notices.is_file():
        raise ValueError('Production bundle needs its third-party notices first')
    license_inventory = json.loads((ROOT / 'docs/licenses/FRONTEND_BUNDLE_INVENTORY.json').read_text('utf-8'))
    actual_assets = {path.relative_to(ROOT / 'frontend/dist').as_posix(): sha(path.read_bytes())
                     for path in sorted((ROOT / 'frontend/dist').rglob('*')) if path.is_file()}
    if actual_assets != license_inventory['bundle_assets_sha256']:
        raise ValueError('Production build differs from license inventory; refresh bundle notices inventory')
    for path in sorted((ROOT / 'frontend/dist').rglob('*')):
        if path.is_file():
            name = path.relative_to(ROOT).as_posix()
            if path.suffix not in {'.js', '.css', '.html', '.svg'}:
                raise ValueError('Unexpected production asset requires review: ' + name)
            review[name] = path.read_bytes()
    if 'frontend/dist/index.html' not in review:
        raise ValueError('Production frontend missing')
    for path in args.video:
        path = path.resolve()
        path.relative_to((ROOT / 'output').resolve())
        if path.suffix not in {'.mp4', '.srt', '.vtt', '.md', '.json', '.txt'} or not path.is_file():
            raise ValueError('Only explicitly selected final video/subtitle metadata may be included')
        review['video/' + path.name] = path.read_bytes()
    kit = archive(review, 'submission-review-kit' + suffix, head, dirty, output)
    print(json.dumps({'public_repository_candidate': verify(public), 'submission_review_kit': verify(kit),
                      'publication_performed': False, 'entry_submitted': False}, indent=2))


if __name__ == '__main__':
    main()
