import csv,importlib.util,json,pathlib,sys,tempfile,unittest
P=pathlib.Path(__file__).resolve().parents[2]/'scripts/catalog';sys.path.insert(0,str(P))
import inventory
class InventoryTests(unittest.TestCase):
 def test_stable_hash_duplicates_and_symlink_not_followed(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'a.txt').write_text('same');(root/'b.txt').write_text('same');(root/'link').symlink_to(root/'a.txt')
   rows=inventory.scan(root);d={x['path']:x for x in rows}
   self.assertEqual(d['a.txt']['sha256'],d['b.txt']['sha256']);self.assertEqual(d['link']['status'],'non_regular_skipped')
 def test_catalog_excluded(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'catalog').mkdir();(p/'catalog'/'x').write_text('x');self.assertEqual(inventory.scan(p),[])
if __name__=='__main__':unittest.main()
