#!/usr/bin/env python3
"""Local recursive inventory; metadata is private, originals never moved. AI: OpenAI Codex."""
import csv,datetime as dt,hashlib,json,os,stat,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data'; OUT=DATA/'catalog'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def kind(path):
 s=str(path).lower()
 if 'ccjs' in s:return 'official_statistics_candidate'
 if 'private/inventory' in s:return 'private_inventory'
 if any(x in s for x in ('판결','법률','법규','법령','aihub','ai-hub')):return 'legal_or_judgment_candidate'
 if any(x in s for x in ('뉴스','언론','news')):return 'news_context_candidate'
 if any(x in s for x in ('양형','형사정책','kicj','jpri')):return 'legal_research_candidate'
 return 'unknown'

def scan(root=DATA):
 rows=[]
 for base,dirs,files in os.walk(root,followlinks=False):
  dirs.sort();files.sort()
  for n in files:
   p=Path(base)/n;rel=p.relative_to(root).as_posix()
   if rel.startswith('catalog/'):continue
   try:
    before=p.lstat()
    if not stat.S_ISREG(before.st_mode):rows.append({'path':rel,'status':'non_regular_skipped'});continue
    digest=sha(p); after=p.stat(); stable=(before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
    rows.append({'path':rel,'format':p.suffix.lower() or 'none','size':before.st_size,'sha256':digest if stable else None,'status':'hashed' if stable else 'changed_during_scan','source_category':kind(rel),'source':'unknown','target_period':'unknown','license_access':'unknown_restricted_by_default','processing_status':'unknown','source_id':('sha256:'+digest) if stable else None})
   except OSError as e:rows.append({'path':rel,'status':'error','error_type':type(e).__name__})
 return rows

def main():
 rows=scan();OUT.mkdir(parents=True,exist_ok=True);name=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');dest=OUT/('inventory-'+name+'.jsonl')
 with dest.open('x',encoding='utf8') as f:
  for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 by=defaultdict(list)
 for row in rows:
  if row.get('sha256'):by[row['sha256']].append(row['path'])
 duplicate={k:v for k,v in by.items() if len(v)>1}
 summary={'recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'inventory':dest.name,'files':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),'formats':dict(Counter(r.get('format','unknown') for r in rows)),'duplicate_hash_groups':len(duplicate),'duplicate_copies':sum(len(v)-1 for v in duplicate.values()),'duplicates':duplicate,'different_versions':'unknown: requires document identity review','note':'catalog files excluded to avoid self-reference; metadata classifications are candidates, licenses unknown'}
 p=OUT/('quality-'+name+'.json');p.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in summary.items() if k!='duplicates'},ensure_ascii=False))
if __name__=='__main__':main()
