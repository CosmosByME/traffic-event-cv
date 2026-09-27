"""Online preparation only. Inference never downloads weights."""
import hashlib
import argparse
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TARGET = ROOT / 'weights/yolo11n.pt'
URL = 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fire-smoke',action='store_true',help='Also fetch the pinned open-weights fire/smoke specialist.')
    args = parser.parse_args()
    TARGET.parent.mkdir(exist_ok=True)
    if not TARGET.exists():
        temporary = TARGET.with_suffix('.download')
        try:
            urllib.request.urlretrieve(URL, temporary)
            if temporary.stat().st_size < 1_000_000:
                raise ValueError('Downloaded weights are unexpectedly small.')
            temporary.replace(TARGET)
        finally:
            temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    expected = (TARGET.parent/'SHA256SUMS').read_text().split()[0]
    if digest != expected:
        raise ValueError('Weights checksum mismatch. Remove the incorrect checkpoint and retry from the official source.')
    print(f'{TARGET}\nSHA256 {digest}')
    if args.fire_smoke:
        from src.fire import FIRE_PATH,FIRE_URL,FIRE_SHA256
        if not FIRE_PATH.exists():
            temporary = FIRE_PATH.with_suffix('.download')
            try:
                urllib.request.urlretrieve(FIRE_URL,temporary)
                if hashlib.sha256(temporary.read_bytes()).hexdigest()!=FIRE_SHA256:
                    raise ValueError('Fire/smoke download checksum mismatch; refusing to install.')
                temporary.replace(FIRE_PATH)
            finally:
                temporary.unlink(missing_ok=True)
        if hashlib.sha256(FIRE_PATH.read_bytes()).hexdigest()!=FIRE_SHA256:
            raise ValueError('Existing fire/smoke weights checksum mismatch.')
        print(f'{FIRE_PATH}\nSHA256 {FIRE_SHA256}')
