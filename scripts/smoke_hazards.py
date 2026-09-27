"""Real two-model video smoke test; no claim of event classification accuracy."""
import argparse
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from src.config import load_config, validate_config
from src.pipeline import analyze
from src.output import validate_prediction


def run(source=None,seconds=6):
    with tempfile.TemporaryDirectory(prefix='roadlens-hazards-') as temp:
        path=Path(temp)/'clip.mp4'
        writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),10,(960,540))
        if not writer.isOpened(): raise RuntimeError('Cannot create test clip')
        cap=None
        try:
            if source:
                cap=cv2.VideoCapture(str(source))
                fps=cap.get(cv2.CAP_PROP_FPS)
                if not cap.isOpened() or not np.isfinite(fps) or fps<=0: raise ValueError('Bad source video')
                stride=max(1,round(fps/10))
                for i in range(round(seconds*fps)):
                    ok,frame=cap.read()
                    if not ok: break
                    if i%stride==0: writer.write(cv2.resize(frame,(960,540)))
            else:
                for _ in range(seconds*10): writer.write(np.zeros((540,960,3),dtype=np.uint8))
        finally:
            writer.release()
            if cap: cap.release()
        config=load_config('configs/C3896.json') if source else validate_config(
            {'calibrated':True,'road':[[0,0],[1,0],[1,1],[0,1]],'risk_enabled':True})
        data=analyze(path,config)
        validate_prediction(data['events'],data['risk'],data['meta']['duration'])
        if not source: assert data['events']==[]
        print(json.dumps({k:data[k] for k in ('meta','model_status','events','risk_summary')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video',type=Path)
    args=parser.parse_args()
    run(args.video)
