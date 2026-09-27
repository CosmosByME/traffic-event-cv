"""Render camera geometry over actual frames; no model inference required."""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', required=True)
    parser.add_argument('--camera', default='configs/C3896.json')
    parser.add_argument('--out', default='outputs/calibration')
    parser.add_argument('--times', nargs='+', type=float, default=[5, 40, 120, 240])
    args = parser.parse_args()
    config = load_config(args.camera)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit('Cannot open reference video')
    try:
        for seconds in args.times:
            cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
            ok, frame = cap.read()
            if not ok:
                raise ValueError(f'Cannot read frame at {seconds}s')
            frame = cv2.resize(frame, (1280, 720))
            cv2.imwrite(str(out / f'frame-{seconds:g}.jpg'), frame)
            for key, polygons, color in [
                ('road', [config['road']], (0, 220, 0)),
                ('crosswalk', config['crosswalks'], (0, 220, 255)),
                ('exclude', config['excluded_zones'], (220, 80, 220)),
                ('queue', config['queue_zones'], (255, 150, 0)),
                ('lane', [x['polygon'] for x in config['lanes']], (255, 255, 0)),
            ]:
                for index, polygon in enumerate(polygons):
                    if not polygon:
                        continue
                    points = (np.array(polygon) * [1280, 720]).astype(np.int32)
                    cv2.polylines(frame, [points], True, color, 2)
                    center = tuple(points.mean(axis=0).astype(int))
                    cv2.putText(frame, f'{key}-{index}', center,
                                cv2.FONT_HERSHEY_SIMPLEX, .5, color, 2)
            path = out / f'overlay-{seconds:g}.jpg'
            cv2.imwrite(str(path), frame)
            print(path.resolve())
    finally:
        cap.release()


if __name__ == '__main__':
    main()
