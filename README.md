# RoadLens — WIUT Hackathon Computer Vision

## 1. Installation and running

Use **64-bit Python 3.11 or 3.12**, not Python 3.14. Open a terminal in the repository root, the folder containing `solution.py`. All commands below use that same Python installation.

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

Installation requires internet. On NVIDIA computers, a compatible GPU driver must already be installed. The default device setting automatically selects CUDA GPU 0 when available and otherwise uses the CPU.

### Obtain model weights before evaluation

Both checkpoints are included in `weights/`. To download missing files and verify existing files against `weights/SHA256SUMS`, run the preparation script **once, with internet, before evaluation**:

```bash
sh weights/download.sh
```

In Windows PowerShell, use this equivalent command **instead**:

```powershell
python scripts/download_weights.py --fire-smoke
```

The script obtains YOLO11n from Ultralytics and the pinned fire/smoke checkpoint from Hugging Face. Together they are approximately 12 MB. Inference uses local files only and never downloads weights.

### Run the official evaluation pipeline

Put the sample MP4 files in `samples/`, then run:

```bash
python run_submission.py --videos samples --out predictions.json
```

For the organizers' test set, replace `samples` with `/data/test` or the actual input folder. This produces **one JSON containing all videos**, their event intervals, per-frame risk scores and processing logs. Each video should report `OK` with an empty `log.errors`. Existing output files are replaced.

To produce the required sample submission file, use `--out predictions_samples.json`. The official `run_submission.py` and `evaluate.py` are unchanged. Check any generated file with:

```bash
python evaluate.py --pred predictions.json --validate-only
```

### Local annotated videos and website

For predictions plus annotated videos, use this **alternative local-review command**, not the official evaluation command:

```bash
python run.py --videos samples
```

It creates `outputs/predictions.json` and `outputs/<video-name>.annotated.mp4`. Green boxes are observed detections; orange boxes are temporary tracker predictions. Add `--overwrite` to replace existing local outputs. This single-pass visualization workflow is separate from the official two-pass evaluation.

To start the website, run `python website/server.py` and open `http://127.0.0.1:8080`.

## 2. Approach, models and datasets

The pipeline is **video frames → object detection → ByteTrack tracking → camera-dependent temporal rules → event intervals**. Default detection sampling is approximately 10 frames per second.

**Learned components:**

- **Ultralytics YOLO11n**, pretrained on COCO, detects road users and supported obstacle categories. The Ultralytics implementation uses [AGPL-3.0](https://github.com/ultralytics/ultralytics/blob/main/LICENSE).
- **YOLOv8n fire/smoke detector**, published by [mfranzon](https://huggingface.co/mfranzon/fire-smoke-yolov8), detects fire and smoke. The publisher declares AGPL-3.0. We pin revision `f1c6426b069c1849cbf13b1ef5d2a260289286db`.

**Tracking and rule-based components:**

ByteTrack associates detections across frames; the [original implementation is MIT-licensed](https://github.com/FoundationVision/ByteTrack/blob/main/LICENSE), while this project uses the Ultralytics integration. Trajectory direction, movement, persistence, pedestrian occupancy and configured road regions produce event candidates. Accident and near-miss detection use experimental motion/contact rules, not a separately trained accident classifier.

Part B maintains independent causal tracking state and uses only received frames to estimate approaching conflicts. Scores are bounded to `[0,1]`, but are not empirically calibrated accident probabilities. It does not reuse future information from Part A.

The default geometry matches the C3896 daytime framing. WNIP8357 has shifted framing and needs `configs/C3896.shifted.json`; profiles are **not selected automatically**. `TRAFFIC_CAMERA` overrides the official runner's default profile. Signal-dependent, prohibited-turn and solid-line event rules remain disabled in the supplied profiles pending validation. Scene observations are documented in [samples/camera.md](samples/camera.md).

**Training data and licences:**

Our team performed **no model training or fine-tuning**. The following datasets are upstream sources for the pretrained models, not datasets we downloaded for training:

- **COCO:** YOLO11n pretraining. Annotations use **CC BY 4.0**; images retain their respective owners' rights and applicable Flickr terms. See the [official terms](https://github.com/cocodataset/cocodataset.github.io/blob/master/dataset/termsofuse.htm).
- **D-Fire:** reported by the fire/smoke model publisher. The dataset collection is released under **CC0 1.0**; its authors state that they do not own the underlying image copyrights. See the [dataset licence](https://github.com/gaia-solutions-on-demand/DFireDataset/blob/master/LICENSE).
- **Domestic Fire and Smoke:** also reported by that publisher, but the model card does not identify the exact dataset release or its licence. **This provenance remains unverified.**

Organizer sample videos are used for scene calibration and testing, not weight training. Checkpoint sources, hashes and additional provenance are recorded in [weights/MODELS.md](weights/MODELS.md) and [weights/SHA256SUMS](weights/SHA256SUMS).

## 3. Seeds and reproducibility

Python `random`, NumPy and PyTorch seeds are fixed to **42** when initializing the detector. cuDNN benchmarking is disabled, cuDNN deterministic mode is enabled, and PyTorch deterministic algorithms are requested with `warn_only=True`. CUDA uses `CUBLAS_WORKSPACE_CONFIG=:4096:8` unless already configured in the environment.

Direct dependencies and checkpoint hashes are pinned. Some transitive dependencies are not pinned. Operations without deterministic implementations can still run with a warning; hardware, drivers, decoder behaviour and library versions can change numerical results. Byte-for-byte reproducibility across CPU/GPU platforms is not guaranteed.

## 4. Team and contributions

| Member | Role | Contribution |
| --- | --- | --- |
| Jaxongir Saidjanov | Backend Engineer | Developed the website backend and application logic. |
| Muhammad Egamov | Video Algorithm Specialist | Developed the video-analysis algorithm and event-detection pipeline. |
| Abdurrahmon Jurayev | Frontend Engineer | Designed and implemented the website's user interface and user experience. |
