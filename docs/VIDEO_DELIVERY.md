# Reality Lab video delivery

Prepared locally on 2 November 2026; the final master (166.16 s) was re-recorded after review showed the first take's Observe chapter did not make the SAM masks visible. The first take is kept privately under `output/submission-video/superseded-v1/`. A final render from the same recording balanced caption lengths (no cue shorter than 4.4 s; sidecar lines of at most 58 characters) after the full review found 0.5-second one-word tail cues; that intermediate render is under `superseded-v2/`. Publication settings and the final description are in [VIDEO_PUBLICATION.md](VIDEO_PUBLICATION.md). The authenticated form's **3-Minute Demo Video** field establishes the duration target. The YouTube placeholder does not by itself establish an exclusive hosting requirement or a required codec. No video has been uploaded or published.

## Finished deliverables

Private files are in `output/submission-video/`:

- `KINETICA-Reality-Lab-demo-1080p.mp4`: actual application screen recording, edited with English offline narration, English burned-in captions and a source/license credit slate.
- `kinetica-demo.en.srt`, `.en.vtt`, `.es.srt`, `.es.vtt`: English and Spanish captions.
- `transcript.en.txt`, `transcript.es.txt`: timed narration and translation for review.
- `CREDITS.txt`: source, author, license, links and changes.
- `YOUTUBE_DESCRIPTION.txt`: review-ready technical description and required source/license credits, with public links still gated on approval.
- `video-manifest.json`: exact duration, dimensions, frame rate, codecs, SHA-256, source/export hashes and chapter timings.
- `authentic-screen-recording.webm`, `capture.json`: unaltered browser viewport recording and action timing record, retained privately for verification.
- `qa-*.jpg`: decoded frames sampled from each finished chapter for visual review.

The MP4 uses H.264/yuv420p at 1920×1080, 25 fps and AAC narration. These are compatibility choices, not an assertion that the form mandates this format. Exact measured duration and size are in the manifest. The rendering command rejects a master longer than 180 seconds.

## What was actually recorded

Observe first opens the existing Compare view, where the app's own status reads "SAM completed. 300 geometry records" and the saved Meta SAM 3.1 boxes/IDs follow the authentic clip played once at the UI's visible 0.5× speed beside the live 3D model. It then returns to Reality Lab and plays the same two-second clip at its real rate. Reality Lab draws the masks at low opacity over similarly coloured parts, so the Compare shot is what makes them legible. The clip is replayed, not extended into invented observations. The original response contains 150 boxes and 150 contours, three IDs across 50 frames. Slider identity is explicitly confirmed through the existing UI.

Predict freezes the local model at frame29/horizon8; Reveal displays the same eight observations and the actual UI values 9.10px / 23.93px / 75.59px. A separate horizon20 sequence displays the source-cut guard and null scores. Break Reality records solver-driven models, impossible-stroke rejection and a feasible change. Ask records only the deterministic mock, with its visible provenance and confirmation before changes. No live Muse success is claimed.

The source/export hashes are checked before and after recording. The browser blocks non-loopback hosts, Meta catalogue and both paid inference routes. No model calls, payments, source modification or synthetic replacement UI were used. Only genuine local UI interactions are recorded. Setup is trimmed; actions and computations run at their recorded rate. Playwright's repeated-frame rounding makes its media clock slightly different from action wall time; chapter/caption positions are mapped proportionally to that recorded clock, without speeding, replacing or inventing screen frames. Narration, subtitles, bottom caption band and clearly editorial end credits are added during video editing.

The scientific limits are spoken and captioned: retrospective inspected-data replay; full-video SAM context; declared geometry; no physical reconstruction accuracy; no independent prospective validation; no forces, materials or buildability evaluation; failed real Muse trial remains unverified.

## Reproduce without cloud services or new dependencies

Use the existing repository, private SAM project/source, installed frontend dependencies, Chrome and existing `imageio-ffmpeg`. Start the local production app first, with `META_ALLOW_PAID=false`:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_video.py --help
node scripts/capture_demo_video.cjs --help

.\.venv\Scripts\python.exe scripts/prepare_demo_video.py --prepare
node scripts/capture_demo_video.cjs --smoke
node scripts/capture_demo_video.cjs
.\.venv\Scripts\python.exe scripts/prepare_demo_video.py --render
```

Narration uses the already installed **Microsoft Zira Desktop** Windows voice through `System.Speech`, entirely offline. The PowerShell child uses only process-scoped script execution; no system policy is changed. Some restricted environments need approved local host permissions for Windows speech and Chrome processes.

The locked Playwright recording runtime initially lacked FFmpeg1011. The newer installed Playwright FFmpeg1013 supports VP9 only, while Playwright1.56.1 requests VP8; the first recording therefore produced no usable video and was rejected. The capture script now verifies VP8 support and reuses the existing optional `imageio-ffmpeg` binary in a workspace-only cache under ignored `output/submission-video/runtime/`. A two-second genuine-app encoder smoke check verifies the recording before the full take. Nothing is downloaded, installed or redistributed. The final encoder also comes from the existing `imageio-ffmpeg` dependency. Python Playwright was absent, so capture uses the project's installed Node Playwright rather than adding a redundant dependency.

Documentation consulted: [Playwright video recording](https://github.com/microsoft/playwright/blob/main/docs/src/videos.md), retrieved through Context7, including explicit recording size and awaiting context close. The installed 1.56.1 API is used without newer optional recording features.

## Rights and approval gates

Footage: **Schubkurbelgetriebe (Eitech), Rhetos, Wikimedia Commons, CC BY-SA4.0**. Source root identity and clip lineage are verified in [RELEASE_RIGHTS.md](RELEASE_RIGHTS.md). The audiovisual adaptation is prepared under CC BY-SA4.0; the original application code remains MIT. The visible end slate and credits retain the author, source/license links and adaptation notice. No stock music or third-party generated imagery was added. Narration is explicitly identified as offline synthesized speech.

This is a private review master. Public upload requires the user's approval, including the audiovisual license and review of contest terms. The full contest grant/sole-ownership warranties require participant review; a verified CC license does not authorize the entrant to promise unlimited rights on behalf of the original creator. No public URL exists yet, and no video field has been populated or submitted.
