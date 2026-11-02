"""Release-tool safeguards only. Fake inputs never establish real SAM evidence."""
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from scripts import build_submission_package as package
from scripts import prepare_review_demo as restore


def test_release_scanner_rejects_secret_without_disclosing_it(monkeypatch):
    sentinel = b'SYNTHETIC-CONFIGURED-SECRET-DO-NOT-PUBLISH'
    monkeypatch.setattr(package, 'known_secrets', lambda: [sentinel])
    with pytest.raises(ValueError) as caught:
        package.scan({'README.md': b'prefix ' + sentinel})
    assert sentinel.decode() not in str(caught.value)
    assert 'configured-secret' in str(caught.value)


@pytest.mark.parametrize('name', ['../outside.txt', '.env', '.git/config', 'frontend/node_modules/key.txt',
                                 'C:/outside.txt', '..\\outside.txt', '\\\\server\\share\\file.txt', 'docs/CON.txt'])
def test_release_scanner_rejects_forbidden_archive_paths(name, monkeypatch):
    monkeypatch.setattr(package, 'known_secrets', lambda: [])
    with pytest.raises(ValueError):
        package.scan({name: b'harmless synthetic test'})


def test_release_archive_verification_detects_tampering(tmp_path, monkeypatch):
    monkeypatch.setattr(package, 'known_secrets', lambda: [])
    entry = b'Explicit synthetic packaging test; no live inference.'
    archive = tmp_path / 'candidate.zip'
    manifest = {'files': {'README.md': {'sha256': hashlib.sha256(entry).hexdigest(), 'bytes': len(entry)}},
                'package_kind': 'synthetic-test-only'}
    with zipfile.ZipFile(archive, 'w') as bundle:
        bundle.writestr('PACKAGE_MANIFEST.json', json.dumps(manifest))
        bundle.writestr('README.md', entry)
    assert package.verify(archive)['verified'] is True
    with zipfile.ZipFile(archive, 'w') as bundle:
        bundle.writestr('PACKAGE_MANIFEST.json', json.dumps(manifest))
        bundle.writestr('README.md', b'changed after scan')
    with pytest.raises(ValueError, match='hash mismatch'):
        package.verify(archive)


def test_review_restore_rejects_existing_different_data(tmp_path, monkeypatch):
    monkeypatch.setattr(restore, 'ROOT', tmp_path)
    demo = tmp_path / 'demo'
    demo.mkdir()
    identity = 'a' * 32
    project = json.dumps({'video': {'id': identity, 'extension': '.mp4'}}).encode()
    metadata = b'{"synthetic_test_only":true}'
    media = b'SYNTHETIC-BYTES-NOT-VALID-VIDEO'
    (demo / 'kinetica-review-project.json').write_bytes(project)
    (demo / 'metadata.json').write_bytes(metadata)
    (demo / 'eitech-sam-input-50.mp4').write_bytes(media)
    (demo / 'PROVENANCE.json').write_text(json.dumps({
        'source_clip_sha256': hashlib.sha256(media).hexdigest(),
        'sanitized_project_sha256': hashlib.sha256(project).hexdigest(),
        'metadata_sha256': hashlib.sha256(metadata).hexdigest()}))
    assert restore.prepare() == 'demo/kinetica-review-project.json'
    target = tmp_path / 'data' / identity / 'source.mp4'
    target.write_bytes(b'pre-existing different private data')
    with pytest.raises(ValueError, match='refusing to overwrite'):
        restore.prepare()
    assert target.read_bytes() == b'pre-existing different private data'


def test_source_copy_removes_user_paths_without_altering_input(monkeypatch):
    synthetic_home = 'C:' + '/Users/' + 'test-reviewer'
    monkeypatch.setattr(package.Path, 'home', lambda: Path(synthetic_home))
    original = ('Project ' + synthetic_home + '/Documents/KINETICA/file.py\r\n').encode()
    exported = package.export_text(original)
    assert b'test-reviewer' not in exported
    assert b'<USER_HOME>/Documents/KINETICA/file.py' in exported
    assert original.endswith(b'\r\n')
    other = package.export_text(('D:' + '\\Users\\' + 'another-user' + '\\x.txt').encode())
    assert b'another-user' not in other and b'<USER_HOME>' in other


def test_review_restore_uses_declared_demo_files_and_rejects_unsafe_names(tmp_path, monkeypatch):
    monkeypatch.setattr(restore, 'ROOT', tmp_path)
    demo = tmp_path / 'demo'
    demo.mkdir()
    project = json.dumps({'video': {'id': 'b' * 32, 'extension': '.mp4'}}).encode()
    metadata, media = b'{"synthetic_test_only":true}', b'SYNTHETIC-ORIGINAL-BYTES'
    (demo / 'SYNTHETIC-p.json').write_bytes(project)
    (demo / 'metadata.json').write_bytes(metadata)
    (demo / 'synthetic.mp4').write_bytes(media)
    inventory = {'project_file': 'SYNTHETIC-p.json', 'media_file': 'synthetic.mp4',
                 'source_clip_sha256': hashlib.sha256(media).hexdigest(),
                 'sanitized_project_sha256': hashlib.sha256(project).hexdigest(),
                 'metadata_sha256': hashlib.sha256(metadata).hexdigest()}
    (demo / 'PROVENANCE.json').write_text(json.dumps(inventory))
    assert restore.prepare() == 'demo/SYNTHETIC-p.json'
    assert (tmp_path / 'data' / ('b' * 32) / 'source.mp4').read_bytes() == media
    (demo / 'PROVENANCE.json').write_text(json.dumps({**inventory, 'media_file': '../outside.mp4'}))
    with pytest.raises(ValueError, match='Invalid packaged demo file name'):
        restore.prepare()


def test_original_media_variant_text_drops_third_party_demo_instructions():
    readme = package.original_readme(Path('README.md').read_bytes().decode('utf-8-sig').encode())
    run = readme.split(b'## Current evidence')[0]
    assert b'kinetica-review-project.json' not in run and b'eitech-sam-input-50.mp4' not in run
    assert package.ORIGINAL_PROJECT.encode() in run and b'not** Meta SAM output' in run
    status = package.status_file('public-repository-candidate-original-media')
    assert b'kinetica-review-project.json' not in status and b'Inspect #2' not in status
    assert b'ONLY original synthetic media' in status
    assert b'kinetica-review-project.json' in package.status_file('public-repository-candidate')


def test_public_repo_audit_scans_history_not_only_the_current_tree(tmp_path, monkeypatch):
    import subprocess
    from scripts import audit_public_repo as audit
    monkeypatch.setattr(audit, 'known_secrets', lambda: [])
    repo = tmp_path / 'candidate'
    repo.mkdir()
    run = lambda *a: subprocess.run(['git', '-C', str(repo), *a], check=True, capture_output=True)
    run('init', '-q'); run('config', 'user.email', 'test@users.noreply.github.com'); run('config', 'user.name', 't')
    (repo / 'notes.txt').write_text('token ghp_' + 'A' * 36)
    run('add', '-A'); run('commit', '-q', '-m', 'synthetic leak')
    (repo / 'notes.txt').write_text('clean')
    run('add', '-A'); run('commit', '-q', '-m', 'remove')
    monkeypatch.setattr('sys.argv', ['audit', str(repo)])
    with pytest.raises(SystemExit) as caught:
        audit.main()
    assert caught.value.code == 1


def test_entrant_private_form_drafts_stay_out_of_public_sources():
    assert not package.source_allowed('docs/submission/CANDIDATE_TEXT.md')
    assert not package.source_allowed('docs/submission/FORM_SCHEMA.json')
    assert package.source_allowed('docs/SUBMISSION_FORM.md') and package.source_allowed('README.md')
