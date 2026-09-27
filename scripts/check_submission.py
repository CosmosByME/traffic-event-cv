"""Developer-only relocated-package smoke check using the UNCHANGED official CLI.

Not an extra setup step for judges. Uses installed dependencies; not a clean-install
or target-GPU benchmark. --python can select a separately installed clean environment.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', type=Path)
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    # Do not resolve a venv's python symlink: that would discard its environment.
    interpreter = str(Path(args.python).absolute())
    with tempfile.TemporaryDirectory(prefix='roadlens-submission-') as temp:
        package = Path(temp)
        for name in ('solution.py', 'run_submission.py', 'evaluate.py', 'requirements.txt'):
            shutil.copy2(ROOT/name, package/name)
        for name in ('src', 'configs', 'weights'):
            shutil.copytree(ROOT/name, package/name, ignore=shutil.ignore_patterns('__pycache__'))
        samples = package/'test videos'
        samples.mkdir()
        path = samples/'smoke.mp4'
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 10, (960, 540))
        if not writer.isOpened():
            raise RuntimeError('Cannot create smoke video')
        cap = cv2.VideoCapture(str(args.video)) if args.video else None
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) if cap else 10
            if cap and (not cap.isOpened() or fps <= 0):
                raise ValueError('Cannot open source video')
            source_index = -1
            for i in range(200):
                if cap:
                    target = round(i*fps/10)
                    ok = True
                    while source_index < target:
                        ok = cap.grab()
                        source_index += 1
                        if not ok:
                            break
                    ok, frame = cap.retrieve() if ok else (False, None)
                    if not ok:
                        raise ValueError('Source video is shorter than 20s')
                    frame = cv2.resize(frame, (960, 540))
                else:
                    frame = np.zeros((540, 960, 3), np.uint8)
                writer.write(frame)
        finally:
            writer.release()
            if cap:
                cap.release()
        command = [interpreter, 'run_submission.py', '--videos', str(samples), '--out', 'predictions.json']
        subprocess.run(command, cwd=package, check=True)
        pred = json.loads((package/'predictions.json').read_text())
        errors = pred['log']['smoke.mp4']['errors']
        if errors:
            raise AssertionError(errors)
        if len(pred['videos']['smoke.mp4']['risk']) != 200:
            raise AssertionError('Part B must produce one score per frame')
        subprocess.run([interpreter, 'evaluate.py', '--pred', 'predictions.json', '--validate-only'],
                       cwd=package, check=True)
        report = {'input': str(args.video) if args.video else 'synthetic black frames',
                  'relocated_package': True, 'official_default_limits': True,
                  'dependency_installation': 'Performed separately; this script does not install packages',
                  'python_executable': interpreter,
                  'log': pred['log'], 'validation': 'passed'}
        output = ROOT/'outputs/submission-check'
        output.mkdir(parents=True, exist_ok=True)
        (output/'smoke-report.json').write_text(json.dumps(report, indent=2))
        print('PASS: relocated package, bundled weights, default Part A+B budget and official validation.')


if __name__ == '__main__':
    main()
