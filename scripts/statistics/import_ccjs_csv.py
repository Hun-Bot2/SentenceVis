#!/usr/bin/env python3
"""Import user-supplied CCJS CSV without network or credentials; AI-assisted."""
import argparse,collections,csv,datetime,decimal,hashlib,json,os,shutil,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/originals/ccjs';PROCESSED=ROOT/'data/processed/ccjs_offense'; TABLE='T187793023556423'
FIELDS=['년도','분류1','분류2','분류3','항목1','항목2','항목3','항목4','항목5','원자료']

def hash_file(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def numeric(s):
 if s=='':return None,'empty'
 try:
  d=decimal.Decimal(s)
  if not d.is_finite():return None,'non_numeric'
  return str(d),'numeric'
 except decimal.InvalidOperation:return None,'non_numeric'

def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();source=a.source.resolve(); digest=hash_file(source)
 RAW.mkdir(parents=True,exist_ok=True);PROCESSED.mkdir(parents=True,exist_ok=True);raw=RAW/(digest+'.csv')
 if not raw.exists():
  fd,tmp=tempfile.mkstemp(dir=RAW,prefix='.import-')
  try:
   with os.fdopen(fd,'wb') as f,source.open('rb') as inp:shutil.copyfileobj(inp,f,1024*1024)
   if hash_file(Path(tmp))!=digest:raise ValueError('source changed during copy')
   os.link(tmp,raw)
  finally:os.unlink(tmp)
 elif hash_file(raw)!=digest:raise ValueError('existing raw hash mismatch')
 out=PROCESSED/(digest+'.jsonl');report=PROCESSED/(digest+'.quality.json')
 if out.exists() or report.exists():raise FileExistsError('output exists; not overwritten')
 gridpath=ROOT/'data/raw/ccjs_statistics/batch_2003_2011/quality_report.json'
 prior=json.loads(gridpath.read_text()); entry=next((x for x in prior['items'] if x['table']==TABLE and x['year']==2003 and x['grid_sha256']),None)
 baseline={}
 if entry:
  gp=gridpath.parent/(entry['grid_sha256']+'.json'); rawgrid=gp.read_bytes()
  if hashlib.sha256(rawgrid).hexdigest()!=entry['grid_sha256']:raise ValueError('reference hash mismatch')
  g=json.loads(rawgrid,parse_float=decimal.Decimal)
  baseline={(r['path'].split('@',1)[1],c['path']):g['data'][i][j].get('value') for i,r in enumerate(g['rows']) for j,c in enumerate(g['cols'])}
 years=collections.Counter();statuses=collections.Counter();keys=set();duplicate=0;cmp=collections.Counter();line=0
 fd,tmp=tempfile.mkstemp(dir=PROCESSED,prefix='.normalize-');os.close(fd)
 try:
  with raw.open(encoding='utf-8-sig',newline='') as src,open(tmp,'w',encoding='utf8') as dst:
   reader=csv.DictReader(src)
   if not reader.fieldnames or any(k not in reader.fieldnames for k in FIELDS):raise ValueError('required CSV headers missing')
   for line,row in enumerate(reader,2):
    if None in row:raise ValueError('malformed CSV record')
    year=row['년도']; r='@'.join(row['분류'+str(i)] for i in range(1,4));c='@'.join(row['항목'+str(i)] for i in range(1,6));value,status=numeric(row['원자료']); key=(year,r,c);duplicate+=key in keys;keys.add(key);years[year]+=1;statuses[status]+=1
    if year=='2003' and baseline:
     ref=baseline.get((r,c),'missing_coordinate')
     cmp['missing_coordinate' if ref=='missing_coordinate' else 'matched' if status=='numeric' and decimal.Decimal(value)==ref else 'different_or_missing']+=1
    record={'source_id':'sha256:'+digest,'source_path':str(raw.relative_to(ROOT)),'source_hash':digest,'source_origin':'user_provided_ccjs_export','source_url':None,'document_date':None,'page_or_section':'csv_record:'+str(line),'extraction_method':'csv_utf8_sig','validation_status':'user_supplied_unverified','table_id':TABLE,'table_identity_basis':'user_download_name_and_reported_context_unverified','year':int(year) if year.isdigit() else None,'row_path':r,'column_path':c,'value_decimal':value,'value_raw':row['원자료'],'value_status':status,'unit':'인원수 (표명 기준; 원전 검증 필요)','source_fields':row,'comparability':'unverified','case_application':'not_established'}
    dst.write(json.dumps(record,ensure_ascii=False)+'\n')
  os.link(tmp,out)
 finally:os.unlink(tmp)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();result={'source_original_filename':source.name,'source_file':str(raw.relative_to(ROOT)),'source_sha256':digest,'source_bytes':raw.stat().st_size,'imported_at_utc':now,'table_id_candidate':TABLE,'records':sum(years.values()),'years':dict(sorted(years.items())),'value_status':dict(statuses),'duplicate_coordinate_rows':duplicate,'comparison_2003':dict(cmp),'reference_coordinate_count':len(baseline),'output_file':str(out.relative_to(ROOT)),'output_sha256':hash_file(out),'limitations':['CSV provenance and table identity user-reported, not independently verified','grid comparison same-provider, not independent source','null and absent meaning unknown','do not add subtotal and detailed rows']}
 with report.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k not in ('years','limitations')},ensure_ascii=False))
if __name__=='__main__':main()
