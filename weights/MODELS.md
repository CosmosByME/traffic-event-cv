# Model provenance

Inference uses local weights only. `python scripts/download_weights.py --fire-smoke`
downloads both checkpoints during preparation; `SHA256SUMS` records their hashes.
Both named checkpoints are included in the submission repository; no download
step is needed after cloning the complete submission. Other weight files remain
Git-ignored. The download script is optional recovery tooling, not inference.

## Road users and recognized obstacles

- Model: official Ultralytics YOLO11n, pretrained on COCO.
- Source: https://github.com/ultralytics/assets/releases/tag/v8.3.0
- Publisher license: Ultralytics AGPL-3.0 (see https://docs.ultralytics.com/help/AGPL-3.0/).
- Data: COCO; annotation and source-image terms differ: https://cocodataset.org/#termsofuse.
- No training or fine-tuning performed by this team.
- Obstacles cover COCO animal, backpack, handbag, suitcase, bottle and chair classes.
  Unknown debris and fallen objects outside these classes are NOT covered reliably.

## Fire and smoke

- Publisher: mfranzon, `fire-smoke-yolov8`.
- Model card: https://huggingface.co/mfranzon/fire-smoke-yolov8
- Revision: `f1c6426b069c1849cbf13b1ef5d2a260289286db`.
- File: `fire_smoke_yolov8.pt`, 6,262,051 bytes; classes `fire`, `smoke`.
- Publisher-declared license: AGPL-3.0.
- Publisher-reported training data: D-Fire + Domestic Fire and Smoke.
  The card does not identify the exact second dataset release or its license.
  Confirm those upstream data details before claiming full dataset-license provenance.
- No training, retraining, or dataset download performed by this team.
- Domain: domestic/cooking/electrical/cigarette fires, not this road camera.
  Road-camera precision/recall is unmeasured; domain shift is a real limitation.
- Checkpoint checksum is verified before loading; inference never fetches dependencies
  or remote models. `dill==0.3.8` is explicitly pinned for checkpoint compatibility.

## Accident and near miss

These are experimental trajectory rules, not separately trained classifiers.
They use only observed tracks, approaching geometry, abrupt motion changes,
contact proxies, and subsequent stopping/clearance. Image-plane overlap cannot
prove collision or distinguish all perspective effects. Single-vehicle crashes
against an untracked fixed object are not covered. Validate on manually labeled
footage before presenting outputs as correct or scores as probabilities.
