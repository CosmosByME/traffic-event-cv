---
license: agpl-3.0
tags:
- ultralytics
- yolov8
- object-detection
- fire-detection
- smoke-detection
library_name: ultralytics
pipeline_tag: object-detection
---

# Early Fire and Smoke (YOLOv8)

A YOLOv8n detector finetuned for **early domestic fire and smoke**: cooking,
electrical, and cigarette scenarios. Part of the
[Model Garden](https://github.com/computer-vision-with-marco) collection of
finetuned computer-vision models.

## Classes

`fire`, `smoke`

## Intended use

Designed to pair with a temporal state machine that escalates through
**clear, smoke present, early warning (growing smoke), fire confirmed**, so
it alerts on persistent, growing smoke rather than a single noisy frame.

## Training

- **Base:** YOLOv8n
- **Data:** D-Fire + Domestic Fire and Smoke
- **Runtime:** ~70 FPS on Apple Silicon (MPS)

## Usage

```python
from ultralytics import YOLO

model = YOLO("fire_smoke_yolov8.pt")
results = model("your_video.mp4", stream=True)
for r in results:
    r.plot()
```

## Limitations

Vision alone is never a life-safety system. This is a research tool, **not** a
substitute for a certified smoke or fire detector.
