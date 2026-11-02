# Evaluation protocol and observed results

## Reproducible synthetic experiment

`python -m scripts.make_synthetic_fixture` creates a 640×360 H.264 clip and exact CSV centers from a known slider-crank (r=32, L=128, rpm=30, e=0; scale=1.5 px/unit, O=(100,180)). Every video frame says **SYNTHETIC TEST FIXTURE — NOT REAL FOOTAGE**. These files stay in ignored `output/`.

Playwright imports the clip, clicks centers, tracks with OpenCV, sets calibration/speed/phase, fits the training frames, checks a reserved residual exists, exports/reimports CSV and restores a saved project. This demonstrates functioning software plumbing. It is not an independent real-world accuracy claim.

For exact solver recovery, Python tests synthesize noiseless observations. Altering held-out x coordinates by +100 px must leave the fitted parameters unchanged and move held-out RMSE to 100 px. Shared golden states verify Python/TypeScript parity. Renderer-pose tests verify link distances under normalization and eccentric base clearance.

## Actual Eitech video: diagnostic, not precise reconstruction

Local file discovered in the user's Desktop: `Schubkurbelgetriebe_(Eitech) (1).mp4`. OpenCV inspection found 1920×1080, 25 fps, 442 decoded frames, 17.68 seconds. The evaluation script records its SHA-256 in the private result. No video was sent to Meta or published.

The initial local baseline was seeded by manual image inspection at frame 150: crank approximately (288,388), slider approximately (905,891). LK produced **4 samples**, then rejected the slider at frame 152 and crank at frame 154. No samples were invented after loss. Held-out coverage is zero, so **LK held-out accuracy is not evaluated**.

After viewing extracted actual frame crops, approximate joint centers were annotated manually at frames 150,152,…,172 (24 samples, two joints per frame). They are stored explicitly in `scripts/evaluate_eitech.py`, with source `manual`. They are not SAM detections and have not been independently verified as ground truth. Motion blur makes some centers ambiguous.

Frames 150–166 supplied 18 training samples; 168,170,172 supplied 6 held-out samples. The fixed similarity calibration (O=(265,306), angle=0.35 rad, 6 px/model-unit) and eccentricity e=−60 are manually selected diagnostic values. Fitting r, L, rpm and phase yielded:

| Calculated quantity | Result |
|---|---:|
| Training RMSE | 61.79 px |
| Held-out RMSE | 58.42 px |
| Constant training-mean baseline, held-out RMSE | 86.60 px |
| Crank radius | 13.1954 relative units |
| Rod length | 141.0074 relative units |
| Angular speed | 84.4983 rpm |
| Physical scale | Unknown |
| Meta inference | None |

The constant baseline predicts each joint's mean training location for every held-out frame. It is intentionally simple and reproducible. Its higher residual does **not** establish general superiority or accurate physical recovery: only three held-out frames were assessed, the camera moves, the projection is oblique, calibration is approximate and annotation uncertainty is unquantified. No confidence interval or physical precision is claimed. The local-fit values are an interpretation, not measured component dimensions.

Reproduce with a compatible, lawfully obtained local copy and a running backend:

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_eitech --video 'C:\path\Schubkurbelgetriebe_(Eitech).mp4'
```

It produces private `output/real-video/eitech-evaluation.json` and a loadable `eitech-project.json`, and imports the source into private `data/`. Open that project from My machines. A separate screenshot utility displays its real video and interpreted model without performing inference.

## Stronger pre-submission experiment

Use a static front-facing camera, short exposure, high-contrast joint markers and a measured length in the mechanism plane. Record multiple complete cycles. Freeze calibration using training data only. Reserve a contiguous later time interval and manually annotate visible centers there, preferably with a second annotator.

Run the exact same seeded frames through the LK baseline and, after authorization, SAM. Evaluate mask/box tracking separately from joint localization: SAM is not automatically a joint-center estimator. Report coverage, identity changes, loss/occlusion frames, manual correction count, and RMSE/max error only over aligned samples. Never give a lost track a zero error. Report annotation disagreement or a defensible uncertainty interval only when measured.

Compare a fixed model, a training-fit model and the simple baseline on the same reserved observations. Add perspective rectification from known planar calibration points and camera stabilization before making claims on handheld oblique footage. Publish the protocol, exact input hash, splits and limitations alongside any metric.
