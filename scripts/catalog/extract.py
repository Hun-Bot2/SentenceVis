#!/usr/bin/env python3
"""Local reversible PDF/CSV extraction; no network, no generated conclusions. AI: OpenAI Codex."""
import argparse,csv,datetime,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from inventory import DATA,sha

OUT=DATA/'interim'/'extracted'

def process(path):
 path=path.resolve();base=DATA.resolve()
 if not path.is_relative_to(base) or not path.is_file():raise ValueError('source must be a regular local data file')
 if path.is_relative_to((DATA/'interim').resolve()) or path.is_relative_to((DATA/'catalog').resolve()):raise ValueError('derivatives are not source inputs')
 digest=sha(path);size=path.stat().st_size;OUT.mkdir(parents=True,exist_ok=True);dest=OUT/(digest+'.jsonl');meta=OUT/(digest+'.metadata.json')
 if dest.exists() or meta.exists():raise FileExistsError('output already exists; do not overwrite')
 source={'source_id':'sha256:'+digest,'source_path':str(path.relative_to(base)),'source_hash':digest,'document_date':None,'validation_status':'unverified'}
 fd,tmp=tempfile.mkstemp(dir=OUT,prefix='.extract-');os.close(fd); count=0;warnings=[]
 try:
  with open(tmp,'w',encoding='utf8') as f:
   if path.suffix.lower()=='.pdf':
    proc=subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,timeout=120)
    if proc.returncode:raise ValueError('pdftotext_error')
    text=proc.stdout.decode('utf8',errors='strict')
    pages=text.split('\f');pages=pages[:-1] if pages[-1]=='' else pages
    if not any(p.strip() for p in pages):warnings.append('no_text_possible_scan')
    warnings.extend(['tables_not_extracted','headings_not_validated'])
    for i,page in enumerate(pages,1):
     record={**source,'page_or_section':str(i),'extraction_method':'pdftotext-layout','text':page}
     f.write(json.dumps(record,ensure_ascii=False)+'\n');count+=1
   elif path.suffix.lower()=='.csv':
    warnings.extend(['schema_semantics_unverified','license_unverified'])
    for enc in ('utf-8-sig','cp949'):
     try:
      with path.open(encoding=enc,newline='') as test:
       while test.read(1024*1024):pass
      break
     except UnicodeDecodeError:continue
    else:raise ValueError('unknown_csv_encoding')
    csv.field_size_limit(50_000_000)
    with path.open(encoding=enc,newline='') as src:
     reader=csv.reader(src); header=next(reader)
     if len(set(header))!=len(header):raise ValueError('duplicate_csv_columns')
     for i,row in enumerate(reader,2):
      if len(row)!=len(header):raise ValueError('csv_column_count_mismatch_line_'+str(i))
      f.write(json.dumps({**source,'page_or_section':'record:'+str(i),'extraction_method':'csv:'+enc,'fields':dict(zip(header,row))},ensure_ascii=False)+'\n');count+=1
   else:raise ValueError('unsupported_format')
  if sha(path)!=digest or path.stat().st_size!=size:raise ValueError('source_changed_during_extraction')
  os.link(tmp,dest);meta.write_text(json.dumps({**source,'records':count,'warnings':warnings,'output_sha256':sha(dest)},ensure_ascii=False,indent=2),encoding='utf8')
  return {'path':str(path.relative_to(base)),'status':'ok','records':count,'warnings':warnings}
 finally:
  if os.path.exists(tmp):os.unlink(tmp)

def main():
 a=argparse.ArgumentParser();a.add_argument('files',nargs='+',type=Path);args=a.parse_args();fail=0
 for p in args.files:
  try:r=process(p)
  except Exception as e:r={'path':str(p),'status':'error','error':str(e)};fail+=1
  log=DATA/'catalog'/'extraction_log.jsonl';log.parent.mkdir(parents=True,exist_ok=True)
  with log.open('a',encoding='utf8') as f:f.write(json.dumps({'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**r},ensure_ascii=False)+'\n')
  print(json.dumps(r,ensure_ascii=False),flush=True)
 return 1 if fail else 0
if __name__=='__main__':sys.exit(main())
