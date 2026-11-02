"""Collect notices for modules actually rendered in the final Vite bundle.

Input is the local write:false build inventory, not a guessed dependency list.
No packages, executable binaries or network resources are downloaded here.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = json.loads((ROOT / 'output/submission-package/bundled-modules.json').read_text('utf-8'))
    packages = set()
    for row in rows:
        if 'dependency_package' in row:
            if row['dependency_package']:
                packages.add(row['dependency_package'])
            continue
        module = row['module']
        if module.startswith('\0') or ':' in module:
            continue
        packages.add('/'.join(module.split('/')[:2]) if module.startswith('@') else module.split('/')[0])
    # Generated Vite/Rollup runtime helpers are also covered conservatively.
    packages.update({'vite', 'rollup'})
    folder = ROOT / 'docs/licenses'
    supplement = folder / 'REACT_THREE_FIBER_9_3_0.txt'
    upstream = ROOT / 'output/submission-rights/fiber-9.3.0.txt'
    if upstream.is_file():
        supplement.write_bytes(upstream.read_bytes())
    elif not supplement.is_file():
        raise ValueError('Verified vendored Fiber license is missing')
    if hashlib.sha256(supplement.read_bytes()).hexdigest() != '9c35b5de7b7493a707fffe4eb23bd2f7f449153c1911f7c6eefb4e591fd5349a':
        raise ValueError('Fiber license differs from the verified exact-version source')
    sections = ['# KINETICA frontend third-party notices\n\n'
                'Covers packages with renderedLength>0 in the final Vite build, plus Vite/Rollup generated helpers.\n'
                'Inventory obtained by a build with write:false; the served dist was not changed.\n'
                'Dependency binaries/node_modules are not redistributed. Original application code remains MIT.\n'
                'Exact package versions and license-source hashes follow; license text is preserved verbatim.\n']
    inventory = []
    for name in sorted(packages):
        package = ROOT / 'frontend/node_modules' / name
        metadata = json.loads((package / 'package.json').read_text('utf-8'))
        texts = [path for path in package.iterdir() if path.is_file() and
                 path.name.lower().startswith(('license', 'licence', 'notice', 'copying'))]
        sources = []
        if name == '@react-three/fiber':
            if metadata['version'] != '9.3.0':
                raise ValueError('Fiber version changed; verify an exact upstream license')
            texts = [supplement]
            sources.append('https://raw.githubusercontent.com/pmndrs/react-three-fiber/v9.3.0/LICENSE')
        if not texts:
            raise ValueError('Missing bundled-package license text: ' + name)
        header = f'\n\n{"=" * 76}\n{name} {metadata["version"]}\nDeclared license: {metadata.get("license", "see source text")}\n'
        if sources:
            header += 'Verified upstream source: ' + ', '.join(sources) + '\n'
        sections.append(header)
        record = dict(name=name, version=metadata['version'], declared_license=metadata.get('license'),
                      license_files=[], upstream_sources=sources)
        for path in sorted(texts):
            raw = path.read_bytes()
            text = raw.decode('utf-8-sig', errors='strict')
            sections.append(f'\n--- {path.name} ---\n' + text)
            record['license_files'].append({'name': path.name, 'sha256': hashlib.sha256(raw).hexdigest()})
        inventory.append(record)
    (folder / 'THIRD_PARTY_FRONTEND.txt').write_text('\n'.join(sections), encoding='utf-8')
    bundle_hashes = {path.relative_to(ROOT / 'frontend/dist').as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted((ROOT / 'frontend/dist').rglob('*')) if path.is_file()}
    report = dict(schema='kinetica-frontend-license-inventory/1', method='Vite write:false emitted chunks; modules renderedLength>0',
                  added_helper_notices=['vite', 'rollup'], packages=inventory, bundle_assets_sha256=bundle_hashes,
                  excluded_from_bundle=['draco3d', 'maath', 'stats-gl', '@mediapipe/tasks-vision'],
                  excluded_reason='No positive renderedLength module from these installed packages in the inspected bundle')
    (folder / 'FRONTEND_BUNDLE_INVENTORY.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'covered_packages': len(inventory), 'bundle_assets': len(bundle_hashes), 'missing_license_texts': 0}))


if __name__ == '__main__':
    main()
