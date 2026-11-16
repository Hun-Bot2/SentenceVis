"""Merge AI-Hub criminal precedents from datasets 12 and 115 into one private cache.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md and docs/research/AIHUB_CROSS_VALIDATION.md.

Usage:
    python3 scripts/align/merge_corpus.py data/private/aihub_scan/<scan_dir> data/private/pipeline/<new_cache>.jsonl

Rules:
  * Unit = law.go.kr 판례일련번호 (serial). One record per serial.
  * Text preference: dataset 12 copy (anonymized by AI-Hub) > 115 TS/VS > 115 SbL.
    115 copies can contain real names/addresses that 12 masks, so every record
    carries `anonymized_source` (True only for dataset 12) and `display_ok`
    (= anonymized_source). The UI must not show text where display_ok is False.
  * Every copy is listed in `copies` (dataset, archive, member, sha256) so the
    provenance of the chosen text and of its duplicates stays inspectable.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from corpus import split_sections  # noqa: E402


def rank(r: dict) -> tuple:
    if r["dataset"] == "12":
        return (0, r["archive"], r["member"])
    return (1 if "/01.원천데이터/" in r["archive"] else 2, r["archive"], r["member"])


def main(scan_dir: str, out_path: str) -> None:
    d, out = Path(scan_dir), Path(out_path)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for line in (d / "members.jsonl").open():
        r = json.loads(line)
        if r.get("kind") == "precedent_fulltext" and r.get("category") == "형사":
            groups[r["serial"]].append(r)
    chosen = {s: sorted(g, key=rank)[0] for s, g in groups.items()}
    want = {r["sha256"]: s for s, r in chosen.items()}
    texts: dict[str, str] = {}
    for ds in ("12", "115"):
        for line in (d / "texts" / f"{ds}.jsonl").open():
            t = json.loads(line)
            if t["sha256"] in want and want[t["sha256"]] not in texts:
                texts[want[t["sha256"]]] = t["text"]
    stats = collections.Counter()
    with out.open("w") as f:
        for s, r in sorted(chosen.items()):
            text = texts[s]
            anon = r["dataset"] == "12"
            stats["from_12" if anon else ("from_115_TS" if "/01.원천데이터/" in r["archive"] else "from_115_SbL")] += 1
            f.write(json.dumps({
                "source_id": f"serial:{s}", "serial": s, "case_no": r["case_no"], "court": r["court"], "date": r["date"],
                "cat": r["category"], "case_name": r.get("case_name", ""), "text": text,
                "sections": [[x.title, x.start, x.end] for x in split_sections(text)],
                "anonymized_source": anon, "display_ok": anon,
                "locator": {"dataset": r["dataset"], "archive": r["archive"], "member": r["member"], "sha256": r["sha256"]},
                "copies": [{k: c[k] for k in ("dataset", "archive", "member", "sha256")} for c in sorted(groups[s], key=rank)],
            }, ensure_ascii=False) + "\n")
    stats["serials"] = len(chosen)
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
