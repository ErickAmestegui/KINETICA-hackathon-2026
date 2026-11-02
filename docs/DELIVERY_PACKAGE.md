# Local submission candidates — packaging and verification

The actual previous checkpoint is `dcc27fd348563efbc2183c08207610aa09440690`. The previous audit archive is named **`KINETICA-final-audit-dcc27fd.zip`**, not `...-dc27fd.zip`. Its inventory has 23 files, 881,616 uncompressed bytes and 74,170 archive bytes. It contains reports, historical test logs, browser snapshots and one audit script; it has no complete backend/frontend source, dependency lockfiles, built studio or source media. **It is audit evidence, not an executable project or a full submission. Do not publish that private audit archive as the project.**

The release tooling prepares two different local candidates. Neither tool publishes anything, submits a form, accepts a contract, installs dependencies or makes a Meta request.

| Candidate | Included | Purpose |
|---|---|---|
| `KINETICA-public-repository-candidate-<HEAD>-<inventory>.zip` | Application/backend/frontend source, tests, exact lockfiles, documentation/licenses and versionable sanitized saved-SAM demo | Review the exact tree proposed for a future authorized public GitHub repository |
| `KINETICA-submission-review-kit-<HEAD>-<inventory>.zip` | Same project and demo, built frontend with third-party notices, plus explicitly selected final video/subtitle files | Rehearse/review the complete local demonstration and recording before any upload |

The public candidate's exported `.gitignore` explicitly allows its single licensed demo MP4. All other original media/data, `.env`, credentials, account/browser snapshots, raw provider responses, private runtime logs, Git history, node_modules, virtualenv and caches are excluded. Original workspace inputs are read only. User-home paths are replaced only in exported text copies; the original source files are not rewritten by packaging.

## Build and verify the candidates

From the original project root, after the final production build and final tests:

```powershell
node scripts/inspect_frontend_bundle.mjs
.\.venv\Scripts\python.exe scripts/collect_frontend_notices.py
.\.venv\Scripts\python.exe scripts/build_submission_package.py
# Include ONLY reviewed final files when available, for example:
.\.venv\Scripts\python.exe scripts/build_submission_package.py --video output/submission-video/KINETICA-Reality-Lab-demo-1080p.mp4 --video output/submission-video/kinetica-demo.en.srt --video output/submission-video/kinetica-demo.es.srt
.\.venv\Scripts\python.exe scripts/build_submission_package.py --verify output/submission-package/EXACT_CANDIDATE_NAME.zip
.\.venv\Scripts\python.exe scripts/verify_submission_package.py --archive output/submission-package/EXACT_REVIEW_KIT_NAME.zip --port 8001
```

The video arguments are examples, not claims that files with those names already exist. Pass the actual reviewed output paths. Output is under ignored `output/submission-package/`; filenames are content-addressed, so another candidate does not overwrite earlier evidence. ZIP timestamps and ordering are fixed for reproducibility. `PACKAGE_MANIFEST.json` records source HEAD, dirty-worktree status, byte counts and SHA-256 for every payload file. Final candidates should be rebuilt from the final clean checkpoint and verified again.

The scanner compares against configured secret bytes without printing them and rejects common credential patterns, private user paths, dotenv files and unsafe archive paths, including Windows drives/UNC/backslashes/reserved names. Only allowlisted source/output files are included. A scanner does not prove that video pixels contain no private text: review the final recording visually too. License-inventory asset hashes must match the built frontend or the builder stops.

`inspect_frontend_bundle.mjs` uses the locally installed Vite dependency to regenerate the module list in memory with `write:false`; it never overwrites the production build. `collect_frontend_notices.py` consumes that list, using only modules with positive `renderedLength`. It uses the verified vendored Fiber license when the original download is absent. The final inspected bundle contains 17 dependency packages plus Vite/Rollup helpers; all 19 have retained license text, including the exact upstream Fiber 9.3.0 license. Full notices and asset hashes are under `docs/licenses/`. Dependency binaries are not distributed. If imports/dependencies change, regenerate the emitted-module list rather than assuming the old inventory applies.

## Restore the portable real-evidence demonstration

The exported `demo/` contains the actual SAM input clip, sanitized project, matching metadata and `PROVENANCE.json`. Its 300 geometry records are unchanged from the original saved response. Only private telemetry and irrelevant original project fields were removed; public media naming and explicit real-source provenance were added. The same original video ID and diagnostic are retained because they join the source and known-cut guard. There are 150 boxes and 150 contours, three IDs and 50 frames — not 300 distinct objects.

In an extracted kit, with Python dependencies already available:

```powershell
python scripts/prepare_review_demo.py --prepare-only
python scripts/replay_reality_lab.py --project demo/kinetica-review-project.json --object-id 2 --confirm-slider --freeze-frame 29 --horizon 8
python scripts/prepare_review_demo.py --port 8001
```

Use the actual Python interpreter/virtualenv where required packages are installed. A clean computer needs Python 3.12 and the exact `backend/requirements-lock.txt`; installation needs a local wheel cache or network. This source distribution does **not** claim to include an offline zero-install runtime. The public source candidate also needs `npm ci` and `npm run build` before serving; the review kit already includes that production frontend. No new application dependency was added for release packaging.

The restoration helper verifies media, metadata and sanitized-project hashes, then creates only the expected `data/<video-id>/` files in the extracted tree. Existing files with different content are refused, not overwritten. The server child inherits an empty `MODEL_API_KEY` and `META_ALLOW_PAID=false`, serves only on loopback, and does not modify operator `.env` files. Open `http://127.0.0.1:8001`, then **My machines → Open project JSON → demo/kinetica-review-project.json**.

For the full browser fixtures in a clean extracted kit, first install the exact development requirements (including the existing `imageio-ffmpeg` fixture dependency), then run `python scripts/prepare_review_demo.py --prepare-only --prepare-tests`. This generates visibly **SYNTHETIC TEST** footage/project data locally with the existing scripts and does not make an HTTP/Meta call. Synthetic fixture geometry is never presented as authentic SAM. The unrelated optional 24-manual-annotation full-video diagnostic is intentionally not distributed; its optional browser case may skip in a clean kit and must be reported as such. Do not claim the original workspace's complete browser total applies unchanged to a clean installation.

Confirm slider #2 after inspection. Freeze29/horizon8 reproduces 9.1046/23.9297/75.5859 px on the same eight observations. Horizon20 invalidates all scores across the known source change. The replay is retrospective and SAM used full-video context. Break Reality is a counterfactual simulation; Ask is explicitly `deterministic_mock`. Muse's failed trial remains unverified, with original cause/consumption unknown. The forensic `audit_hackathon_evidence.py` intentionally requires the private originals and is not the portable kit's reproduction command.

## Rights, official links and final authorization

The Commons source hash and all 50 clip-frame transformations are now documented in [RELEASE_RIGHTS.md](RELEASE_RIGHTS.md), [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) and `docs/evidence/media-lineage.json`. The clip/derived media retain CC BY-SA 4.0, required credits and change notices; original code remains separately MIT. The public-source candidate can be reviewed locally before permission to publish. The organizer's broad grant/ownership declarations still require participant review; verified CC permission must not be described as unrestricted sole ownership.

The authenticated form requires a **public GitHub repository URL** and a **three-minute demo-video URL**, plus its actual required textual/team fields. A ZIP alone does not satisfy those URL fields. Public URLs, entrant-specific declarations and final submission remain pending the user's authorization and review. No generated archive is an entry receipt or a claim of acceptance/eligibility. See the final checklist for ready items, authorization gates and any official requirement still unconfirmed.
