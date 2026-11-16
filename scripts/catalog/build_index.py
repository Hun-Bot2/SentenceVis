#!/usr/bin/env python3
"""Build local source-linked full-text index from extracted PDF pages only."""
import argparse,json,sqlite3
from pathlib import Path
from inventory import DATA

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output.resolve()
 if not out.is_relative_to((DATA/'interim').resolve()) or out.exists():p.error('output must be new and inside data/interim')
 out.parent.mkdir(parents=True,exist_ok=True);con=sqlite3.connect(out);con.execute('create virtual table pages using fts5(source_id UNINDEXED, source_path UNINDEXED, page UNINDEXED, text)');n=0
 for meta in (DATA/'interim/extracted').glob('*.metadata.json'):
  m=json.loads(meta.read_text());fname=meta.name.removesuffix('.metadata.json')+'.jsonl'
  if not m['source_path'].lower().endswith('.pdf'):continue
  with (meta.parent/fname).open() as f:
   for line in f:
    x=json.loads(line);con.execute('insert into pages values(?,?,?,?)',(x['source_id'],x['source_path'],x['page_or_section'],x['text']));n+=1
 con.commit();con.close();print('indexed_pages',n)
if __name__=='__main__':main()
