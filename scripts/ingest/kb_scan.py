"""Full scan of the AI-Hub legal knowledge base (data/법률 지식베이스).

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/ingest/kb_scan.py data/private/aihub_scan/<scan_dir>

Streams every member of every ZIP (N-Triples line by line, the JSON-RDF files
by their pretty-printed key lines, OWL as XML) without extracting to disk.
Writes into the scan dir:
  kb_summary.json        per member: triples, subjects, predicates, malformed lines
  kb_precedents.jsonl    Precedent nodes (id, caseNumber, court, date, type, refArticle…)
  kb_decree_versions.json  statute article nodes grouped by law id and version date
JSON vs N-Triples of the same dataset are compared (subject sets, value counts).
"""
from __future__ import annotations

import collections
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
KB = ROOT / "data" / "법률 지식베이스"
NT = re.compile(r'^(<[^>]*>|_:\S+)\s+<([^>]*)>\s+(<[^>]*>|_:\S+|"(?:[^"\\]|\\.)*"(?:\^\^<[^>]*>|@[\w-]+)?)\s*\.\s*$')
UESC = re.compile(r"\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{8})")
PREC = "http://www.aihub.or.kr/kb/law/Precedent/"
KBNS = "http://www.aihub.or.kr/kb/law/"


def unesc(s: str) -> str:
    return UESC.sub(lambda m: chr(int(m.group(1) or m.group(2), 16)), s)


def literal(o: str) -> str:
    m = re.match(r'^"((?:[^"\\]|\\.)*)"', o)
    if not m:
        return unesc(o.strip("<>"))
    v = m.group(1)
    return unesc(v.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\"))


def scan_nt(f, prec: dict | None, decree: collections.Counter | None) -> dict:
    triples = bad = 0
    subjects: set[str] = set()
    preds = collections.Counter()
    for raw in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = NT.match(line)
        if not m:
            bad += 1
            continue
        s, p, o = unesc(m.group(1).strip("<>")), unesc(m.group(2)), m.group(3)
        triples += 1
        subjects.add(s)
        preds[p.rsplit("/", 1)[-1].rsplit("#", 1)[-1]] += 1
        if prec is not None and s.startswith(PREC) and p.startswith(KBNS):
            rec = prec.setdefault(s[len(PREC):], collections.defaultdict(list))
            rec[p[len(KBNS):]].append(literal(o))
        if decree is not None and "/decree/조/_" in s and p.endswith("rdf-syntax-ns#type"):
            mm = re.search(r"/_(\d+)-(\d{8})_", s)
            if mm:
                decree[(mm.group(1), mm.group(2))] += 1
    return {"format": "nt", "triples": triples, "subjects": len(subjects), "malformed_lines": bad,
            "predicates": dict(preds.most_common(40)), "_subjects": subjects}


def scan_jsonrdf(f) -> dict:
    """Pretty-printed RDF/JSON: subject keys sit at two-space indent, values on '"value" :' lines."""
    subjects: set[str] = set()
    values = 0
    for raw in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
        m = re.match(r'^  "([^"]+)"\s*:\s*\{', raw)
        if m:
            subjects.add(m.group(1))
        elif re.match(r'^\s*"value"\s*:', raw):
            values += 1
    return {"format": "json-rdf", "subjects": len(subjects), "values": values, "_subjects": subjects}


def main(scan_dir: str) -> None:
    out = Path(scan_dir)
    summary: dict = {"members": [], "json_vs_nt": []}
    prec: dict = {}
    decree: collections.Counter = collections.Counter()
    subject_sets: dict[str, set] = {}
    for zp in sorted(KB.rglob("*.zip")):
        rel = str(zp.relative_to(ROOT / "data"))
        z = zipfile.ZipFile(zp)
        for info in z.infolist():
            if info.is_dir():
                continue
            row = {"archive": rel, "member": info.filename, "bytes": info.file_size}
            with z.open(info) as f:
                ext = Path(info.filename).suffix.lower()
                if ext == ".nt":
                    r = scan_nt(f, prec if "관련판례" in rel or "precedent" in info.filename else None,
                                decree if "decree_조" in info.filename else None)
                elif ext == ".json":
                    r = scan_jsonrdf(f)
                elif ext == ".owl":
                    root = ET.parse(f).getroot()
                    tags = collections.Counter(el.tag.rsplit("}", 1)[-1] for el in root.iter())
                    r = {"format": "owl", "classes": tags.get("Class", 0), "object_properties": tags.get("ObjectProperty", 0),
                         "datatype_properties": tags.get("DatatypeProperty", 0)}
                else:
                    r = {"format": ext or "unknown"}
            subj = r.pop("_subjects", None)
            if subj is not None:
                subject_sets[rel] = subj
            row.update(r)
            summary["members"].append(row)
            print(rel.split("/")[-1], {k: v for k, v in r.items() if k != "predicates"}, flush=True)
    # JSON vs N-Triples of the same dataset: compare subject sets
    for rel, subj in subject_sets.items():
        if "(Json)" in rel:
            twin = rel.replace("(Json)", "(N-triple)")
            if twin in subject_sets:
                nt = subject_sets[twin]
                summary["json_vs_nt"].append({"json": rel, "nt": twin, "json_subjects": len(subj), "nt_subjects": len(nt),
                                              "common": len(subj & nt), "only_json": len(subj - nt), "only_nt": len(nt - subj)})
    with (out / "kb_precedents.jsonl").open("w") as f:
        for pid, rec in prec.items():
            f.write(json.dumps({"kb_id": pid, **{k: v for k, v in rec.items()}}, ensure_ascii=False) + "\n")
    laws = collections.defaultdict(set)
    for (law, date), _ in decree.items():
        laws[law].add(date)
    vc = collections.Counter(len(v) for v in laws.values())
    (out / "kb_decree_versions.json").write_text(json.dumps(
        {"article_nodes": sum(decree.values()), "laws": len(laws), "law_versions": len(decree),
         "versions_per_law_histogram": dict(sorted(vc.items())),
         "version_dates_min_max": [min(d for _, d in decree), max(d for _, d in decree)] if decree else None},
        ensure_ascii=False, indent=2))
    summary["precedent_nodes"] = len(prec)
    (out / "kb_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary["json_vs_nt"], ensure_ascii=False, indent=1))
    print("precedent nodes", len(prec))
    print((out / "kb_decree_versions.json").read_text())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
