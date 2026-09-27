"""Regression checks for the manually reviewed C3896 image geometry."""
import unittest
from src.config import ROOT, load_config
from src.events import inside, RuleEngine


class CameraCalibrationTest(unittest.TestCase):
    def setUp(self):
        self.c = load_config(ROOT / 'configs/C3896.json')

    def test_default_matches_reviewed_profile(self):
        self.assertEqual(load_config(ROOT / 'configs/camera.json'), self.c)
        self.assertFalse(load_config(ROOT / 'configs/uncalibrated.json')['calibrated'])

    def test_curb_car_is_not_on_crosswalk(self):
        # Actual saved track 3 bottom center at 40.04s.
        point = [.9525688489, .4354168362]
        self.assertFalse(any(inside(point, p) for p in self.c['crosswalks']))
        self.assertTrue(any(inside(point, p) for p in self.c['excluded_zones']))

    def test_visible_crossings_and_refuges(self):
        for pixels, index in [((450, 383), 0), ((1020, 341), 1), ((400, 625), 2)]:
            self.assertTrue(inside([pixels[0]/1280, pixels[1]/720], self.c['crosswalks'][index]))
        for x, y in [(820, 371), (419, 485), (530, 569)]:
            self.assertTrue(any(inside([x/1280, y/720], p) for p in self.c['excluded_zones']))

    def test_unverified_restrictions_are_disabled(self):
        for key in ('signals', 'stop_lines', 'solid_lines', 'turn_rules'):
            self.assertEqual(self.c[key], [])

    def test_signal_queue_is_not_a_stopped_vehicle(self):
        engine = RuleEngine(self.c)
        point = [550/1280, 315/720]
        obj = dict(id=1, **{'class': 'car'}, point=point,
                   box=[point[0]-.03, point[1]-.05, point[0]+.03, point[1]])
        for i in range(130):
            engine.step([obj], i/10)
        self.assertNotIn('stopped_vehicle', [x[2] for x in engine.finish(13)])


if __name__ == '__main__':
    unittest.main()
