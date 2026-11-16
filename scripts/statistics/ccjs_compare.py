#!/usr/bin/env python3
"""Small official gateway comparison, no secrets printed; AI-assisted."""
import json, time, urllib.parse, urllib.request, urllib.error, sys
from pathlib import Path
from decimal import Decimal
from ccjs_fetch import DEFAULT, NoRedirect, load_env_key, normalize_key

ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/'data/raw/ccjs_statistics/probe_20261116/appeal_aggregate_2003_catalog_data.json'
OUT=ROOT/'data/raw/ccjs_statistics/comparison_2003.json'

def call(key, rows, cols):
    p={'serviceKey':key,'table':'T184253023609419','year':'2003','row':','.join(rows),'col':','.join(cols)}
    url=DEFAULT+'?'+urllib.parse.urlencode(p)
    try:
        with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url,headers={'Accept':'application/json'}),timeout=25) as r: data=r.read(2000001)
        if len(data)>2000000: return {'error':'response_too_large'}
        obj=json.loads(data,parse_float=Decimal); result=obj.get('response',{}); h=result.get('header',{}); b=result.get('body',{}); items=b.get('items',{}).get('item',[])
        return {'code':str(h.get('resultCode','unknown')),'count':h.get('totalCount'),'items':items if isinstance(items,list) else []}
    except (urllib.error.URLError,TimeoutError,ValueError,TypeError,KeyError): return {'error':'request_or_parse_failed'}

def main():
    x=json.loads(FILE.read_text(),parse_float=Decimal); key=normalize_key(load_env_key(ROOT/'.env'))
    pairs=[(0,0),(1,3),(4,5),(8,9),(13,2),(18,11)]; results=[]
    for ri,ci in pairs:
        row=x['rows'][ri]['path'].split('@',1)[1]; col=x['cols'][ci]['path']; expect=x['data'][ri][ci]['value']; r=call(key,[row],[col]); items=r.pop('items',[])
        match=len(items)==1 and items[0].get('row')==row and items[0].get('col')==col and items[0].get('value')==expect
        results.append({'row_index':ri,'col_index':ci,'code':r.get('code'),'count':r.get('count'),'matches':match,'error':r.get('error')})
        print('cell',ri,ci,'match',match,'code',r.get('code'),flush=True)
        if r.get('code')!='00':break
        time.sleep(2)
    if len(results)==len(pairs) and all(y['matches'] for y in results):
        rows=[x['rows'][i]['path'].split('@',1)[1] for i in (0,1)]; col=x['cols'][0]['path']; r=call(key,rows,[col]); items=r.pop('items',[])
        r['returned_coordinates']=[{'row':i.get('row'),'col':i.get('col')} for i in items]
        r['matches_expected'] = len(items)==2 and all(any(i.get('row')==rows[j] and i.get('col')==col and i.get('value')==x['data'][j][0]['value'] for i in items) for j in range(2))
    else:r={'status':'skipped'}
    out={'table':'T184253023609419','year':2003,'sample':results,'batch_two_rows':r,'full_table_complete':False}
    if OUT.exists(): print('기존 비교 보고서가 있어 덮어쓰지 않습니다.');return 1
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); print('batch:',json.dumps(r,ensure_ascii=False));return 0
if __name__=='__main__':sys.exit(main())
