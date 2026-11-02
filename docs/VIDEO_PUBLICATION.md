# Demo video — publication sheet (prepared, not uploaded)

**Submission video: original-media version.** File `KINETICA-Reality-Lab-demo-1080p.mp4` from `output/submission-video-original/`, 2:48 (168.16 s), 1920×1080 H.264/AAC, −20.2 LUFS, true peak −2.0 dBFS. SHA-256 `4e90552ed457cce48d9f11f1139ddce7d6df98e0f6cc67f70d33a0af645263c2`. Captions: English burned in; sidecars `kinetica-demo.en.srt` and `kinetica-demo.es.srt`.

It is a genuine screen recording of the local application running on an **original synthetic clip** rendered by KINETICA's own code. It contains no third-party footage, images or music. The earlier Eitech-footage version is kept only as historical evidence and must not be uploaded unless the competition's media conditions are resolved in writing.

## Upload settings (requires entrant approval)

- **Platform / visibility:** YouTube, **Unlisted** (judges need only the link).
- **License:** **Standard YouTube License**.
- **AI use (Attributes):** proposed **No**. YouTube asks for disclosure of realistic AI-generated or altered content ([policy](https://support.google.com/youtube/answer/14328491)). This clip is a procedural, non-photorealistic render, labeled synthetic, not made with generative AI; the narration is a generic offline text-to-speech voice that imitates no real person and is disclosed in the description.
- **Audience:** not made for kids. **Category:** Science & Technology. **Language:** English.
- **Subtitles:** upload `kinetica-demo.en.srt` (English) and `kinetica-demo.es.srt` (Spanish).
- **Optional backup:** attach the same MP4 and SRT files to a GitHub Release `v1.0-hackathon`.

## Title

KINETICA Reality Lab — from footage to a testable machine (original synthetic demo, Meta SAM 3.1)

## Description

```text
KINETICA Reality Lab turns observed mechanism motion into a mechanical hypothesis you can inspect, challenge and change. This is a genuine screen recording of the local app, running on an ORIGINAL SYNTHETIC clip rendered by KINETICA's own code. It is not a real recording. No new model inference was made for this video.

0:00 Original material only
0:22 Observe — synthetic geometry, labeled as such
0:42 Predict — seal before reveal
1:01 Reveal — compare the same observations
1:21 Insufficient evidence is refused
1:37 Break Reality — solver-driven alternatives
1:59 Ask the Machine — labeled deterministic mock
2:18 Meta integration — where the real evidence lives

What is synthetic: the clip and its saved geometry (derived from the known motion plus measurement noise; not Meta SAM output). The true motion contains a motor speed ripple the model is not told about. Freezing after frame 74 with a 20-frame horizon gives model RMSE 7.67 px vs 52.05 px (constant) and 129.82 px (linear) on the same twenty observations. This checks the pipeline against a known ground truth; it is NOT validation on real footage.
What is real: Meta SAM 3.1 ran on a separate third-party clip (diagnostic e14d21bb8f3c: 150 boxes + 150 contours, three IDs over 50 frames). That footage and its geometry are kept as historical evidence, documented in the repository and not shown in this video. The Meta Model API panel shown at the end is the real integration: cost estimate first, paid inference blocked by default.
What is simulated or unverified: Break Reality is a counterfactual solver simulation. Ask the Machine is a deterministic mock. Live Muse Spark remains unverified after a failed trial.

Code (MIT): https://github.com/ErickAmestegui/KINETICA

All footage, geometry, captions and graphics are original work of the KINETICA entrant. Narration: offline synthetic voice (Microsoft Zira Desktop). No music or third-party footage.
```

The repository URL resolves only after the repository is made public.

## End credits (burned into the video)

KINETICA REALITY LAB · MEDIA / ORIGINAL MATERIAL ONLY · Footage: original synthetic clip rendered by scripts/make_original_demo_clip.py · Geometry: derived from known synthetic motion plus noise. Not Meta SAM output. · No third-party footage, music or images. Application code: MIT. · Real Meta SAM 3.1 evidence (300 records) belongs to a separate third-party clip; documented in the repository, not shown or applied in this video. · Narration synthesized offline. No new inference. Muse live remains unverified.

## Known on-screen wording

The stable interface uses some generic wording written for real footage: for example, "SAM completed" after the explicit "SIMULATED TEST — no real Meta inference" prefix in the Model connections panel, and footnotes on the Reveal panel about the saved SAM request. The narration, captions, the SYNTHETIC TEST badge, the per-frame clip label and the lower band ("ORIGINAL SYNTHETIC FOOTAGE, NOT A REAL RECORDING") state the provenance throughout. The Compare overlay, which prefixes saved boxes with "SAM #", is not shown in this video.
