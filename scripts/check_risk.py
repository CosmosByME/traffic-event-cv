"""Read-only audit of analysis, website prediction or organizer prediction JSON."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.output import risk_summary


def audit(data):
    videos = data.get('videos',{'video':data})
    if not isinstance(videos,dict) or not videos:
        raise ValueError('No videos to check.')
    report = {}
    for name,video in videos.items():
        if not isinstance(video,dict) or 'risk' not in video:
            raise ValueError(f'{name}: missing risk rows.')
        summary = risk_summary(video['risk'])
        last = -1
        for index,(timestamp,score) in enumerate(video['risk']):
            if timestamp<=last:
                raise ValueError(f'{name}: non-increasing timestamp at row {index}.')
            last = timestamp
        summary['last_timestamp_seconds'] = last if last>=0 else None
        report[name] = summary
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prediction',type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(json.loads(args.prediction.read_text())),indent=2,allow_nan=False))
    except (ValueError,TypeError,KeyError) as exc:
        parser.exit(1,f'INVALID: {exc}\n')
