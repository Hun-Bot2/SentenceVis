#!/usr/bin/env python3
"""Plan and checkpoint bounded CCJS gateway collection from local official table snapshots.
No catalogue crawling. AI assistance: OpenAI Codex.
"""
import argparse, datetime as dt, hashlib, json, os, sqlite3, sys, time, urllib.parse, urllib.request, urllib.error
from decimal import Decimal
from pathlib import Path
from ccjs_fetch import DEFAULT, NoRedirect, load_env_key, normalize_key

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/raw/ccjs_statistics'
ALLOWED={'T184523023697992','T187793023556423','T184253023609419'}

def plan(snapshot, year):
    rows=snapshot['rows']; cols=snapshot['cols']; grid=snapshot['data']
    if str(snapshot['statblId']) not in ALLOWED or len(grid)!=len(rows) or any(len(r)!=len(cols) for r in grid): raise ValueError('invalid grid or table')
    rpaths=[r['path'] for r in rows]; cpaths=[c['path'] for c in cols]
    prefix=str(year)+'@'
    if any(not p.startswith(prefix) or ',' in p for p in rpaths) or any(',' in p for p in cpaths): raise ValueError('invalid row year or delimiter')
    if len(set(rpaths))!=len(rpaths) or len(set(cpaths))!=len(cpaths): raise ValueError('duplicate axes')
    jobs=[]
    for ci,col in enumerate(cpaths):
        for i in range(0,len(rows),2):
            jobs.append({'table':snapshot['statblId'],'year':year,'rows':[p[len(prefix):] for p in rpaths[i:i+2]],'col':col,'cells':[[j,ci] for j in range(i,min(i+2,len(rows)))]})
    return jobs

def request(key,job):
    query={'serviceKey':key,'table':job['table'],'year':str(job['year']),'row':','.join(job['rows']),'col':job['col']}
    req=urllib.request.Request(DEFAULT+'?'+urllib.parse.urlencode(query),headers={'Accept':'application/json','User-Agent':'SentenScope-CCJS/1.0'})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=30) as r: raw=r.read(5_000_001)
        if len(raw)>5_000_000: return None,'response_too_large'
        if key.encode() in raw or urllib.parse.quote(key,safe='').encode() in raw: return None,'credential_in_response'
        return raw,None
    except urllib.error.HTTPError as e: return None,'http_'+str(e.code)
    except (urllib.error.URLError,TimeoutError): return None,'network_error'

def validate(raw,job,snapshot):
    try:
        obj=json.loads(raw,parse_float=Decimal); response=obj['response']; header=response['header']; body=response['body']; items=body['items']['item']
        if str(header['resultCode'])!='00' or not isinstance(items,list): return 'api_error'
        found={}
        for v in items:
            k=(v['row'],v['col'])
            if k in found: return 'duplicate_item'
            found[k]=v.get('value')
        expected={(r,job['col']) for r in job['rows']}
        if set(found)!=expected or header.get('totalCount')!=len(expected): return 'incomplete_response'
        for row,(ri,ci) in zip(job['rows'],job['cells']):
            if found[(row,job['col'])]!=snapshot['data'][ri][ci].get('value'): return 'value_mismatch'
        return 'matched'
    except (KeyError,TypeError,ValueError):return 'parse_error'

def main():
    a=argparse.ArgumentParser();a.add_argument('--snapshot',type=Path,required=True);a.add_argument('--year',type=int,required=True);a.add_argument('--execute',action='store_true');a.add_argument('--max-calls',type=int,default=150);a.add_argument('--delay',type=float,default=2.0);args=a.parse_args()
    if args.year not in range(2003,2012) or not 1<=args.max_calls<=10000 or args.delay<2: a.error('invalid year, call limit, or delay')
    raw=args.snapshot.read_bytes(); snap=json.loads(raw,parse_float=Decimal); jobs=plan(snap,args.year); digest=hashlib.sha256(raw).hexdigest()
    print('table',snap['statblId'],'year',args.year,'rows',len(snap['rows']),'cols',len(snap['cols']),'cells',len(snap['rows'])*len(snap['cols']),'calls',len(jobs),'snapshot_sha256',digest,flush=True)
    if not args.execute:return 0
    # Other clients may share quota; use a conservative configured local budget.
    if (snap['statblId'],args.year)!=('T184253023609419',2003):
        proof=BASE/'runs/T184253023609419-2003/quality.json'
        if not proof.exists() or json.loads(proof.read_text()).get('complete_and_matched') is not True: raise ValueError('2003 aggregate verification required before expansion')
    key=normalize_key(load_env_key(ROOT/'.env')); dest=BASE/'runs'/f"{snap['statblId']}-{args.year}"; dest.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(dest/'checkpoint.sqlite3');db.execute('create table if not exists jobs (id integer primary key, snapshot text, status text, sha256 text, recorded_at text)');db.execute('create table if not exists calls (day text, id integer)'); db.commit()
    current=db.execute('select distinct snapshot from jobs').fetchall()
    if current and any(v[0]!=digest for v in current): raise ValueError('snapshot changed; manual review required')
    for ix,job in enumerate(jobs):
        status=db.execute('select status from jobs where id=?',(ix,)).fetchone()
        if status and status[0]=='matched': continue
        day=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
        # Count this tool's calls across all table/year checkpoint databases.
        used=0
        for checkpoint in (BASE/'runs').glob('*/checkpoint.sqlite3'):
            with sqlite3.connect(checkpoint) as quota_db:
                used += quota_db.execute('select count(*) from calls where day=?',(day,)).fetchone()[0]
        if used>=args.max_calls:print('local daily limit reached');break
        db.execute('insert into calls values (?,?)',(day,ix));db.commit()
        response,error=request(key,job); now=dt.datetime.now(dt.timezone.utc).isoformat(); sha=None
        if response is not None:
            sha=hashlib.sha256(response).hexdigest(); file=dest/(sha+'.json')
            if not file.exists():
                fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as f:f.write(response)
            status=validate(response,job,snap)
        else:status=error
        db.execute('insert or replace into jobs values (?,?,?,?,?)',(ix,digest,status,sha,now));db.commit()
        print('job',ix+1,'/',len(jobs),status,flush=True)
        if status!='matched':break
        time.sleep(args.delay)
    entries=db.execute('select status,count(*) from jobs group by status').fetchall(); count=dict(entries); done=count.get('matched',0)
    quality={'table':snap['statblId'],'year':args.year,'source_snapshot_sha256':digest,'rows':len(snap['rows']),'cols':len(snap['cols']),'planned_cells':len(snap['rows'])*len(snap['cols']),'planned_requests':len(jobs),'job_status':count,'complete_and_matched':done==len(jobs),'aggregation_check':'not_performed','hierarchy_change':'not_compared','null_semantics':'unverified','unit':'people per table name; verify source definitions','notes':'A local quota cannot detect use by other clients. No automatic retry; review any failure.'}
    (dest/'quality.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if quality['complete_and_matched'] else 1
if __name__=='__main__': sys.exit(main())
