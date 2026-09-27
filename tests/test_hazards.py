import math
import unittest
from unittest.mock import patch
from src.config import validate_config
from src.events import RuleEngine, merge_events
from src.hazards import HazardRules
from src.risk import PersistentRisk
from src.output import risk_summary
from src.yield_rule import YieldRule
from scripts.check_risk import audit

ROAD = [[0,0],[1,0],[1,1],[0,1]]
CROSSING = [[.4,.2],[.6,.2],[.6,.8],[.4,.8]]


def config(**kwargs):
    return validate_config(dict(calibrated=True,road=ROAD,**kwargs))


def obj(x=.5,y=.5,ident=1,cls='car',confidence=.95):
    return dict(id=ident,point=[x,y],box=[x-.04,y-.08,x+.04,y],confidence=confidence,**{'class':cls})


def motion(o,v=(0,0)):
    return o,v,math.hypot(*v),True


class HazardTests(unittest.TestCase):
    def test_fire_requires_persistent_learned_evidence(self):
        h=HazardRules(config())
        for t in [0,.5,1,1.5]: h.step([], [obj(cls='smoke',ident=-1)], t)
        self.assertEqual(h.finish(1.6), [[0,1.6,'fire_smoke']])
        h=HazardRules(config())
        h.step([], [obj(cls='fire',ident=-1)], 0)
        h.step([], [], .6)
        self.assertEqual(h.finish(1), [])

    def test_road_obstacle_not_carried_item_or_vehicle(self):
        h=HazardRules(config())
        for t in [0,.5,1,1.5]:
            objects=[obj(cls='dog'),obj(.7,cls='suitcase',ident=2),obj(.7,cls='person',ident=3)]
            h.step([motion(o) for o in objects],objects,t)
        self.assertEqual(h.finish(1.6), [[0,1.6,'road_obstacle']])
        h=HazardRules(config())
        for t in [0,.5,1,1.5]:
            objects=[obj()]
            h.step([motion(o) for o in objects],objects,t)
        self.assertEqual(h.finish(1.6), [])

    def test_fire_gap_and_low_confidence_are_not_bridged(self):
        h=HazardRules(config())
        h.step([], [obj(cls='fire',ident=-1)],0)
        h.step([], [obj(cls='fire',ident=-1)],1)
        h.step([], [obj(cls='fire',ident=-1,confidence=.1)],1.2)
        self.assertEqual(h.finish(1.3), [])

    def test_hazards_respect_scene_and_feature_switches(self):
        for c in [validate_config({'calibrated':False}),
                  config(excluded_zones=[ROAD]),config(fire_smoke_enabled=False,obstacle_detection_enabled=False)]:
            h=HazardRules(c)
            for t in [0,.5,1,1.5]: h.step([], [obj(cls='fire',ident=-1),obj(.3,cls='dog')],t)
            self.assertEqual(h.finish(1.6), [])

    def test_accident_needs_approach_contact_and_abrupt_braking(self):
        h=HazardRules(config())
        for t,x1,x2,v in [(0,.4,.5,.2),(.1,.44,.5,.2),(.2,.49,.5,.2),
                           (.3,.49,.5,.02),(.41,.49,.5,.02),(.5,.49,.5,0),
                           (.7,.49,.5,0),(1.01,.49,.5,0)]:
            a,b=motion(obj(x1), (v,0)),motion(obj(x2,ident=2),(-v,0))
            h.step([a,b],[a[0],b[0]],t)
        events=h.finish(1.1)
        self.assertEqual([e[2] for e in events],['accident'])
        self.assertAlmostEqual(events[0][0],.2)
        self.assertAlmostEqual(events[0][1],.5)
        h.step([],[],2)
        self.assertEqual(len(h.finish(2.1)),1)

    def test_near_miss_needs_evasion_then_clearance_without_contact(self):
        h=HazardRules(config())
        for t,x1,x2,v in [(0,.4,.5,.2),(.2,.43,.5,.2),(.3,.43,.5,.02),
                           (.5,.42,.51,-.1),(.7,.40,.53,-.1),(1,.34,.6,-.1)]:
            a,b=motion(obj(x1),(v,0)),motion(obj(x2,ident=2),(-v,0))
            h.step([a,b],[a[0],b[0]],t)
        events=h.finish(1.1)
        self.assertEqual([e[2] for e in events],['near_miss'])
        self.assertAlmostEqual(events[0][0],.3)
        self.assertAlmostEqual(events[0][1],1)

    def test_overlap_and_co_moving_traffic_are_not_collisions(self):
        h=HazardRules(config())
        for i in range(30):
            a,b=motion(obj(.4+i*.002),(.02,0)),motion(obj(.42+i*.002,ident=2),(.02,0))
            h.step([a,b],[a[0],b[0]],i/10)
        self.assertEqual(h.finish(3),[])

    def test_contact_disqualifies_near_miss(self):
        h=HazardRules(config())
        for t,x1,x2,v in [(0,.4,.5,.2),(.2,.49,.5,.2),(.3,.49,.5,.02),(.4,.35,.65,-.2)]:
            a,b=motion(obj(x1),(v,0)),motion(obj(x2,ident=2),(-v,0))
            h.step([a,b],[a[0],b[0]],t)
        self.assertNotIn('near_miss',[e[2] for e in h.finish(.5)])

    def test_engine_obstacle_is_not_stopped_vehicle(self):
        e=RuleEngine(config(stopped_seconds=1))
        for i in range(30): e.step([obj(cls='dog')],i/10)
        self.assertEqual([x[2] for x in e.finish(3)],['road_obstacle'])

    def test_yield_needs_witnessed_entry_and_displacement(self):
        rule=YieldRule(config(crosswalks=[CROSSING]))
        for i in range(100):
            rule.step([motion(obj(.5+.001*(i%2)),(.01,0)),motion(obj(.5,ident=2,cls='person'))],i/10)
        self.assertEqual(rule.finish(10),[])
        for i,x in enumerate([.3,.38,.42,.46,.5,.55,.61]):
            rule.step([motion(obj(x),(.2,0)),motion(obj(.5,ident=2,cls='person'))],11+i*.2)
        events=rule.finish(12.4)
        self.assertEqual(len(events),1)
        self.assertAlmostEqual(events[0][0],11.4)
        self.assertAlmostEqual(events[0][1],12.2)

    def test_yield_does_not_merge_disjoint_visits(self):
        events=[[0,1,'failure_to_yield'],[1.1,2,'failure_to_yield']]
        self.assertEqual(merge_events(events,2),events)
        self.assertEqual(merge_events(events+[[.9,1.2,'failure_to_yield']],2),[[0,2,'failure_to_yield']])

    def test_risk_summary_and_audit_distinguish_time_from_score(self):
        self.assertEqual(risk_summary([[340.3,.7]])['max_score'],.7)
        self.assertEqual(audit({'risk':[[340.3,.7]]})['video']['last_timestamp_seconds'],340.3)
        for row in [[0,12],[0,float('nan')],[0,float('inf')],[0,-.1],[.7,340.3],['0',.1]]:
            with self.assertRaises(ValueError): risk_summary([row])

    def test_complete_engine_hazard_intervals_validate(self):
        from src.output import validate_prediction
        e=RuleEngine(config())
        for i in range(30):
            e.step([obj(.2,ident=-1,cls='smoke'),obj(.8,ident=2,cls='dog')],i/10)
        events=e.finish(3)
        self.assertEqual({x[2] for x in events},{'fire_smoke','road_obstacle'})
        validate_prediction(events,[[0,0],[2.9,.5]],3)

    def test_official_risk_estimator_bounds_all_return_paths(self):
        import numpy as np
        from solution import RiskEstimator
        with patch('solution.load_config',return_value=config(risk_enabled=True,sample_fps=10)), \
             patch('src.pipeline.Detector') as detector, patch('src.events.RuleEngine') as engine:
            detector.return_value.step.return_value=[]
            engine.return_value.step.side_effect=[99,-99,float('nan')]
            r=RiskEstimator()
            r.reset({'fps':20})
            scores=[r.step(np.zeros((10,10,3),dtype=np.uint8),i/20) for i in range(6)]
            self.assertTrue(all(math.isfinite(x) and 0<=x<=1 for x in scores))
            self.assertEqual(scores[0],scores[1])
            self.assertFalse(detector.call_args.args[0]['fire_smoke_enabled'])

    def test_risk_requires_persistence_and_rejects_low_confidence(self):
        r=PersistentRisk(config())
        pair=[motion(obj(.3),(.1,0)),motion(obj(.7,ident=2),(-.1,0))]
        self.assertEqual(r.step(pair,0),0)
        self.assertEqual(r.step(pair,.2),0)
        self.assertGreater(r.step(pair,.41),.5)
        self.assertEqual(r.step([], .5),0)
        pair[0][0]['confidence']=.1
        for t in [.6,.8,1,1.2]: self.assertEqual(r.step(pair,t),0)

    def test_fire_weights_missing_is_explicit(self):
        from src.fire import FireDetector
        with patch('src.fire.FIRE_PATH') as path:
            path.is_file.return_value=False
            with self.assertRaisesRegex(FileNotFoundError,'--fire-smoke'):
                FireDetector(config())


if __name__=='__main__': unittest.main()
