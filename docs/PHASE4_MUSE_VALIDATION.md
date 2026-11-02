# Phase 4 — preparing an authentic Muse trial and an independent-validation protocol (neither result is claimed)

Prepared 2026-10-29 from checkpoint 96a8615. No billable request, catalogue request, upload, publication or submission. `META_ALLOW_PAID=false` throughout this work. Original video/SAM evidence is retained.

## What changed

The original Ask adapter produced a structured proposed-call object but did not consume an authentic `tool_calls` response. The new `backend/muse_trial.py` implements a single Chat Completions request with one developer-defined function, `propose_parameter_change`, strict parameters, `tool_choice:auto` and `parallel_tool_calls:false`. It rejects plain text, refusals, truncation, multiple calls, unexpected function names, nonnumeric/nonfinite values and extra properties. Local geometry validation follows parsing. The original mock and structured-output helper remain available; the angular-speed mock bug was corrected so “duplica la velocidad angular” doubles rpm rather than stroke.

Official contract: [tool calling](https://dev.meta.ai/docs/tool-calling), [cookbook](https://dev.meta.ai/docs/cookbook/tool-function-calling). Current documentation states only `auto` is supported for tool choice. `strict:true` validates the schema subset on the server; it does not remove the need to validate returned arguments. A model may choose plain text: that is recorded as an unsuccessful trial, never silently retried or relabeled as success.

The model proposes; KINETICA validates and computes an original/proposed position/velocity preview at t=0.25 s with the existing solver. The user must then confirm an alternate change. No arbitrary file, shell, code or built-in web tool is supplied. A model explanation would require a separate request and budget; none is automatic. `model_live_verified` is set only after a real HTTP result passes the permitted-call parser. No authentic Muse result has been obtained in this phase.

## Concrete trial budget

Instruction: **Duplica la velocidad angular del mecanismo**. CLI reference parameters: r32, L128, rpm40, e0, phase0, with proposed rpm80 expected. A different valid tool response is reviewed as received rather than fabricated into the expected answer.

Model: `muse-spark-1.3`, Standard mode. Text only, no video/images/paths. One request; zero retries; 512 maximum completion tokens, including any model reasoning covered by that limit. No second explanation completion.

[Official pricing](https://dev.meta.ai/docs/pricing-rate-limits), checked 2026-10-29: input US$1.25/million, output US$4.25/million. Reference input allowance 2,048 tokens, output limit 512:

`2048 × 1.25 / 1e6 + 512 × 4.25 / 1e6 = US$0.004736`.

The offline allowance is max(2,048, UTF-8 serialized request bytes + 256 framing provision). It is deliberately labeled an estimate, **not an authoritative tokenizer result or guaranteed billing cap**. No provider token-count endpoint is called. Actual usage is retained if returned; billing interpretation and credits require account verification. No cached-input discount is assumed.

Each quote is bound to immutable server-held prompt/parameters/payload hash, expires in five minutes and is single-use. A quote prepared with paid=false cannot later be executed after enabling payments: a fresh quote is mandatory. A token is consumed before inference and cannot be reused after timeout, HTTP error or parser failure. Transport redirects and retries are disabled. Failed attempts do not switch automatically to a mock or retry. Only safe diagnostics and selected usage fields persist; raw private response bodies and Authorization headers are not logged.

## Future ONE-request procedure — not authorized now

1. Obtain new explicit human authorization for this specific text, model, parameters and estimated amount. Keep current paid=false until that happens.
2. Only after approval, privately enable META_ALLOW_PAID=true and restart the local backend. Do not add payments or subscriptions. This is a future operator step, not performed here.
3. In Reality Lab → Ask the Machine choose “Use angular-speed trial prompt”, then “Prepare Muse token estimate”. Verify exact prompt, parameter snapshot, estimate and one request. A disabled-era quote must not be reused.
4. Press “Authorize ONE real Muse trial” exactly once. No automatic retry or follow-up call occurs. Review the returned permitted tool, local validation, usage and diagnostic. Successful parsed evidence is stored privately in `data/muse-evidence/muse-<diagnostic>.json`. If the request fails, stop and inspect account usage before considering another authorization.
5. Review before “Confirm alternate change”. The original model remains unchanged. Return META_ALLOW_PAID=false and restart. Preserve the authentic evidence privately; do not publish it without review.

Equivalent future local CLI:

```powershell
# Safe now: estimate only, no inference.
.venv/Scripts/python.exe scripts/muse_trial.py quote
# ONLY after fresh human authorization and a NEW enabled quote:
.venv/Scripts/python.exe scripts/muse_trial.py run --quote output/muse-trial/NEW_QUOTE_ID.json --approve-one
```

Never paste the API key into chat. The CLI talks only to the local backend. It cannot execute a quote prepared while disabled. The GUI has a disabled run button under the current configuration.

## Persistence after restart

Reveal now automatically saves a content-addressed JSON under `data/<video-id>/lab-results/`. The report binds the source video SHA-256. `GET /api/videos/<id>/lab/results` lists local artifacts; the corresponding `<evidence-id>` route checks report/source integrity before recovery. “Recover preserved replay” reloads historical results even after in-memory sessions disappear. The recovered record remains historical replay evidence and cannot be used as a fresh blind prediction. Project JSON retains study/preferences; the private data folder remains necessary for video/result recovery. Muse evidence is separately persisted; pending quote authorizations are intentionally not restored after restart.

## Independent protocol — designed, not yet performed

The eight-frame Eitech result remains retrospective: 9.10 px model / 23.93 px constant / 75.59 px linear for the same frames30–37 after freeze29. It does not establish independent validation. The original full-video SAM request may have incorporated future temporal context; local optimizer isolation alone cannot rule that out.

Use a new, continuous fixed-tripod recording of a planar mechanism with visible joint/slider markers, no cuts, speed changes from editing or frame duplication. Record timing, calibration and source hash; declare r/L/e assumptions before fitting. Choose cutoff/horizon using a pilot recording and commit the protocol before opening future labels. A template is in `sample-data/independent-protocol.template.json` and is intentionally NOT an experiment.

Keep training-only observations separate. Use manual past annotations or a genuinely causal tracking/segmentation process restricted to the past clip; the old full-video SAM run cannot satisfy that condition. Freeze the model and export “sealed forecast” before reveal. Separately, a blinded annotator labels future frames in image pixels without seeing predictions. Store `video_sha256`, `source:manual_future_blinded` and `points:[{frame,t,x,y}]` in a separate file. The new evaluator does no fitting and never opens future labels during sealing.

```powershell
# Fill a NEW protocol, change status to preregistered_local, commit/hash it first.
.venv/Scripts/python.exe scripts/independent_protocol.py seal --protocol output/NEW-protocol.json --forecast output/kinetica-sealed-forecast.json --out output/NEW-seal.json
# Only after sealing, obtain separate future manual annotations:
.venv/Scripts/python.exe scripts/independent_protocol.py evaluate --seal output/NEW-seal.json --annotations output/NEW-future-labels.json --out output/NEW-evaluation.json
```

Files are created exclusively, never overwritten. Source/split agreement, disjoint training frames, complete evaluation frames, timestamps and seal integrity are checked. All methods share identical future frames: model, final training position, linear OLS on last eight training centroids. Report RMSE in pixels with sample count and no post-hoc exclusions. Missing labels invalidate the evaluation rather than interpolating. The evaluator reports independence_verified=false because a local hash cannot prove prior external registration, blinding or capture conditions. Attach that evidence separately before asserting independence. No independent RMSE is invented here.

## Demonstration and release

Use the existing five-act three-minute walkthrough in REALITY_LAB.md. Observe saved authentic SAM masks; freeze/reveal as retrospective replay; show cut-crossing No evaluado; modify relative geometry; then show the mock alongside the blocked real Muse budget. Do not imply the mock is authentic Muse. After a future authorized real trial, replace that section only with its actual preserved outcome.

See HACKATHON_REQUIREMENTS.md for confirmed public event facts versus unverified official submission requirements, and ATTRIBUTIONS.md for audiovisual conditions. No application submission or publication is authorized by this preparation.

## Executed verification

110 Python tests, 22 TypeScript tests, 16 Chrome E2E cases and production build passed. The new tests use MockTransport and synthetic credentials only; global fixtures forbid real external transports. They cover one-use authorization after success/HTTP billing/quota/timeout/parser failures, disabled-era quote rejection, strict numeric arguments, tool allowlist, separate future labels, sealed integrity and disk recovery after session loss. The browser verifies the exact reference token budget, disabled execution, quote invalidation on text edits and preserved replay recovery. An actual local backend stop/start recovered the real eight-frame report byte-identically, with the same pixel metrics; `output/phase4-restart-check.json` is private evidence. CLI budget preparation made no Meta request. Existing bundle-size/TestClient deprecation warnings remain.
