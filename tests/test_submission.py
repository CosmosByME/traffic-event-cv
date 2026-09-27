import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import ROOT
from src.runtime import configure_runtime, verify_weights
from solution import CLASSES
from evaluate import OFFICIAL_CLASSES


class SubmissionTest(unittest.TestCase):
    def test_official_files_are_unchanged(self):
        expected = {
            'run_submission.py': 'a47b494afae14432a65166b43cd5f2a278408ce661aecf0fb86b6fa05a06c204',
            'evaluate.py': '111c6fa04709c9f1df4ea3db4bede749953b2c27bdc5679c2ef56794637573b5',
        }
        for name, sha in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), sha)
        self.assertEqual(set(CLASSES), set(OFFICIAL_CLASSES))

    def test_bundled_weights_are_complete_and_small(self):
        total = 0
        for line in (ROOT/'weights/SHA256SUMS').read_text().splitlines():
            sha, name = line.split()
            path = ROOT/'weights'/name
            verify_weights(path, sha)
            total += path.stat().st_size
        self.assertLess(total, 5_000_000_000)

    def test_missing_or_corrupt_weights_fail_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp)/'missing.pt'
            with self.assertRaises(FileNotFoundError):
                verify_weights(missing, '0'*64)
            with self.assertRaises(ValueError):
                verify_weights(ROOT/'weights/SHA256SUMS', '0'*64)

    def test_auto_device_uses_cuda_when_available(self):
        c = {'device': 'auto'}
        with patch('torch.cuda.is_available', return_value=True):
            self.assertEqual(configure_runtime(c)['device'], '0')
        self.assertEqual(c['device'], 'auto')

    def test_auto_device_cpu_fallback_and_explicit_override(self):
        with patch('torch.cuda.is_available', return_value=False):
            self.assertEqual(configure_runtime({'device':'auto'})['device'], 'cpu')
        with patch('torch.cuda.is_available', return_value=True):
            self.assertEqual(configure_runtime({'device':'cpu'})['device'], 'cpu')


if __name__ == '__main__':
    unittest.main()
