"""Audit every object in a candidate public Git repository before publication.

Scans all blobs in all commits (not only the checked-out tree) for configured secrets,
common token formats, private user paths/e-mail, third-party Eitech media and SAM geometry
derived from it. Reports categories and paths only, never matching content. No network.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_submission_package import CLIP_SHA, PROJECT_SHA, SECRET_PATTERNS, known_secrets  # noqa: E402

EXTRA_PATTERNS = {
    'bearer-token': re.compile(rb'(?i)bearer\s+[A-Za-z0-9._~+/-]{24,}'),
    'openai-style-key': re.compile(rb'sk-[A-Za-z0-9_-]{20,}'),
    'assigned-api-key': re.compile(rb'(?i)(?:api[_-]?key|secret|token)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{24,}'),
    'private-user-path': re.compile(rb'(?i)[A-Z]:[\\/]+Users[\\/]+(?!<USER_HOME>)[^\\/\s"\'<>`]+[\\/]'),
    'personal-email': re.compile(rb'(?i)[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com)(?:gmail|hotmail|outlook|yahoo|icloud)\.[a-z]+'),
}
EITECH_SHA = {'a80d4fc0c85b1d4ec747fe2049349cf656579c3e0d02894c4ae437a412665e66', CLIP_SHA, PROJECT_SHA}
MEDIA_MAGIC = {b'\x1aE\xdf\xa3': 'webm/mkv', b'ftyp': 'mp4/mov'}


def git(repo, *args, data=None):
    return subprocess.run(['git', '-C', str(repo), *args], input=data, capture_output=True, check=True).stdout


def objects(repo):
    listing = git(repo, 'rev-list', '--objects', '--all').decode('utf-8').splitlines()
    paths = {}
    for line in listing:
        sha, _, name = line.partition(' ')
        paths.setdefault(sha, set()).add(name)
    kinds = git(repo, 'cat-file', '--batch-check', data='\n'.join(paths).encode()).decode().splitlines()
    return {line.split()[0]: paths[line.split()[0]] for line in kinds if line.split()[1] == 'blob'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--allowed-media', action='append', default=[], help='path of an allowed original media file')
    args = parser.parse_args()
    repo = args.repo.resolve()
    secrets = known_secrets()
    issues, media, sam_geometry = [], [], []
    blobs = objects(repo)
    for sha, names in blobs.items():
        raw = git(repo, 'cat-file', 'blob', sha)
        name = sorted(names)[0]
        if hashlib.sha256(raw).hexdigest() in EITECH_SHA:
            issues.append({'path': name, 'category': 'eitech-media-or-project'})
        if raw[:4] in MEDIA_MAGIC or raw[4:8] == b'ftyp':
            media.append(name)
            if name not in args.allowed_media:
                issues.append({'path': name, 'category': 'unlisted-media'})
        if any(secret in raw for secret in secrets):
            issues.append({'path': name, 'category': 'configured-secret'})
        for category, pattern in {**SECRET_PATTERNS, **EXTRA_PATTERNS}.items():
            # Third-party license notices must keep their authors' copyright addresses.
            if category == 'personal-email' and name.startswith('docs/licenses/'):
                continue
            if pattern.search(raw) and not name.endswith(('build_submission_package.py', 'audit_public_repo.py')):
                issues.append({'path': name, 'category': category})
        # Geometry export = the original diagnostic plus a real record set, not a mention of it.
        if b'e14d21bb8f3c' in raw and raw.count(b'"path"') >= 20:
            sam_geometry.append(name)
            issues.append({'path': name, 'category': 'eitech-sam-geometry'})
    commits = git(repo, 'log', '--all', '--format=%H %an <%ae>').decode().splitlines()
    authors = sorted({line.split(' ', 1)[1] for line in commits})
    refs = git(repo, 'for-each-ref', '--format=%(refname)').decode().split()
    report = dict(repo=repo.name, commits=len(commits), refs=refs, authors=authors, blobs=len(blobs),
                  media=sorted(media), issues=issues, clean=not issues)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if not issues else 1)


if __name__ == '__main__':
    main()
