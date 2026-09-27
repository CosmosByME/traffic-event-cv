# RoadLens — WIUT traffic-event submission

## Run on another computer

Open a terminal in this repository's root folder (`traffic-event-cv`, the folder containing `solution.py`). Use Python **3.11 or 3.12** with pip. Place the supplied test MP4 files in `samples/` (or substitute their folder path). Only these two commands are needed:

```bash
pip install -r requirements.txt
python run_submission.py --videos samples --out predictions.json
```

Installation needs internet, or pre-provisioned dependency wheels. Inference is offline. The two model checkpoints are included in the repository (about 12 MB total): **no download script, manual camera edit, GPU flag, website server, or extra launch script is required**. Keep `pip` and `python` pointed at the same Python installation. A fresh virtual environment is recommended when other projects already use that installation, but is not a runtime dependency.

The organizers' exact run command is:

```bash
python run_submission.py --videos /data/test --out predictions.json
```

On Windows, replace `/data/test` with the actual video folder, quoting paths with spaces. Output contains both event intervals and per-frame risk scores. Reusing an output filename overwrites that JSON. The output's parent directory must already exist (this is behavior of the unchanged official runner).

**Device:** the bundled camera config uses `auto`: NVIDIA CUDA GPU 0 when available, otherwise CPU. Requirements select the pinned CUDA 12.8 PyTorch build on Windows/Linux x86-64 and native wheels on macOS. NVIDIA machines need a compatible installed driver; the app does not install system drivers. See [official PyTorch installation versions](https://pytorch.org/get-started/previous-versions/#v280). CPU fallback supports functional testing but is not guaranteed to meet the organizers' time limit on full-resolution videos.

**Success:** each video should print `OK`, with no entries in its `log.errors`. Inspect this: the official runner can exit successfully even when an individual video failed or exceeded its budget. Its combined Part A + B budget remains the official 3× duration; no limits were relaxed.

## Submission layout

- `solution.py`: required `CLASSES`, `detect_events`, and causal `RiskEstimator`.
- `run_submission.py`, `evaluate.py`: byte-identical copies of the supplied organizer files; do not modify.
- `requirements.txt`, `Dockerfile`: environment setup. Docker defaults to the official run command.
- `weights/`: both local checkpoints, checksums and attribution.
- `src/`: detector/tracker, temporal event rules, risk and runtime setup.
- `configs/`: bundled C3896 scene geometry and tracker settings.
- `predictions_samples.json`: existing sample output; **currently stale**, regenerate before final submission.
- `website/`: separate optional website, not required by the organizer inference command.
- `scripts/`, `tests/`: developer tools, not additional setup steps.
- `samples/camera.md`: team-authored scene notes; the revised PDF does not require this file.

The project folder is the Git repository root; it must not be wrapped in an extra folder inside the uploaded repository. Large road videos, virtual environments, caches and diagnostic outputs remain ignored. The two named model files are explicitly allowed in Git; make sure they are included when committing/pushing or sending the folder to a teammate.

## Optional developer checks

Packaging verification: clean Python 3.12 install and relocated-package inference
passed on this Mac. A 20-second resized C3896 clip took 47.1s for both official
passes (60s budget), with zero runner/validator errors. This is not a Windows/T4
or full-resolution performance guarantee. All 60 tests pass.

These are not needed to run the submission:

```bash
python evaluate.py --pred predictions.json --validate-only
python -m unittest discover -s tests -v
python scripts/check_submission.py --video samples/C3896.MP4
```

The last command copies the inference package to a temporary unrelated directory and runs both official passes on a 20-second resized clip under the original time budget. It checks deployment plumbing, not accuracy or full-resolution performance.

To start the separate website after installation: `python website/server.py`, then visit http://127.0.0.1:8080. See `website/README.md`. Website hosting is separate from the offline submission.

For local annotated playback, `dev_run.py` remains available, but it is not the submission entry point. `scripts/download_weights.py --fire-smoke` is retained only as an optional repair/source-provenance tool; inference never downloads weights.

## Calibration

Edit the selected profile under the HTML website's "Edit camera configuration" control, then download it to save the settings. Coordinates are normalized [x/width, y/height]; tracked points use bounding-box bottom centers. Set calibrated=true only after specifying road, crosswalks, queue_zones, and lanes accurately. Lane direction is a nonzero vector in image coordinates (positive y points down). Assign each lane a `group` such as `northbound` so congestion requires occupancy in all lanes of that direction. The default is now the reviewed C3896 profile. Use configs/uncalibrated.json for a different camera; never apply C3896 geometry to an unrelated view.

Example lane: `{"polygon": [[0.1,0.2],[0.4,0.2],[0.5,1],[0.1,1]], "direction": [0,-1], "group":"northbound"}`.

Set device to `auto`, `cpu`, `mps`, or `0` for CUDA GPU 0. `auto` is the packaged default; it selects CUDA if available, otherwise CPU. Set `TRAFFIC_CAMERA` to another JSON path for batch/organizer inference. Image-plane speed thresholds require tuning for perspective. A new camera requires new geometry.

## Implemented scope

YOLO11n pretrained on COCO → ByteTrack → trajectories and camera geometry, plus a separate fire/smoke detector. All 14 IDs now have implementation paths; this is not a claim of complete real-world coverage or validated accuracy.

* stopped_vehicle: persistent stationary track on the road outside signal queue regions.
* wrong_way: sustained motion opposite a configured lane direction.
* jaywalking: pedestrian on road outside configured crosswalks.
* congestion: slow vehicles across every lane in a direction group.

* failure_to_yield: moving vehicle traverses a crossing while a pedestrian occupies it; event persists until vehicle exits.
* red_light: crosses a configured stop line against a verified red signal; ends when leaving the intersection.
* stop_line: stops in a configured beyond-line region on red; ends on green or disappearance.
* solid_line_crossing: track crosses a finite configured solid-line segment; ends when projected contact corners cross it.
* illegal_turn / illegal_u_turn: verified prohibited entry → maneuver → exit sequences.

* accident: experimental approach + contact proxy + abrupt braking, ending on participant stopping/disappearance. Does not cover single-vehicle impacts against untracked fixed objects.
* near_miss: experimental approaching conflict + abrupt evasion + separation without observed contact proxy. Ordinary braking/occlusion can still fool it.
* road_obstacle: persistent recognized COCO animals/items inside the road; carried items are suppressed. Arbitrary debris outside those learned categories is not reliably detected.
* fire_smoke: learned fire/smoke detections from a pinned YOLOv8n checkpoint, with road-region and temporal confirmation. The checkpoint is from a different domain and needs road-camera validation.

These are event candidates, not verified legal findings. Finite geometry, contact-point approximation, signal visibility, occlusion and boundaries require validation. No sample/hidden-set accuracy is claimed. Flags `collision_rules_enabled`, `obstacle_detection_enabled`, and `fire_smoke_enabled` default to true but require a calibrated road. Fire/smoke weights are required when that detector is enabled; missing weights fail explicitly. Disable a feature only if you intend to submit/demo reduced coverage.

## Use your C3896 video

```bash
.venv/bin/python dev_run.py --videos samples --camera configs/C3896.json --out predictions_samples.json --render
```

Reviewed C3896 v2 geometry includes road boundaries, three crossings, refuge/curb exclusions, the signal queue approach, four near-side lane cores and three measured (inactive) solid-divider segments. The curb car is no longer inside the far crossing. Signal ownership and prohibited turns remain unset; their dependent rules are disabled. Measured solid lines remain inactive after replay exposed implausibly long candidates. Lane coverage is partial and event accuracy is unvalidated. See samples/camera.md for observations and limitations. The old C3896.draft.json is retained only as a historical comparison.

The official interface uses C3896 daytime-framing geometry in configs/camera.json by default. The third supplied screenshot shows shifted framing; configs/C3896.shifted.json is a separate manual profile, not automatically selected. Same physical camera does not guarantee identical framing. Verify the source video before choosing a profile; do not choose by darkness alone. TRAFFIC_CAMERA can override it. Generate review overlays with `python scripts/preview_camera.py --video samples/C3896.MP4`. Ensure packaged configuration and regenerated predictions_samples.json agree before submission.

To iterate quickly using existing saved detections:

```bash
.venv/bin/python scripts/replay_events.py outputs/C3896.analysis.json --camera configs/C3896.json --out outputs/C3896.events-v2.analysis.json
```

Replay does not improve old YOLO detections/IDs or extract missing signal crops. Run dev_run.py again to apply detector/tracker improvements. The sampled analysis carries exact config and a replay flag; older runtime metadata is retained and is not replay runtime.

## Tracking continuity and risk format

Detector confidence 0.10 lets ByteTrack use low-confidence detections for recovery; new tracks still require 0.35. The buffer is measured in seconds at the actual sampling rate. Event states bridge only brief missing observations (0.5 seconds); visible contrary evidence closes an event. Amber predicted boxes last at most 0.5 seconds and are for display only. They never enter rules, counts or risk. Lower confidence can add false associations; validation on your footage is still needed.

Every official risk row is **[timestamp_seconds, score_0_to_1]**. For example `[12.5, 0.7]` means score 0.7 at time 12.5 seconds. Scores are explicitly finite and clamped at every output boundary, with time-based smoothing. The demo has a labeled risk CSV. Clamping guarantees format, not probability calibration.

Run `python scripts/check_risk.py predictions_samples.json` (or any downloaded predictions/full-analysis JSON) to audit every score. The saved C3896 outputs checked on September 26 contain 10,200 rows, scores 0–0.760849, and timestamps up to 340.306633 seconds: no score-range violation was found. Analysis and website downloads now include a named `risk_summary`. The browser rejects malformed/out-of-range risk rather than silently clipping it. New risk requires confident, sustained closing evidence and rejects ordinary co-moving pairs; it remains uncalibrated.

Full analysis includes `raw_events` and `event_evidence` so you can distinguish a long per-track event from several overlapping same-class events merged for the official schema. Yield detection requires a witnessed crossing entry and displacement while a pedestrian is present. Tracks first seen inside a crossing can therefore be missed; inaccurate crossing boundaries still cause errors.

## Update the Windows GPU machine

After pulling the committed changes, run from the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_weights.py --fire-smoke
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_risk.py predictions_samples.json
.\.venv\Scripts\python.exe website/server.py
```

The requirements install CUDA 12.8 PyTorch 2.8.0/torchvision 0.23.0 on Windows/Linux x86-64; `device: auto` selects an available CUDA GPU without profile edits. Rerun actual inference to obtain the new obstacle/fire detections and confidence scores; replaying old tracks cannot create missing detections. `python scripts/smoke_hazards.py --video samples/C3896.MP4` runs a six-second two-model integration check, not an accuracy benchmark.

## Camera-dependent rule configuration

Additional config arrays default empty:

* `signals`: `{id, lamps: {red: [x1,y1,x2,y2], green: [x1,y1,x2,y2]}}`. Use tight lamp crops; ambiguous/unseen color is unknown. Three consistent observations are required.
* `stop_lines`: `{signal_id, line: [[x,y],[x,y]], direction:[dx,dy], intersection: polygon, violation_zone: polygon}`. Link only the signal that controls the lane. Violation zone must exclude the intersection.
* `solid_lines`: `{line: [[x,y],[x,y]]}`. Only include verified solid markings.
* `turn_rules`: `{label: "illegal_turn" or "illegal_u_turn", entry: polygon, maneuver: polygon, exit: polygon}`. Define only prohibited routes.
* `excluded_zones`: refuge islands/parking/sidewalk regions excluded from pedestrian and stopped-vehicle rules.

## Required repository layout

The submission interface stays at root (`solution.py`), implementation stays under `src/`, dependencies in `requirements.txt`, checkpoints in `weights/`, and sample predictions at `predictions_samples.json`. `configs/`, `scripts/`, `tests/`, and `website/` are additional support folders. The root `Dockerfile` runs the HTML website. The unchanged official `run_submission.py` and `evaluate.py` must be added at root when supplied; neither is fabricated here. `dev_run.py` is explicitly a development runner. No notebook is required to run inference.

Part B is off by default. `risk_enabled=true` enables an experimental closest-approach heuristic in normalized image space. This is not metric time-to-collision or calibrated probability. RiskEstimator only consumes received frames, with independent detector/tracker state; no Part A output or video files are accessed. Budget Part A and B together: enabling risk can approximately double detector work under the official harness.

The HTML website accepts MP4 up to 3 GB (3072 MB), 10 minutes, and 4K. It streams uploads to temporary disk storage and serves video playback, track overlays, event timelines, count/risk charts and downloads. Its limits are in website/server.py. Recent jobs expire after two hours, server shutdown, or eviction beyond four retained jobs. See website/README.md. Public hosting and official sample visualizations remain release tasks.

## Reproducibility and attribution

Dependencies are pinned; seeds are fixed at 42, CUDA benchmarking disabled, deterministic algorithms requested with warnings. Byte-for-byte reproducibility on the target GPU remains to be verified. No training has been performed. Source data for pretrained detector: COCO; no external event dataset has been downloaded or used for training.

* Ultralytics YOLO11: https://docs.ultralytics.com/models/yolo11/ (Ultralytics AGPL-3.0 terms; retain attribution and review redistribution obligations before publishing).
* ByteTrack: https://github.com/FoundationVision/ByteTrack (original implementation MIT; integration distributed by Ultralytics).
* COCO: https://cocodataset.org/#termsofuse (annotations and source images have distinct terms).

Record exact model SHA256, hardware, evaluation commands, development labels, and results before release. Populate configs/team.json with real team members and contributions; no invented portfolios or results are shown.

## Remaining release gates

1. Verify the friend's fresh checkout includes both bundled weight files; run the official command and inspect its per-video errors.
2. Annotate sample events, validate the reviewed geometry, tune rules, and compare per-class scores using the official evaluator.
3. Validate/tune the four experimental hazard paths with real positives and negatives; confirm upstream fire-model dataset-license provenance.
4. Export annotated playback for every sample video; publish real EDA, results, failure examples, and report.
5. Measure two-pass Part A + B runtime on a T4-class machine; keep below 3× video duration with margin and weights below 5 GB.
6. Clean install/offline/repeat-run checks, public demo deployment, complete team details, final tagged commit.
