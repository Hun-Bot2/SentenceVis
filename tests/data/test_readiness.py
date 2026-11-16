import pathlib,sys,unittest
p=pathlib.Path(__file__).resolve().parents[2]/'scripts/ingest';sys.path.insert(0,str(p))
import readiness
class ReadinessTests(unittest.TestCase):
 def test_section_headings_conservative(self):
  self.assertEqual(readiness.title_kind('주    문'),'order')
  self.assertEqual(readiness.title_kind('원심판결'),'prior_judgment')
  self.assertIsNone(readiness.title_kind('법령의 적용'))
 def test_prison_mentions_are_only_candidates(self):
  self.assertIsNotNone(readiness.PRISON.search('징역 3년'))
  self.assertIsNone(readiness.PRISON.search('집행유예 3년'))
 def test_case_pattern_does_not_treat_dates_as_cases(self):
  self.assertEqual(readiness.compact(readiness.CASE.search('원심 2005 고합 52 판결').group()),'2005고합52')
  self.assertIsNone(readiness.CASE.search('2005년 5월 2일'))
if __name__=='__main__':unittest.main()
