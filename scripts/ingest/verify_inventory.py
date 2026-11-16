#!/usr/bin/env python3
"""Independent ZIP/count reconciliation; no legal interpretation or raw text output."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3

import zipfile


def verify(snapshot):
    manifest = json.loads((snapshot/'manifest.json').read_text())
    root = Path(manifest['data_root'])
    counts = Counter()
    labels = Counter()
    archive_hash_checks = 0
    for archive in manifest['archives']:
        path = root/archive['relative_path']
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for b in iter(lambda:stream.read(1024*1024), b''): h.update(b)
        assert h.hexdigest()==archive['sha256'], 'archive_changed_since_inventory'
        archive_hash_checks += 1
        if archive['dataset']!='12': continue
        with zipfile.ZipFile(path) as z:
            members=[i for i in z.infolist() if not i.is_dir() and i.filename.endswith('.json')]
            assert len(members)==archive['parsed_count'], 'core_coverage_mismatch'
            counts[archive['role']]+=len(members)
            if archive['role']=='label':
                for member in members:
                    o=json.loads(z.read(member).decode('utf-8-sig'))
                    labels[(archive['split'],archive['subset'],o['info'].get('caseClass'))]+=1
    with sqlite3.connect(f'file:{(snapshot/"catalog.sqlite").resolve()}?mode=ro',uri=True) as db:
        actual = Counter({r[0]:r[1] for r in db.execute('SELECT a.role,count(*) FROM documents d JOIN archives a USING(archive_id) GROUP BY a.role')})
        assert actual==counts, 'representation_count_mismatch'
        sql_labels=Counter({(r[0],r[1],r[2]):r[3] for r in db.execute('''SELECT a.split,a.subset,d.category,count(*)
                FROM documents d JOIN archives a USING(archive_id) WHERE a.role='label' GROUP BY 1,2,3''')})
        assert labels==sql_labels, 'label_category_count_mismatch'
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[], 'orphan_reference'
        assert db.execute("SELECT count(*) FROM documents WHERE source_legal_verification<>'unverified'").fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM documents').fetchone()[0]==db.execute('SELECT count(DISTINCT source_id) FROM documents').fetchone()[0]
    result={'status':'passed','scope':'archive hashes + core coverage + independent label-category reconciliation + DB references',
            'archive_hash_checks':archive_hash_checks,'core_representation_counts':dict(counts),
            'criminal_label_records':sum(n for (_,_,category),n in labels.items() if category in ('형사','형사A','형사B')),
            'legal_correctness':'unverified','redistribution_rights':'unverified'}
    output=snapshot/'verification.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot',type=Path)
    args=parser.parse_args()
    # Do not write verification receipts into a public directory.
    root=Path(__file__).resolve().parents[2]/'data/private'
    if not args.snapshot.resolve().is_relative_to(root.resolve()): parser.error('snapshot must be under data/private')
    verify(args.snapshot)
