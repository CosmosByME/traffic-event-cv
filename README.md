# RoadLens — WIUT traffic-event baseline

Python 3.11 or 3.12 recommended. This is a functional starter implementation, not a validated competition submission. Official sample videos, camera.md, run_submission.py and evaluate.py have not yet been provided. Do not replace the official harness/evaluator with local approximations.

The local `.venv` and official YOLO11n weights are already installed in this workspace. Start the HTML website with `.venv/bin/python website/server.py` and open http://127.0.0.1:8080. Its HTML/CSS/JavaScript frontend lives in `website/public/`, with the model API in `website/server.py`. See `website/README.md` for setup and upload details. The `.venv` and weights are excluded from Git; the download script verifies the committed SHA256.

## Install and run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_weights.py
python website/server.py
```

The one-time download fetches YOLO11n from the official Ultralytics assets release and prints its SHA256. Bundle the weights or run `sh weights/download.sh` before offline evaluation. Inference checks local weights first and does not fetch them. Set `TRAFFIC_WEIGHTS` to an alternate local checkpoint. The detector explicitly selects ByteTrack and disables dependency auto-installation.

Run all supplied videos locally:

```bash
python dev_run.py --videos samples --out outputs/predictions_samples.json
python dev_run.py --videos samples --out outputs/predictions_samples.json --render
python -m unittest discover -s tests -v
python scripts/smoke_inference.py
```

`dev_run.py` is a development tool. It does not enforce organizer time limits and is not a replacement for their harness. Once supplied, put the unchanged official files at the repository root, then run:

```bash
python run_submission.py --videos samples --out predictions_samples.json
python evaluate.py --pred predictions_samples.json --validate-only
```

## Calibration

Edit the selected profile under the HTML website's "Edit camera configuration" control, then download it to save the settings. Coordinates are normalized [x/width, y/height]; tracked points use bounding-box bottom centers. Set calibrated=true only after specifying road, crosswalks, queue_zones, and lanes accurately. Lane direction is a nonzero vector in image coordinates (positive y points down). Assign each lane a `group` such as `northbound` so congestion requires occupancy in all lanes of that direction. Defaults make no event predictions; a generic scene is not safe to assume.

Example lane: `{"polygon": [[0.1,0.2],[0.4,0.2],[0.5,1],[0.1,1]], "direction": [0,-1], "group":"northbound"}`.

Set device to `cpu`, `mps`, or `0` for CUDA GPU 0. CPU is the portable default. Set `TRAFFIC_CAMERA` to another JSON path for batch/organizer inference. Image-plane speed thresholds require tuning for perspective. A new camera requires new geometry.

## Implemented scope

YOLO11n pretrained on COCO → ByteTrack → trajectories → ten configurable rules:

* stopped_vehicle: persistent stationary track on the road outside signal queue regions.
* wrong_way: sustained motion opposite a configured lane direction.
* jaywalking: pedestrian on road outside configured crosswalks.
* congestion: slow vehicles across every lane in a direction group.

* failure_to_yield: moving vehicle traverses a crossing while a pedestrian occupies it; event persists until vehicle exits.
* red_light: crosses a configured stop line against a verified red signal; ends when leaving the intersection.
* stop_line: stops in a configured beyond-line region on red; ends on green or disappearance.
* solid_line_crossing: track crosses a finite configured solid-line segment; ends when projected contact corners cross it.
* illegal_turn / illegal_u_turn: verified prohibited entry → maneuver → exit sequences.

All 14 official IDs are exposed in solution.py. Accident, near_miss, road_obstacle and fire_smoke remain unsupported. These rules are heuristics, not verified legal findings. Finite geometry, contact-point approximation, signal visibility, occlusion and boundaries require validation. No sample/hidden-set accuracy is claimed.

## Use your C3896 video

```bash
.venv/bin/python dev_run.py --videos samples --camera configs/C3896.draft.json --out predictions_samples.json --render
```

This draft was drawn from your video: road, crossings, refuge exclusions and signal queue area. It enables stopped_vehicle, jaywalking, failure_to_yield and experimental risk. It deliberately leaves lane directions, signal mapping, solid lines and prohibited turns unset; rules depending on those do not activate. Review the geometry before trusting the predictions. Do not apply this camera profile to unrelated footage or the hidden camera without checking the view.

For the official interface, use `TRAFFIC_CAMERA=configs/C3896.draft.json` only when the input matches this camera, or copy reviewed settings into configs/camera.json before packaging. Otherwise solution.py keeps using the uncalibrated default. Ensure packaged configuration and predictions_samples.json agree before submission.

To iterate quickly using existing saved detections:

```bash
.venv/bin/python scripts/replay_events.py outputs/C3896.analysis.json --camera configs/C3896.draft.json --out outputs/C3896.events-v2.analysis.json
```

Replay does not improve old YOLO detections/IDs or extract missing signal crops. Run dev_run.py again to apply detector/tracker improvements. The sampled analysis carries exact config and a replay flag; older runtime metadata is retained and is not replay runtime.

## Tracking continuity and risk format

Detector confidence 0.10 lets ByteTrack use low-confidence detections for recovery; new tracks still require 0.35. The buffer is measured in seconds at the actual sampling rate. Event states bridge only brief missing observations (0.5 seconds); visible contrary evidence closes an event. Amber predicted boxes last at most 0.5 seconds and are for display only. They never enter rules, counts or risk. Lower confidence can add false associations; validation on your footage is still needed.

Every official risk row is **[timestamp_seconds, score_0_to_1]**. For example `[12.5, 0.7]` means score 0.7 at time 12.5 seconds. Scores are explicitly finite and clamped at every output boundary, with time-based smoothing. The demo has a labeled risk CSV. Clamping guarantees format, not probability calibration.

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

1. Add the official starter files, sample videos, and camera.md.
2. Annotate sample events, calibrate geometry, tune rules, and compare per-class scores using the official evaluator.
3. Add reliable implementations of remaining event classes as time permits.
4. Export annotated playback for every sample video; publish real EDA, results, failure examples, and report.
5. Measure two-pass Part A + B runtime on a T4-class machine; keep below 3× video duration with margin and weights below 5 GB.
6. Clean install/offline/repeat-run checks, public demo deployment, complete team details, final tagged commit.
