import math
import unittest
from src.config import validate_config
from src.events import RuleEngine
from src.risk import bounded_score,smooth_score
from src.road_rules import RoadRules
from src.tracking import DisplayTracker
from src.output import validate_prediction
from src.signals import SignalReader

ROAD=[[0,0],[1,0],[1,1],[0,1]]
def obj(x=.5,y=.5,ident=1,cls='car'):
    return dict(id=ident,point=[x,y],box=[x-.025,y-.05,x+.025,y],**{'class':cls})
def config(**kwargs):
    return validate_config(dict(calibrated=True,road=ROAD,**kwargs))
def motion(o,v=(.1,0)):
    return (o,v,math.hypot(*v),True)

class ExtendedRulesTest(unittest.TestCase):
    def test_gap_does_not_split_event(self):
        e=RuleEngine(config())
        for i in range(30): e.step([] if i in (10,11) else [obj(cls='person')],i/10)
        self.assertEqual(e.finish(3),[[0.0,3.0,'jaywalking']])

    def test_long_gap_closes_at_last_observation(self):
        e=RuleEngine(config())
        for i in range(30): e.step([obj(cls='person')] if i<10 else [],i/10)
        self.assertEqual(e.finish(3),[[0.0,.9,'jaywalking']])

    def test_predictions_do_not_create_events(self):
        e=RuleEngine(config())
        for i in range(30): e.step([dict(obj(cls='person'),predicted=True)],i/10)
        self.assertEqual(e.finish(3),[])

    def test_display_expiration_and_identity(self):
        tracker=DisplayTracker(.5)
        self.assertFalse(tracker.update([obj()],0)[0]['predicted'])
        recovered=tracker.update([],.2)[0]
        self.assertTrue(recovered['predicted'])
        self.assertEqual(recovered['id'],1)
        self.assertFalse(tracker.update([obj()],.3)[0]['predicted'])
        self.assertEqual(tracker.update([],1),[])

    def test_risk_contract(self):
        for x in [-5,0,.4,2,float('inf'),float('-inf'),float('nan')]:
            for value in (bounded_score(x),smooth_score(.5,x,.1)):
                self.assertTrue(math.isfinite(value))
                self.assertGreaterEqual(value,0)
                self.assertLessEqual(value,1)

    def test_reassigned_id_does_not_leave_ghost_box(self):
        display=DisplayTracker(.5)
        display.update([obj(ident=1)],0)
        boxes=display.update([obj(ident=2)],.1)
        self.assertEqual([x['id'] for x in boxes],[2])

    def test_crosswalk_boundary_tolerance(self):
        e=RuleEngine(config(crosswalks=[[[.3,.3],[.6,.3],[.6,.6],[.3,.6]]],crosswalk_margin=.015))
        for i in range(20): e.step([obj(.605,cls='person')],i/10)
        self.assertEqual(e.finish(2),[])

    def test_output_rejects_wrong_risk_column(self):
        with self.assertRaises(ValueError): validate_prediction([],[[0,12]],20)
        with self.assertRaises(ValueError): validate_prediction([],[[0,float('nan')]],20)
        validate_prediction([],[[12,.7]],20)

    def test_signal_requires_consistent_visible_lamp(self):
        import numpy as np
        reader=SignalReader([{'id':'a','lamps':{'red':[0,0,.5,1],'green':[.5,0,1,1]}}])
        frame=np.zeros((20,20,3),dtype=np.uint8)
        frame[:,:10]=[0,0,255]
        self.assertEqual(reader.step(frame)['a'],'unknown')
        self.assertEqual(reader.step(frame)['a'],'unknown')
        self.assertEqual(reader.step(frame)['a'],'red')
        frame[:]=0
        self.assertEqual(reader.step(frame)['a'],'unknown')

    def signal_config(self):
        return config(signals=[{'id':'north','lamps':{'red':[0,0,.1,.1],'green':[.1,0,.2,.1]}}],
                      stop_lines=[{'signal_id':'north','line':[[.5,0],[.5,1]],'direction':[1,0],
                                   'intersection':[[.5,0],[.9,0],[.9,1],[.5,1]],
                                   'violation_zone':[[.5,0],[.6,0],[.6,1],[.5,1]]}])

    def test_red_light_until_intersection_exit(self):
        r=RoadRules(self.signal_config())
        for t,x in [(0,.4),(.2,.55),(.4,.7),(.6,.95)]:
            r.step([motion(obj(x))],t,{'north':'red'})
        self.assertEqual(r.finish(.7),[[0,.6,'red_light']])

    def test_unknown_light_never_means_red(self):
        r=RoadRules(self.signal_config())
        for t,x in [(0,.4),(.2,.6),(.4,.95)]: r.step([motion(obj(x))],t,{})
        self.assertEqual(r.finish(.5),[])

    def test_stop_line_ends_at_green(self):
        r=RoadRules(self.signal_config())
        r.step([motion(obj(.55),v=(0,0))],0,{'north':'red'})
        r.step([motion(obj(.55),v=(0,0))],.2,{'north':'red'})
        r.step([motion(obj(.55),v=(0,0))],.4,{'north':'green'})
        self.assertEqual(r.finish(.5),[[0,.4,'stop_line']])

    def test_solid_line_crossing(self):
        r=RoadRules(config(solid_lines=[{'line':[[.5,0],[.5,1]]}]))
        r.step([motion(obj(.4))],0,{})
        r.step([motion(obj(.51))],.2,{})
        r.step([motion(obj(.6))],.4,{})
        self.assertEqual(r.finish(.5),[[0,.4,'solid_line_crossing']])

    def test_configured_illegal_turn(self):
        rule=dict(label='illegal_turn',entry=[[0,0],[.3,0],[.3,1],[0,1]],
                  maneuver=[[.3,0],[.7,0],[.7,1],[.3,1]],exit=[[.7,0],[1,0],[1,1],[.7,1]])
        r=RoadRules(config(turn_rules=[rule]))
        for t,x in [(0,.2),(.2,.4),(.4,.6),(.6,.8)]: r.step([motion(obj(x))],t,{})
        self.assertEqual(r.finish(.7),[[.2,.6,'illegal_turn']])

    def test_all_lanes_needed_for_congestion(self):
        lanes=[dict(polygon=[[0,0],[.45,0],[.45,1],[0,1]],direction=[0,1]),
               dict(polygon=[[.55,0],[1,0],[1,1],[.55,1]],direction=[0,1])]
        e=RuleEngine(config(lanes=lanes,congestion_min_vehicles=2,congestion_seconds=1))
        for i in range(30): e.step([obj(.2,ident=1),obj(.3,ident=2)],i/10)
        self.assertNotIn('congestion',[x[2] for x in e.finish(3)])

if __name__=='__main__': unittest.main()
