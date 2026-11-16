import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[2]/'scripts/statistics/import_ccjs_csv.py'
s=importlib.util.spec_from_file_location('ccjs_csv',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CsvTests(unittest.TestCase):
 def test_numeric_preserves_zero_and_missing(self):
  self.assertEqual(m.numeric('0'),('0','numeric'))
  self.assertEqual(m.numeric(''),(None,'empty'))
  self.assertEqual(m.numeric('-'),(None,'non_numeric'))
  self.assertEqual(m.numeric('NaN'),(None,'non_numeric'))
 def test_numeric_precision(self):
  self.assertEqual(m.numeric('2.0000000001'),('2.0000000001','numeric'))
if __name__=='__main__':unittest.main()
