#!/usr/bin/env python3
"""Private source-linked candidate inventory; does not assert legal identity or meaning.
AI assistance: OpenAI Codex. Reads original ZIP members without extracting paths.
"""
import collections,datetime,hashlib,importlib.util,json,re,sqlite3,sys,zipfile
from pathlib import Path
_spec=importlib.util.spec_from_file_location('sentenscope_source_inventory',Path(__file__).with_name('inventory.py'))
_inventory=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_inventory)
digest_file,read_member,nfc=_inventory.digest_file,_inventory.read_member,_inventory.nfc

ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'data';CAT=DATA/'private/inventory/2026-11-13-v4/catalog.sqlite'
OUT=DATA/'private/readiness'
CASE=re.compile(r'(?<!\d)(?:19|20)\d{2}\s*(?:고합|고단|고정|노|노합|노단)\s*\d+')
PRISON=re.compile(r'징\s*역\s*(?:[0-9]+|[일이삼사오육칠팔구십백]+)\s*(?:년|월)')
def compact(s):return re.sub(r'\s+','',nfc(str(s or '')))
def title_kind(title):
 t=compact(title)
 if t in ('주문','주문및이유'):return 'order'
 if '원심판결' in t or t in ('제1심판결','제일심판결'):return 'prior_judgment'
 if t in ('피고인','피고인들'):return 'defendant_heading'
 if '항소이유' in t:return 'appeal_ground_heading'
 if t in ('이유','판단','항소이유에대한판단') or '판단' in t:return 'reasoning_heading'
 return None

def main():
 OUT.mkdir(parents=True,exist_ok=True);ts=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');path=OUT/('readiness-'+ts);path.mkdir(mode=0o700)
 con=sqlite3.connect('file:'+str(CAT)+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
 rows=con.execute("""select d.*,a.relative_path,a.sha256 as archive_sha from documents d join archives a using(archive_id) where a.role='label' and a.subset='general' and d.category in ('형사','형사A','형사B') order by a.relative_path,d.member_index""").fetchall()
 pool=collections.defaultdict(list)
 for r in rows:
  if r['case_no']:pool[compact(r['case_no'])].append(r)
 stats=collections.Counter();errors=[];edges=[];names={};docs=[]
 for r in rows:
  arc=DATA/r['relative_path']
  try:
   if r['relative_path'] not in names:
    if digest_file(arc)!=r['archive_sha']:raise ValueError('archive_hash_changed')
    names[r['relative_path']]=zipfile.ZipFile(arc)
   archive=names[r['relative_path']];info=archive.infolist()[r['member_index']]
   if info.filename!=r['member_path']:raise ValueError('member_locator_changed')
   raw=read_member(archive,info)
   if hashlib.sha256(raw).hexdigest()!=r['member_sha256']:raise ValueError('member_hash_changed')
   obj=json.loads(raw);sections=obj.get('sections',[])
   if not isinstance(sections,list):raise ValueError('sections_not_array')
   year=compact(r['decision_date'])[:4]; in_window=year.isdigit() and 2002<=int(year)<=2011
   if not in_window:continue
   evidence=collections.defaultdict(list);prison=[];prior=[]
   for idx,section in enumerate(sections):
    if not isinstance(section,dict):continue
    t=section.get('text');kind=title_kind(section.get('title'))
    if not kind or not isinstance(t,str):continue
    locator={'section_ordinal':idx,'section_id':section.get('section_id'),'section_title':section.get('title'),'text_sha256':hashlib.sha256(t.encode()).hexdigest()}
    evidence[kind].append(locator)
    if kind=='order':
     for m in PRISON.finditer(t):prison.append({'text':m.group(),'start_codepoint':m.start(),'end_codepoint_exclusive':m.end(),'locator':locator,'status':'unverified_not_assigned_to_defendant'})
    if kind=='prior_judgment':
     for m in CASE.finditer(t):prior.append({'case_no':compact(m.group()),'locator':locator,'start_codepoint':m.start(),'end_codepoint_exclusive':m.end()})
   case=compact(r['case_no']); appellate=bool(re.fullmatch(r'(?:19|20)\d{2}노(?:합|단)?\d+',case))
   item={'source_id':r['source_id'],'source_path':r['relative_path'],'archive_sha256':r['archive_sha'],'member_index':r['member_index'],'member_path':r['member_path'],'member_sha256':r['member_sha256'],'case_no':r['case_no'],'court':r['court'],'decision_date':r['decision_date'],'court_level_candidate':'appeal_case_number_pattern' if appellate else 'unknown','court_level_status':'unverified','defendants':None,'defendant_alignment':'unverified','sentences':None,'suspension':None,'appeal_grounds':None,'court_dispositions':None,'reasoning_relations':None,'evidence':dict(evidence),'prison_mentions':prison,'prior_references':prior,'verification_status':'unverified','source_basis':'label_sections_not_legal_gold'}
   docs.append(item);stats['documents']+=1
   for f in ('case_no','court','decision_date'):
    if not r[f]:stats['missing_'+f]+=1
   if appellate:stats['appeal_pattern']+=1
   for k in ['order','prior_judgment','defendant_heading','appeal_ground_heading','reasoning_heading']:
    if evidence[k]:stats[k+'_present']+=1
   if prison:stats['prison_mention_documents']+=1
   if appellate:
    for ref in prior:
     matches=pool.get(ref['case_no'],[])
     for target in matches:
      if target['source_id']==r['source_id']:continue
      edges.append({'appeal_source_id':r['source_id'],'prior_source_id':target['source_id'],'prior_case_reference':ref,'basis':'case_number_exact_only','court_match':'unverified','offense_match':'unverified','case_link_status':'candidate_unverified','defendant_alignment_status':'unverified'})
  except Exception as e:errors.append({'source_id':r['source_id'],'error_type':type(e).__name__,'error':str(e)})
 for z in names.values():z.close()
 for name,values in [('documents.jsonl',docs),('case_link_candidates.jsonl',edges),('errors.jsonl',errors)]:
  with (path/name).open('x',encoding='utf8') as f:
   for v in values:f.write(json.dumps(v,ensure_ascii=False)+'\n')
 stats=dict(stats);stats.update({'source_population_label_general_criminal':len(rows),'error_count':len(errors),'case_link_candidate_edges':len(edges),'unique_candidate_appeals':len({x['appeal_source_id'] for x in edges}),'prior_case_list_187_and_94':'not_found','verified_case_links':0,'verified_defendant_alignments':0,'verified_reasoning_relations':0})
 (path/'summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'output':str(path.relative_to(ROOT)),**stats},ensure_ascii=False))
if __name__=='__main__':sys.exit(main())
