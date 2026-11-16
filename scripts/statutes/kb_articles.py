"""Article-level statute index from the AI-Hub legal knowledge base (법률데이터_법령).

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/statutes/kb_articles.py data/private/statutes/<new_file>.jsonl

One row per article (조): law name, law node, version id and date taken from the
article node id (<법령일련번호>-<YYYYMMDD>_<조>), article number (with 의-branch),
title (제명/명칭), and paragraph texts (항) in order. The KB holds ONE version per
law (2002–2019 effective dates), so text may differ from the version in force at a
2002–2011 decision; every row carries `version_note` for the UI.
"""
from __future__ import annotations

import collections
import io
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/ingest"))
from kb_scan import NT, literal, unesc  # noqa: E402

ZIP = ROOT / "data" / "법률 지식베이스" / "법률데이터" / "법률데이터_법령.zip"


def triples(z: zipfile.ZipFile, suffix: str):
    info = next(x for x in z.infolist() if x.filename.endswith(suffix))
    for raw in io.TextIOWrapper(z.open(info), encoding="utf-8"):
        m = NT.match(raw.strip())
        if m:
            yield unesc(m.group(1).strip("<>")), unesc(m.group(2)), m.group(3)


def main(out_path: str) -> None:
    out = Path(out_path)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    z = zipfile.ZipFile(ZIP)
    law_label, law_eff, art_law = {}, {}, {}
    for s, p, o in triples(z, "/법령.nt"):
        if p.endswith("rdf-schema#label"):
            law_label[s] = literal(o)
        elif p.endswith("/시행일자"):
            law_eff[s] = literal(o)
        elif p.endswith("법령/조문"):
            art_law[literal(o)] = s
    title, number, insert, paras = {}, {}, {}, collections.defaultdict(list)
    for s, p, o in triples(z, "decree_조.nt"):
        if p.endswith("제명/명칭"):
            title[s] = literal(o)
        elif p.endswith("제명/번호"):
            number[s] = literal(o)
        elif p.endswith("제명/삽입번호"):
            insert[s] = literal(o)
        elif p.endswith("조/항"):
            paras[s].append(literal(o))
    para_text, para_no = {}, {}
    for s, p, o in triples(z, "decree_항.nt"):
        if p.endswith("제명/명칭") or p.endswith("항/내용"):
            para_text.setdefault(s, literal(o))
        elif p.endswith("제명/번호"):
            para_no[s] = literal(o)
    n = 0
    with out.open("w") as f:
        for art, law in sorted(art_law.items()):
            if art not in title:
                continue
            m = re.search(r"/_(\d+)-(\d{8})_", art)
            ps = sorted(paras.get(art, []), key=lambda x: int(para_no.get(x, "0") or 0))
            no = number.get(art, "") + (f"-{insert[art]}" if art in insert else "")
            f.write(json.dumps({
                "law": law_label.get(law, ""), "law_node": law, "law_effective": law_eff.get(law, ""),
                "version_id": m.group(1) if m else "", "version_date": m.group(2) if m else "",
                "article": no, "title": title[art], "paragraphs": [para_text.get(x, "") for x in ps],
                "source": "AI-Hub 법률 지식베이스 법률데이터_법령 (NIA 2018)",
                "version_note": "single KB version; may differ from the version in force at the decision date",
                "source_basis": "contextual",
            }, ensure_ascii=False) + "\n")
            n += 1
    print(json.dumps({"articles": n, "laws": len({v for v in art_law.values()})}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
