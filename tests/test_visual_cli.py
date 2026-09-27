import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

import run
from src.config import validate_config
from evaluate import validate


def result():
    return {'events': [], 'risk': [[0., .1]], 'meta': {'duration': 1.}}


class VisualCLITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.samples = self.root/'samples'
        self.samples.mkdir()
        self.video = self.samples/'road.MP4'
        self.video.touch()
        self.out = self.root/'outputs'

    def args(self):
        return ['--videos', str(self.samples), '--out-dir', str(self.out)]

    def test_creates_predictions_and_calls_existing_renderer(self):
        with patch('run.analyze', return_value=result()), patch('run.render_video') as render:
            self.assertEqual(run.main(self.args()), 0)
        render.assert_called_once()
        self.assertEqual(render.call_args.args[2], self.out/'road.annotated.mp4')
        data = json.loads((self.out/'predictions.json').read_text())
        self.assertEqual(validate(data), ([], []))
        self.assertEqual(data['log']['road.MP4']['status'], 'complete')

    def test_render_failure_keeps_predictions_and_continues(self):
        (self.samples/'second.mp4').touch()
        with patch('run.analyze', return_value=result()), patch('run.render_video', side_effect=[RuntimeError('encoder'), None]):
            self.assertEqual(run.main(self.args()), 1)
        data = json.loads((self.out/'predictions.json').read_text())
        self.assertEqual(len(data['videos']), 2)
        self.assertEqual(data['videos']['road.MP4']['risk'], [[0., .1]])
        self.assertEqual(data['log']['second.mp4']['status'], 'complete')

    def test_existing_results_require_explicit_overwrite(self):
        self.out.mkdir()
        path = self.out/'predictions.json'
        path.write_text('previous')
        with self.assertRaises(SystemExit):
            run.main(self.args())
        self.assertEqual(path.read_text(), 'previous')

    def test_input_collision_rejected_even_with_overwrite(self):
        (self.samples/'road.annotated.mp4').touch()
        with self.assertRaises(SystemExit):
            run.main(['--videos', str(self.samples), '--out-dir', str(self.samples), '--overwrite'])

    def test_actual_video_export_uses_green_and_orange_boxes(self):
        writer = cv2.VideoWriter(str(self.video), cv2.VideoWriter_fourcc(*'mp4v'), 10, (160, 120))
        self.assertTrue(writer.isOpened())
        for _ in range(10):
            writer.write(np.zeros((120, 160, 3), np.uint8))
        writer.release()
        class FakeDetector:
            def __init__(self, config): self.tick = 0
            def step(self, frame):
                self.tick += 1
                if self.tick > 5: return []
                return [{'id': 1, 'class': 'car', 'point': [.5, .8], 'box': [.3, .4, .7, .8]}]
        cfg = validate_config({'sample_fps': 10, 'risk_enabled': False})
        with patch('run.load_config', return_value=cfg), patch('src.pipeline.Detector', FakeDetector), patch('src.render.shutil.which', return_value=None):
            self.assertEqual(run.main(self.args()), 0)
        cap = cv2.VideoCapture(str(self.out/'road.annotated.mp4'))
        frames = []
        while True:
            ok, frame = cap.read()
            if not ok: break
            frames.append(frame)
        cap.release()
        self.assertEqual(len(frames), 10)
        observed = frames[2][70, 48].astype(int)
        predicted = frames[6][70, 48].astype(int)
        self.assertGreater(observed[1], observed[2])
        self.assertGreater(predicted[2], predicted[0]+80)
        self.assertGreater(predicted[1], predicted[0]+60)


if __name__ == '__main__':
    unittest.main()
