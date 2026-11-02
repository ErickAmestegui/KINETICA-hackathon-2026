# Release rights and media lineage — 2 November 2026

Prepared against base `dcc27fd348563efbc2183c08207610aa09440690`. This is an asset and permission inventory, not a certification of legal title or entrant eligibility. No public upload, publisher agreement, provider inference or competition submission was performed.

## Eitech: the source identity is now established

Primary source: [Wikimedia Commons, Schubkurbelgetriebe (Eitech).webm](https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm), page revision [1289404022](https://commons.wikimedia.org/w/index.php?title=File:Schubkurbelgetriebe_(Eitech).webm&oldid=1289404022), inspected and downloaded 2026-11-02. The uploader identifies the work as their own, author **Rhetos**, and declares **CC BY-SA 4.0**. The source page lists creation 19 October 2026 and upload 20 October 2026. These are the uploader's declarations, not independently verified ownership warranties.

Public original download: `https://upload.wikimedia.org/wikipedia/commons/2/25/Schubkurbelgetriebe_%28Eitech%29.webm`.

| Object | Identity / finding |
|---|---|
| Public original | 5,157,101 bytes; SHA-256 `a80d4fc0c85b1d4ec747fe2049349cf656579c3e0d02894c4ae437a412665e66` |
| Preserved original local source | Exact same SHA-256 as the public original; earlier `.mp4` filename does not identify the actual container |
| Actual original container | EBML/WebM, verified header `1a45dfa3`; 1920×1080, 25 fps, **442 decoded frames** |
| OpenCV frame-count estimate | Reports 443 before decoding; actual sequential decode yields 442. Verification uses decoded frames, not the estimated count. |
| 50-frame SAM input | SHA-256 `4e179551a3dde38da847c9392e277331bc93fd1ac28d3524da8a6ca4872a1677`; H.264, 960×540, 25 fps |
| Clip lineage | Original frames 150–199 inclusive; resize/re-encode, audio removed, timestamps reset |
| Image correspondence | All 50 corresponding frames compared with half-size original using OpenCV INTER_AREA: mean PSNR **41.134893 dB**, minimum **39.100047 dB**; encoding/resampler differences expected |

The fresh download's byte identity establishes the relationship that earlier audits could not prove. The source was not replaced, edited or reclassified as new evidence. PSNR here checks clip/source correspondence; it is not SAM accuracy, kinematic reconstruction accuracy or independent validation.

Reproduce after separately downloading that public original (no network or provider transport occurs in the verifier):

```powershell
.\.venv\Scripts\python.exe scripts/verify_media_lineage.py
```

Default download location: `output/submission-rights/Schubkurbelgetriebe-Eitech-original.webm`. The command compares the preserved `output/sam-local/eitech-50-cfr.mp4`, rejects unexpected source/clip hashes or frame correspondence and rechecks hashes after decoding. It creates a content-addressed result under `output/submission-rights/`. The executed result is also preserved as [docs/evidence/media-lineage.json](evidence/media-lineage.json), without original video, credentials or account data. Public-page HTML and the untouched public original remain in ignored output storage.

## Attribution and license conditions

Use this credit with the source and license links in the packaged evidence and video description/end slate:

> Schubkurbelgetriebe (Eitech) — Rhetos — CC BY-SA 4.0 — via Wikimedia Commons. Excerpted, resized, converted, annotated and incorporated in the KINETICA demonstration.

Links: [source](https://commons.wikimedia.org/wiki/File:Schubkurbelgetriebe_(Eitech).webm), [license](https://creativecommons.org/licenses/by-sa/4.0/), [full legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en). The downloaded legal code is included in [licenses/CC-BY-SA-4.0.txt](licenses/CC-BY-SA-4.0.txt).

The license allows sharing and adaptation subject to attribution, change notices, the applicable share-alike terms and no additional downstream restrictions. It grants no endorsement, trademark or privacy rights and includes a disclaimer. A format conversion alone is treated separately from a creative adaptation in section 2(a)(4); the annotated audiovisual demonstration is conservatively treated as adapted material. The proposed license for KINETICA's contributions to that adaptation is CC BY-SA 4.0, subject to the entrant's approval before publication. The original application source remains MIT; third-party materials keep their separate notices.

### Competition rights gate: still requires entrant review

The [Official Rules / waiver](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver) include a broad perpetual, irrevocable, worldwide, royalty-free, non-exclusive submission license, with modification, distribution and other exploitation rights, and an ownership/third-party-rights warranty. The rule text explicitly mentions compliant open-source software/hardware. A comparable exception for third-party audiovisual media is not explicit in the inspected text.

Therefore **do not certify unrestricted sublicensing or sole ownership of Eitech footage** merely because its CC license is verified. CC BY-SA is non-sublicensable and operates through a direct license offer to recipients. Its conditions cannot be removed by KINETICA. Whether the final competition declarations accommodate a separately licensed third-party-media contribution remains unresolved and must be reviewed by the entrant before they approve the entry. No checkbox or legally binding declaration was accepted by this audit.

If the required declaration conflicts with those rights, the available routes are additional rights-holder permission or entrant-authorized original footage. User approval alone cannot remove a third party's rights. A new original recording could replace visual material, but the existing SAM masks would remain evidence only for the verified Eitech source; no new segmentation or successful Meta run could be claimed for replacement footage without an authentic authorized run. Do not spend credits to solve this gate.

### Re-verification and determination — 2 November 2026, 16:50 (UTC−4)

Commons API, page revision 1289404022 (unchanged): `author=[[User:Rhetos|Rhetos]]`, `source={{own}}`, license template `{{self|cc-by-sa-4.0}}`, `AttributionRequired: true`, 5,157,101 bytes, uploaded 2026-10-20 05:07 UTC by Rhetos. The description cites the author's site `rhetos.de`. Categories: Slider crank; Lernwerkstatt Aachen.

**Is the demo video ShareAlike?** Yes, conservatively. The clip is shown with SAM boxes/contours drawn over it, cropped/resized and edited into a narrated sequence: that is "Adapted Material" (CC BY-SA 4.0 §1(a)), so §3(b) requires the adapter's license for those contributions to be CC BY-SA 4.0 or a BY-SA-compatible license, and no additional terms that restrict recipients. The synchronization rule for sound recordings does not apply: the clip has no audio. The KINETICA **source code is not an adaptation**: it does not incorporate the footage. The repository merely ships the 50-frame clip as a separate, credited file (aggregation), so code stays MIT.

**Comparison with the Official Rules (verbatim, rendered 2 November):**

- Submission warranty: the Submission "(a) is their … original work product; (b) is solely owned by the Participant … with no other person or entity having any right or interest in it; and (c) does not violate the intellectual property … rights … of any other person". The only stated exception: "Participants may also include open source software or hardware, provided applicable open source licenses are followed".
- Submission license: "a perpetual, irrevocable, worldwide, royalty-free, and non-exclusive license to use, reproduce, adapt, modify, publish, distribute … and otherwise exploit the Submission for any purpose without restriction".
- Materials clause: "a royalty free, transferable, sub-licensable, worldwide and perpetual and irrevocable license".

**Conflict.** For KINETICA's own code, narration, UI and edit, the entrant can make these warranties and grant these licenses (dual licensing alongside CC BY-SA is allowed for one's own contributions). For the Eitech frames, Rhetos holds the copyright: warranty (b) "solely owned … no other person … having any right" cannot be truthfully given for that component, and the entrant cannot grant a sub-licensable, "without restriction" license over it. CC BY-SA is not sublicensable (§2(a)(5)(A)) and keeps its attribution and ShareAlike conditions. The open-source exception names software or hardware, not audiovisual media. Compliance with CC BY-SA (credit, link, change notice, same-license adaptation) avoids infringement (c), but it does not by itself satisfy (b).

**Legally compatible routes**, in order of preference:

1. **Written permission from Rhetos** granting the Organizers a non-exclusive, perpetual, worldwide, royalty-free license to use the 50-frame excerpt and its annotated adaptation as part of the submission and its promotion, with credit. A draft request is in `output/submission-rights/permission-request-rhetos.txt` (not sent). Combine with route 2's disclosure, because (b) still literally speaks of sole ownership.
2. **Written clarification from the Organizers** that third-party footage under CC BY-SA, used unmodified as demo input with attribution, is acceptable under the open-source/third-party allowance. A draft question is in `output/submission-rights/organizer-question.txt` (not sent).
3. **Entrant-owned footage.** Record a slider-crank that the entrant owns rights to, and replace the Eitech clip in the video and repository. Warranties (a)–(b) then hold for the media. The cost: the saved SAM 3.1 evidence exists only for Eitech. Authentic SAM on new footage needs a new, separately authorized (billable) request; otherwise the video can show only the software without Meta SAM evidence. This loses the strongest Meta-integration proof before the deadline.

Submitting with the Eitech clip and only the CC credit, without route 1 or 2, means the entrant gives warranty (b) for a component they do not solely own. That is the entrant's decision and risk; this audit does not certify it.

## Other release assets

| Asset | Inspected basis / release treatment |
|---|---|
| Procedural 3D mechanism and application UI | Repository source geometry and shaders, not a downloaded mesh/texture. Original project code under MIT; preserve LICENSE. This audit does not independently certify the author's conceptual originality. |
| Favicon / logo geometry | `frontend/public/favicon.svg`, existing repository SVG. No external raster logo is bundled. |
| Reference JPG | Visual direction only; not in tracked release assets. Exclude any private reference file from the package. |
| Fonts | CSS names system fonts/fallbacks. No font binaries or remote web-font files were found in tracked release assets. |
| Lighting/environment | Procedural local light cards in the existing renderer; no external HDR texture needed. |
| Lucide icons and frontend libraries | Maintain their own licenses. `THIRD_PARTY_FRONTEND.txt`/the emitted-module inventory prepared with packaging cover actual bundled code; do not treat the minified bundle as solely MIT application code. |
| Python dependencies | Install from pinned requirements; do not redistribute the existing virtualenv, platform binaries or bundled FFmpeg executable. Dependency licenses remain applicable at installation. |
| Official SAM parser fixture | Existing documented fixture from `meta-sam-parser` is under its SAM License, not application MIT. Preserve `docs/licenses/SAM-LICENSE.txt` and the attribution. It is a parser test, not authentic model-response evidence. |
| Saved SAM geometry | Preserve authentic-source provenance and separate manual interpretation. No new licensing title or unrestricted relicensing of provider outputs is certified by this asset audit. No raw response headers, credentials or account screens belong in the release. |
| Audio/narration | Do not add unlicensed music or stock audio. If an offline synthetic voice is used, label that narration production method; it supplies no scientific evidence. |

No external image/model/texture file was found in `git ls-files assets sample-data frontend/public`, apart from original SVG and data/documentation. Package selection still needs its explicit allowlist and secret scan; this source inventory does not prove the contents of an arbitrary ZIP.

## Release status

- **Prepared:** verified public-source identity, clip correspondence, author/license source, machine-readable evidence, full CC license and exact credit.
- **Pending authorization/review:** publication, proposed CC BY-SA audiovisual licensing, and compatibility of the concrete entry's declarations with third-party media rights.
- **Do not claim:** Eitech authorship, author endorsement, an unrestricted license for the footage, independent SAM accuracy, a new Meta run, or rights clearance from merely renaming/cropping the video.
