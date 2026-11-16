import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[2] / 'scripts/sentencing/collect.py'
spec = importlib.util.spec_from_file_location('sentencing_collect', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CollectorTests(unittest.TestCase):
    def test_extract_table_and_link(self):
        p = m.parse('<a href="/sc/krsc/criterion/past/a">과거</a><table><tr><th>유형</th><th>감경</th></tr><tr><td>1</td><td>1년 ~ 2년</td></tr></table>'.encode())
        self.assertEqual(p.tables[0][1], ['1', '1년 ~ 2년'])
        self.assertEqual(p.links[0][1], '과거')
    def test_host_restriction(self):
        self.assertTrue(m.official('https://sc.scourt.go.kr/a'))
        self.assertFalse(m.official('https://sc.scourt.go.kr.evil.test/a'))
        self.assertFalse(m.official('http://sc.scourt.go.kr/a'))
    def test_unknown_encoding_fails(self):
        with self.assertRaises(ValueError): m.decode(b'\xff\xff', None)
    def test_robots_path_is_anchored_and_product_group(self):
        p = m.robots_parser('User-agent: AhrefsBot\nDisallow: /\n\nUser-agent: SemrushBot\nDisallow: /\n\nUser-agent: *\nDisallow: /criterion/\n')
        self.assertTrue(p.can_fetch(m.PRODUCT_TOKEN, 'https://sc.scourt.go.kr/sc/krsc/criterion/past/sex_2011/sex_2011_01.jsp'))
        self.assertFalse(p.can_fetch(m.PRODUCT_TOKEN, 'https://sc.scourt.go.kr/criterion/past/x'))
        self.assertFalse(p.can_fetch('AhrefsBot', '/sc/krsc/criterion/past/x'))
    def test_robots_longest_and_equal_allow(self):
        p = m.robots_parser('User-agent: *\nDisallow: /a\nAllow: /a/b\nDisallow: /a/b/c\nAllow: /a/b/c\n')
        self.assertFalse(p.can_fetch(m.PRODUCT_TOKEN, '/a/z'))
        self.assertTrue(p.can_fetch(m.PRODUCT_TOKEN, '/a/b/c'))
    def test_redirect_is_not_followed(self):
        with self.assertRaises(m.urllib.error.HTTPError) as caught:
            m.NoRedirect().redirect_request(m.urllib.request.Request('https://sc.scourt.go.kr/sc/example'), None, 302, 'redirect', {}, 'https://sc.scourt.go.kr/criterion/x')
        self.assertEqual(caught.exception.code, 302)

if __name__ == '__main__': unittest.main()
