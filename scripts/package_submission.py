"""Build a small friend-test ZIP without videos, caches, credentials or a venv."""
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.runtime import verify_weights


def main():
    files = [ROOT/name for name in (
        '.gitignore', '.gitattributes', '.dockerignore', 'solution.py',
        'run_submission.py', 'evaluate.py', 'requirements.txt', 'Dockerfile',
        'README.md', 'STATUS.md', 'predictions_samples.json', 'dev_run.py',
        'samples/camera.md', 'weights/SHA256SUMS', 'weights/MODELS.md',
        'weights/download.sh', 'weights/yolo11n.pt', 'weights/fire_smoke_yolov8.pt')]
    for directory, suffixes in (
        ('src', {'.py'}), ('scripts', {'.py'}), ('tests', {'.py'}),
        ('configs', {'.json', '.yaml'}), ('website', {'.py', '.html', '.css', '.js', '.md'}),
    ):
        files.extend(p for p in (ROOT/directory).rglob('*')
                     if p.is_file() and p.suffix in suffixes and '__pycache__' not in p.parts)
    for line in (ROOT/'weights/SHA256SUMS').read_text().splitlines():
        sha, name = line.split()
        verify_weights(ROOT/'weights'/name, sha)
    target = ROOT/'outputs/roadlens-test-package.zip'
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            if path.stat().st_size > 100_000_000:
                raise ValueError(f'Unexpectedly large package file: {path}')
            archive.write(path, Path('traffic-event-cv')/path.relative_to(ROOT))
        archive.writestr('traffic-event-cv/TEST_PACKAGE.txt',
                         'Friend-test package; not an accuracy-certified final submission.\n'
                         'Use Python 3.11/3.12. From traffic-event-cv:\n'
                         'pip install -r requirements.txt\n'
                         'python run_submission.py --videos samples --out predictions.json\n'
                         'Supply the sample MP4 files separately; weights are included.\n'
                         'predictions_samples.json is an older reference output and must be regenerated.\n'
                         'Inspect every video log.errors: the official harness can exit 0 on video failure.\n')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Archive integrity check failed')
    print(f'{target}\n{target.stat().st_size / 1_000_000:.2f} MB')


if __name__ == '__main__':
    main()
