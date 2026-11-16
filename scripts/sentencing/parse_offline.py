#!/usr/bin/env python3
"""Parse manually obtained local HTML only. No network access. AI: OpenAI Codex."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
from collect import parse, official


def process(root, manifest):
    root = root.resolve()
    results, failures = [], []
    for index, item in enumerate(manifest):
        try:
            file = (root / item['file']).resolve()
            if not file.is_relative_to(root) or not file.is_file():
                raise ValueError('file must exist inside input directory')
            if not official(item['url']):
                raise ValueError('source URL must be the official host')
            data = file.read_bytes()
            page = parse(data, item.get('charset'))
            results.append({'file': item['file'], 'source_url': item['url'],
                            'collected_at': item.get('collected_at'),
                            'sha256': hashlib.sha256(data).hexdigest(),
                            'parsed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            'tables': page.tables, 'verification_status': 'unverified',
                            'comparability': 'unknown',
                            'warnings': (['collected_at_missing'] if not item.get('collected_at') else []) +
                                        (['no_tables'] if not page.tables else []) +
                                        ['merged_cells_not_resolved', 'semantic_extraction_not_verified']})
        except (KeyError, ValueError, OSError) as exc:
            failures.append({'manifest_index': index, 'error': str(exc)})
    return results, failures


def main():
    ap = argparse.ArgumentParser(description='Parse local manually collected HTML; never connects to network')
    ap.add_argument('--input-dir', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    a = ap.parse_args()
    manifest = json.loads(a.manifest.read_text(encoding='utf-8'))
    if not isinstance(manifest, list): ap.error('manifest must be an array')
    results, failures = process(a.input_dir, manifest)
    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir/'manual_documents.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    quality = {'manifest_entries':len(manifest), 'parsed_documents':len(results), 'failed_documents':len(failures),
               'missing_collected_at':sum(not r['collected_at'] for r in results), 'errors':failures,
               'coverage':'unknown', 'comparison':'unknown', 'verification_status':'unverified'}
    (a.output_dir/'manual_quality.json').write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(quality, ensure_ascii=False))
    return 1 if failures else 0

if __name__ == '__main__': raise SystemExit(main())
