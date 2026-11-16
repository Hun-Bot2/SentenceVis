"""Draw a fixed-seed random labeling sample from a pipeline run.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/annotate/make_sample.py RUN_DIR OUT_DIR [--seed 20261116]

Tasks (simple random samples without replacement inside each frame, so
precision estimates generalize to that frame only — not to Korean courts):
  link       accepted 1심→항소심 links (auto_strict/auto_alias) n=40
  link_part  rejected-by-rule 1심→항소심 links (auto_partial)  all
  supreme    accepted 항소심→대법원 links + parsed outcome    n=20
  v1         V1-eligible defendant rows                       n=30
  cue        reasoning cues, stratified by cue_type           n=10 per type
  doc        appeal documents for set-level recall of grounds n=15
Text excerpts are copied for the local labeling tool only (private dir).
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

N = {"link": 40, "supreme": 20, "v1": 30, "cue_per_type": 10, "doc": 15}


def read(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def excerpt(doc: dict, title: str, limit: int = 4000) -> dict:
    for t, s, e in doc["sections"]:
        if t == title:
            return {"title": title, "start": s, "text": doc["text"][s : min(e, s + limit)], "truncated": e - s > limit}
    return {"title": title, "start": None, "text": "", "truncated": False}


def window(doc: dict, span: list[int], pad: int = 600) -> dict:
    s, e = max(0, span[0] - pad), min(len(doc["text"]), span[1] + pad)
    return {"start": s, "text": doc["text"][s:e], "hl": [span[0] - s, span[1] - s]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=20261116)
    ap.add_argument("--cache", default="data/private/pipeline/merged_criminal_cache.jsonl")
    a = ap.parse_args()
    run, out = Path(a.run), Path(a.out)
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    rng = random.Random(a.seed)
    docs = {d["source_id"]: d for d in read(Path(a.cache))}
    links = read(run / "links.jsonl")
    rows = read(run / "defendants.jsonl")
    cues = read(run / "paths.jsonl")
    items: list[dict] = []

    def head(d: dict) -> dict:
        return {k: d[k] for k in ("source_id", "case_no", "court", "date", "case_name")}

    sup = [x for x in links if x["link_status"] in ("auto_strict", "auto_alias") and x.get("instance_pair") == "2-3"]
    links = [x for x in links if x.get("instance_pair", "1-2") == "1-2"]
    acc = [x for x in links if x["link_status"] in ("auto_strict", "auto_alias")]
    sup_out = {}
    for r in rows:
        for s_ in r.get("supreme", []):
            sup_out[s_["supreme_id"]] = s_["actions"]
    for i, x in enumerate(rng.sample(acc, min(N["link"], len(acc)))):
        items.append({"item_id": f"link-{i:03d}", "task": "link", "frame": "accepted_links", "frame_size": len(acc), "record": x,
                      "trial": head(docs[x["trial_id"]]), "appeal": head(docs[x["appeal_id"]]),
                      "views": [excerpt(docs[x["appeal_id"]], "원심판결"), excerpt(docs[x["trial_id"]], "주문"), excerpt(docs[x["appeal_id"]], "주문")]})
    part = [x for x in links if x["link_status"] == "auto_partial"]
    for i, x in enumerate(part):
        items.append({"item_id": f"part-{i:03d}", "task": "link", "frame": "partial_links", "frame_size": len(part), "record": x,
                      "trial": head(docs[x["trial_id"]]), "appeal": head(docs[x["appeal_id"]]),
                      "views": [excerpt(docs[x["appeal_id"]], "원심판결"), excerpt(docs[x["trial_id"]], "주문"), excerpt(docs[x["appeal_id"]], "주문")]})
    for i, x in enumerate(rng.sample(sup, min(N["supreme"], len(sup)))):
        items.append({"item_id": f"sup-{i:03d}", "task": "link", "frame": "supreme_links", "frame_size": len(sup),
                      "record": dict(x, parsed_outcome=[a["action"] + (":" + a.get("scope", "")[:30]) for a in sup_out.get(x["appeal_id"], [])]),
                      "trial": head(docs[x["trial_id"]]), "appeal": head(docs[x["appeal_id"]]),
                      "views": [excerpt(docs[x["appeal_id"]], "원심판결"), excerpt(docs[x["appeal_id"]], "주문")]})
    v1 = [r for r in rows if r.get("v1_eligible")]
    for i, r in enumerate(rng.sample(v1, min(N["v1"], len(v1)))):
        items.append({"item_id": f"v1-{i:03d}", "task": "v1", "frame": "v1_eligible_rows", "frame_size": len(v1), "record": r,
                      "trial": head(docs[r["trial_id"]]), "appeal": head(docs[r["appeal_id"]]),
                      "views": [excerpt(docs[r["trial_id"]], "주문"), excerpt(docs[r["appeal_id"]], "주문")]})
    types = sorted({c["cue_type"] for c in cues})
    for t in types:
        frame = [c for c in cues if c["cue_type"] == t]
        for i, c in enumerate(rng.sample(frame, min(N["cue_per_type"], len(frame)))):
            d = docs[c["appeal_id"]]
            items.append({"item_id": f"cue-{t}-{i:02d}", "task": "cue", "frame": f"cue:{t}", "frame_size": len(frame), "record": c,
                          "appeal": head(d), "views": [dict(window(d, c["span"]), title="이유 (발췌)")]})
    appeal_ids = sorted({x["appeal_id"] for x in acc})
    for i, aid in enumerate(rng.sample(appeal_ids, min(N["doc"], len(appeal_ids)))):
        d = docs[aid]
        found = sorted({c["label"] for c in cues if c["appeal_id"] == aid and c["cue_type"] == "ground" and c["in_grounds_summary"]})
        items.append({"item_id": f"doc-{i:02d}", "task": "doc", "frame": "accepted_appeals", "frame_size": len(appeal_ids),
                      "record": {"appeal_id": aid, "extracted_grounds": found,
                                 "extracted_ex_officio": any(c["appeal_id"] == aid and c["cue_type"] == "ex_officio" for c in cues)},
                      "appeal": head(d), "views": [excerpt(d, "주문"), excerpt(d, "이유", 12000)]})
    (out / "items.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items))
    meta = {"run": str(run), "seed": a.seed, "sizes": N, "counts": {}}
    for x in items:
        meta["counts"][x["frame"]] = meta["counts"].get(x["frame"], 0) + 1
    (out / "sample_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
