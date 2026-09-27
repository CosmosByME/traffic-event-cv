# C3896 camera - team-authored calibration notes

This is our scene interpretation, not an organizer-provided file. The revised
instructions do not require camera.md. Reference: supplied C3896.MP4, fixed
3840x2160 view, approximately 29.970 fps. Reviewed frames: 5, 40, 120 and 240 s.

## Coordinates and use

Coordinates in configs/C3896.json and configs/camera.json are normalized x/width,
y/height; origin is top left, positive y is down. Objects use bounding-box bottom
centers, not wheel positions. Geometry applies only to this unchanged viewpoint
and aspect ratio; cropped, rotated or different-camera videos need recalibration.
This is image-region calibration, not metric speed or probability calibration.

## Observed layout

- Main road runs diagonally from upper left toward lower right.
- Three conservative lane cores cover the near-side approach toward the junction.
  Their direction vectors point down/right. They intentionally exclude the open
  turning area. Opposite carriageway lane geometry is not yet configured.
- Three zebra crossing regions cover the near-side approach, far-side approach,
  and foreground side-road crossing. Crossings terminate at curb/refuge edges.
- Raised median, pedestrian refuges and the far-right curb recess are excluded.
- The near-side signal queue approach is excluded from stopped-vehicle detection.
- The far-right curb car (saved track 3 around 40 s) is outside the far crossing;
  the earlier draft mistakenly included its stopped location.

## Deliberately unconfigured

Traffic signal heads are visible, but reliable separate red/green lamp ROIs and
their controlling-lane mapping have not been established. Stop-line/red-light
rules remain disabled. Prohibited turns, U-turn restrictions and solid-line
violation geometry are not verified and remain disabled. Do not infer legal
restrictions from ordinary vehicle motion alone.

## Validation limitations

Lane coverage is partial: congestion and wrong-way detection only cover those
configured lane cores. Signal queues may resemble congestion under the current
rule. Bottom-center tracking can misplace wheels or pedestrian feet, particularly
under occlusion. Event accuracy and risk probabilities are not validated by this
geometry review. Label representative clips and use the official evaluator.

Generate overlays with:

    python scripts/preview_camera.py --video samples/C3896.MP4

The saved-detection replay is diagnostic only; it cannot create new hazard
detections missing from the old analysis. Regenerate final sample predictions
with actual inference and the official runner before submission.
