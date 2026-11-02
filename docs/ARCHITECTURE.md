# Architecture and mathematical contract

The React studio runs an analytic solver on a shared clock. `engine.ts` supplies both the chart and `modelPose.ts`; `Machine.tsx` consumes the pose rather than maintaining an independent animation. During video playback the clock reads the HTML media element's presentation time. Frame stepping uses OpenCV decoder timestamps retained at import. CSS transforms never animate the mechanism.

FastAPI serves local uploads, frame thumbnails, LK tracking, SciPy fitting, validation and the Meta adapters. The production build is mounted on the same origin. Local data uses UUID directories, never filenames supplied by users. Metadata survives backend restarts. Browser project exports hold parameters, calibration, observations and inference evidence, while referencing video IDs.

## Coordinates

- Fixed crank center O = (0,0). Model x runs along the slider axis, y is upward, θ increases counterclockwise.
- `θ(t) = phase + rpm × 2π × t / 60`. Negative rpm is supported by the engine.
- Crank pin `A = (r cos θ, r sin θ)`.
- Right/open slider assembly `B = (r cos θ + √[L² − (e − r sin θ)²], e)`.
- Full-cycle nonsingular motion requires **r > 0 and L > r + |e|**. Equality is intentionally rejected. The crossed assembly is not implemented.
- With `q = e − r sin θ`, `h = √(L² − q²)`, slider velocity is `ω [−r sin θ + q r cos θ / h]`.
- Dead-center x bounds are `√[(L − r)² − e²]` and `√[(L + r)² − e²]`.
- No masses, torque, force, energy or hidden geometry are inferred.

Image coordinates have y downward. Calibration angle α is clockwise in image space, scale s is pixels/model-unit:

```
u = ox + s (cos α · x + sin α · y)
v = oy + s (sin α · x − cos α · y)
```

This is a **similarity projection**, not perspective rectification. A tilted camera generally projects a circle to an ellipse; this model cannot explain that exactly. `mm` is an explicit user scale declaration, not an independently verified calibration.

Renderer dimensions are normalized uniformly to fit the studio. Joint distances retain the physical ratios. Moving rod, crank and support planes are separated in z; eccentric base clearance adapts to the solver. Bushings/rails are stylized contact interfaces, not a manufacturing CAD solid or a general collision simulation. Tests verify the rendered endpoints and basic ground/guide clearance; they do not certify arbitrary part interference.

## Fitting and validation

SciPy minimizes concatenated pixel residuals of crank and slider centers with `soft_l1` loss and bounds, fitting r, positive rod clearance, rpm and phase. Origin, axis, scale and eccentricity are held fixed. Minimum: 12 training observations, both joints, 8 distinct frames and 0.7 revolution at the initial speed. Rank-deficient or nonconvergent solutions are rejected. This is a local solver: an incorrect speed initialization may find a wrong frequency.

Whole frames share one split. Held-out observations are never passed to the optimizer. Saved fitted-frame IDs guard against relabeling a previously fitted frame as validation. A contaminated split produces `No evaluado` until refitting. The report records train/validation sample counts, RMSE and maximum Euclidean pixel error; no match percentage is fabricated.

Nearby tracked samples are correlated. A separate contiguous time block and independent manual annotations are preferable to random per-frame splits. Local LK estimates are not independent ground truth for LK itself. Adjusting calibration after looking at validation contaminates scientific independence even if software prevents frame overlap; this remains a documented experimental responsibility.

## Provenance

1. Observations: `manual`, `opencv-lk`, or explicitly `synthetic` CSV samples. Footage has an independent real/synthetic/unclassified declaration.
2. AI: raw semantic proposals and parsed segmentation geometry, with outcomes/usage/diagnostics and model identification.
3. Manual corrections: replace a joint/frame sample with source `manual`; edits to proposals preserve original response evidence.
4. Simulation: parameters and algebraic positions, separate from image measurements.

SAM component IDs belong to masks/boxes, not joints. A user marks the joint center even when segmentation succeeds. Full occlusion/reentry can break object identity and requires review.

## Local security boundary

`MODEL_API_KEY` is read only on the backend from environment/private `.env`. No frontend key, arbitrary API URL, arbitrary model-executed code or remote file path is accepted. Mutating browser requests reject foreign origins and Host is restricted to localhost. Inference requires server opt-in, explicit request approval and an expiring one-use quote. No retries. Upstream error bodies are not exposed or logged.

This is single-user localhost software. It does not implement user accounts, authentication for hostile local processes, per-user data isolation, network deployment security or a global lifetime spend ledger. Input limits and no automatic remote calls reduce risk; they do not turn it into a public SaaS.

## Phase 4: tool-call authorization and persistent evidence

Ask mock remains `/api/lab/ask`. Real text-only preparation uses `/api/lab/muse/quote` → server-held immutable payload/hash and expiring one-use token. `/api/lab/muse/run` requires the server paid flag, individual approval and a fresh enabled quote; HTTPX performs one POST with zero retries. A permitted `tool_calls` response is parsed strictly, computed locally and preserved under private `data/muse-evidence/`. The browser receives only the sanitized proposal/result/usage. Confirmation changes the alternate model; no generated code executes and no second model completion is automatic.

Reveal snapshots are content-addressed under the source video's private lab-results folder, bind the video hash, and can be recovered after backend restart through the source-scoped results routes. Pending authorization and in-memory freeze tokens intentionally do not survive restart. The independent-validation module seals a preregistered protocol/prediction without opening future labels, then evaluates a separate future annotation file; hashes enforce integrity while independence remains unverified until capture/blinding evidence exists.
