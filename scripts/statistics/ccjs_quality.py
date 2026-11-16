#!/usr/bin/env python3
"""Summarize collected CCJS response completeness and structural changes."""
import json,sqlite3
from pathlib import Path
from ccjs_pipeline import BASE
RUN=BASE/'batch_2003_2011'

def main():
 with sqlite3.connect(RUN/'checkpoint.sqlite3') as db: jobs=db.execute('select table_id,year,metadata_sha,grid_sha,gateway_sha,status,recorded_at from jobs order by table_id,year').fetchall();calls=db.execute('select count(*) from calls').fetchone()[0]
 result=[]; previous={}
 for table,year,meta,grid,gate,status,timestamp in jobs:
  item={'table':table,'year':year,'status':status,'recorded_at_utc':timestamp,'metadata_sha256':meta,'grid_sha256':grid,'gateway_sha256':gate,'source':'https://apis.data.go.kr/B554626/ccjs/getstatistics','metadata_url':'https://api2.kicj.re.kr/api/v1/statistics/'+table+'/metadata','grid_url':'https://api2.kicj.re.kr/api/v1/statistics/'+table+'/data?fromYear='+str(year)+'&toYear='+str(year),'unit':'인원수 (표명 기준); 원전 정의 검토 필요','null_semantics':'unknown','case_application':'not_established'}
  if grid:
   x=json.loads((RUN/(grid+'.json')).read_text());rows=[r['path'].split('@',1)[1] for r in x['rows']];cols=[c['path'] for c in x['cols']];cells=[v for r in x['data'] for v in r]; vals=[v.get('value') for v in cells if 'value' in v]
   axis=(rows,cols);item.update({'rows':len(rows),'cols':len(cols),'cells':len(cells),'zero':sum(v==0 for v in vals if v is not None),'null':sum(v is None for v in vals),'value_key_absent':len(cells)-len(vals),'hierarchy_changed_from_previous_available_year':None if table not in previous else previous[table]!=axis});previous[table]=axis
   if gate:
    response=json.loads((RUN/(gate+'.json')).read_text())
    try:
     points=response['response']['body']['items']['item'];item['gateway_value_key_absent']=sum('value' not in point for point in points)
    except (KeyError,TypeError):item['gateway_value_key_absent']='unverified'
   if table=='T184253023609419' and year==2003 and len(rows)==19 and len(cols)==12:
    z=x['data'];item['subtotal_checks_passed']=sum(z[0][j]['value']==z[1][j]['value']+z[2][j]['value'] and z[2][j]['value']==sum(z[i][j]['value'] for i in range(3,19)) for j in range(12));item['subtotal_checks_total']=12
  result.append(item)
 report={'generated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'expected_table_years':27,'recorded_table_years':len(jobs),'matched_table_years':sum(j[-2]=='matched' for j in jobs),'gateway_calls_this_checkpoint':calls,'items':result,'limitations':['null과 미제공 및 비해당의 원본 정의는 미확인','집계와 세부 항목을 함께 합산하지 않음','기관이나 다른 클라이언트의 사용량은 로컬 호출 수에 포함되지 않음','연도별 분류 차이의 의미 및 법률 검증은 미확인','사건 수와 인원 수는 서로 대체 불가']}
 (RUN/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('matched',report['matched_table_years'],'/',27,'gateway calls',calls)
if __name__=='__main__':main()
