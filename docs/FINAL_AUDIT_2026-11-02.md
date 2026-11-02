# Final local audit — 2 November 2026

Base HEAD verified as `8abe7c024dd199f71b525fde97c6eb29ffa10669`, with a clean working tree before work. The original repository and all existing functionality were retained. The final checkpoint is recorded in the delivery report. No new Meta inference, external media upload, payment, public deployment, publication or application submission occurred. The local production server is available at `http://127.0.0.1:8000`; live health confirms `paid_enabled=false`.

## Executed checks

| Check | Result | Private evidence |
|---|---|---|
| Python engine/API/parser/spend guards | **113 passed**, 43.26 s | `output/final-audit/python-tests-host.txt` |
| TypeScript engine and renderer tests | **23 passed**, seven files | `output/final-audit/typescript-tests.txt` |
| Chrome Playwright | **17 passed**, no skips, 2.4 min | `output/final-audit/playwright.txt`; `output/playwright/results.json` |
| Production build | **Passed**, TypeScript + Vite | `output/final-audit/build.txt` |
| Python dependencies | pip check clean; all 28 locked distributions match installed versions | `output/final-audit/pip-check.txt`, `python-lock-check.json` |
| npm dependencies | Installed direct versions match; audit reports **zero known advisories** | `output/final-audit/npm-audit.json` |
| Source/SAM/replay/Muse-log integrity | **Passed**, offline; original hashes unchanged | [evidence audit](EVIDENCE_AUDIT_2026-11-02.md) |

Commands used, from the repository root unless a directory change is shown:

```powershell
$env:TEMP=(Resolve-Path output/tmp).Path
$env:TMP=$env:TEMP
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe scripts/audit_hackathon_evidence.py
Set-Location frontend
npm.cmd ls --depth=0
npm.cmd test
npm.cmd run build
# Existing local production server must already be running.
npm.cmd run test:e2e
npm.cmd audit --json
```

The test fixtures and private source inputs already existed in this checkout. Clean installations must follow README fixture preparation; private Eitech evidence is intentionally not distributed. Python tests block external transport and clear operator credentials. Browser automation blocks external hosts and live inference routes; its synthetic Muse scenario establishes confirmation/solver behavior, not live model compatibility.

## Failures investigated and resolved

The first restricted Python run had 57 passes and 56 setup errors. A focused reproduction identified Windows temporary-directory access denial; TestClient also requires local asyncio sockets. The unchanged full suite passed with the approved local host permissions and workspace temporary directory. The initial TypeScript invocation failed before tests because esbuild could not read parent directories under the sandbox; approved local execution passed. These were environment restrictions; no test was disabled or assertion weakened.

The PowerShell launcher was blocked by this machine's script execution policy. The app was started directly with its existing virtualenv executable, hidden and bound only to loopback. The recording guide now provides the direct uvicorn command, avoiding a permanent policy change. Generated Playwright MCP logs are now ignored to keep browser traces out of Git.

Warnings remain disclosed: Starlette TestClient/httpx deprecation, Vite's approximately 1.258 MB minified JavaScript bundle warning, and Playwright's NO_COLOR/FORCE_COLOR notice. No runtime/product failure was found by the final suites. pip check is a compatibility check, not a Python vulnerability audit; no Python advisory scanner was installed or run.

## Reality Lab and scientific evidence

- **SAM:** 300 geometry records = 150 boxes + 150 contours; three IDs over 50 frames, not 300 distinct objects. No missing/duplicate/malformed geometry in this export. This does not establish IoU, semantic correctness or joint-center accuracy.
- **Predict the Unseen:** cutoff29/horizon8 reproduced **9.104608 px model / 23.929742 px constant / 75.585863 px linear**, on the same eight observations. Horizon20 returns null scores across the known cut37–38. This is retrospective replay with full-video SAM context; independent prospective validation remains absent. The negative full-clip result remains preserved.
- **Break Reality:** browser checks exercised two solver-driven views, feasible changes, impossible centered-stroke rejection, shared clock and restoration. It is a counterfactual simulation, without forces/material/buildability validation.
- **Ask the Machine:** mock tool interpretation, validation and explicit confirmation passed. A synthetic Muse-shaped result changed only the alternate after review; actual Muse remains unverified.
- **Muse d25cbc08d7c2:** preserved logs confirm one local quote200/run502 pair. The original code retained no provider response or usage. Exact root cause, provider receipt and consumption remain undetermined. Current telemetry repairs pass local tests but cannot reconstruct the old failure. No retry was made.

Real UI captures were refreshed in `output/playwright/reality-lab-{predict,reveal,break,ask,mobile}.png`; desktop Ask was visually inspected. The responsive browser case also passed. These are private captures of the working application, not generated measurement imagery.

## Documentation and release gates

Updated README and the [recording script](HACKATHON_DEMO.md); added the offline evidence-audit command and report; updated the [official requirements](HACKATHON_REQUIREMENTS.md) and [final checklist](SUBMISSION_CHECKLIST.md). A separate reader review found no missing local links and checked walkthrough labels against UI/tests. The obsolete instruction to show a successful Muse answer was removed. Three minutes is an internal video target, not a verified official limit.

Rendered Official Rules are now verified. The official deadline is **4 November 2026, 22:00 Bolivia / 5 November 02:00 UTC**. Judging weights: impact30%, Meta tooling25%, technical execution20%, demo25%. Full source links and preserved browser evidence are in the requirements audit.

Remaining gates: accepted-participant identity/eligibility and team authority; authenticated form fields/video/repository requirements (portal redirects to login); entrant review of the contract; exact converted-media lineage and required publication rights; actual video recording and approved public delivery links. No live Muse success or independent physical validation is claimed. A future paid Muse trial requires fresh specific authorization. Public release and the completed candidature each require the user's authorization.
