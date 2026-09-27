# C3896 intersection - team-authored scene calibration v2

These are team observations, not an organizer-provided camera description. The
revised task does not require camera.md. Calibration is image-region geometry,
not metric speed estimation or calibrated accident probability.

## References and coordinate system

- Original C3896.MP4: 3840x2160, approximately 29.970 fps; reviewed frames at
  5, 40, 120 and 240 seconds.
- Clear daytime screenshots: 2026-09-27 13.41.10.jpg and 13.41.23.jpg.
- Shifted-view screenshot: 2026-09-27 13.41.31.jpg (evening).
- Each screenshot is 2560x1662 including player borders. Use the 2560x1440 content
  rectangle [left=0, top=138, right=2560, bottom=1578], not the full screenshot.
- Screenshot pixel conversion: x_normalized = x/2560;
  y_normalized = (y-138)/1440. Review overlays use 1280x720.
- Runtime coordinates apply to the original 16:9 video content. They do not apply
  to a screenshot or video with embedded black borders without coordinate adjustment.
- Track anchors are bounding-box bottom centers, not measured wheel positions.

## Viewpoint distinction - important

The first two screenshots match the original C3896 framing. Static-feature checks
against its 40-second frame found over 350 consistent matches in each daytime
screenshot and a near-identity transform.

The third screenshot is from the same physical camera/location according to the
team, but has different framing. For example, the triangular refuge tip moves
from about (410,445) to (383,470) in the 1280x720 content image. The signal gantry,
median tip and crossing endpoints also move. This is not explained by exposure.

- configs/camera.json and configs/C3896.json: daytime/C3896 framing, active default.
- configs/C3896.shifted.json: separate manual regions for the third screenshot.
  Its source video filename and matching original frame remain unconfirmed.
  It is NOT automatically selected by the runner or by darkness.
- The same framing may occur in daylight or evening. Never choose geometry from
  lighting alone, and never average the two sets of crossing boundaries.
- Do not mix different-framing videos in a run using one static profile. Verify
  the original video framing and assign/select its profile before final evaluation.
  The current package does not automatically register different viewpoints.

## Visible road layout in the default profile

- Main road runs diagonally upper-left to lower-right. Near-side approach traffic
  travels down/right toward the junction; the other carriageway travels up/left.
- The clearer near-side approach shows three solid lane dividers, defining four
  approach lanes. Four conservative lane cores now replace the earlier three
  approximate regions. Cores terminate before the open intersection/turning area.
- Three visible solid-divider segments are recorded under calibration.observed_solid_lines.
  They are measurements only, NOT active event rules. Enabling the existing rule
  produced an implausible 190-second merged candidate on saved-track replay, so
  solid_line_crossing remains disabled pending temporal/contact logic validation.
- The near-side transverse stop marking is documented in calibration metadata,
  but does not activate signal-dependent violations.
- Three zebra crossing polygons follow the near-side approach, far-side approach
  and foreground side-road crossing, excluding the waiting/refuge islands.
- Raised median, three foreground/refuge islands and the far-right curb recess
  are excluded. The stopped curb car (old saved track 3 around 40 seconds) remains
  outside the far crossing.
- Signal queues on the near-side approach are excluded from stopped_vehicle.

## What remains unverified / disabled

Signal heads and some red/green lamps are visible. Still images do not establish
a robust time-varying lamp classifier or all signal-to-lane relationships. Signal
ROIs and ownership remain unset, so red_light and stop_line remain disabled.
The measured solid lines are also inactive for the validation reason above.
Prohibited turn/U-turn permissions are not established; those rules remain disabled.

Opposite-carriageway lane cores are not configured. The shifted-view profile
currently has road, crossings, queues and exclusion regions only; its lane and
solid-line rules remain unset pending original-video review.

## Accuracy and testing limitations

Congestion/wrong-way coverage is limited to configured lane cores. Routine signal
queues can resemble congestion under the current rule. Bounding-box bottom centers
can misplace tire/foot contacts, especially under occlusion. Solid-line candidate
events require video review; adding visible geometry is not accuracy validation.
Day/evening detector quality and risk calibration need separately labeled clips.

Developer preview examples (not organizer setup commands):

    python scripts/preview_camera.py --video samples/C3896.MP4
    python scripts/preview_camera.py --image "reference.jpg" --crop 0 138 2560 1578 --camera configs/C3896.json

Diagnostic overlays/replay are under outputs/calibration-v2. Saved-track replay
cannot add detections absent from the old analysis. Regenerate final predictions
with full inference after profile selection and manual event review.
