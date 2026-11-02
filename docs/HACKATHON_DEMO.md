# Reality Lab — reproducible three-minute recording script

Prepared 2026-11-02 for the existing KINETICA workspace. Target: Indie Developer / Push the Frontier. Deadline: **4 November 2026, 22:00 Bolivia (UTC−4)**. The [authenticated form](SUBMISSION_FORM.md) now confirms a **3-Minute Demo Video** URL; encoding and duration tolerance are unspecified. Official Rules and exact fields were reviewed without editing or submission. This walkthrough is the recording reference; see [VIDEO_DELIVERY.md](VIDEO_DELIVERY.md) for the actual rendered video's duration, chapters, subtitles and verification. No public upload or submission has occurred.

## Recording preflight

Use the existing configured checkout and private evidence. Keep `META_ALLOW_PAID=false`; this entire walkthrough needs no Meta request, catalogue check, upload or paid retry. Build from the repository root, then start the local service:

```powershell
Set-Location frontend
npm.cmd run build
Set-Location ..
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Check `/api/health` first if a server may already be running; use the verified KINETICA service rather than starting a duplicate. The command above runs in the foreground (Ctrl+C stops it) and avoids Windows script-execution policy restrictions. **My machines → Open project JSON** → `output/kinetica-project.json`. The JSON requires its original private `data/<video-id>/` directory and source video; these inputs are excluded from Git. It does not embed the video. Use 1440×1000 or a legible desktop viewport, close unrelated windows, and keep account screens, keys and private paths out of the recording.

Before recording, rehearse both freezes and inspect the source masks. In Reality Lab, select tracked object **#2**, check **I inspected this object and confirm the slider identity**, and set **Freeze after frame = 29**. The selector is a human interpretation, not SAM joint identification. Rehearse with horizon 20 first, then horizon 8; reset to 20 for the recording. Do not edit or overwrite the original evidence.

## 0:00–0:25 — Observe the real source

**On screen:** show the imported source, enter Reality Lab and briefly play the observed masks, then pause. Keep `SAVED SAM EVIDENCE` visible. Show #2 and the explicit identity confirmation.

**Narration:** “KINETICA turns observed component motion into a mechanical hypothesis we can inspect and test. These are preserved results from a real Meta SAM request: 150 boxes and 150 contours for three IDs over 50 frames. I confirm which component is the slider; segmentation does not identify its joint center.”

## 0:25–1:00 — Freeze the hypothesis

**On screen:** **Predict the Unseen**, cutoff 29/horizon 20 → **FREEZE REALITY**. Wait for **REVEAL REALITY** to enable. Show the frozen video, gold forecast and withheld errors. Export the sealed forecast if it fits the recording.

**Narration:** “Freeze fixes this replay's cutoff and horizon. KINETICA fits only earlier local observations and seals the next coordinates before reveal. The geometry remains declared. This is retrospective replay of inspected data; the original SAM call saw the full clip, so it does not prove causal online prediction.”

## 1:00–1:40 — Reveal evidence, including a failure

**On screen:** reveal horizon 20 and show `No evaluado` with the known framing-change reason. **Reset replay**, set **Hidden horizon = 8**, freeze, wait, then reveal frames 30–37. Show all three scores and **Export replay evidence**.

**Narration:** “The first horizon crosses the source change at frames 37–38, so KINETICA withholds all scores. In the separately declared eight-frame replay, model RMSE is 9.10 pixels, constant baseline 23.93, and linear baseline 75.59, on exactly the same observations. These image-coordinate results are not physical reconstruction accuracy or an independent experiment.”

Reference values in exported reports: **9.1046 / 23.9297 / 75.5859 px**. Preserve the null cut-crossing result. The earlier full-clip evaluation performed slightly worse than its constant baseline (61.3916 vs 60.9799 px); these different protocols must not be presented as a single before/after improvement. See [methods](MASK_MOTION.md).

## 1:40–2:15 — Break Reality with calculated constraints

**On screen:** enter **Break Reality**, press **Animate both machines**, orbit the assemblies, then pause. Set **Requested slider stroke = 500**, press **Calculate requested stroke**, and show rejection. Use **100** for a feasible centered request with the original L=128, calculate, and move the shared clock. Press **Restore original** before Ask.

**Narration:** “Both models share one clock and a constraint solver. A centered stroke request determines the crank radius; impossible geometry is rejected. The alternate is a counterfactual calculation, not a measured machine, force analysis or fabrication certificate.”

The exact condition for full rotation is `L > r + |e|`; centered stroke inversion is supported only at e=0. Each rendered pose is solved from the current geometry, including transitions.

## 2:15–2:45 — Ask, review, then confirm

**On screen:** **Ask the Machine** → select **Quiero duplicar el recorrido de la corredera** → **Interpret locally (mock)**. Keep `DETERMINISTIC MOCK · MUSE NOT CALLED` and `deterministic_mock` in view. Inspect the proposed tool before **Confirm alternate change**. Return briefly to Break Reality to show the alternate changed.

**Narration:** “This local interpreter supports a bounded set of intents. It proposes a tool call; KINETICA validates the geometry, and I confirm before the alternate changes. Muse's real trial failed and remains unverified. We do not present this mock as a live Muse answer.”

Do not click the real Muse authorization button. The saved failure `d25cbc08d7c2` has no retained provider response or usage, so neither its exact cause nor consumption can be established from local evidence. A future attempt requires a fresh, specific authorization. See [incident report](MUSE_INCIDENT_d25cbc08d7c2.md).

## 2:45–3:00 — Contribution and limits

**On screen:** show the exported evidence or source/protocol summary, then the original and alternate models. Keep any footage credit readable in an end slate or accompanying description after source identity is established.

**Narration:** “The contribution is one inspectable loop: authentic saved Meta segmentation, explicit human interpretation, sealed local hypotheses and solver-driven alternatives. The next evidence milestone is continuous independent footage with a fixed protocol and untouched labels. KINETICA is ready for that experiment.”

## Reproduce the real replay without a server

From the repository root, using the private original project and referenced video:

```powershell
.\.venv\Scripts\python.exe scripts/replay_reality_lab.py --project output/kinetica-project.json --object-id 2 --confirm-slider --freeze-frame 29 --horizon 20
.\.venv\Scripts\python.exe scripts/replay_reality_lab.py --project output/kinetica-project.json --object-id 2 --confirm-slider --freeze-frame 29 --horizon 8
```

The script imports no Meta transport, rejects simulated exports and writes content-addressed reports under ignored `output/reality-lab/`. Reports include source-video and source-export hashes, protocol, measured points, predictions, baselines and `inference_performed=false`. New freeze sessions expire after 15 minutes; re-freeze rather than presenting a recovered result as a new experiment. **Recover preserved replay** retrieves a historical local result after restart.

## Evidence and publication checklist

- Preserve the original project/video and actual local outcomes. Never replace real evidence with a synthetic fixture, generated visual, edited score or a successful parser mock.
- Use [verification](VERIFICATION.md) for executed test results and scope. Browser tests demonstrate UI/solver behavior; they do not establish live Muse compatibility or segmentation accuracy.
- Eitech source identity is now established by a byte-identical official Wikimedia download and all50 clip-frame comparisons: [RELEASE_RIGHTS.md](RELEASE_RIGHTS.md). Credit: “Schubkurbelgetriebe (Eitech), Rhetos, CC BY-SA 4.0, via Wikimedia Commons; excerpted, resized, converted and annotated for KINETICA.” Retain source/license links and indicate changes; adapted media has share-alike obligations separate from application code. The entrant must review compatibility with the competition's broad rights grant before approving publication/submission; no unrestricted ownership of third-party footage is claimed.
- A local rehearsal may use the existing private evidence. A public fallback must have independently established rights and must retain its actual provenance. Synthetic footage is labeled synthetic and supplies no new Meta evidence.
- Check actual video duration, legibility, sound, exported protocol and source credit against the finished files in VIDEO_DELIVERY.md. A script alone is not a recorded deliverable.
- Complete authenticated portal review and entrant contract approval; obtain specific authorization before any public repository push, video upload, deployment, payment, inference or application submission. No jury score, award or readiness percentage is promised.
