# Attribution and licenses

KINETICA application code and procedural mechanical model are original work created for this project. The supplied reference JPG was used as visual direction, not as measured evidence or a bundled asset. No reused Anatomy/SKY-001 code or 3D assets are claimed; Anatomy was not cloned. The separately licensed Eitech source footage is identified below and must not be confused with original application assets.

Key dependencies retain their own licenses: React, Vite, Three.js, React Three Fiber/Drei, FastAPI, HTTPX and pytest (MIT); TypeScript (Apache-2.0); NumPy/SciPy (BSD); OpenCV (Apache-2.0); Lucide (ISC); Playwright (Apache-2.0). Consult each installed package's actual license before redistribution. The lockfiles identify exact installed versions. Optional `imageio-ffmpeg` includes a separately licensed FFmpeg binary; review its build/license terms if distributing that binary. KINETICA does not vendor or redistribute dependency binaries in its source repository.

`meta-sam-parser` is the official Meta parser. `tests/test_meta.py` contains a short mask example from its published 0.1.0 package documentation, Copyright Meta Platforms, Inc. and affiliates, under the package's **SAM License (19 November 2025)**, reproduced in [docs/licenses/SAM-LICENSE.txt](docs/licenses/SAM-LICENSE.txt). The fixture content is excluded from the application MIT license. This fixture is protocol evidence, not a live KINETICA response. Official project: https://github.com/meta-models/meta-sam .

## Original synthetic demo media

The demo clip `demo/kinetica-original-synthetic-slider-crank.mp4`, its saved geometry and the submission demo video are original work of the KINETICA entrant: the clip is rendered by `scripts/make_original_demo_clip.py`, the video is a screen recording of this application with offline synthesized narration (Microsoft Zira Desktop), and no third-party footage, images or music are included. The synthetic geometry is not Meta SAM output.

## Eitech video — historical SAM evidence, not distributed in the public repository

The public repository does not contain the Eitech footage or the SAM geometry derived from it; both are kept separately as historical evidence while the competition's media conditions are clarified. The source facts below are retained so the documented SAM 3.1 run can be traced.

A matching source page was found for **Schubkurbelgetriebe (Eitech).webm**, author **Rhetos**, own work, date listed 19 October 2026, **Creative Commons Attribution–ShareAlike 4.0 International**:

- [Wikimedia Commons source page](https://commons.wikimedia.org/wiki/File%3ASchubkurbelgetriebe_%28Eitech%29.webm)
- [CC BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/)

On 2 November 2026 the public original was downloaded directly from Wikimedia Commons. Its SHA-256 is **a80d4fc0c85b1d4ec747fe2049349cf656579c3e0d02894c4ae437a412665e66**, exactly matching the original local 442-decoded-frame source. The local original's `.mp4` filename was misleading: its bytes are the same EBML/WebM source, not a separate MP4 conversion. The 50-frame SAM input **is** an H.264 conversion/downscale of original frames 150–199; all 50 corresponding decoded frames were checked (mean PSNR 41.1349 dB, minimum 39.1000 dB). Source and clip hashes were unchanged. See [rights audit](docs/RELEASE_RIGHTS.md), [machine-readable evidence](docs/evidence/media-lineage.json) and `scripts/verify_media_lineage.py`. This supersedes the historical unresolved-lineage statements below.

Credit for the supplied clip and derived audiovisual material: “Schubkurbelgetriebe (Eitech), Rhetos, CC BY-SA 4.0, via Wikimedia Commons; excerpted, resized, converted, annotated and incorporated in the KINETICA demonstration.” Retain the source and license links, indicate changes, retain the disclaimer and comply with share-alike for adapted media. The license text is included at [docs/licenses/CC-BY-SA-4.0.txt](docs/licenses/CC-BY-SA-4.0.txt). This media license is separate from original application code. Do not label the video or source footage MIT.

Local preparation does not authorize publication. The entrant must review the competition's broad rights grant and ownership warranty: the public rules explicitly permit compliant open-source software/hardware but do not explicitly resolve a CC BY-SA third-party-media exception. CC BY-SA provides reuse permission under its conditions, not authority to grant unrestricted sublicensing or claim sole ownership. The proposed video and media contributions must retain compatible CC BY-SA terms; if the official declarations cannot accommodate those rights, replace the media with separately authorized original footage or obtain additional permission. Replacing footage cannot turn the old SAM result into evidence for a new source.

The manual diagnostic coordinates were read from the actual source frames. They are approximate annotations, not author-supplied ground truth or Meta detections.

## Phase 4 verification — historical, 2026-10-29

The linked Wikimedia Commons page was rechecked and continues to identify Rhetos and CC BY-SA 4.0. Exact local MP4-to-source lineage is still not established by a visual match/hash of the conversion alone. Retain the source URL, author, license link and conversion/crop/overlay change notice in any eventual video credit slate. No media was uploaded or redistributed during Phase 4. Dependency licenses and the separately licensed SAM parser fixture remain governed by the records above.
