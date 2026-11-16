import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

scripts = pathlib.Path(__file__).resolve().parents[2] / 'scripts/sentencing'
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location('offline', scripts/'parse_offline.py')
offline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(offline)

class OfflineTests(unittest.TestCase):
    def test_local_input_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root/'a.html').write_text('<table><tr><td>감경</td></tr></table>', encoding='utf-8')
            results, errors = offline.process(root, [{'file':'a.html', 'url':'https://sc.scourt.go.kr/sc/example'}])
            self.assertFalse(errors)
            self.assertEqual(results[0]['tables'], [[['감경']]])
            self.assertEqual(len(results[0]['sha256']), 64)
            self.assertIn('collected_at_missing', results[0]['warnings'])
            self.assertEqual(results[0]['comparability'], 'unknown')
    def test_rejects_path_escape_and_nonofficial_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            results, errors = offline.process(pathlib.Path(tmp), [{'file':'../outside', 'url':'https://sc.scourt.go.kr/a'}, {'file':'a', 'url':'https://example.com'}])
            self.assertFalse(results)
            self.assertEqual(len(errors), 2)

if __name__ == '__main__': unittest.main()
