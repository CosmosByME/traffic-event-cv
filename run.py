"""Local visual CLI. The unchanged run_submission.py remains the judge entry point."""
import argparse
import json
from pathlib import Path
import sys
import time

from src.config import load_config
from src.output import validate_prediction
from src.pipeline import analyze
from src.render import render_video


def save_json(path, payload):
    """Checkpoint after each video without leaving a half-written JSON file."""
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--videos', type=Path, required=True, help='MP4 file or folder of MP4 files')
    parser.add_argument('--out-dir', type=Path, default=Path('outputs'))
    parser.add_argument('--camera', type=Path, help='Override the default camera profile')
    parser.add_argument('--team', default='unnamed-team')
    parser.add_argument('--overwrite', action='store_true', help='Replace this run’s existing output files')
    args = parser.parse_args(argv)
    source = args.videos
    if source.is_file() and source.suffix.lower() == '.mp4':
        videos = [source]
    elif source.is_dir():
        videos = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() == '.mp4')
    else:
        parser.error('Specify an existing MP4 file or video folder.')
    if not videos:
        parser.error(f'No MP4 files found in {source}.')
    # A.mp4/A.MP4 must not silently write to the same annotated filename.
    if len({p.stem.casefold() for p in videos}) != len(videos):
        parser.error('Input videos must have distinct filenames, ignoring extension and case.')
    output = args.out_dir
    if output.exists() and not output.is_dir():
        parser.error('--out-dir must be a directory.')
    prediction_path = output / 'predictions.json'
    targets = [output / f'{p.stem}.annotated.mp4' for p in videos]
    intermediates = [p.with_name(p.stem + '.intermediate.mp4') for p in targets]
    artifacts = [prediction_path, prediction_path.with_name('predictions.json.tmp'), *targets, *intermediates]
    sources = {p.resolve() for p in videos}
    if any(p.resolve() in sources for p in artifacts):
        parser.error('Output paths must not overwrite input videos, even with --overwrite.')
    existing = [str(p) for p in artifacts if p.exists()]
    if existing and not args.overwrite:
        parser.error('Output files already exist. Choose another --out-dir or use --overwrite: '
                     + ', '.join(existing))
    try:
        config = load_config(args.camera)
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))
    output.mkdir(parents=True, exist_ok=True)
    payload = {'team': args.team, 'videos': {}, 'log': {}}
    save_json(prediction_path, payload)
    print(f'Camera: {config.get("name", "unnamed")} | device: {config["device"]}', flush=True)
    print('Local visual run: single-pass website analysis, not the official timed A+B benchmark.', flush=True)
    print('Green = observed detection; orange = short-lived tracker prediction, not event evidence.', flush=True)
    failed = False
    for number, (video, target) in enumerate(zip(videos, targets), 1):
        started = time.perf_counter()
        log = {'errors': [], 'annotated_video': None}
        payload['log'][video.name] = log
        print(f'[{number}/{len(videos)}] {video.name}: analyzing…', flush=True)
        last_percent = -1

        def progress(fraction):
            nonlocal last_percent
            percent = int(fraction * 100)
            if percent >= last_percent + 5 or percent == 100:
                if percent != last_percent:
                    print(f'  Analysis {percent}%', flush=True)
                last_percent = percent

        try:
            result = analyze(video, config=config, progress=progress)
            validate_prediction(result['events'], result['risk'], result['meta']['duration'])
            payload['videos'][video.name] = {k: result[k] for k in ('events', 'risk')}
            log['analysis_sec'] = round(time.perf_counter() - started, 2)
            log['duration_sec'] = result['meta']['duration']
            log['status'] = 'rendering'
            save_json(prediction_path, payload)
            print('  Predictions saved. Rendering annotated MP4 (may take several minutes for 4K)…', flush=True)
            render_started = time.perf_counter()
            render_video(video, result, target)
            log['render_sec'] = round(time.perf_counter() - render_started, 2)
            log['annotated_video'] = target.name
            log['status'] = 'complete'
            print(f'  Saved {target}', flush=True)
        except Exception as exc:
            failed = True
            payload['videos'].setdefault(video.name, {'events': [], 'risk': []})
            log['errors'].append(f'{type(exc).__name__}: {exc}')
            log['status'] = 'failed'
            print(f'  FAILED: {exc}', file=sys.stderr, flush=True)
        finally:
            log['total_sec'] = round(time.perf_counter() - started, 2)
            save_json(prediction_path, payload)
    print(f'Results: {prediction_path.resolve()}', flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
