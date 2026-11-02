# Meta integration: implemented versus verified

Checked against official docs on 2026-10-28:

- [Overview / model IDs](https://dev.meta.ai/docs/overview)
- [SAM prompts and video file IDs](https://dev.meta.ai/docs/sam/segmenting)
- [Official parser contract](https://dev.meta.ai/docs/sam/client-libraries)
- [Structured outputs](https://dev.meta.ai/docs/structured-output)
- [Pricing](https://dev.meta.ai/docs/pricing-rate-limits)

Base URL: `https://api.meta.ai/v1`. Models: `sam-3.1`, `muse-spark-1.3`. Standard mode only; no Contributor mode permission is silently granted.

## Current saved-response evidence (2026-10-29)

The private original export corroborates diagnostic e14d21bb8f3c: completed, 300 geometry records, zero parser diagnostics and cleanup recorded as deleted. Phase 2 performs only local measurement and does not recheck remote storage or consume credits. See [MASK_MOTION.md](MASK_MOTION.md). Keep META_ALLOW_PAID=false. The previous failed 442-frame request remains a separate unresolved incident.

## Historical state after offline SAM repair

The user reports a 442-frame SAM request counted by Meta but ending in local HTTP 502. Its cause is not identified. A private `.env` now exists and `META_ALLOW_PAID=false` remains enforced. This repair made **no Meta API requests**, including no catalogue check. See [SAM_REPAIR.md](SAM_REPAIR.md) for contracts, safe diagnostics, partial/failed handling, offline tests and the private 50-frame candidate clip. Do not follow spending steps below without new explicit authorization.

## Verified locally

The installed `meta-sam-parser==0.1.0` exposes `parse_responses_stream(events, video_segmentation_format())`, not a Python `parse_video_stream` convenience function. KINETICA uses the actual installed public interface. It validates stream lanes and termination, decodes official masks to local SVG paths, carries frame and object IDs, and retains diagnostics. Box-local mask coordinates are translated/scaled using their reported bounds.

Tests exercise an official published mask example, chunk boundaries, no detections, malformed records, premature EOF, failed response events, authorization gates and sanitized 400/401/402/403/429/500 errors. These are **protocol/test fixtures**, not an authenticated response received by this app.

## Implemented call paths

SAM: upload the approved clip to `/files` with purpose `user_data`, pass `file_id` in an `input_video` part to streamed `/responses`, consume SSE with the official parser, and attempt deletion of the remote upload after processing. Cleanup failure is surfaced. Text prompts or manually selected box prompts are supported. The full clip is billed; selection does not silently imply a shorter tracking range.

Muse: extract three ordered video frames locally, resize to a maximum dimension of 640 pixels, encode JPEG, call `/chat/completions` with a strict JSON schema, and independently validate the returned structure. It proposes visible components, joint types, evidence and limitations. It does not recover exact geometry or execute generated code. No response is fabricated when unavailable.

## Historical initial-build evidence (superseded by incident below)

On this computer, checks returned false for `MODEL_API_KEY` in process, user and machine environment; `.env` did not exist. `/api/meta/status` reported missing key. `/api/meta/catalogue` returned local HTTP 503 before any upstream request. No claim about the actual account's authentication, quota, promotional balance or billing can be made from this result.

The user's prior Playground result is separate evidence: user reports preliminary SAM tracking of foam blocks in Eitech footage. It is not imported/captured API evidence and does not prove joint localization.

## Next authorized verification

1. Privately set `MODEL_API_KEY` in `.env` or the backend environment; never paste it in chat. Keep `META_ALLOW_PAID=false`.
2. Restart backend and use the read-only catalogue button. Preserve only status/model IDs, not headers or secrets. A successful catalogue does not prove inference eligibility.
3. Prepare a quote with the intended video and model. Authorize a concrete request only after reviewing price and media transfer. Enable `META_ALLOW_PAID=true` locally only when ready. Each quote expires after five minutes and is consumed once.
4. SAM pricing checked: $0.20/1,000 video frames, minimum 50 frames; $2.50/1,000 images. Eitech's 442-frame clip would have an estimated segmentation price of **$0.0884** for one full-clip request at that rate. This is an estimate, not authorization. Recheck provider pricing/account conditions before spending.
5. Muse pricing checked: $1.25/1M input tokens and $4.25/1M output tokens. UI uses a $0.03 planning estimate for three resized frames and at most 1,800 output tokens. Exact image/input/reasoning token usage may differ; this estimate is **not a guaranteed cap**.
6. Run once. Save actual usage, completion state, object IDs, no-object cases, parser diagnostics and overlays. Compare them to manually identified centers/regions. If billing fails, preserve the sanitized HTTP status and continue local work. No retry loop.

Before submission, add an actual-response regression fixture only after removing private media/metadata and obtaining any necessary rights. Until then, live SAM parsing, Muse schema acceptance, billing eligibility and remote cleanup remain unverified.
