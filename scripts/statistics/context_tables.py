"""Context tables for SentenScope: CCJS appeal statistics and 양형기준 timing.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/statistics/context_tables.py RUN_DIR

Writes RUN_DIR/context_ccjs_by_year.json and RUN_DIR/context_guideline_pairs.jsonl.
Both are `contextual`: they never explain an individual judgment.

CCJS: the user-supplied 죄명별 항소심 인원수표 has only leaf offense rows
(the 계 row is 0 in every year), so year totals are sums of leaf rows of a
single column; parent and child rows are never added together. Whether the
table covers all appellate courts or only some is unverified, and CCJS counts
persons while AI-Hub counts documents, so no sampling rate is computed.

양형기준: first guidelines took effect in 2009 for 살인·뇌물·성범죄·강도·
횡령배임·위증·무고 (sc.scourt.go.kr introduction page, checked 2026-11-15;
exact effective date per version not yet verified against originals). They
apply by 공소제기 date, which the judgments rarely state, so the only firm
rule used: a first-instance decision before ASSUMED_EFFECTIVE implies the
indictment was earlier, hence `not_applicable_by_date`. Everything else is
`unknown`; the flag depends on ASSUMED_EFFECTIVE being confirmed.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CCJS = sorted((ROOT / "data/processed/ccjs_offense").glob("*.jsonl"))
ASSUMED_EFFECTIVE = "20090701"  # unverified against the guideline originals
FIRST_GROUPS = {"살인": r"살인", "뇌물": r"뇌물", "성범죄": r"강간|추행|성폭력|성매매", "강도": r"강도",
                "횡령배임": r"횡령|배임", "위증": r"위증", "무고": r"무고"}
COLS = {
    "processed_total": "처리@처리계@처리계@처리계@처리계",
    "reversed_prison": "처리@파기@자판@자유형@유기",
    "reversed_suspended": "처리@파기@자판@자유형@집행유예",
    "dismissed_after_hearing": "처리@항소기각@변론경유@변론경유@변론경유",
    "dismissed_without_hearing": "처리@항소기각@변론불경유@변론불경유@변론불경유",
}


def ccjs_by_year() -> dict:
    out: dict = {}
    if not CCJS:
        return {"status": "ccjs_file_missing"}
    acc: dict = defaultdict(lambda: defaultdict(float))
    for line in CCJS[0].open():
        r = json.loads(line)
        if r["row_path"].startswith("계@"):
            continue
        for key, col in COLS.items():
            if r["column_path"] == col:
                acc[r["year"]][key] += float(r["value_decimal"])
    for y in sorted(acc):
        out[str(y)] = {k: int(v) for k, v in acc[y].items()}
    return {
        "source": str(CCJS[0].relative_to(ROOT)),
        "unit": "persons (table label; unverified)",
        "coverage_of_appellate_courts": "unverified",
        "source_basis": "contextual",
        "years": out,
    }


def main(run: str) -> None:
    import re

    run_dir = Path(run)
    ctx = ccjs_by_year()
    summary = json.loads((run_dir / "summary.json").read_text())
    ctx["aihub_accepted_appeal_documents_by_year"] = summary["accepted_appeals_by_year"]
    ctx["note"] = "Counts side by side only; documents ≠ persons; no ratio computed."
    (run_dir / "context_ccjs_by_year.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=2))
    docs = {json.loads(l)["source_id"]: json.loads(l) for l in (run_dir / "documents.jsonl").read_text().splitlines()}
    links = [json.loads(l) for l in (run_dir / "links.jsonl").read_text().splitlines()]
    with (run_dir / "context_guideline_pairs.jsonl").open("w") as f:
        for x in links:
            if x["link_status"] not in ("auto_strict", "auto_alias") or x.get("instance_pair", "1-2") != "1-2":
                continue
            t = docs[x["trial_id"]]
            groups = [g for g, pat in FIRST_GROUPS.items() if re.search(pat, t["case_name"] or "")]
            status = "not_applicable_by_date" if t["date"] < ASSUMED_EFFECTIVE else "unknown"
            f.write(json.dumps({
                "trial_id": x["trial_id"], "appeal_id": x["appeal_id"], "trial_date": t["date"],
                "offense_groups_by_case_name": groups, "guideline_status": status,
                "assumed_effective_date": ASSUMED_EFFECTIVE, "effective_date_status": "unverified",
                "source_basis": "contextual",
            }, ensure_ascii=False) + "\n")
    print(json.dumps(ctx, ensure_ascii=False, indent=1)[:2500])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
