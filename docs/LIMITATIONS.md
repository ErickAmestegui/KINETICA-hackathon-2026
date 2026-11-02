# Known limitations and next work

## Blocks a competitive Meta submission

- No successfully verified Meta integration. The user reports a 442-frame SAM call counted by Meta but ending in local HTTP 502; cause remains unknown. Offline repair is tested; paid calls remain blocked. Live response/usage/cleanup behavior is unverified. See SAM_REPAIR.md.
- Real-video tracking on the reviewed Eitech seed fails almost immediately. The manual diagnostic fit has 58.42 px held-out error and only three held-out frames. This is not adequate evidence of robust reconstruction.
- No perspective rectification or camera stabilization. A similarity transform is insufficient for the handheld oblique Eitech view.
- SAM masks are displayed with persistent response IDs but are not converted automatically to mechanical joint centers. Manual center identification remains essential.

## Product scope

- Right/open planar slider-crank only. No arbitrary mechanism topology, exact visible/hidden CAD recovery, force/torque estimation or collision-certified assembly.
- 3D geometry is an original stylized interpretation. Mechanical bores/contact surfaces are simplified; link constraints and basic envelope clearance are tested, manufacturing tolerances are not.
- Local least-squares fitting depends on initial speed, fixed calibration and fixed eccentricity. It can find a local minimum. Phase is wrapped after fitting.
- LK stops on forward/backward or photometric failure; no automatic reidentification after occlusion. Re-mark visible centers and track again.
- Source video codec must work in both OpenCV and the browser. MP4/MOV containers alone do not guarantee this. Recommend H.264 MP4; an unsupported browser codec is reported. Import rejects non-monotonic decoder timestamps; it does not certify all codecs/VFR timing.
- Video limits: 100 MB, 60 seconds, 1080p, 3600 frames. One local track operation processes at most 600 frames. These protect the 16 GB machine.
- For very short links or extreme ratios, fixed decorative hardware sizes may not represent a manufacturable assembly. The numerical model remains the source of kinematic truth.
- Study save is one local browser slot, plus JSON exports. Deleting private `data/` breaks associated media references. No cloud sync or multi-user workspace.
- No calibrated uncertainty interval. Source labels, parser diagnostics, track losses and pixel residuals expose limitations; they are not uncertainty statistics.
- Browser playback uses presentation time and decoded timestamp lookup. Automated tests cover fixture frame stepping, not every variable-frame-rate source.
- Python dependency security scanning was not automated in this session; dependencies are pinned and functional tests pass. npm audit returned zero known advisories after targeted Vite/Vitest updates; this is not a security guarantee.
- Backend test client emits a Starlette deprecation notice about future httpx2 transport migration. Current tests pass; no production behavior depends on TestClient.

## Publication gate

Review `.gitignore` and staged files, verify no keys/private videos/results, verify media identity/license, complete actual Meta evidence, record the demo and obtain user approval before pushing, publishing or submitting. The reference JPG is not redistributed. No Eitech media is included in versioned source.
