# Implementation status — HTML website and event tracking

## Local annotated-video CLI

`python run.py --videos samples` now creates outputs/predictions.json and an
annotated MP4 for every input using the existing website analyzer/renderer.
The website, shared inference/rendering code and official runner are unchanged
by this addition. Local JSON is checkpointed per video, render errors preserve
predictions, and existing outputs require explicit --overwrite. Green/orange
box colors were checked in an actual encoded-video regression test with controlled
detections. This local single-pass workflow is not the official timed A+B run.

## Clear-screenshot calibration v2 (supersedes v1 geometry notes)

Reviewed the three user-provided 2560x1662 screenshots after excluding player
borders. First two align with C3896; the third shows different framing despite
the same physical camera. Default geometry now has refined crossing boundaries,
four near-side lane cores and three measured (inactive) solid-divider segments. A separate
configs/C3896.shifted.json stores the third view's road/crosswalk/refuge regions;
it is not automatically selected and its source video mapping is still unknown.
Signal ownership and prohibited turns remain unverified/disabled. See
samples/camera.md for exact coordinate conventions and limitations. Do not apply
the default profile indiscriminately to shifted-view videos.
62 tests pass for this update; the saved-track output passes official format
validation. This is not evidence of event accuracy. Solid-line measurements are
stored but inactive after a replay exposed implausibly long merged events.

## Submission packaging update (supersedes packaging notes below)

Official run_submission.py and evaluate.py are now included byte-for-byte at the
repo root; tests pin their SHA256. Both weight files are explicitly allowed in
Git for a complete checkout (~12 MB total); no online download step at inference.
Device auto selects CUDA GPU 0 when available, otherwise CPU. Requirements pin
the CUDA 12.8 build on Windows/Linux x86-64 and native builds on macOS.
README begins with the required install-and-run commands. The optional Docker
default now runs the official harness instead of starting the website.
60 unit/integration tests pass. A fresh isolated Python 3.12 environment installed
requirements.txt successfully with pip check clean. From a relocated copy using
that environment, the unchanged official runner processed a 20-second C3896 clip
(resized to 960x540 at 10 FPS): 47.1s combined Part A+B against the default 60s
budget, 200 risk rows, no runner errors, official format validator passed. This is
a Mac CPU packaging smoke test, not full-resolution/T4/Windows accuracy validation.
The friend-test ZIP includes code and weights, not the large videos or a venv.
Sample predictions remain stale; model accuracy,
unconfigured scene rules, target-GPU timing, website publication and final Git
submission are separate release gates, not solved by packaging.

## September 27 calibration update (supersedes camera notes below)

C3896 geometry v1 is now in configs/C3896.json and the default configs/camera.json.
Road/crosswalk boundaries, refuge/curb exclusions, signal queue area and three
near-side lane cores were visually reviewed at 5, 40, 120 and 240 seconds.
Website defaults to that profile, with a separate uncalibrated other-camera option.
Signal mapping, solid-line and prohibited-turn rules remain unconfigured.
No metric speed, event accuracy or risk probability calibration is claimed.
The official kit is now available in ../wiut_cv_scripts, but its runner/evaluator
still need packaging unchanged. The revised PDF no longer requires camera.md;
samples/camera.md contains our own observations and limitations.
55 tests passed, including five calibration regressions. Diagnostic replay and
overlays are under outputs/calibration; final sample predictions remain unchanged.
The old roughly 50-second first yield segment no longer occurs with this geometry.
Actual full-video inference and manual ground-truth evaluation remain release gates.

## Historical September 26 implementation notes

Implemented and checked locally through September 26, 2026:

- Python 3.12 virtual environment with pinned direct dependencies.
- Official YOLO11n checkpoint with recorded SHA256; offline inference smoke passed.
- ByteTrack adapter, normalized trajectories, ten scene rules plus four experimental hazard paths (all 14 label IDs).
- Optional causal risk estimator with explicit finite [0,1] bounds and labeled exports.
- HTML/CSS/JavaScript website with a Python model API: streamed MP4 uploads, JSON calibration, event table/timeline, object counts, risk curve, download results and optional annotated video.
- Batch processing, annotated sample export, Docker packaging.
- 50 tests passed after hazard/risk updates, covering event lifecycle, signal rules, missing observations, display-only predictions, risk bounds (including the official interface), output validation, video pipeline, hazard positives/negatives and website behavior. Frontend risk validation also passed a direct JavaScript check.
- Browser verified at http://127.0.0.1:8080. The superseded Streamlit UI has been removed; use the root requirements.txt and Dockerfile for the website.

Actual C3896 review: 450 frames / 15.015 seconds resized to 1280×720; updated YOLO/ByteTrack analysis took 7.90 seconds on CPU, excluding extraction and annotated export. Risk range 0–0.534913. Predictions and annotated review are under outputs/tracking-review/. This is not a target-GPU or two-pass organizer benchmark. No annotated ground-truth accuracy or ID-switch score is available.

Tracking improvements: weak detections reach ByteTrack's recovery pass, retention follows actual sample rate, event states tolerate brief missing observations, and amber display-only boxes bridge short gaps. Predicted boxes never enter event evidence. Duplicate predictions overlapping a new observed ID are suppressed. Identity switches can still occur.

Ten scene rules: stopped_vehicle, wrong_way, jaywalking, congestion, failure_to_yield, red_light, stop_line, solid_line_crossing, illegal_turn and illegal_u_turn. Added accident/near_miss trajectory candidates, road_obstacle from persistent COCO animals/items, and fire_smoke from a separate revision/checksum-pinned pretrained model. These are not validated classifiers: unknown debris and untracked fixed-object collisions remain coverage gaps. See weights/MODELS.md. The C3896 visual draft still lacks lane directions, traffic-light ownership and prohibited routes.

Latest full-video rule replay is in outputs/review-v4/C3896.analysis.json and predictions.json. These use earlier detections and cannot add fire/obstacle detections, confidence scores or demonstrate improved tracking. Original predictions_samples.json is preserved and is stale relative to the new code. Regenerate it with real inference before submission. The roughly 50-second yield remains tied to track #3 staying in a draft crossing region near the curb; geometry needs review. Default camera.json remains uncalibrated.

Risk audit: both saved C3896.analysis.json and predictions_samples.json contain 10,200 rows, scores 0–0.760849 and times 0–340.306633 seconds. Zero out-of-range scores found. Only column 2 is a score. New code adds named min/max summaries, a read-only checker, browser rejection of invalid rows, confident sustained pair evidence and co-moving-traffic suppression. Latest saved-track replay scores are 0–0.635943. Risk remains uncalibrated.

Real two-model smoke check: first six seconds of C3896 downsampled to 960x540 at 10 FPS; analysis took 4.45 seconds on this Mac CPU, excluding extraction. Both detectors loaded offline, output validated, and no events were emitted. This is NOT a positive-class accuracy test or a T4/two-pass benchmark. The fire specialist also returned no detections on a black image. Full RTX/organizer runtime and fire/smoke positive footage remain untested.

Required layout is preserved: solution.py at root, implementation in src/, requirements.txt, weights/, predictions_samples.json. Official run_submission.py and evaluate.py are missing and must be supplied unchanged; dev_run.py is explicitly a local runner.

Still needed: official camera.md/harness/evaluator, reviewed geometry and manual dev labels, full-video rerun with new detectors, positive/negative hazard evaluation, upstream fire training-data provenance, organizer-GPU runtime validation, team profiles and public deployment. Do not submit unchanged as a validated final challenge solution.
