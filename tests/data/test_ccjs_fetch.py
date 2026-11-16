import importlib.util
import pathlib
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

p = pathlib.Path(__file__).resolve().parents[2]/'scripts/statistics/ccjs_fetch.py'
s = importlib.util.spec_from_file_location('ccjs', p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)

class Tests(unittest.TestCase):
    def test_url_encoding_once_and_key_roundtrip(self):
        u=m.build_url(m.DEFAULT,'abc%2Bdef%2Fghi%3D',{'table':'T1','year':'2011','row':'가@나','col':'다'})
        self.assertEqual(parse_qs(urlsplit(u).query)['serviceKey'],['abc+def/ghi='])
    def test_disallow_untrusted_or_query_url(self):
        for url in ['https://evil.example/B554626/ccjs','http://apis.data.go.kr/B554626/ccjs','https://apis.data.go.kr/B554626/ccjs?serviceKey=x']:
            with self.assertRaises(ValueError): m.endpoint_url(url)
    def test_snapshot_deduplicates_and_records_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); params={'table':'T1','year':'2011','row':'r','col':'c'}
            a,_=m.write_snapshot(b'{"data":[]}',m.DEFAULT,params,root)
            b,_=m.write_snapshot(b'{"data":[]}',m.DEFAULT,params,root)
            self.assertEqual(a,b); self.assertEqual(len(list(root.glob('*.json'))),1)
            self.assertEqual(len((root/'requests.jsonl').read_text().splitlines()),2)
    def test_env_key_and_reject_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'.env'
            path.write_text('KICJ_SERVICE_KEY="example%2Bkey"\n')
            self.assertEqual(m.normalize_key(m.load_env_key(path)), 'example+key')
            path.write_text('KICJ_SERVICE_KEY=a\nKICJ_SERVICE_KEY=b\n')
            with self.assertRaises(ValueError): m.load_env_key(path)

if __name__=='__main__': unittest.main()
