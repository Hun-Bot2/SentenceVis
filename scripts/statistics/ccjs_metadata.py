#!/usr/bin/env python3
"""Save one official CCJS catalogue metadata and one year grid snapshot; no key required."""
import argparse, datetime as dt, hashlib, json, os, time, urllib.request
from pathlib import Path
from ccjs_fetch import NoRedirect
from ccjs_pipeline import ALLOWED, plan, BASE

def main():
 a=argparse.ArgumentParser(); a.add_argument('--table',required=True,choices=sorted(ALLOWED)); a.add_argument('--year',required=True,type=int,choices=range(2003,2012)); q=a.parse_args()
 proof=BASE/'runs/T184253023609419-2003/quality.json'
 if not proof.exists() or json.loads(proof.read_text()).get('complete_and_matched') is not True: a.error('2003년 집계표 전수 검증 후에만 실행')
 base='https://api2.kicj.re.kr/api/v1/statistics/'+q.table
 urls=[base+'/metadata',base+'/data?fromYear='+str(q.year)+'&toYear='+str(q.year)]
 opener=urllib.request.build_opener(NoRedirect); values=[]
 for url in urls:
  with opener.open(urllib.request.Request(url,headers={'User-Agent':'SentenScope-CCJS/1.0'}),timeout=30) as r: data=r.read(10_000_001)
  if len(data)>10_000_000: raise ValueError('response too large')
  values.append((data,dt.datetime.now(dt.timezone.utc).isoformat()));time.sleep(2)
 metadata=json.loads(values[0][0]); grid=json.loads(values[1][0]);
 if q.year not in metadata.get('availableYears',[]):raise ValueError('year unavailable')
 jobs=plan(grid,q.year)
 out=BASE/'metadata_snapshots';out.mkdir(parents=True,exist_ok=True)
 records=[]
 for (data,when),url in zip(values,urls):
  sha=hashlib.sha256(data).hexdigest();p=out/(sha+'.json')
  if not p.exists():
   fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'wb') as f:f.write(data)
  records.append({'url':url,'sha256':sha,'retrieved_at_utc':when,'file':p.name})
 with (out/'manifest.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(records,ensure_ascii=False)+'\n')
 print('snapshot',records[1]['file'],'rows',len(grid['rows']),'cols',len(grid['cols']),'gateway_requests',len(jobs))
if __name__=='__main__': main()
