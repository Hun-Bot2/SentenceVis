#!/usr/bin/env python3
"""Extract SpreadsheetML XML saved as .xls without interpreting formulas. AI-assisted."""
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/interim/spreadsheet_xml';NS='{urn:schemas-microsoft-com:office:spreadsheet}'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 for path in sorted((ROOT/'data').glob('*.xls')):
  raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();dest=OUT/(digest+'.jsonl');meta=OUT/(digest+'.quality.json')
  if dest.exists() or meta.exists():print('existing',digest);continue
  try:
   text=raw.decode('euc-kr').lstrip();text=re.sub(r'^<\?xml[^?]*\?>','',text,count=1)
   repairs=text.count('< 통계표 메타자료 >');text=text.replace('< 통계표 메타자료 >','&lt; 통계표 메타자료 &gt;')
   text,amp_repairs=re.subn(r'&(?!amp;|lt;|gt;|quot;|apos;|#[0-9]+;|#x[0-9A-Fa-f]+;)', '&amp;', text)
   tree=ET.fromstring(text); sheets=tree.findall(NS+'Worksheet');row_count=0;cell_count=0
   with dest.open('x',encoding='utf8') as f:
    for sheet in sheets:
     sn=sheet.get(NS+'Name');table=sheet.find(NS+'Table')
     if table is None:continue
     logical_row=0
     for row in table.findall(NS+'Row'):
      logical_row=int(row.get(NS+'Index',logical_row+1)); cells=[];ci=0
      for cell in row.findall(NS+'Cell'):
       ci=int(cell.get(NS+'Index',ci+1));value=cell.find(NS+'Data');cells.append({'column_index_1based':ci,'value_raw':value.text if value is not None else None,'value_type':value.get(NS+'Type') if value is not None else None,'merge_across':cell.get(NS+'MergeAcross'),'merge_down':cell.get(NS+'MergeDown'),'formula':cell.get(NS+'Formula')});cell_count+=1
      f.write(json.dumps({'source_id':'sha256:'+digest,'source_path':str(path.relative_to(ROOT)),'source_hash':digest,'document_date':None,'page_or_section':{'sheet':sn,'row':logical_row},'extraction_method':'spreadsheetml_xml','validation_status':'unverified','cells':cells},ensure_ascii=False)+'\n');row_count+=1
   meta.write_text(json.dumps({'source_sha256':digest,'sheets':len(sheets),'rows':row_count,'cells':cell_count,'xml_literal_escape_repairs':repairs,'xml_ampersand_repairs':amp_repairs,'merged_cells':'preserved_not_expanded','formula':'not_evaluated','semantic_headers':'unverified'},ensure_ascii=False,indent=2),encoding='utf8');print('ok',path.name,'sheets',len(sheets),'rows',row_count,'cells',cell_count)
  except (ET.ParseError,UnicodeError,ValueError,OSError) as e:print('error',path.name,type(e).__name__);return 1
 return 0
if __name__=='__main__':sys.exit(main())
