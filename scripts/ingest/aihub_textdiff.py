"""Classify why two copies of the same precedent (same 판례일련번호) differ in text.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
Usage: python3 scripts/ingest/aihub_textdiff.py SCAN_DIR [--n 400 --seed 20261116]
Random sample of the B-check text mismatches; difflib on whitespace-free text.
Writes SCAN_DIR/textdiff.json. Category rules are heuristics, stated in the output.
"""
import argparse, collections, difflib, json, random, re
from pathlib import Path

HANJA = re.compile(r"[一-鿿豈-﫿]")
RULES = {
    "anonymization": "one side contains #이름#/#…#, A_01-style, 소외N, ○ or '…생략' masking tokens",
    "hanja_transliteration": "one side contains Hanja",
    "punctuation_symbol": "both sides ≤3 chars without Hangul/Hanja/digits",
    "other": "anything else (inspect)",
}

def cat(a, b):
    s = a + b
    if "#" in s or re.search(r"[A-Z]_\d|소외\s*\d|생략|[가-힣]\s*○", s):
        return "anonymization"
    if HANJA.search(s):
        return "hanja_transliteration"
    if len(a) <= 3 and len(b) <= 3 and not re.search(r"[가-힣0-9一-鿿]", s):
        return "punctuation_symbol"
    return "other"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("scan"); ap.add_argument("--n", type=int, default=400); ap.add_argument("--seed", type=int, default=20261116)
    a = ap.parse_args(); d = Path(a.scan)
    X = [json.loads(l) for l in (d / "crosscheck_mismatches.jsonl").open() if '"text_sha"' in l]
    M = {}
    for l in (d / "members.jsonl").open():
        r = json.loads(l)
        if r.get("kind") == "precedent_fulltext":
            M[r["member"]] = r
    samp = random.Random(a.seed).sample(X, min(a.n, len(X)))
    need = {M[x[k]]["sha256"] for x in samp for k in ("a_member", "b_member")}
    T = {}
    for ds in ("12", "115"):
        for l in (d / "texts" / f"{ds}.jsonl").open():
            t = json.loads(l)
            if t["sha256"] in need:
                T[t["sha256"]] = re.sub(r"\s+", "", t["text"])
    ratios, ops_by, docs_with, other_examples = [], collections.Counter(), collections.Counter(), []
    for x in samp:
        ta, tb = T[M[x["a_member"]]["sha256"]], T[M[x["b_member"]]["sha256"]]
        sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
        ratios.append(sm.ratio())
        seen = set()
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            c = cat(ta[i1:i2], tb[j1:j2]); ops_by[c] += 1; seen.add(c)
            if c == "other" and len(other_examples) < 15:
                other_examples.append([ta[max(0, i1 - 8):i2 + 8], tb[max(0, j1 - 8):j2 + 8]])
        for c in seen:
            docs_with[c] += 1
    ratios.sort(); q = lambda p: round(ratios[int(p * (len(ratios) - 1))], 4)
    out = {"population_text_mismatches": len(X), "sample": len(samp), "seed": a.seed,
           "similarity_quantiles": {"min": q(0), "p05": q(0.05), "median": q(0.5), "max": q(1)},
           "diff_ops_by_category": dict(ops_by), "docs_with_category": dict(docs_with), "rules": RULES,
           "other_examples_private": other_examples}
    (d / "textdiff.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "other_examples_private"}, ensure_ascii=False, indent=2))
    for e in other_examples[:8]: print("  other:", e)

if __name__ == "__main__":
    main()
