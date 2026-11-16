#!/usr/bin/env python3
"""Normalize verified local CCJS grid snapshots without contacting network or changing originals."""
import datetime as dt,hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'data/raw/ccjs_statistics/batch_2003_2011';OUT=ROOT/'data/processed/ccjs_catalog'

def main():
 uri='file:'+str(RUN/'checkpoint.sqlite3')+'?mode=ro'
 with sqlite3.connect(uri,uri=True) as db:jobs=db.execute("select table_id,year,grid_sha,gateway_sha,status,recorded_at from jobs where status='matched' order by table_id,year").fetchall()
 name=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');OUT.mkdir(parents=True,exist_ok=True);out=OUT/('ccjs-'+name+'.jsonl'); diffs=[];previous={}; count=0
 with out.open('x',encoding='utf8') as f:
  for table,year,gridsha,gatehash,status,when in jobs:
   path=RUN/(gridsha+'.json'); raw=path.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=gridsha: raise ValueError('grid checksum mismatch')
   gateway=RUN/(gatehash+'.json')
   if hashlib.sha256(gateway.read_bytes()).hexdigest()!=gatehash: raise ValueError('gateway checksum mismatch')
   x=json.loads(raw); rows=[r['path'].split('@',1)[1] for r in x['rows']]; cols=[c['path'] for c in x['cols']]
   if len(x['data'])!=len(rows) or any(len(r)!=len(cols) for r in x['data']):raise ValueError('grid shape mismatch')
   prior=previous.get(table)
   if prior:
    diffs.append({'table':table,'from_year':prior[0],'to_year':year,'rows_added':sorted(set(rows)-set(prior[1])),'rows_removed':sorted(set(prior[1])-set(rows)),'cols_added':sorted(set(cols)-set(prior[2])),'cols_removed':sorted(set(prior[2])-set(cols)),'semantic_comparability':'unverified'})
   previous[table]=(year,rows,cols)
   for i,row in enumerate(rows):
    for j,col in enumerate(cols):
     cell=x['data'][i][j]; present='value' in cell
     o={'source_id':'sha256:'+gridsha,'source_path':str(path.relative_to(ROOT)),'source_hash':gridsha,'gateway_hash':gatehash,'source_url':'https://api2.kicj.re.kr/api/v1/statistics/'+table+'/data?fromYear='+str(year)+'&toYear='+str(year),'document_date':None,'table_id':table,'year':year,'row_path':row,'column_path':col,'value':cell.get('value'),'value_status':('value' if present and cell['value'] is not None else 'null' if present else 'missing_key'),'unit':'persons_inferred_from_title_unverified','page_or_section':f'data[{i}][{j}]','extraction_method':'ccjs_grid_snapshot','validation_status':'same_provider_gateway_matched','independent_validation':'unverified','comparability':'unverified','recorded_at_utc':when}
     f.write(json.dumps(o,ensure_ascii=False)+'\n');count+=1
 summary={'created_at':name,'rows_written':count,'table_years':len(jobs),'output':str(out.relative_to(ROOT)),'source_checkpoint':str((RUN/'checkpoint.sqlite3').relative_to(ROOT)),'axis_differences':diffs,'notes':['same provider comparison is not independent validation','never sum subtotal and detail together','no case-level link inferred']}
 report=OUT/('summary-'+name+'.json');report.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8'); print(json.dumps({'rows':count,'table_years':len(jobs),'output':str(out),'summary':str(report)},ensure_ascii=False))
if __name__=='__main__':main()
