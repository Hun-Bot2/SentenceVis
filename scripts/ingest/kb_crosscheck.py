"""Cross-check AI-Hub knowledge-base Precedent nodes against AI-Hub judgment files.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
Usage: python3 scripts/ingest/kb_crosscheck.py SCAN_DIR
Join key: KB node id == law.go.kr 판례일련번호 carried by datasets 12/115.
Compares case number, court, decision date, case type, and whether each KB
refArticle (law + article) occurs in the judgment's own 참조조문 field.
Writes SCAN_DIR/kb_crosscheck.json and appends kb_* rows to crosscheck_mismatches.jsonl.
"""
import collections, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/align"))
from link_pairs import normalize_court  # noqa: E402

def nows(s): return re.sub(r"\s+", "", s or "")
def date8(s):
    m = re.fullmatch(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})\D*", (s or "").strip())
    return f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}" if m else re.sub(r"\D", "", s or "")
ART = re.compile(r"(.+?)제(\d+)조(?:의(\d+))?")

def art_key(a):
    m = ART.match(nows(a))
    return (m.group(1), m.group(2) + ("-" + m.group(3) if m.group(3) else "")) if m else None

def main(d):
    d = Path(d)
    prec = {}
    for l in (d / "members.jsonl").open():
        r = json.loads(l)
        if r.get("kind") == "precedent_fulltext":
            prec.setdefault(r["serial"], r)
    kb = [json.loads(l) for l in (d / "kb_precedents.jsonl").open()]
    mism = (d / "crosscheck_mismatches.jsonl").open("a")
    agg, n = collections.Counter(), 0
    art_total = art_found = 0
    cats = collections.Counter()
    for k in kb:
        r = prec.get(k["kb_id"])
        if not r:
            continue
        n += 1
        pairs = {"case_no": (nows((k.get("caseNumber") or [""])[0]), r["case_no"]),
                 "court": (normalize_court((k.get("courtName") or [""])[0]), normalize_court(r["court"])),
                 "date": (date8((k.get("sentenceDate") or [""])[0]), r["date"]),
                 "category": ((k.get("caseType") or [""])[0], r.get("category", ""))}
        for f, (a, b) in pairs.items():
            ok = a == b
            agg[f] += ok
            if not ok:
                mism.write(json.dumps({"check": "E_kb", "key": k["kb_id"], "field": f, "a": a, "b": b, "a_member": "kb", "b_member": r["member"]}, ensure_ascii=False) + "\n")
        refs = r.get("ref_articles", "")
        for a in k.get("refArticle", []):
            key = art_key(a)
            if not key:
                continue
            art_total += 1
            hit = bool(re.search(re.escape(key[0][-6:]) + r".{0,40}?제" + key[1].replace("-", "조의") + r"(?!\d)", refs)) or (f"제{key[1].replace('-', '조의')}" in refs and key[0] in refs)
            art_found += hit
        cats[pairs["category"][1]] += 1
    rate = lambda a, b: {"agree": a, "n": b, "rate": round(a / b, 4) if b else None}
    res = {"kb_precedent_nodes": len(kb), "matched_by_serial": n, "unmatched": len(kb) - n,
           "fields": {f: rate(agg[f], n) for f in ("case_no", "court", "date", "category")},
           "kb_refArticle_found_in_judgment_참조조문": rate(art_found, art_total),
           "matched_by_category": dict(cats.most_common()),
           "note": "refArticle check is textual (law-name tail + article number); 참조조문 may use abbreviations, so misses are upper-bound disagreements."}
    (d / "kb_crosscheck.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main(sys.argv[1])
