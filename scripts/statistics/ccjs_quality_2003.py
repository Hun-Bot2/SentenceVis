#!/usr/bin/env python3
"""Bounded consistency check for the 2003 appeal aggregate snapshot; not legal validation."""
import json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'data/raw/ccjs_statistics'
x=json.loads((ROOT/'probe_20261116/appeal_aggregate_2003_catalog_data.json').read_text())
rows=x['rows']; grid=x['data']; cols=x['cols']
if len(rows)!=19 or len(cols)!=12 or '원심판결인원계' not in rows[0]['path'] or '불변경' not in rows[1]['path'] or '변경 소계' not in rows[2]['path']:
 print('unexpected layout; no arithmetic inference');sys.exit(1)
checks=[]
for ci,col in enumerate(cols):
 vals=[row[ci].get('value') for row in grid]
 if any(v is None for v in vals):checks.append({'col':col['path'],'status':'missing'});continue
 checks.append({'col':col['path'],'total_equals_unchanged_plus_changed':vals[0]==vals[1]+vals[2], 'changed_equals_breakdown':vals[2]==sum(vals[3:])})
dest=ROOT/'runs/T184253023609419-2003'; db=dest/'checkpoint.sqlite3'
with sqlite3.connect(db) as con:statuses=dict(con.execute('select status,count(*) from jobs group by status').fetchall())
q={'table':x['statblId'],'year':2003,'rows':19,'cols':12,'cells':228,'job_status':statuses,'matched_cells':sum(2 for i in range(120) if i%10<9) + sum(1 for i in range(120) if i%10==9) if statuses.get('matched')==120 else None,'zeros':sum(cell.get('value')==0 for row in grid for cell in row if cell.get('value') is not None),'nulls':sum(cell.get('value') is None for row in grid for cell in row),'subtotal_checks':checks,'note':'명시적으로 구분된 소계 관계만 검사; 원본 분류 정의 및 미제공·비해당 표기는 별도 검증','unit':'인원수 (표명 기준)','version_comparability':'unverified'}
(dest/'quality_checks.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf8'); print('matched jobs',statuses.get('matched',0),'of 120; subtotal columns',sum(c.get('total_equals_unchanged_plus_changed') and c.get('changed_equals_breakdown') for c in checks),'of',len(checks),'zero',q['zeros'],'null',q['nulls'])
