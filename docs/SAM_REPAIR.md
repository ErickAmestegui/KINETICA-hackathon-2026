# SAM 3.1 — offline repair and verification

28 October 2026. Existing KINETICA repository; no new project. The pre-existing diagnostic change was preserved in Git commit `8d19e10` before edits.

## Incident and limits of the conclusion

The user reports one Eitech request (442 frames, prompt `white foam block`), approximately 442 additional frames accounted by Meta, and a local HTTP 502: `SAM transport, parser or response failed; no inference retry.` This is evidence of a failed application workflow, **not evidence that timeout or parser failure caused it**. No captured response or sufficiently specific original diagnostic was available to reproduce that incident. Do not claim its root cause is fixed or identified.

This repair made **zero requests to Meta's API**: no catalogue request, upload, inference, deletion, authentication or billing operation. Only public documentation was consulted. The private `.env` had `META_ALLOW_PAID=false`; the running backend was restarted with the same false flag. Tests do not inherit the operator key. No credentials, remote response bodies or private media are versioned.

## Verified defects and corrections

1. The official parser wraps source exceptions in `ResponsesStreamSourceError`. The former broad handler hid HTTP/connection/timeout distinctions. Synthetic tests first reproduced this information loss. The replacement inspects bounded exception-cause chains by known types/codes, without reading their messages or embedded events.
2. Former cleanup information was lost on some exception paths. A single DELETE attempt now runs after an acknowledged upload regardless of parse outcome; cleanup status and failure are independent fields even in HTTP 502 responses. Unknown upload acknowledgement is explicit. Remote IDs are not put in logs or error messages.
3. `asdict(outcome)` could include provider `detail`; this is now reduced to allowlisted status/reason. Raw parser diagnostic text/messages and arbitrary usage fields are also excluded.
4. Accepted partial geometry is retained using the latest cumulative parser snapshot. Snapshots are not appended together. Fatal errors cannot turn partial records into a completed result.
5. Frontend records failure responses, preserves status through save/restore and report export, and displays persistent warnings in Compare, Meta and Report views. Older overlay-only projects without outcome receive an unknown-status warning. Segmentation never sets `reconstruction_verified=true` and never changes joint observations or fit parameters.

## Contract checked

- [Official client libraries](https://dev.meta.ai/docs/sam/client-libraries): installed `meta-sam-parser==0.1.0` public Python interface is `parse_responses_stream(..., video_segmentation_format())`. Single-consumer stream; cumulative snapshots; official SVG mask decoder. `completed` requires a valid terminal event and finalized text lane. EOF is incomplete, not success. Recoverable malformed records remain diagnostics.
- [Segmentation and upload](https://dev.meta.ai/docs/sam/segmenting): `POST /v1/files`, `purpose=user_data`, synchronous successful upload, then `input_video.file_id` on streamed `/responses`. No readiness polling needed. Request uses `one_bit` masks and confidence metadata. Upload ID is validated before forming a deletion URL.
- [Pricing](https://dev.meta.ai/docs/pricing-rate-limits): $0.20 per 1,000 video frames, 50-frame minimum; `usage.video_frames_processed` is the billed frame count. Known numeric usage fields are retained; arbitrary provider fields are not.

## Outcome and HTTP semantics

| Outcome | Local behavior |
|---|---|
| `completed` | HTTP 200; final accepted geometry, including legitimately empty detections; diagnostic count remains visible. Completion is not a validated reconstruction. |
| `incomplete`, `reason=response` | HTTP 200; explicit API-declared partial result. No automatic continuation/retry. |
| `incomplete`, `reason=eof` | HTTP 200; stream ended without a valid terminal event; category `premature_eof`. `[DONE]` alone cannot certify completion. |
| `failed` | HTTP 502 with structured `detail`; any accepted partial geometry is inspection-only. Categories distinguish HTTP status, timeout, connection, disconnection, SSE framing/JSON/encoding, parser lane, API failed/error/refusal, mask conversion, upload contract and internal error. |

`cleanup.status` is separately `not_needed`, `deleted`, `failed` or `unknown_upload`. A cleanup error never replaces the inference error or changes a completed segmentation to a successful cleanup. Inspect the remote dashboard manually before another paid request when cleanup is uncertain; no remote action is authorized in this session.

`SAM_DIAGNOSTIC` includes a randomly generated local ID, phase, byte/event counts, last allowlisted event type, failure category, HTTP status, parser code and cleanup result. It excludes headers, key, filenames, remote IDs, prompts, masks, exception messages, provider bodies and parser raw output. Structured geometry is returned privately to the local UI, not written to diagnostic logs.

The SSE layer accepts fragmented UTF-8, CR/LF/CRLF, comments, multiline data, a last data field at EOF and `[DONE]`. Decompressed input is capped at 64 MiB. Existing 180-second HTTP timeout /20-second connect timeout were retained; they were **not** lengthened on an unproven timeout hypothesis. No inference retry was added.

## Offline proof

- **68 Python tests passed**: original mathematics/vision/API tests plus 39 SAM offline cases. Real official mask decoding; partial snapshots; completed/failed/incomplete/empty streams; fragmented SSE and UTF-8; safe usage; 400/401/402/403/429/500 at upload and stream stages; read/write timeouts; connection errors; protocol disconnects; malformed JSON/encoding/event shapes; cleanup failure both after success and failure; unknown upload ID; parser lane/mask failure; authorization before I/O; log sentinel exclusion.
- **13 TypeScript tests passed**, including all three outcome labels and cleanup warnings.
- **8 Playwright tests passed** in Chrome, including three fully mocked SAM workflows (502 included), saved-project restoration, report download, blocked inference-route fallback, and all four existing studio/video/responsive cases. The optional existing Eitech diagnostic project was available and passed.
- Production build passes. Existing large JS chunk warning remains. Python emits the existing Starlette/httpx TestClient deprecation warning. No dependency upgrades were needed.

Python `tests/conftest.py` replaces environment values before dotenv loading, fixes `META_ALLOW_PAID=false`, blocks real HTTPX transports and non-loopback socket connections. Only explicit `MockTransport` clients are used in protocol integration tests. A test-local authorization stub allows exercising transport code without ever enabling the environment flag; its headers are a fixed dummy string. The unmodified SAM and Muse entry points are separately proven to reject approved requests before client construction when the flag is false.

Every current browser spec imports `e2e/fixtures.ts`: non-local URLs are aborted, catalogue is mocked, unmocked `/api/meta/run` is rejected, and service workers are blocked. The SAM UI cases supply synthetic permissions and responses entirely in Playwright interception; those permissions never reach/change the backend. All added screenshots say Synthetic video test and are local mock evidence only.

Commands from the repository root:

```powershell
$env:TEMP=(Resolve-Path output/tmp).Path
$env:TMP=$env:TEMP
.venv/Scripts/python.exe -m pytest tests -q
Set-Location frontend
npm.cmd test
npm.cmd run build
npm.cmd run test:e2e
```

E2E requires the local server and the existing synthetic clip (`scripts/make_synthetic_fixture.py` creates it). Windows sandbox socket/temporary-directory restrictions may require execution permissions for local tests; this is not permission for external Meta requests.

## Prepared private input

`output/sam-local/eitech-50-cfr.mp4`: decoded and verified **50 frames, 25 fps, 2.00 seconds, 960×540**, source frames 150–199 inclusive. Local H.264 re-encode with no B frames, audio removed, constant-rate timestamps. Adjacent JSON records source/clip SHA-256 and transformations. Both are ignored by Git; no upload was made.

The first timestamp-preserving encode had inconsistent duration/frame metadata and decoded only 49 frames in both OpenCV and FFmpeg. It is explicitly rejected and retained under a REJECTED filename. The corrected clip uses explicit constant-rate timestamps and was independently decoded again. This media-preparation issue is separate from the original SAM incident.

Reproduce with `scripts/prepare_sam_clip.py --video <private-original-path> --start 150 --output <new-private-output.mp4>`. The script refuses to overwrite files and verifies all 50 frames by decoding.

## Conditions for a future live test — not authorization

1. Explicit new user approval for one request, the exact 50-frame clip, prompt `white foam block`, and media transfer; recheck pricing. Current estimated segmentation charge is **US$0.0100** (50 × $0.20 /1,000), subject to account terms. No retry or larger clip is included.
2. Confirm private credential setup without sharing its value; confirm the previous remote upload's retention/cleanup status through an authorized operation. No such check was performed here.
3. Only after that new authorization may the operator change the payment gate for the one request. Keep it false now and disable it again immediately after the authorized run.
4. Record only safe diagnostics, outcome, numeric usage, geometry and cleanup status locally. Compare actual masks to the clip; keep partial/failure labels. Never claim joints, accurate reconstruction or an unobserved success.

Outstanding: original incident cause, authenticated end-to-end response behavior, actual `one_bit` service output/usage and real cleanup remain unverified. Offline mocks cannot establish them.
