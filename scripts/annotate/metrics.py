"""Accuracy of automatic extraction against the reviewer's labels.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/annotate/metrics.py data/private/labeling/<sample> [--json OUT]

Method: each estimate is a proportion over the labeled items of one sample
frame (simple random sample, fixed seed) with a 95% Wilson score interval.
`unsure` answers are excluded from the denominator and reported. Estimates
describe that frame of this run only. One reviewer → no inter-annotator
agreement can be reported; say so wherever these numbers are used.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

Z = 1.959963984540054  # 95%


def wilson(k: int, n: int) -> dict:
    if n == 0:
        return {"k": 0, "n": 0, "p": None, "lo": None, "hi": None}
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return {"k": k, "n": n, "p": round(p, 4), "lo": round(max(0.0, c - h), 4), "hi": round(min(1.0, c + h), 4)}


def proportion(answers: list[str]) -> dict:
    yes = sum(a == "yes" for a in answers)
    no = sum(a == "no" for a in answers)
    out = wilson(yes, yes + no)
    out["unsure"] = sum(a == "unsure" for a in answers)
    out["na"] = sum(a == "na" for a in answers)
    return out


def compute(sample: Path) -> dict:
    items = {x["item_id"]: x for x in map(json.loads, (sample / "items.jsonl").read_text().splitlines())}
    latest: dict[str, dict] = {}
    lp = sample / "labels.jsonl"
    if lp.exists():
        for line in lp.read_text().splitlines():
            rec = json.loads(line)
            latest[rec["item_id"]] = rec
    by: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for iid, lab in latest.items():
        it = items[iid]
        by[it["frame"]].append((it, lab["answer"]))
    res: dict = {"labeled": len(latest), "items": len(items),
                 "reviewers": sorted({x["reviewer"] for x in latest.values()}), "frames": {}}
    for frame, pairs in sorted(by.items()):
        task = pairs[0][0]["task"]
        r: dict = {"task": task, "frame_size": pairs[0][0]["frame_size"], "labeled": len(pairs)}
        if task == "link":
            key = "actually_correct_rate" if frame == "partial_links" else "precision"
            r[key] = proportion([a.get("link") for _, a in pairs])
            if frame == "supreme_links":
                r["outcome_precision"] = proportion([a.get("outcome") for _, a in pairs])
        elif task == "v1":
            for k in ("same_person", "trial_months", "trial_susp", "appeal_months", "appeal_susp"):
                r[k] = proportion([a.get(k) for _, a in pairs])
            full = [a for _, a in pairs if all(a.get(k) in ("yes", "no") for k in ("same_person", "trial_months", "trial_susp", "appeal_months", "appeal_susp"))]
            r["row_all_correct"] = wilson(sum(all(a[k] == "yes" for k in ("same_person", "trial_months", "trial_susp", "appeal_months", "appeal_susp")) for a in full), len(full))
        elif task == "cue":
            r["type_precision"] = proportion([a.get("type") for _, a in pairs])
            r["origin_precision"] = proportion([a.get("origin") for _, a in pairs])
            r["relation_precision"] = proportion([a.get("relation") for _, a in pairs])
        elif task == "doc":
            tp = fp = fn = 0
            ex = []
            for it, a in pairs:
                gold = set(a.get("grounds", [])) - {"기타"}
                pred = set(it["record"]["extracted_grounds"])
                tp += len(gold & pred); fp += len(pred - gold); fn += len(gold - pred)
                if a.get("ex_officio") in ("yes", "no"):
                    ex.append("yes" if (a["ex_officio"] == "yes") == it["record"]["extracted_ex_officio"] else "no")
            r["ground_set_precision"] = wilson(tp, tp + fp)
            r["ground_set_recall"] = wilson(tp, tp + fn)
            r["ex_officio_agreement"] = proportion(ex)
            r["note"] = "micro-averaged over (document, ground type) pairs; 기타 excluded (no extractor class)"
        res["frames"][frame] = r
    res["caveats"] = [
        "Simple random samples within each frame of one pipeline run; not Korean courts at large.",
        "AI-Hub corpus is not a probability sample of appeals.",
        "Single reviewer: no inter-annotator agreement." if len(res["reviewers"]) <= 1 else "Multiple reviewers: compute agreement separately.",
        "Reviewer judgment is not legal-expert certification unless the reviewer is one.",
    ]
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sample")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = compute(Path(a.sample))
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.json:
        Path(a.json).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
