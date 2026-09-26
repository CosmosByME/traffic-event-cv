# Implementation status — HTML website and event tracking

Implemented and checked locally through September 26, 2026:

- Python 3.12 virtual environment with pinned direct dependencies.
- Official YOLO11n checkpoint with recorded SHA256; offline inference smoke passed.
- ByteTrack adapter, normalized trajectories, ten configurable event rules.
- Optional causal risk estimator with explicit finite [0,1] bounds and labeled exports.
- HTML/CSS/JavaScript website with a Python model API: streamed MP4 uploads, JSON calibration, event table/timeline, object counts, risk curve, download results and optional annotated video.
- Batch processing, annotated sample export, Docker packaging.
- 34 tests passed after cleanup, covering event lifecycle, signal rules, missing observations, display-only predictions, risk bounds, output validation, video pipeline and website behavior.
- Browser verified at http://127.0.0.1:8080. The superseded Streamlit UI has been removed; use the root requirements.txt and Dockerfile for the website.

Actual C3896 review: 450 frames / 15.015 seconds resized to 1280×720; updated YOLO/ByteTrack analysis took 7.90 seconds on CPU, excluding extraction and annotated export. Risk range 0–0.534913. Predictions and annotated review are under outputs/tracking-review/. This is not a target-GPU or two-pass organizer benchmark. No annotated ground-truth accuracy or ID-switch score is available.

Tracking improvements: weak detections reach ByteTrack's recovery pass, retention follows actual sample rate, event states tolerate brief missing observations, and amber display-only boxes bridge short gaps. Predicted boxes never enter event evidence. Duplicate predictions overlapping a new observed ID are suppressed. Identity switches can still occur.

Ten implemented rules: stopped_vehicle, wrong_way, jaywalking, congestion, failure_to_yield, red_light, stop_line, solid_line_crossing, illegal_turn and illegal_u_turn. The C3896 visual draft only configures road/crossing/queue/refuge regions; lane directions, traffic-light ownership and prohibited routes are unset. Four classifications remain unsupported: accident, near_miss, road_obstacle and fire_smoke.

Full-video rule replay is in outputs/C3896.events-v2.analysis.json; corresponding competition-shaped predictions are at predictions_samples.json. These use earlier detections and cannot demonstrate improved tracking. Original outputs are preserved. Replay results and draft geometry need manual review before being presented as accurate traffic-event detections. Default camera.json remains uncalibrated; use the explicit C3896 profile for this video.

The official risk format is [timestamp_seconds, score_0_to_1]. Old scores were all zero because Part B was disabled. Only the second number is bounded; timestamps naturally exceed one. Risk remains a heuristic, not a calibrated accident probability.

Required layout is preserved: solution.py at root, implementation in src/, requirements.txt, weights/, predictions_samples.json. Official run_submission.py and evaluate.py are missing and must be supplied unchanged; dev_run.py is explicitly a local runner.

Still needed: official camera.md/harness/evaluator, reviewed geometry and manual dev labels, full-video rerun with new tracker, four remaining event classes, organizer-GPU runtime validation, team profiles and public deployment. Do not submit unchanged as a completed challenge solution.
