# Verification record

**Latest release validation: 2 November 2026 — 127 Python, 23 TypeScript, 17 Chrome E2E (no skips), production build passed; see [FINAL_RELEASE_VALIDATION](validation/FINAL_RELEASE_VALIDATION_2026-11-02.md).** Earlier audit the same day: 113 Python, 23 TypeScript, 17 Chrome E2E, build. All 28 Python locked distributions match installed versions, pip check passes, npm audit reports zero known advisories. See [final audit, exact commands, environment failures and scope](FINAL_AUDIT_2026-11-02.md) and [preserved evidence verification](EVIDENCE_AUDIT_2026-11-02.md). No new Meta inference was performed. Earlier entries below are historical.

This record describes executed checks, not planned capabilities. **Phase 2 (2026-10-29): 87 Python, 20 TypeScript, 13 Chrome E2E passed; production build passed.** See [MASK_MOTION.md](MASK_MOTION.md). The current suites cover contour centroids/holes, malformed and duplicate geometry, manual provenance, reserved-frame isolation, conditional timing recovery, retrospective windows, stale-response rejection, shared-clock playback and original SAM safeguards. Tests remain offline. Earlier counts below are historical. **Final SAM preflight: 71 Python, 16 TypeScript, 10 Chrome E2E scenarios passed; build passed.** See [SAM_PREFLIGHT.md](SAM_PREFLIGHT.md). Earlier totals below are historical. Latest SAM repair: **68 Python, 13 TypeScript, 8 Chrome E2E passed**, production build passed; no Meta API requests. See [SAM_REPAIR.md](SAM_REPAIR.md). The table below is the historical initial-build record; its missing-key/no-prior-call statements are not the current incident state.

| Check | Evidence |
|---|---|
| Python engine/API/vision/parser suite | **29 passed** (`python -m pytest tests -q`) |
| TypeScript engine/render-pose suite | **8 passed** (`npm test`) |
| Production build | TypeScript + Vite 7.3.7 build successful |
| Browser E2E | **4 passed** on Chrome, including optional real Eitech diagnostic project |
| Responsive layouts | Captured at 1440×1000, 1280×800, 390×844; no horizontal DOM overflow |
| npm dependency audit | **0 known advisories** after targeted Vite 7.3.7 / Vitest 4.1.12 updates |
| Local FastAPI | Health endpoint and production frontend reachable on 127.0.0.1:8000 |
| Real input video | Eitech MP4 inspected, imported, played, annotated manually, compared and project restored |
| Meta authenticated catalogue | **Blocked locally**: no MODEL_API_KEY configured |
| Meta paid inference | **Not run**; no authorization or spending |

Browser E2E verifies live canvas creation; parameter-driven timeline changes; play/pause advancing the shared clock; analysis/report switching; no fabricated Meta evidence; JSON report downloads; explicit missing-key response; H.264 import/playback; point annotation; local LK tracking; calibrated fitting; CSV export/import; browser project save/recovery; modal keyboard dismissal; and opening the actual Eitech diagnostic with its 58.42 px held-out residual. It checks page runtime errors in the initial studio and real-video flow. It does not prove real Meta model behavior.

Python tests cover centered/eccentric length preservation, singular/invalid parameters, finite-difference velocity, image coordinate conventions, fit recovery, held-out exclusion, empty metrics, true residual magnitude, malformed/empty/incomplete SAM streams, actual official mask decoding, synthetic API errors, spend blocking, invalid Muse proposals, MP4 import, HTTP ranges, thumbnails, LK translation, occlusion loss, CSV export, bad files, origin rejection, split leakage, cross-language references and scale declaration semantics.

## Corrections made during verification

- Windows temporary-directory permissions: used writable `output/tmp`; asyncio/browser tests needed host socket permissions. These were environment failures, not silently skipped tests.
- Separated Vitest source tests from Playwright E2E specs after the toolchain update.
- Fixed an E2E status locator matching both progress and notification elements.
- Fixed a phase range whose irrational minimum conflicted with its decimal step, preventing setting exactly zero.
- Corrected camera reset behavior and responsive framing.
- Kept shaft bearings at the mathematical origin while changing radius; moved the rod in front of the guide-support plane; adapted base/guide placement for eccentricity; normalized renderer dimensions uniformly.
- Corrected SAM mask placement from local mask coordinates to source-video bounds.
- Made joint/trajectory strokes scale with source resolution so 1080p annotations remain visible.
- Preserved fitted-frame provenance so relabeling training frames does not create a false held-out metric.
- Added explicit synthetic/unclassified/real footage declaration; missing metrics display `No evaluado` with a reason.
- Corrected the parser attribution to SAM License after inspecting the installed license.

## Artifacts

Private generated artifacts (ignored by Git):

- `output/playwright/studio-desktop.png`, `studio-1280.png`, `studio-390.png`
- `output/playwright/compare-video.png`, `analysis.png` — clearly synthetic test flow
- `output/playwright/real-eitech-compare.png`, `real-eitech-analysis.png` — actual source footage with manual diagnostic data
- `output/playwright/results.json` — browser test results
- `output/real-video/eitech-evaluation.json`, `eitech-project.json`
- `output/synthetic-slider-crank.mp4`, `synthetic-ground-truth.csv`

Remaining notices: the production 3D bundle is approximately 1.2 MB uncompressed / 346 KB gzip and triggers Vite's chunk-size warning; the app runs successfully. Starlette's test client emits a deprecation notice about future httpx2 support. Neither warning was hidden or treated as a successful check of unrelated functionality.

## Phase 2 visual evidence

Playwright CLI loaded the original real-response replay, audited 300 records, checked the diagnostic, confirmed #2, fitted interval 0–37, stepped to source frame 20 (0.800 s), and saved the local study. Real-source screenshots at 1440×1000, 1280×800 and 390×844 are in ignored output/playwright/phase2-real-*.png. No horizontal overflow at 390 px; zero console errors or warnings. The graph and 3D use the fitted video-time parameters, while physical scale and joint validation remain unknown. All private source exports and video hashes remain unchanged.

## Reality Lab delivery — 2026-10-29

91 Python, 22 TypeScript and 15 Chrome E2E passed, production build passed. See REALITY_LAB.md for temporal-isolation invariance, invalid cut-crossing evaluation, baseline protocols, reviewed mock tools, valid geometry interpolation, project recovery and authentic-source visual captures. New cases exercise all three modes and narrow layout without paid routes. Full-video SAM context is explicitly disclosed.

## Phase 4 — 2026-10-29

110 Python, 22 TypeScript, 16 browser scenarios and production build passed. See PHASE4_MUSE_VALIDATION.md for the real tool-call contract, offline quote, no-retry/one-use gating, strict response mocks, independent seal/evaluate protocol and actual backend restart integrity check. All paid routes are intercepted in browser automation. No real Muse inference was performed; paid=false and original video/export retained.

## Muse recovery d25cbc08d7c2

113 Python, 23 TypeScript, 17 browser cases and build passed. See MUSE_INCIDENT_d25cbc08d7c2.md for safe per-phase diagnostics, preflight storage guards, retained usage on unsuccessful responses, response-vs-persistence distinction, synthetic confirmation-to-3D flow and actual restart evidence. Original failure cause and billing remain undetermined; no new paid request was made. META_ALLOW_PAID was found enabled and safely disabled under the user's technical-configuration authorization.
