# Final release validation — 2 November 2026

## Update — original-media submission release

The entrant chose the **original-media** release for the submission. This repository contains only material of documented authorship: an original synthetic clip rendered by `scripts/make_original_demo_clip.py` (labeled synthetic on every frame) with geometry derived from its known motion, not SAM output. The Eitech excerpt and its 300 real SAM 3.1 records are kept separately as historical evidence and are not distributed here; the sections below describe the earlier Eitech-based candidate and remain as history.

- Demo video (original media): 168.16 s, 1920×1080, SHA-256 `4e90552ed457cce48d9f11f1139ddce7d6df98e0f6cc67f70d33a0af645263c2`, −20.2 LUFS, true peak −2.0 dBFS; authentic capture with no page errors and no blocked or paid requests. Reviewed end to end: every chapter matches its narration; the real Meta Model API panel (local estimate, paid inference blocked) is shown; the Compare overlay's generic "SAM #" box prefix is not shown on synthetic data.
- Synthetic replay (freeze 74, horizon 20): model 7.67 px, constant 52.05 px, linear 129.82 px; freeze 49 refused. Reproduced from the extracted review kit on a separate port with paid inference disabled. These figures check the pipeline only; they are not validation on real footage.
- Python suite: 130 passed. Frontend code unchanged since the earlier 23 vitest / 17 E2E / build results.
- Public history audit (`scripts/audit_public_repo.py`): every blob of every commit scanned for configured secrets, token formats, private paths and e-mail, Eitech media and Eitech-derived SAM geometry — clean (one commit, no-reply author).
- Live Muse Spark remains unverified (failed trial d25cbc08d7c2).

Base checkpoint `dcc27fd348563efbc2183c08207610aa09440690`. Environment: Windows, Python 3.12.14 (`.venv`, `pip check` clean), Node 24.22.1, Chrome via Playwright. Local server on 127.0.0.1:8000 with `META_ALLOW_PAID=false`. No Meta request, payment, publication or form submission was made.

## Test results

| Suite | Command | Result |
|---|---|---|
| Python | `.venv\Scripts\python.exe -m pytest tests -q` (TEMP under `output/tmp`) | 127 passed, 1 Starlette deprecation warning |
| TypeScript | `npm test` (frontend) | 23 passed in 7 files |
| Production build | `npm run build` (frontend) | Passed; bundle-size warning (>1.2 MB chunk) |
| Chrome E2E | `npm run test:e2e` (frontend) | 17 passed, none skipped, 2.6 min |

## Failures found and resolved during final preparation

- **Muse diagnostic persistence on Windows.** One synthetic test (`bad-parser`) intermittently left the diagnostic at `request_started` instead of `failed`. A controlled probe reproduced it: Windows denies `Path.replace` (WinError 5) while another process holds the destination open, and the final write was dropped. `backend/muse_trial.py` now retries the atomic replace for up to two seconds on `PermissionError`. New test `test_transient_windows_replace_denial_still_preserves_failed_status` covers it. This touches local diagnostics only; it says nothing about the original incident d25cbc08d7c2, whose cause remains undetermined.
- **Two E2E failures in an earlier run** (`explicit video-time fit…`, `private real SAM replay…`) happened while the video encoder saturated the CPU, and the run was cut off at 15 of 17. The uncontended rerun passed all 17 with no test changes.
- **Video review.** The first master's Observe chapter did not make the SAM masks visible (Reality Lab draws them at 25% opacity over turquoise parts). The capture now opens the existing Compare view, which shows the saved boxes/IDs and the "SAM completed. 300 geometry records" status, before returning to Reality Lab. No UI or value was altered; the first take is kept under `output/submission-video/superseded-v1/`.

- **Public repository hygiene (pre-publication pass).** The builder now excludes entrant-private form drafts (`docs/submission/`, including proposed survey answers) and replaces any Windows user-profile path, not only the original workstation's. The README gained a judge quick start for the bundled `demo/` and lost machine- and agent-specific notes. Covered by `test_entrant_private_form_drafts_stay_out_of_public_sources` and the extended path test. The private Git history (13 commits) holds no keys or tokens, but it does contain local Windows paths and internal working notes, so the public repository starts from a fresh single-commit history built from the verified candidate.

## Final video

`KINETICA-Reality-Lab-demo-1080p.mp4` — 166.16 s, 1920×1080, 25 fps, H.264/yuv420p, AAC; SHA-256 `0d42ea0c12ac49f5cdfb6c8ff62cdc24335eb137b593ec02a06bb341c3e7590a` (caption-balanced render of the same recording; the earlier `cd98d65d…` render is superseded).

Full review (pre-publication pass): contact sheets every 3.5 s across the whole master plus full-resolution frames of each act. Observe shows the saved SAM boxes/IDs and "SAM completed. 300 geometry records"; Reveal shows 9.10 / 23.93 / 75.59 px; the cut horizon shows "No evaluado"; Ask shows "DETERMINISTIC MOCK · MUSE NOT CALLED"; the credit slate carries author, source, license and change notice. No local path, key, e-mail or account screen is visible. Audio: integrated −20.1 LUFS, true peak −2.6 dBFS, longest pause 3.5 s. Captions: 25 English and 25 Spanish cues, valid UTF-8 without BOM, no overlaps, shortest cue 4.4 s, first caption 0.08–0.09 s ahead of speech onset in every chapter. Source clip and project export hashes checked before and after recording (`4e179551…1677`, `f4e09b06…ff65a`). Browser blocked all non-loopback hosts and the Meta catalogue/run routes; zero blocked requests and zero page errors were recorded.

## Clean-environment reproduction (public candidate)

The public candidate was extracted into an empty folder and set up only from its README: a new Python 3.12.14 virtualenv, `pip install -r backend/requirements-lock.txt` and `requirements-dev.txt` from PyPI (`pip check` clean), `npm ci`, `npm run build`. Results: **127 pytest passed; 23 vitest passed; build passed**. `prepare_review_demo.py --prepare-only` followed by the CLI replay reproduced 9.1046 / 23.9297 / 75.5859 px. A server started with `prepare_review_demo.py --port 8002` reported no key and paid inference off. Chrome E2E against it: **14 passed, 3 skipped**. The three skipped tests need private originals that are deliberately not distributed (the full 442-frame source video, the private SAM export and the optional manual-annotation project). The SAM preflight test previously failed in this situation instead of skipping; it now skips, and still passes in the original workspace (17/17).

## Final packages (built from clean `7737914`)

| Candidate | Files | Bytes | SHA-256 |
|---|---|---|---|
| `KINETICA-public-repository-candidate-7737914-ed4a08a517a0.zip` | 132 | 1,729,805 | `a54dcd86b7a0eca8642c6c3c2d605df297c452c599d30a8f57628f76dee3228f` |
| `KINETICA-submission-review-kit-7737914-6e62f3cd4ecb.zip` (adds built frontend, final MP4, captions, transcripts, credits, video manifest) | 145 | 29,070,241 | `b855b0f0cbcb5bd08063dfb8b215ed71abbfaaa64454af5d182370706bfc4615` |

## GitHub repository (prepared, private)

`https://github.com/ErickAmestegui/KINETICA` was created **private** and holds one fresh commit: the public candidate above without its two packaging-status files. Commit author: the account's GitHub no-reply address, so no personal e-mail is exposed. Scan of the pushed tree: no keys/tokens, no Windows user paths, no username, no broken relative Markdown links. The only e-mail addresses are third-party authors' inside their own license texts. Making it public is a single visibility change awaiting the entrant's approval.

Both packages passed the builder's manifest, secret and private-path checks (`source_worktree_dirty: false`, no credentials, raw provider responses or dependency binaries). The review kit was extracted and served from its own source on port 8001 with an empty key and paid inference off: the root page, clip metadata and a decoded thumbnail were served; the replay reproduced 9.1046 / 23.9297 / 75.5859 px for horizon 8 and null scores for horizon 20; original input hashes were unchanged; zero Meta requests. Earlier candidates built from `dcc27fd`, `fce9df2` and `91eb8bc` are superseded and kept privately under `output/submission-package/superseded/`. The previous `KINETICA-final-audit-dcc27fd.zip` is audit evidence only (23 files, no runnable project) and must not be submitted as the project.

Raw logs remain in ignored `output/submission-validation/` because they contain local user paths.
