# Phase 2 — saved real masks to measured motion

Date: 2026-10-29. All processing in this phase is local. **META_ALLOW_PAID=false; no Meta requests, uploads, retries or inference.** No publication performed.

## Preserved evidence

The private `output/kinetica-project.json` contains the user-reported real response: diagnostic `e14d21bb8f3c`, completed, 300 geometry records, zero parser diagnostics, remote cleanup recorded as `deleted`. This is corroborated by the saved export, not a new authenticated verification of Meta's account or remote storage. The local integrity hash is not provider authentication.

Export SHA-256: `f4e09b06aa2323348e79b182c598a1f34f57816f65b3eb91b44184d645eff65a`.

Video ID: `3e4c5e12f8b84af0996f02a9dfa89989`. Source: 50 decoded frames, 960×540, 25 fps, `eitech-50-cfr.mp4`. Original 442-frame video remains unchanged: SHA-256 `a80d4fc0c85b1d4ec747fe2049349cf656579c3e0d02894c4ae437a412665e66`.

The audit finds 3 IDs, 150 boxes and 150 masks. Each ID has 50 valid masks and 50 boxes; no missing frames, duplicate geometry or malformed contours in this export. ID continuity does not prove correct semantic association.

| ID | Centroid bounding span, px | Visual interpretation |
|---|---:|---|
| 0 | 19.75 | Right support, apparently fixed in the apparatus |
| 1 | 33.10 | Foam support below the motor, apparently fixed in the apparatus |
| 2 | 127.38 | Central block moving with the slider; selected by visual inspection |

These spans are the Euclidean diagonal of centroid x/y ranges, **not calibrated strokes**. All three objects move in image coordinates above the declared 2-px jitter threshold. Apparent fixed supports must not be called stationary in world coordinates solely from this test. The #2 assignment was visually inspected by the assistant using source frames; the user can confirm, change or revoke it. It is not automated joint identification or a claim of human ground truth.

## Discontinuity: source evidence

`scripts/diagnose_saved_motion.py` decodes the source and registers a declared upper-right background region using OpenCV LK with forward/backward error <1 px, followed by affine RANSAC (1.5 px threshold). This is diagnostic image registration, not physical calibration.

At 37→38, the background median displacement is (+5.36, −21.46) px. An affine fit has 94/156 inliers and median residual 0.986 px. Neighboring 35→36 and 36→37 transitions are subpixel in the background. Mean absolute image difference rises to 28.22 on the 0–255 grayscale scale, compared with 3.70 in the preceding pair. Source frame inspection shows a changed view. Pairs 39/40, 41/42 and later are nearly repeated; they are not asserted byte-identical.

Original frames 186–189 match clip frames 36–39 with mean absolute RGB differences 1.42–1.46 after resizing/recompression. The change is already in the supplied video. It is **not exclusively a SAM parser/tracking artifact**. Camera repositioning/editing and altered temporal sampling are plausible; exact capture/edit history is unknown. Do not claim that this identifies the earlier 442-frame HTTP 502 cause.

Centroid temporal review flags occur for all three objects near 37–38. The heuristic measures deviation from timestamp-weighted neighboring centroids, using threshold max(5 px, training median + 6 scaled MAD). It does not exclude data, infer occlusion or assert an ID switch. No automatic stabilization or time correction has been applied.

## Measurement and fitting conventions

Centroids are signed polygon-area centroids of the retained SVG contours; winding subtracts holes. The original RLE raster is unavailable in this older export. Coordinates use image x right / y down, pixels. A mask centroid measures visible area, not a joint.

PCA uses training frames only; axis sign is chosen toward positive image x. Observed displacement is the dot product of centroid minus first training centroid with that axis. The model remains the existing right/open slider-crank. Its projection is `offset + gain × [slider_x(t) − slider_x(0)]`. No physical scale follows from the image gain.

Default fitting estimates gain and offset only. Optional timing fitting estimates positive speed (6–180 rpm in **video seconds**) and phase, with r/L/e fixed. Deterministic bounded multistart least squares uses only training centroids. A minimum 1.25 training cycles, finite motion, convergence and conditioning guards reject weak fits. Rotation direction is assumed, not measured. The speed is not physical shaft rpm for edited/retimed footage. This conditional fit does not identify absolute dimensions or uniquely establish the mechanism geometry.

The final 25% of the selected frame interval is reserved. No reserved coordinates enter axis estimation, timing optimization or projection fitting. These are SAM observations, **not independent ground-truth labels**. Timing uncertainty has no calibrated confidence interval. A successful optimizer is not reconstruction verification.

## Actual evaluations — retain both

| Evaluation | Training / reserved | Training RMSE | Reserved RMSE | Constant training-mean baseline, reserved |
|---|---|---:|---:|---:|
| Entire clip, declared 40 rpm / phase 0 | 0–37 / 38–49 (38 / 12) | 37.30 px | **61.39 px** | 60.98 px |
| Retrospective interval 0–37, timing fitted | 0–28 / 29–37 (29 / 9) | 4.82 px | **8.72 px** | 50.53 px |

The first model fails to improve the baseline. The second fits video-time speed 80.927596 rpm and phase −1.236229 rad, conditional on r=32, L=128, e=0 relative units. Axis (0.965371, 0.260882); gain 1.562187 px/model unit; offset −9.849536 px. Reserved cross-axis RMS is 11.02 px, so the 1D score does not describe all 2D mismatch.

The second interval was selected **after examining the discontinuity and the original evaluation**. Its held-out set differs. Do not report 61.39→8.72 as a same-test improvement or independent prospective validation. The masks, original footage and all 50 original samples are preserved.

An earlier exploratory timing fit over the entire clip reduced training error but produced about 79.91 px reserved RMSE. It was not selected as a successful reconstruction. A future independent continuous video is needed to test generalization.

## Reproduce privately

From the repository root, without enabling Meta:

```powershell
.venv/Scripts/python.exe scripts/diagnose_saved_motion.py --project output/kinetica-project.json
.venv/Scripts/python.exe scripts/analyze_saved_sam.py --project output/kinetica-project.json --object-id 2 --confirm-slider --write-demo
.venv/Scripts/python.exe scripts/analyze_saved_sam.py --project output/kinetica-project.json --object-id 2 --confirm-slider --end-frame 37 --estimate-timing --write-demo
```

Outputs are addressed by export hash and full analysis hash, so different decisions do not overwrite each other. They include `audit.json`, per-object measured CSVs, `selected-motion.csv` with predictions/residuals/splits and a private `replay-project.json`. The actual retrospective run is in `output/sam-motion/f4e09b06aa232334/b29b09122917ca48/`. The frame investigation and contact sheet are in `output/sam-motion/discontinuity/`.

Open KINETICA locally. **My machines → Open project JSON → Compare → Audit saved masks**. Inspect/select #2 and explicitly confirm its role. Enter analysis end frame 37 and enable optional speed/phase fitting to reproduce the retrospective case, or leave the full interval/default timing for the original comparison. Fit locally; video, observed displacement, mathematical prediction and 3D use the same clock. Prediction overlays are limited to the selected interval; playing outside it is not validation evidence.

“Correct mask centroid”, coordinate fields, frame exclusion and per-frame ID reassignment record manual changes separately; reset restores original measurements. Missing masks are not interpolated. Parameter edits invalidate stale fits; navigating between tabs preserves valid fits; late responses cannot overwrite changed inputs. Export mask analysis and the validation report. Joint-observation CSV remains separate because mask centers are not automatically joint observations.

“Preserve detections locally” writes append-only content-addressed snapshots into the existing private video folder. Outcome/provenance form part of the snapshot hash. Back up `data/` and `output/` privately; Git intentionally excludes them. The replay needs the same local source video ID.

## Verification and remaining work

See CONTINUITY.md and VERIFICATION.md for final executed test totals. Tests use explicitly synthetic fixtures and block external transport; mock completed/incomplete/failed SAM states are never labeled real. Real saved evidence is used only in the private replay and source investigation.

Before presenting: ratify the #2 role; obtain independent manual joint/centroid labels; use continuous fixed-camera footage with known timing and scale; assess perspective and stabilization; test on an untouched recording; verify media rights. No real inference is needed to reproduce this phase. Any future paid inference requires new explicit authorization. Muse live behavior remains unverified here, and the original 442-frame HTTP 502 root cause remains unknown.
