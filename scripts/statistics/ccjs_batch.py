#!/usr/bin/env python3
"""Collect explicit table-years via official metadata and authenticated gateway; AI-assisted."""
import datetime as dt, hashlib, json, os, sqlite3, sys, time, urllib.parse, urllib.request, urllib.error
from decimal import Decimal
from pathlib import Path
from ccjs_fetch import DEFAULT, NoRedirect, load_env_key, normalize_key
from ccjs_pipeline import plan, BASE

TABLES=['T184253023609419','T184523023697992','T187793023556423']
YEARS=range(2003,2012)
RUN=BASE/'batch_2003_2011'

def fetch(url):
 try:
  with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'SentenScope-CCJS/1.0'}),timeout=30) as r:
   b=r.read(10_000_001)
  if len(b)>10_000_000:return None,'too_large'
  return b,None
 except urllib.error.HTTPError as e:return None,'http_'+str(e.code)
 except (urllib.error.URLError,TimeoutError):return None,'network_error'

def save(b):
 sha=hashlib.sha256(b).hexdigest(); p=RUN/(sha+'.json')
 if not p.exists():
  fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'wb') as f:f.write(b)
 return sha

def now():return dt.datetime.now(dt.timezone.utc).isoformat()

def main():
 RUN.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(RUN/'checkpoint.sqlite3'); db.execute('create table if not exists jobs (table_id text,year integer,metadata_sha text,grid_sha text,gateway_sha text,status text,recorded_at text,primary key(table_id,year))'); db.execute('create table if not exists calls (day text,table_id text,year integer)');db.commit()
 key=normalize_key(load_env_key(Path(__file__).resolve().parents[2]/'.env')); count=0
 for table in TABLES:
  meta_url='https://api2.kicj.re.kr/api/v1/statistics/'+table+'/metadata'; mb,err=fetch(meta_url)
  if err:print('metadata error',table,err);return 1
  m=json.loads(mb);msha=save(mb);time.sleep(2)
  for year in YEARS:
   if db.execute('select status from jobs where table_id=? and year=?',(table,year)).fetchone()==('matched',):continue
   if year not in m.get('availableYears',[]):
    db.execute('insert or replace into jobs values(?,?,?,?,?,?,?)',(table,year,msha,None,None,'year_unavailable',now()));db.commit();continue
   grid_url='https://api2.kicj.re.kr/api/v1/statistics/'+table+'/data?fromYear='+str(year)+'&toYear='+str(year)
   b,err=fetch(grid_url)
   if err:print('grid error',table,year,err);return 1
   g=json.loads(b,parse_float=Decimal);gsha=save(b)
   try: plan(g,year)
   except ValueError:
    db.execute('insert or replace into jobs values(?,?,?,?,?,?,?)',(table,year,msha,gsha,None,'unsafe_or_invalid_axes',now()));db.commit()
    print('axis delimiter conflict or invalid structure',table,year,flush=True);return 1
   time.sleep(2)
   rows=[r['path'].split('@',1)[1] for r in g['rows']];cols=[c['path'] for c in g['cols']]
   query=urllib.parse.urlencode({'serviceKey':key,'table':table,'year':str(year),'row':','.join(rows),'col':','.join(cols)})
   if len(query)>12000:print('query too long, split required',table,year);return 1
   # At most 27 gateway calls in this run; counts used by other clients remain unknown.
   day=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
   if count>=27 or db.execute('select count(*) from calls where day=?',(day,)).fetchone()[0]>=150:print('local gateway limit reached');return 1
   db.execute('insert into calls values (?,?,?)',(day,table,year));db.commit()
   count+=1; response,err=fetch(DEFAULT+'?'+query)
   if err:print('gateway error',table,year,err);return 1
   if key.encode() in response or urllib.parse.quote(key,safe='').encode() in response:print('credential in response');return 1
   sha=save(response)
   try:
    obj=json.loads(response,parse_float=Decimal)['response'];h=obj['header'];items=obj['body']['items']['item']; found={(v['row'],v['col']):v.get('value') for v in items}; expected={(rows[i],cols[j]):g['data'][i][j].get('value') for i in range(len(rows)) for j in range(len(cols))}
    ok=str(h['resultCode'])=='00' and len(items)==len(found)==len(expected) and h.get('totalCount')==len(expected) and all('value' in v for v in items) and all('value' in v for row in g['data'] for v in row) and found==expected
    if table==TABLES[0] and year==2003:
     ok=ok and len(rows)==19 and len(cols)==12 and all(g['data'][0][j]['value']==g['data'][1][j]['value']+g['data'][2][j]['value'] and g['data'][2][j]['value']==sum(g['data'][i][j]['value'] for i in range(3,19)) for j in range(12))
   except (ValueError,KeyError,TypeError):ok=False
   status='matched' if ok else 'mismatch_or_incomplete';db.execute('insert or replace into jobs values(?,?,?,?,?,?,?)',(table,year,msha,gsha,sha,status,now()));db.commit()
   print(table,year,status,'rows',len(rows),'cols',len(cols),'cells',len(rows)*len(cols),flush=True)
   if not ok:return 1
   time.sleep(2)
 return 0
if __name__=='__main__':sys.exit(main())
