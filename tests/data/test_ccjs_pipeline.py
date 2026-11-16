import importlib.util,sys,pathlib,unittest,json
p=pathlib.Path(__file__).resolve().parents[2]/'scripts/statistics'
sys.path.insert(0,str(p));spec=importlib.util.spec_from_file_location('ccjs_pipeline',p/'ccjs_pipeline.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PipelineTests(unittest.TestCase):
 def setUp(self):self.s={'statblId':'T184253023609419','rows':[{'path':'2003@a'},{'path':'2003@b'},{'path':'2003@c'}],'cols':[{'path':'x'}],'data':[[{'value':0}],[{'value':None}],[{'value':3}]]}
 def test_plan_groups_two(self):
  j=m.plan(self.s,2003);self.assertEqual(len(j),2);self.assertEqual(j[0]['rows'],['a','b'])
 def test_validate_null_and_zero(self):
  j=m.plan(self.s,2003)[0];r={'response':{'header':{'resultCode':'00','totalCount':2},'body':{'items':{'item':[{'row':'a','col':'x','value':0},{'row':'b','col':'x','value':None}]}}}}
  self.assertEqual(m.validate(json.dumps(r).encode(),j,self.s),'matched');r['response']['body']['items']['item'][1]['value']=0
  self.assertEqual(m.validate(json.dumps(r).encode(),j,self.s),'value_mismatch')
 def test_bad_year_and_duplicate(self):
  with self.assertRaises(ValueError):m.plan(self.s,2004)
  self.s['rows'][1]['path']='2003@a'
  with self.assertRaises(ValueError):m.plan(self.s,2003)
