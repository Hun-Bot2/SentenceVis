#!/usr/bin/env python3
"""Read-only AI-Hub ZIP inventory and private research index. AI-assisted; see ATTRIBUTION.

Never extracts archives. Non-core schema samples are bounded; core dataset 12 JSONs
are fully parsed. Source text stays in the original ZIP; SQLite stores locators/metadata.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import sys
import tempfile
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
MAX_MEMBER_BYTES = 8 * 1024 * 1024
VERSION = 'inventory-v4'


def nfc(value):
    return unicodedata.normalize('NFC', value)


def digest_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def safe_member(info):
    name = info.filename.replace('\\', '/')
    # Leading '/' is retained as an archive locator only; no filesystem extraction.
    return ('..' not in PurePosixPath(name).parts
            and not re.match(r'^[A-Za-z]:', name) and '\x00' not in name
            and not stat.S_ISLNK(info.external_attr >> 16) and not info.flag_bits & 1
            and 0 <= info.file_size <= MAX_MEMBER_BYTES)


def read_member(archive, info):
    if not safe_member(info):
        raise ValueError('unsafe_or_oversized_member')
    with archive.open(info) as stream:
        data = stream.read(MAX_MEMBER_BYTES + 1)
    if len(data) > MAX_MEMBER_BYTES:
        raise ValueError('oversized_member')
    return data


def describe_schema(value, profile, prefix='$'):
    kind = ('null' if value is None else 'boolean' if isinstance(value, bool)
            else 'object' if isinstance(value, dict) else 'array' if isinstance(value, list)
            else 'string' if isinstance(value, str) else 'number')
    profile[prefix][kind] += 1
    if isinstance(value, dict):
        for key, child in value.items():
            describe_schema(child, profile, prefix + '.' + key)
    elif isinstance(value, list):
        for child in value:
            describe_schema(child, profile, prefix + '[]')


def archive_context(path, data_root):
    relative = path.relative_to(data_root)
    family = nfc(relative.parts[0]).split('.')[0]
    prefix = path.name[:2]
    split = 'training' if prefix in ('TS', 'TL') else 'validation' if prefix in ('VS', 'VL') else 'auxiliary'
    role = 'source' if prefix in ('TS', 'VS') else 'label' if prefix in ('TL', 'VL') else 'auxiliary'
    subset = ('multi_instance' if family == '12' and '02.' in path.name
              else 'general' if family == '12' and '01.' in path.name else 'other')
    return relative.as_posix(), family, split, role, subset


def metadata(obj, role):
    data = obj.get('PrecService') if role == 'source' else obj.get('info')
    if not isinstance(data, dict):
        raise ValueError('unexpected_core_schema')
    mapping = ({'source_key': '판례정보일련번호', 'case_no': '사건번호', 'court': '법원명',
                'decision_date': '선고일자', 'category': '사건종류명', 'court_type': '판결유형'} if role == 'source'
               else {'source_key': 'caseNoID', 'case_no': 'caseNo', 'court': 'courtNm',
                     'decision_date': 'judmnAdjuDe', 'category': 'caseClass', 'court_type': 'courtType'})
    result = {name: str(data[key]) if isinstance(data.get(key), (str, int)) else None for name, key in mapping.items()}
    if role == 'source' and '행정심판례일련번호' in data:
        # This is a different source record kind, not a missing criminal judgment.
        result.update(source_key=data.get('행정심판례일련번호'), court=data.get('재결청'),
                      decision_date=data.get('의결일자'), court_type=data.get('재결례유형명'))
    return result


def init_db(db):
    db.executescript('''
    CREATE TABLE archives(archive_id TEXT PRIMARY KEY, relative_path TEXT, dataset TEXT,
      split TEXT, role TEXT, subset TEXT, sha256 TEXT, bytes INTEGER, status TEXT,
      member_count INTEGER, json_count INTEGER, parsed_count INTEGER DEFAULT 0);
    CREATE TABLE documents(source_id TEXT PRIMARY KEY, archive_id TEXT, member_index INTEGER,
      member_path TEXT, member_sha256 TEXT, source_key TEXT, case_no TEXT, court TEXT,
      decision_date TEXT, category TEXT, court_type TEXT, section_count INTEGER,
      annotation_count INTEGER, origin_reference_section_count INTEGER,
      source_legal_verification TEXT DEFAULT 'unverified', FOREIGN KEY(archive_id) REFERENCES archives);
    CREATE TABLE sections(source_id TEXT, ordinal INTEGER, section_id TEXT, title TEXT,
      text_sha256 TEXT, codepoint_length INTEGER, utf16_length INTEGER, declared_char_count INTEGER,
      PRIMARY KEY(source_id,ordinal), FOREIGN KEY(source_id) REFERENCES documents);
    CREATE TABLE issues(archive_id TEXT, member_index INTEGER, code TEXT, count INTEGER);
    CREATE TABLE pairing_candidates(label_source_id TEXT, source_source_id TEXT,
      basis TEXT, status TEXT DEFAULT 'candidate');
    CREATE INDEX document_identity ON documents(source_key,case_no,court,decision_date);
    CREATE INDEX archive_role ON archives(dataset,split,role,subset);
    CREATE INDEX pairing_label ON pairing_candidates(label_source_id);
    CREATE INDEX pairing_source ON pairing_candidates(source_source_id);
    ''')


def profile_core(db, obj, source_id, archive_id, index, member, payload, role):
    meta = metadata(obj, role)
    sections = obj.get('sections', []) if role == 'label' else []
    annotations = obj.get('annotations', []) if role == 'label' else []
    if not isinstance(sections, list) or not isinstance(annotations, list):
        raise ValueError('unexpected_core_arrays')
    origin = sum(isinstance(s, dict) and bool(re.search(r'원심|제\s*1\s*심\s*판결|제\s*일\s*심\s*판결', s.get('title', ''))) for s in sections)
    db.execute('INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
               (source_id, archive_id, index, member.filename, hashlib.sha256(payload).hexdigest(),
                meta['source_key'], meta['case_no'], meta['court'], meta['decision_date'],
                meta['category'], meta['court_type'], len(sections), len(annotations), origin, 'unverified'))
    known = set()
    issues = collections.Counter()
    for ordinal, section in enumerate(sections):
        if not isinstance(section, dict) or not isinstance(section.get('text'), str):
            issues['invalid_section'] += 1
            continue
        sid, title, text = section.get('section_id'), section.get('title'), section['text']
        if sid in known:
            issues['duplicate_section_id'] += 1
        known.add(sid)
        count = section.get('char_count')
        if not isinstance(count, int):
            count = None
        db.execute('INSERT INTO sections VALUES(?,?,?,?,?,?,?,?)',
                   (source_id, ordinal, sid, title, hashlib.sha256(text.encode()).hexdigest(),
                    len(text), len(text.encode('utf-16-le', errors='surrogatepass')) // 2, count))
    for annotation in annotations:
        if not isinstance(annotation, dict):
            issues['invalid_annotation'] += 1
            continue
        refs = annotation.get('section_id', [])
        if not isinstance(refs, list):
            issues['non_array_annotation_section_ids'] += 1
            refs = [refs]
        for ref in refs:
            if ref not in known:
                issues['annotation_unknown_section_id'] += 1
        for span in annotation.get('span', []):
            if (not isinstance(span, dict) or not isinstance(span.get('start'), int)
                    or not isinstance(span.get('end'), int) or span['start'] < 0 or span['end'] < span['start']):
                issues['invalid_span_numbers'] += 1
    info = obj.get('info', {})
    if role == 'label' and info.get('annotation_count') != len(annotations):
        issues['annotation_count_mismatch'] += 1
    for name, value in meta.items():
        if value is None or not value.strip():
            issues['missing_' + name] += 1
    for code, count in issues.items():
        db.execute('INSERT INTO issues VALUES(?,?,?,?)', (archive_id, index, code, count))


def normalized(value):
    return re.sub(r'\s+', '', nfc(value)) if isinstance(value, str) else None


def normalized_date(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if re.fullmatch(r'\d{8}', value):
        return value
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return value.replace('-', '')
    return None


def check_pairings(db):
    db.create_function('norm', 1, normalized)
    db.create_function('normdate', 1, normalized_date)
    # Same metadata across source/label is a candidate correspondence, not a legal link.
    db.execute('''INSERT INTO pairing_candidates(label_source_id,source_source_id,basis)
      SELECT l.source_id,s.source_id,'source_key+NFC_no_space_case_no/court+date_format+split+subset'
      FROM documents l JOIN archives la ON la.archive_id=l.archive_id
      JOIN documents s ON s.source_key=l.source_key AND norm(s.case_no)=norm(l.case_no)
        AND norm(s.court)=norm(l.court) AND normdate(s.decision_date)=normdate(l.decision_date)
      JOIN archives sa ON sa.archive_id=s.archive_id
      WHERE la.role='label' AND sa.role='source' AND la.dataset=sa.dataset
        AND la.split=sa.split AND la.subset=sa.subset
        AND l.source_key IS NOT NULL AND trim(l.source_key)<>''
        AND l.case_no IS NOT NULL AND trim(l.case_no)<>''
        AND l.court IS NOT NULL AND trim(l.court)<>''
        AND l.decision_date IS NOT NULL AND trim(l.decision_date)<>'' ''')
    db.execute('''UPDATE pairing_candidates SET status='ambiguous'
      WHERE label_source_id IN (SELECT label_source_id FROM pairing_candidates GROUP BY label_source_id HAVING count(*)<>1)
      OR source_source_id IN (SELECT source_source_id FROM pairing_candidates GROUP BY source_source_id HAVING count(*)<>1)''')


def private_output(path, data_root):
    destination = path.resolve()
    if not destination.is_relative_to((data_root / 'private').resolve()):
        raise ValueError('output_must_be_under_data_private')
    return destination


def run(data_root, output, sample_limit=10):
    data_root = data_root.resolve()
    output = private_output(output, data_root)
    if output.exists():
        raise ValueError('output_already_exists_choose_new_directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    working = Path(tempfile.mkdtemp(prefix='.inventory-', dir=output.parent))
    try:
        db = sqlite3.connect(working / 'catalog.sqlite')
        db.execute('PRAGMA foreign_keys=ON')
        init_db(db)
        profiles, manifests, leftovers = {}, [], []
        paths = sorted(p for p in data_root.rglob('*') if p.is_file()
                       and p.relative_to(data_root).parts[0] not in ('raw', 'private', 'processed', 'cache')
                       and p.name not in ('README.md', '.DS_Store'))
        for path in paths:
            relative, family, split, role, subset = archive_context(path, data_root)
            if path.suffix.lower() != '.zip':
                leftovers.append({'relative_path': relative, 'bytes': path.stat().st_size,
                                  'sha256': digest_file(path), 'status': 'not_processed'})
                continue
            before = path.stat()
            sha = digest_file(path)
            archive_id = hashlib.sha256((relative + '\0' + sha).encode()).hexdigest()
            record = dict(archive_id=archive_id, relative_path=relative, dataset=family, split=split,
                          role=role, subset=subset, sha256=sha, bytes=before.st_size,
                          status='ok', member_count=0, json_count=0, parsed_count=0, attempted_count=0,
                          crc_scope='fully_read_members_only', schema_scope='all_core_json' if family == '12' else f'first_{sample_limit}_safe_supported_members')
            db.execute('INSERT INTO archives VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                       (archive_id, relative, family, split, role, subset, sha, before.st_size, 'scanning', 0, 0, 0))
            schema = collections.defaultdict(collections.Counter)
            try:
                with zipfile.ZipFile(path) as archive:
                    members = archive.infolist()
                    files = [(i, m) for i, m in enumerate(members) if not m.is_dir()]
                    record['member_count'] = len(files)
                    record['extensions'] = dict(collections.Counter(Path(m.filename).suffix.lower() for _, m in files))
                    record['json_count'] = record['extensions'].get('.json', 0)
                    record['uncompressed_bytes'] = sum(m.file_size for _, m in files)
                    record['duplicate_member_paths'] = sum(c-1 for c in collections.Counter(m.filename for _, m in files).values())
                    record['unsafe_or_oversized_members'] = sum(not safe_member(m) for _, m in files)
                    record['absolute_member_paths'] = sum(PurePosixPath(m.filename.replace('\\','/')).is_absolute() for _,m in files)
                    for index, member in files:
                        if not safe_member(member):
                            db.execute('INSERT INTO issues VALUES(?,?,?,?)',(archive_id,index,'unsafe_or_oversized_member',1))
                            continue
                        suffix = Path(member.filename).suffix.lower()
                        if family == '12' and suffix != '.json':
                            continue
                        if family != '12' and record['attempted_count'] >= sample_limit:
                            break
                        if suffix not in ('.json', '.xml', '.csv'):
                            continue
                        record['attempted_count'] += 1
                        try:
                            payload = read_member(archive, member)
                            if suffix == '.json':
                                obj = json.loads(payload.decode('utf-8-sig'))
                                describe_schema(obj, schema)
                                if family == '12':
                                    source_id = hashlib.sha256(f'{archive_id}:{index}'.encode()).hexdigest()
                                    with db:
                                        profile_core(db, obj, source_id, archive_id, index, member, payload, role)
                            elif suffix == '.xml':
                                if b'<!DOCTYPE' in payload or b'<!ENTITY' in payload:
                                    raise ValueError('xml_doctype_not_supported')
                                tree = ET.fromstring(payload)
                                for element in tree.iter():
                                    schema['xml.'+element.tag]['element'] += 1
                            else:
                                try: text = payload.decode('utf-8-sig')
                                except UnicodeDecodeError: text = payload.decode('cp949')
                                rows = list(csv.reader(io.StringIO(text)))
                                for row in rows:
                                    schema['csv.row_width'][str(len(row))] += 1
                            record['parsed_count'] += 1
                        except (ValueError, KeyError, TypeError, UnicodeError, ET.ParseError, zipfile.BadZipFile, RuntimeError) as error:
                            db.execute('INSERT INTO issues VALUES(?,?,?,?)',(archive_id,index,'member_error_'+type(error).__name__,1))
                    record['multi_instance_groups'] = len({PurePosixPath(m.filename).parts[1] for _,m in files
                        if len(PurePosixPath(m.filename).parts)>2}) if subset == 'multi_instance' else None
            except (zipfile.BadZipFile, OSError, RuntimeError) as error:
                record['status'] = 'unreadable_archive_' + type(error).__name__
            after = path.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                raise ValueError('input_changed_during_scan')
            record['issue_count'] = db.execute('SELECT coalesce(sum(count),0) FROM issues WHERE archive_id=?',(archive_id,)).fetchone()[0]
            if record['status']=='ok' and record['issue_count']:
                record['status']='issues_recorded'
            db.execute('UPDATE archives SET status=?,member_count=?,json_count=?,parsed_count=? WHERE archive_id=?',
                       (record['status'],record['member_count'],record['json_count'],record['parsed_count'],archive_id))
            db.commit()
            profiles[archive_id] = {k:dict(v) for k,v in sorted(schema.items())}
            manifests.append(record)
            print(f"dataset={family} archive={len(manifests)} status={record['status']} parsed={record['parsed_count']}",flush=True)
        check_pairings(db)
        db.commit()
        summary = {
            'schema_version': VERSION, 'data_root': str(data_root),
            'inspected_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'python_version': sys.version.split()[0],
            'proposal_sha256': digest_file(ROOT/'slides.pdf') if (ROOT/'slides.pdf').exists() else None,
            'acquired_at': None,
            'script_sha256': digest_file(Path(__file__)), 'archive_count': len(manifests),
            'unreadable_archives': sum(a['status'].startswith('unreadable') for a in manifests),
            'non_archive_files': leftovers, 'archives': manifests,
            'legal_verification': 'unverified', 'redistribution_rights': 'unverified',
            'core_documents_by_partition': [dict(zip(('dataset','split','role','subset','category','count'),r)) for r in db.execute('''
                SELECT a.dataset,a.split,a.role,a.subset,d.category,count(*) FROM documents d
                JOIN archives a USING(archive_id) GROUP BY 1,2,3,4,5 ORDER BY 1,2,3,4,5''')],
            'pairing_status_counts': dict(db.execute('SELECT status,count(*) FROM pairing_candidates GROUP BY status')),
            'issues': dict(db.execute('SELECT code,sum(count) FROM issues GROUP BY code')),
            'limits': ['non-core content is sampled, not fully validated', 'archive header counts are not unique legal items',
                       'source-label matches are not trial-appeal or defendant links', 'annotation offset unit is unverified', 'absolute member paths are read as archive locators only, never extracted',
                       'date normalization changes syntax only; era/calendar and legal dates remain unverified']}
        db.close()
        (working / 'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (working / 'schema_profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2)+'\n')
        working.rename(output)
        print(f'Private inventory written: {output}',flush=True)
    except BaseException:
        import shutil
        shutil.rmtree(working,ignore_errors=True)
        raise


def export_record(catalog, source_id, output):
    output = private_output(output, ROOT / 'data')
    if output.exists():
        raise ValueError('output_already_exists')
    with sqlite3.connect(f'file:{catalog.resolve()}?mode=ro',uri=True) as db:
        row = db.execute('''SELECT a.relative_path,a.sha256,d.member_index,d.member_path,d.member_sha256
              FROM documents d JOIN archives a USING(archive_id) WHERE source_id=?''',(source_id,)).fetchone()
    if row is None:
        raise ValueError('unknown_source_id')
    path = ROOT / 'data' / row[0]
    if digest_file(path)!=row[1]:
        raise ValueError('archive_hash_changed')
    with zipfile.ZipFile(path) as archive:
        member = archive.infolist()[row[2]]
        if member.filename!=row[3]:
            raise ValueError('member_locator_changed')
        payload = read_member(archive, member)
    if hashlib.sha256(payload).hexdigest()!=row[4]:
        raise ValueError('member_hash_changed')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as stream: stream.write(payload)
    print('Original record written to the requested private path; no text printed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    scan = sub.add_parser('scan')
    scan.add_argument('--data-root',type=Path,default=ROOT/'data')
    scan.add_argument('--output',type=Path,required=True)
    scan.add_argument('--sample-limit',type=int,default=10)
    record = sub.add_parser('record')
    record.add_argument('--catalog',type=Path,required=True)
    record.add_argument('--source-id',required=True)
    record.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.command=='scan':
        if args.sample_limit<1: parser.error('sample-limit must be positive')
        run(args.data_root,args.output,args.sample_limit)
    else: export_record(args.catalog,args.source_id,args.output)

if __name__=='__main__':
    main()
