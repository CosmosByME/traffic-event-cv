"""Development runner; does not replace the missing official harness."""
import argparse
import json
from pathlib import Path
from src.pipeline import analyze
from src.config import load_config
from src.output import validate_prediction

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--videos', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=Path('outputs/predictions.json'))
    parser.add_argument('--team', default='Team name pending')
    parser.add_argument('--camera', type=Path, help='Camera JSON; default configs/camera.json')
    parser.add_argument('--render', action='store_true', help='Export annotated sample MP4s; ffmpeg enables browser H.264.')
    args = parser.parse_args()
    if not args.videos.is_dir():
        parser.error(f'Video folder does not exist: {args.videos.resolve()}')
    files = sorted(path for path in args.videos.iterdir()
                   if path.is_file() and path.suffix.lower() == '.mp4')
    if not files:
        parser.error(f'No MP4 videos found in {args.videos.resolve()} (accepts .mp4 and .MP4).')
    payload = {'team': args.team, 'videos': {}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for path in files:
        print(f'Processing {path.name} — loading model and decoding video…', flush=True)
        last_percent = [-1]
        def progress(fraction):
            percent = int(fraction * 100)
            if percent > last_percent[0]:
                print(f'  Analysis: {percent}%', flush=True)
                last_percent[0] = percent
        result = analyze(path, config=load_config(args.camera), progress=progress)
        validate_prediction(result['events'],result['risk'],result['meta']['duration'])
        payload['videos'][path.name] = {k: result[k] for k in ('events', 'risk')}
        (args.out.parent / (path.stem+'.analysis.json')).write_text(json.dumps(result))
        if args.render:
            print('  Exporting annotated video…', flush=True)
            from src.render import render_video
            render_video(path, result, args.out.parent / (path.stem+'.annotated.mp4'))
        print(path.name, result['meta'], result['events'])
    args.out.write_text(json.dumps(payload, indent=2))
