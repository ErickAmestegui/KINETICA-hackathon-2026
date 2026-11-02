# Reality Lab — implemented experience and evidence

2026-10-29. Same KINETICA repository; original source and SAM export retained. No inference, private upload, payment change, publication, deployment or submission in this task. `META_ALLOW_PAID=false`.

## Reproduce

Start the existing app with `scripts/Start-Kinetica.ps1` after building the frontend. Open My machines → Open project JSON → private `output/kinetica-project.json`, then the new **Reality Lab** tab. Existing Studio, Compare, Analysis, Report and Meta gates remain available.

1. **Observe / Predict:** inspect the source, select #2 and explicitly confirm its slider identity. Default freeze frame 29 and horizon 20 are locked when FREEZE REALITY is pressed. The original video pauses, a golden ghost projection appears, and scores/hidden observations remain withheld. Press REVEAL REALITY to reveal the actual saved masks and assessment. The default horizon crosses the known 37–38 source cut, so all three scores are No evaluado. Reset, select horizon 8 and repeat for a retrospective single-view replay of frames 30–37.
2. **Break Reality:** original interpreted model and calculated alternate share one clock. Change radius, rod length, video-time speed or phase. Centered requested stroke uses r=stroke/2. Invalid geometry is rejected with L > r + |e| explained. Restore original resets the alternate. Geometry transitions interpolate feasible parameters and solve every pose. Orbit, zoom and component inspection are retained. Positive geometry does not establish physical buildability.
3. **Ask the Machine:** select or enter a supported natural-language instruction, interpret locally, inspect the tool request and calculated proposal, then confirm an alternate change. The deterministic mock supports doubling centered stroke, faster motion, geometry explanation and scenario comparison. Unsupported wording returns current state. **No general language understanding or live Muse response is claimed.**

Save study / export project preserves cutoff, horizon and alternate parameters. Slider identity must be reconfirmed in a new Lab session. Frozen server sessions expire after 15 minutes and are not restored as trusted predictions; re-freeze locally. Download the revealed evidence JSON for an enduring protocol/result record. Eight sessions maximum bound private in-memory storage.

CLI reproduction, with no HTTP or provider transport:

```powershell
.venv/Scripts/python.exe scripts/replay_reality_lab.py --project output/kinetica-project.json --object-id 2 --confirm-slider --freeze-frame 29 --horizon 20
.venv/Scripts/python.exe scripts/replay_reality_lab.py --project output/kinetica-project.json --object-id 2 --confirm-slider --freeze-frame 29 --horizon 8
```

The script writes content-addressed reports under private ignored `output/reality-lab/`, including original export/video hashes, protocol, predictions, measured coordinates, baselines and provenance.

## Temporal isolation and scientific limits

Freeze discards all future geometry, manual corrections and ID assignments **before** contour centroid extraction, PCA or timing optimization. Prior fitted speed/phase are reset, so a full-study timing estimate cannot seed the fit. r/L/e remain user-declared conditional assumptions, not recovered physical dimensions. The interactive fit ranks its deterministic coarse grid by training error and refines the best twelve seeds to bound CPU latency; this is a local conditional fit, with no global-optimum guarantee. Existing Phase 2 fitting retains its exhaustive refinement. Training uses frames 0–29, and future timestamps determine the evaluation grid. The optimizer's conditioning/minimum-cycle guards can return Insufficient evidence.

Prediction stores a fixed model, axis and future outputs before reveal. Reveal alone reads future centroids. Constant prediction uses the final training centroid; linear prediction uses an ordinary least-squares extrapolation over the final eight training samples. All three use exactly the same measured evaluation frames and projected image coordinate. Missing masks invalidate the aggregate score rather than supplying interpolated observations.

The known real diagnostic `e14d21bb8f3c` registers the source view/time change at 37–38. A horizon including frame 38 or later has null scores and an explicit reason. This registration is specific to the inspected Eitech clip; general automatic cut detection is not implemented. New sources require review.

**This is a replay of previously inspected data.** The cutoff/horizon are locked before each fit, but they were designed after studying this dataset. It is not independent prospective validation. Furthermore, the original SAM request processed the entire clip; causal online segmentation is unverified. Local optimizer isolation does not prove that original SAM centroids were obtained without future context. Independent continuous footage, past-only segmentation/annotations, calibration and untouched test protocols remain necessary.

## Measured real replay

| Freeze / horizon | Evaluation frames | Model 1D RMSE | Constant RMSE | Linear RMSE |
|---|---|---:|---:|---:|
| 29 / 8 | 30–37, n=8 | 9.1046 px | 23.9297 px | 75.5859 px |
| 29 / 20 | 30–49, n=20 | No evaluado | No evaluado | No evaluado |

The second crosses the known cut. The first fits 81.037651 video-rpm and phase −1.240151 rad on training masks, conditional on r32/L128/e0. Absolute dimensions, actual shaft speed, joint centers, 3D reconstruction, forces and material strength are unknown. These values supplement the Phase 2 61.39/8.72-px evaluations; the differing protocols are not interchangeable.

## Meta contribution and future integration

SAM supplied the already authorized component segmentations: 300 real records, three IDs, 50 frames. Manual inspection assigns slider #2; corrections retain separate provenance. KINETICA computes all motion and errors. Muse has **not** been called in this task.

`backend/reality_lab.py` defines an allowlisted Pydantic ToolCall, strict change arguments, a deterministic mock, and a pure Muse request builder / response parser. It uses the documented `muse-spark-1.3` structured-output envelope with `additionalProperties:false`, required fields, strict schema and completion checks. The tool-call cookbook informed the propose → validate → execute boundary; the implementation chooses a structured proposed call so no arbitrary tool execution loop exists. There is no file access, shell tool or code execution in the allowlist. Geometry is validated before review; proposed changes affect only the alternate after confirmation.

Official references inspected: [tool/function calling](https://dev.meta.ai/docs/cookbook/tool-function-calling), [structured output](https://dev.meta.ai/docs/cookbook/structured-output). The real transport for this new interpreter remains deliberately disconnected. It needs an explicit authorized cost proposal, guarded one-request transport, authentic response verification and a separately authorized explanation call if desired. The existing paid gates must not be bypassed. Synthetic parser tests establish contract handling only, not live Muse compatibility.

## Verification and artifacts

91 Python tests, 22 TypeScript tests and 15 browser scenarios passed. Production build passed; existing Starlette TestClient deprecation and Vite bundle-size warnings remain. Final focused checks cover returning from the alternate scene to the same source-video timestamp. External transports and paid routes are blocked in the automated harness.

New tests check future-mask/correction perturbation invariance, prior-timing seed isolation, identical evaluation frames for baselines, missing masks/cut invalidation, unsupported tools, non-executable structured proposals, centered stroke inversion, confirmation before changes and project recovery. Browser checks exercise all three modes, original regressions and 390-px layout. Playwright CLI separately opened and inspected the modes.

Private screenshots: `output/playwright/reality-lab-predict.png`, `reality-lab-reveal.png`, `reality-lab-break.png`, `reality-lab-ask.png`, `reality-lab-mobile.png`. They are real application captures. No generated visual is used as measurement evidence.

## Three-minute judge walkthrough

- **0:00–0:30 / Observe:** load Eitech and highlight original SAM masks. State that component segmentation requires manual slider identity and does not identify joints.
- **0:30–1:05 / Predict:** show fixed cutoff/horizon; freeze at frame 29 and explain that hidden coordinates are discarded before fitting. Identify the exercise as saved-data replay.
- **1:05–1:35 / Reveal:** reveal the default cut-crossing horizon and its invalid score. Show the separately declared eight-frame replay and all three baselines. Mention full-video SAM context and the need for an untouched causal evaluation.
- **1:35–2:15 / Break Reality:** animate two solver-driven models, change stroke, show an impossible request rejected, restore the original. Explain that relative geometry is not a fabrication certificate.
- **2:15–2:45 / Ask:** enter “duplicar el recorrido”, display deterministic mock provenance, review the strict proposed tool, then confirm. State that Muse live transport awaits authorization.
- **2:45–3:00 / Contribution:** authentic saved Meta segmentation + explicit human interpretation + verified mathematical tools. Next evidence milestone: independent continuous recording and authorized authentic Muse response. No jury score or readiness percentage is asserted.
