import unittest
from src.config import validate_config
from src.events import RuleEngine, merge_events

ROAD = [[0,0],[1,0],[1,1],[0,1]]

def config(**kwargs):
    return validate_config(dict(calibrated=True, road=ROAD, **kwargs))

def obj(x=.5, y=.5, cls='car', ident=1):
    return {'id': ident, 'class': cls, 'point': [x,y], 'box': [x-.04,y-.1,x+.04,y]}

class RulesTest(unittest.TestCase):
    def test_stationary_threshold_and_boundary(self):
        engine = RuleEngine(config())
        for i in range(121):
            engine.step([obj()], i/10)
        events = engine.finish(12.1)
        self.assertEqual(events[0][2], 'stopped_vehicle')
        self.assertLess(events[0][0], 1)
        short = RuleEngine(config())
        for i in range(50): short.step([obj()], i/10)
        self.assertEqual(short.finish(5), [])

    def test_queue_excluded(self):
        e = RuleEngine(config(queue_zones=[ROAD]))
        for i in range(130): e.step([obj()], i/10)
        self.assertEqual(e.finish(13), [])

    def test_uncalibrated(self):
        c = config(); c['calibrated'] = False
        e = RuleEngine(c)
        for i in range(130): e.step([obj(cls='person')], i/10)
        self.assertEqual(e.finish(13), [])

    def test_crosswalk_excluded(self):
        e = RuleEngine(config(crosswalks=[ROAD]))
        for i in range(20): e.step([obj(cls='person')], i/10)
        self.assertEqual(e.finish(2), [])

    def test_jaywalking(self):
        e = RuleEngine(config())
        for i in range(20): e.step([obj(cls='person')], i/10)
        self.assertEqual(e.finish(2), [[0.0,2.0,'jaywalking']])

    def test_wrong_way(self):
        e = RuleEngine(config(lanes=[{'polygon':ROAD,'direction':[1,0]}]))
        for i in range(40): e.step([obj(x=.8-i*.01)], i/10)
        self.assertIn('wrong_way', [x[2] for x in e.finish(4)])

    def test_merge_same_class_only(self):
        result = merge_events([[0,2,'a'],[1,3,'a'],[1,2,'b'],[-1,.1,'c']], 3)
        self.assertEqual(result, [[0.0,3.0,'a'],[1.0,2.0,'b']])

    def test_risk_approach_vs_separation(self):
        a, b = obj(.3), obj(.7, ident=2)
        self.assertGreater(RuleEngine.risk([(a,(.1,0),.1,True),(b,(-.1,0),.1,True)]), .5)
        self.assertEqual(RuleEngine.risk([(a,(-.1,0),.1,True),(b,(.1,0),.1,True)]), 0)

    def test_no_future_state_influence(self):
        a, b = RuleEngine(config(risk_enabled=True)), RuleEngine(config(risk_enabled=True))
        for i in range(20):
            objects = [obj(.2+i*.01),obj(.8-i*.01,ident=2)]
            self.assertEqual(a.step(objects,i/10),b.step(objects,i/10))

    def test_invalid_geometry(self):
        with self.assertRaises(ValueError): config(lanes=[{'polygon':ROAD,'direction':[0,0]}])
        with self.assertRaises(ValueError): config(sample_fps=0)

if __name__ == '__main__': unittest.main()
