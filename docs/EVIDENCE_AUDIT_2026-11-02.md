# Private evidence audit — 2 November 2026

Audited offline from base checkpoint `8abe7c024dd199f71b525fde97c6eb29ffa10669` in the original repository. No Meta requests, new inference, uploads, payments, publication or submission were performed by this audit. Source files and preserved incident logs were read only.

## Reproduce

From the repository root with the existing virtual environment:

```powershell
.venv/Scripts/python.exe scripts/audit_hackathon_evidence.py
```

The command rejects changed source/export hashes, synthetic or incomplete responses, missing/malformed/duplicate geometry, altered preserved incident logs, unexpected replay metrics, and any result that evaluates across the known source cut. It imports only local mathematical/measurement code, not Meta adapters or transport. Input hashes are rechecked after evaluation. Output is private, content-addressed and ignored by Git:

`output/final-audit/evidence-cd90d5773575a556.json`

Report SHA-256: `87a0e2a344634015f1350bba18d056b359ca8a75a6bfe68bd213cc37479bdb54`.

The final script was executed successfully after adding explicit clip-hash and decoder-fps checks. It reproduced the same report as the initial run.

## Preserved source integrity

| Evidence | SHA-256 |
|---|---|
| Original SAM project export | `f4e09b06aa2323348e79b182c598a1f34f57816f65b3eb91b44184d645eff65a` |
| Original 442-frame video, located in private local data | `a80d4fc0c85b1d4ec747fe2049349cf656579c3e0d02894c4ae437a412665e66` |
| Actual SAM input clip | `4e179551a3dde38da847c9392e277331bc93fd1ac28d3524da8a6ca4872a1677` |

The clip decoded successfully to exactly 50 images, all 960 × 540 pixels; OpenCV decoder and saved metadata both report 25 fps. Metadata contains 50 strictly increasing presentation timestamps. Export dimensions/frame count match local source metadata. The clip hash also matches a pre-existing private Reality Lab replay report. These hashes establish local integrity; they do not authenticate a provider response or establish the source media's licensing lineage.

## SAM: 300 geometry records

The saved response identifies diagnostic `e14d21bb8f3c`, completed outcome and zero parser diagnostics. The audit confirms **150 boxes plus 150 contours**, corresponding to **three IDs over 50 frames**, with one box and one contour per ID per frame. There are no missing observations, malformed contours or duplicate geometry records in this export. This is not a claim of 300 distinct objects or 300 independent detections.

| ID | Boxes | Valid contours | Missing frames | Centroid image span |
|---|---:|---:|---:|---:|
| 0 | 50 | 50 | 0 | 19.7483 px |
| 1 | 50 | 50 | 0 | 33.1027 px |
| 2 | 50 | 50 | 0 | 127.3752 px |

The span is the diagonal of centroid x/y ranges, not a calibrated stroke. ID #2 remains an explicitly manual slider interpretation. Contour-area centroids are not joint centers, ID continuity does not prove semantic correctness, and no independent segmentation labels or IoU benchmark exist.

## Predict the Unseen: saved-data replay

The script fixes frame 29 as the cutoff, uses frames 0–29 only for local fitting, checks that freeze exposes no evaluation rows or scores, then reveals the saved observations. Conditional geometry is r32/L128/e0. Training-only fitting again yields 81.037651 video-rpm and phase −1.240151 rad.

| Horizon | Evaluation frames | n | Model RMSE | Constant RMSE | Linear RMSE | Valid |
|---|---|---:|---:|---:|---:|---|
| 8 | 30–37 | 8 | 9.104608 px | 23.929742 px | 75.585863 px | Yes, as retrospective image-space agreement |
| 20 | 30–49 | 20 | null | null | null | No: known source change at 37–38 |

All three methods are evaluated on the same observations. The source change is already documented from image registration/source inspection; this audit rechecks the guard, not a fresh independent camera-motion experiment. The prior full-clip negative result remains **61.39 px model vs 60.98 px constant baseline** and is not superseded by this different protocol.

This dataset and cutoff were previously inspected. Original SAM segmentation used full-video context. Local optimizer isolation therefore does not prove causal segmentation or independent prospective performance. No physical shaft speed, scale, unique 3D reconstruction, force or material-strength result follows from these measurements. Independent continuous footage, past-only labels/segmentation and an untouched protocol remain absent.

## Muse Spark failure d25cbc08d7c2

The preserved stdout log contains exactly one local `POST /api/lab/muse/quote` returning 200 and one local `POST /api/lab/muse/run` returning 502. Both log hashes match the incident assessment:

| Log | SHA-256 |
|---|---|
| stdout | `60b83d5d2668ded630987456fd701214b90814b1ec4ab78756ecc297a4beaa3c` |
| stderr | `ffc26c67c50b82b92815ae765098460b9871956901a732626f696f70ca81d7a9` |

The pre-repair path did not retain phase telemetry or the failed provider response. Available evidence cannot establish external HTTP status, provider receipt, completion, tokens or amount billed. **Root cause and consumption remain undetermined**, rather than zero. A 502 from the local API is not a provider billing receipt. Timeout, truncation, parser rejection, provider failure and filesystem failure cannot be distinguished retrospectively from this log.

The current per-phase diagnostic/usage-preservation repair is documented in [MUSE_INCIDENT_d25cbc08d7c2.md](MUSE_INCIDENT_d25cbc08d7c2.md) and exercised by local synthetic tests in the main final verification. Its presence does not retroactively prove what caused the original incident or validate live Muse compatibility. Any future inference still requires new specific authorization.
