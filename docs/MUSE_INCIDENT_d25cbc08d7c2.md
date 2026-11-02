# Muse incident d25cbc08d7c2 — evidence and repair

Investigated against checkpoint d90728e. No new paid request, retry, upload, publication or submission was performed. Operator configuration was found enabled, then safely changed to META_ALLOW_PAID=false and the local server restarted. Credentials were not printed or placed in Git.

## What is established

- The preserved local access log contains one `POST /api/lab/muse/quote` returning 200 followed by one `POST /api/lab/muse/run` returning 502. This proves the local attempt; it is not a provider billing receipt.
- The user reports the generic failure bearing d25cbc08d7c2 for “Duplica la velocidad angular del mecanismo”. Its reference quote was US$0.004736.
- The old code consumed the in-memory quote before entering the provider request block, generated a diagnostic ID, and caught transport/JSON/tool-validation/filesystem errors under the same message. It did not preserve failed diagnostics or usage before parsing. Only fully successful results were written to disk.
- No corresponding successful Muse evidence file, retained HTTP response, external HTTP code, token usage or provider request ID exists in the available local artifacts. The diagnostic string was not logged. Original logs were copied privately into `output/muse-incident-d25cbc08d7c2/` before restart.

Therefore the exact original category is **undetermined**. It is incorrect to declare timeout, insufficient completion tokens, parser failure, provider rejection or disk failure as the root cause. The request path attempted provider I/O, but available evidence cannot confirm provider receipt, inference completion or the amount billed. Known HTTP rejections normally had a separate handler, but the runtime response itself was not retained and cannot be reconstructed from the generic UI string.

## Consumption check and access limitation

The [official usage guide](https://dev.meta.ai/help/usage-and-limits/api-usage) describes a Team usage dashboard with model/date filters and combined API/Playground totals. It does not establish a documented per-diagnostic historical lookup for this local UUID. No guessed usage endpoint was called and no inference was sent to test connectivity.

The existing Meta browser window was located for read-only inspection, but Computer Use stopped because it could not determine the browser URL sufficiently to enforce policy. That protection was not bypassed. Previous usage remains **unavailable**, not zero. Future usage can be preserved from the response before parsing; account-level billing still belongs to Meta's records.

## Repaired locally

`backend/muse_trial.py` now journals an atomic, safe diagnostic before any provider I/O. Unavailable storage blocks the operation before spending. Stages distinguish preflight, transport, HTTP response, JSON decoding, tool parsing, local solver validation, result persistence and completion. The diagnostic records planned/attempted request counts separately, HTTP status when known, receipt of an external HTTP response, safe request correlation ID, allowed finish reasons/tool-call counts and reported token totals. No raw exception strings, credentials, Authorization headers or private response text are persisted or returned.

Usage is captured before tool-call validation. A truncated or malformed successful HTTP result remains an unsuccessful integration result, with usage retained when available. Filesystem failure after a valid response is separately identified as persistence failure; HTTP billing/quota rejection, timeout, connection/disconnection and parsing have distinct categories. If the diagnostic itself cannot be persisted, the safe error response says so. Truncation is classified as incomplete_response, a plain completed answer without a tool as no_tool_call, and a content-filter finish as refusal; these are not confused with invalid tool arguments. The frontend formats this diagnostic legibly and preserves “usage unavailable” rather than displaying a fictitious zero.

Quotes still expire, are single-use and consumed for an attempted authorized operation. There is no automatic retry or fallback to a fake live result. Tests use MockTransport with synthetic credentials; the real server flag stays false. The completion limit remains 512: there is no evidence justifying a claim that this limit caused the original incident.

## Scientific and presentation status

The original SAM export and 442-frame input were preserved. Offline re-audit finds 300 records, 3 IDs, 150 boxes/150 masks, 50 mask frames per ID and the original diagnostic e14d21bb8f3c. The frame29/horizon8 replay remains model9.1046 px / constant23.9297 px / linear75.5859 px for the same eight observations. The source cut37–38 and full-video SAM context remain disclosed. No independent experiment can be claimed without a new continuous recording, a prior fixed protocol and separate blinded future labels. The seal/evaluator tools are ready, but no missing real data were fabricated.

The five-act demo, alternate models, mock review/confirmation, evidence exports and restart recovery remain the judge-ready local flow. Real Muse remains **unverified**. Official full submission fields, converted-media lineage and new independent evidence remain release gates; see HACKATHON_REQUIREMENTS.md, ATTRIBUTIONS.md and REALITY_LAB.md. Public organizer/pricing pages were rechecked without submitting anything.

## One possible subsequent economic authorization

After local repair verification, one fresh controlled Muse request would establish the actual live outcome with the new telemetry. Reference budget remains 2,048 input-token allowance plus 512 completion-token cap, estimated US$0.004736 using [official Standard rates](https://dev.meta.ai/docs/pricing-rate-limits). This is an estimate, not an authoritative token count or hard billing ceiling. A new authorization is required; the prior one has not been reused.

On approval the agent, rather than the user, will temporarily enable the flag, restart, prepare a NEW quote bound to the exact instruction/parameters, issue exactly one request, preserve its actual outcome, and return the server/configuration to paid=false. No repeated attempt is authorized by that approval. No commands or manual configuration work are required from the user. A model explanation requiring another completion is not included.

## Executed verification and final state

113 Python, 23 TypeScript, 17 browser cases and production build passed. Playwright CLI confirmed the local budget remains disabled with zero console errors/warnings. Twenty focused Muse tests were rechecked after final phase-classification changes. New tests distinguish preflight storage failure (zero request attempts) from storage failure after HTTP200, preserve usage on truncation and keep private exception text out of diagnostics. A browser mock confirms that rpm40 remains unchanged until confirmation, then the alternate uses rpm80 and the solver's expected displacement difference at t=0.25s. Its synthetic provenance stays visible; no real provider call was made by tests. A browser run interrupted by a restart was discarded; the subsequent full uninterrupted run passed.

Saved real replay recovery after actual backend restart matched the captured response hash. Private `output/muse-incident-d25cbc08d7c2/restart-check.json` records that comparison. The source video and SAM export remain unchanged. Existing bundle-size and Starlette TestClient deprecation warnings remain. No release, public deployment or hackathon submission occurred.
