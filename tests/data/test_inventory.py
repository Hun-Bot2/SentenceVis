"""Synthetic fixtures only; no legal ground truth or licensed dataset in tests."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

MODULE = Path(__file__).resolve().parents[2] / 'scripts/ingest/inventory.py'
spec = importlib.util.spec_from_file_location('inventory', MODULE)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


def source(key='SYNTHETIC-ID'):
    return {'PrecService': {'판례정보일련번호': key, '사건번호': 'SYNTHETIC-CASE',
            '법원명': '합성 법원', '선고일자': '20200102', '사건종류명': '형사', '판결유형': '합성'}}


def label(key='SYNTHETIC-ID'):
    return {'info': {'caseNoID': key, 'caseNo': 'SYNTHETIC-CASE', 'courtNm': '합성 법원',
            'judmnAdjuDe': '2020-01-02', 'caseClass': '형사', 'courtType': '합성', 'annotation_count': 0},
            'sections': [{'section_id': 's1', 'title': '원심판결', 'text': '합성😀', 'char_count': 3}],
            'annotations': []}


def write_zip(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w') as z:
        for name, obj in contents:
            z.writestr(name, json.dumps(obj, ensure_ascii=False).encode())


class InventoryTests(unittest.TestCase):
    def test_schema_profiles_store_types_not_original_text(self):
        from collections import defaultdict, Counter
        result = defaultdict(Counter)
        inventory.describe_schema({'private': 'SYNTHETIC_SECRET', 'absent': None}, result)
        self.assertNotIn('SYNTHETIC_SECRET', json.dumps(result))
        self.assertEqual(result['$.absent']['null'], 1)

    def test_path_traversal_and_oversized_entries_are_refused(self):
        for name in ['../escape.json', 'a/../../escape.json', 'C:/escape.json']:
            self.assertFalse(inventory.safe_member(zipfile.ZipInfo(name)))
        member = zipfile.ZipInfo('normal.json')
        member.file_size = inventory.MAX_MEMBER_BYTES + 1
        self.assertFalse(inventory.safe_member(member))

    def test_absolute_archive_name_can_be_read_without_extraction(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('/archive-locator-only.json', '{}')
        with zipfile.ZipFile(stream) as z:
            self.assertEqual(inventory.read_member(z, z.infolist()[0]), b'{}')

    def test_date_format_normalization_does_not_convert_era_or_guess(self):
        self.assertEqual(inventory.normalized_date('2020-01-02'), '20200102')
        self.assertEqual(inventory.normalized_date('4293-12-28'), '42931228')
        self.assertIsNone(inventory.normalized_date('2020/01/02'))

    def test_output_cannot_escape_private_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)/'data'
            with self.assertRaises(ValueError):
                inventory.private_output(Path(folder)/'public/result.json', data)
            self.assertEqual(inventory.private_output(data/'private/result.json', data), (data/'private/result.json').resolve())

    def test_source_label_pairing_is_candidate_and_marks_ambiguity(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)/'data'
            dataset = data/'12.synthetic'
            write_zip(dataset/'TS_01.general.zip', [('a.json', source()), ('b.json', source())])
            write_zip(dataset/'TL_01.general.zip', [('a.json', label())])
            output = data/'private/scan'
            with contextlib.redirect_stdout(io.StringIO()): inventory.run(data, output, 1)
            with sqlite3.connect(output/'catalog.sqlite') as db:
                self.assertEqual(db.execute('SELECT status,count(*) FROM pairing_candidates GROUP BY status').fetchall(), [('ambiguous', 2)])
                self.assertEqual(db.execute('SELECT source_legal_verification FROM documents LIMIT 1').fetchone()[0], 'unverified')
                self.assertEqual(db.execute('SELECT codepoint_length,utf16_length FROM sections').fetchone(), (3, 4))
            with self.assertRaises(ValueError): inventory.run(data, output)

    def test_bad_archive_is_recorded_without_hiding_good_records(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)/'data'
            dataset = data/'12.synthetic'
            write_zip(dataset/'TS_01.general.zip', [('a.json', source())])
            write_zip(dataset/'TL_01.general.zip', [('a.json', label())])
            (dataset/'bad.zip').write_bytes(b'not a zip')
            output = data/'private/scan'
            with contextlib.redirect_stdout(io.StringIO()): inventory.run(data, output, 1)
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['unreadable_archives'], 1)
            self.assertEqual(manifest['pairing_status_counts'], {'candidate': 1})
            self.assertEqual(manifest['legal_verification'], 'unverified')

    def test_annotation_ref_failures_remain_separate_from_legal_status(self):
        obj = label()
        obj['annotations'] = [{'section_id': ['missing'], 'span': [{'start': -1, 'end': 2}]}]
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)/'data'
            write_zip(data/'12.synthetic/TL_01.general.zip', [('a.json', obj)])
            output = data/'private/scan'
            with contextlib.redirect_stdout(io.StringIO()): inventory.run(data, output, 1)
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['issues']['annotation_unknown_section_id'], 1)
            self.assertEqual(manifest['issues']['invalid_span_numbers'], 1)
            self.assertEqual(manifest['issues']['annotation_count_mismatch'], 1)

    def test_record_export_checks_archive_hash_and_keeps_bytes(self):
        original_root = inventory.ROOT
        try:
            with tempfile.TemporaryDirectory() as folder:
                inventory.ROOT = Path(folder)
                data = Path(folder)/'data'
                archive = data/'12.synthetic/TS_01.general.zip'
                write_zip(archive, [('a.json', source())])
                output = data/'private/scan'
                with contextlib.redirect_stdout(io.StringIO()): inventory.run(data, output, 1)
                with sqlite3.connect(output/'catalog.sqlite') as db:
                    sid = db.execute('SELECT source_id FROM documents').fetchone()[0]
                result = data/'private/record.json'
                with contextlib.redirect_stdout(io.StringIO()): inventory.export_record(output/'catalog.sqlite', sid, result)
                with zipfile.ZipFile(archive) as z:
                    self.assertEqual(result.read_bytes(), z.read('a.json'))
                write_zip(archive, [('changed.json', source('changed'))])
                with self.assertRaisesRegex(ValueError, 'archive_hash_changed'):
                    inventory.export_record(output/'catalog.sqlite', sid, data/'private/other.json')
        finally:
            inventory.ROOT = original_root

if __name__ == '__main__':
    unittest.main()
