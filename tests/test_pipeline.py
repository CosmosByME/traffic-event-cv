import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np
from src.config import validate_config
from src.pipeline import analyze
from src.render import render_video
from solution import RiskEstimator


class FakeDetector:
    def __init__(self, config): pass
    def step(self, frame):
        return [{'id':1,'class':'person','point':[.5,.5],'box':[.4,.3,.6,.5]}]


class PipelineTest(unittest.TestCase):
    def test_decode_events_render_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp)/'input.mp4'
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'mp4v'), 10, (160,120))
            self.assertTrue(writer.isOpened())
            for i in range(30): writer.write(np.full((120,160,3), 50, dtype=np.uint8))
            writer.release()
            cfg = validate_config({'calibrated':True,'road':[[0,0],[1,0],[1,1],[0,1]]})
            with patch('src.pipeline.Detector', FakeDetector):
                result = analyze(video, cfg)
            self.assertEqual(result['events'], [[0.0,3.0,'jaywalking']])
            self.assertEqual(len(result['risk']), 30)
            annotated = render_video(video, result, Path(tmp)/'annotated.mp4')
            cap = cv2.VideoCapture(str(annotated))
            self.assertTrue(cap.read()[0])
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),30)
            cap.release()

    def test_invalid_video_fails_explicitly(self):
        with self.assertRaises(ValueError): analyze('/nonexistent/video.mp4')

    def test_disabled_risk_never_loads_model(self):
        r = RiskEstimator()
        with patch('solution.load_config',return_value=validate_config({'risk_enabled':False})):
            r.reset({'fps':25})
        with patch('src.pipeline.Detector',side_effect=AssertionError('Must not load')):
            self.assertEqual(r.step(np.zeros((10,10,3),dtype=np.uint8),0),0)

    def test_risk_reset_clears_prior_video(self):
        with patch('solution.load_config',return_value=validate_config({'risk_enabled':True})), patch('src.pipeline.Detector',FakeDetector):
            r = RiskEstimator()
            r.reset({})
            r.step(np.zeros((10,10,3),dtype=np.uint8),0)
            first = r.engine
            r.reset({})
            r.step(np.zeros((10,10,3),dtype=np.uint8),0)
            self.assertIsNot(first,r.engine)

if __name__ == '__main__': unittest.main()
