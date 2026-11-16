"""Export a LOCAL prototype dataset for the V1/V2 views (not a public export).

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/publish/export_prototype.py RUN_DIR data/private/export/prototype.json

Privacy and provenance rules:
  * Output stays under data/private (git-ignored) and is served only by the Vite dev server.
  * Sentences are included only for documents with display_ok (dataset-12 anonymized copy);
    other documents get text = null and status 'withheld' (D-015, AIHUB_CROSS_VALIDATION §4).
  * Every value keeps its {value, status, reason} block from the pipeline; nothing is filled in.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/private/pipeline/merged_criminal_cache.jsonl"
STEP_KO = {"offense_and_choice": "해당법조·형의 선택", "imaginative_concurrence": "상상적 경합", "repeat_aggravation": "누범가중",
           "concurrent_aggravation": "경합범가중", "legal_mitigation": "법률상 감경", "discretionary_mitigation": "작량감경",
           "suspension": "집행유예", "probation_service": "보호관찰·사회봉사", "detention_credit": "미결구금 산입",
           "workhouse": "노역장 유치", "provisional_payment": "가납명령", "confiscation": "몰수·추징", "unlabeled": "(단계 표시 없음)"}
FACTOR_KO = {"no_punishment_wish": "처벌불원", "settlement": "합의", "deposit": "공탁", "damage_recovery": "피해 회복",
             "remorse": "반성", "no_record": "형사처벌 전력 없음", "same_type_record": "동종 전과", "repeat_offender": "누범",
             "diminished_capacity": "심신미약", "surrender": "자수", "minor_role": "소극 가담", "planned": "계획적 범행",
             "vulnerable_victim": "취약한 피해자", "serious_harm": "중한 피해", "victim_wants_punishment": "엄벌 탄원",
             "accidental": "우발적", "age_health_family": "연령·건강·부양", "art51_conditions": "형법 제51조 문구"}
GENERAL = {"30", "37", "38", "39", "40", "50", "53", "55", "57", "62", "62-2", "69", "70", "35", "48", "56", "51"}


def jl(p: Path):
    return [json.loads(x) for x in p.open() if x.strip()]


def sentence(text: str, span) -> str:
    s, e = span
    return text[s:e].strip()[:240]


def main(run: str, out: str) -> None:
    run_dir, out_p = Path(run), Path(out)
    out_p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    links = jl(run_dir / "links.jsonl")
    acc = [x for x in links if x["link_status"] != "auto_partial" and x.get("instance_pair", "1-2") == "1-2"]
    need = {x[k] for x in acc for k in ("trial_id", "appeal_id")}
    docs = {}
    for line in CACHE.open():
        d = json.loads(line)
        if d["source_id"] in need:
            docs[d["source_id"]] = d
    rows = jl(run_dir / "defendants.jsonl")
    cues = collections.defaultdict(list)
    for c in jl(run_dir / "paths.jsonl"):
        cues[c["appeal_id"]].append(c)
    la = {d["doc_id"]: d for d in jl(run_dir / "law_application.jsonl")}
    sf = collections.defaultdict(list)
    for c in jl(run_dir / "sentencing_factors.jsonl"):
        sf[c["doc_id"]].append(c)
    orders = {o["source_id"]: o for o in jl(run_dir / "orders.jsonl")}

    def head(i):
        d = docs[i]
        return {"id": i, "case_no": d["case_no"], "court": d["court"], "date": d["date"], "display_ok": d.get("display_ok", True)}

    def txt(i, span):
        d = docs[i]
        return sentence(d["text"], span) if d.get("display_ok", True) else None

    def terms(i):
        """Separate prison terms named in the 주문 for a single-defendant document (not_scalar rows)."""
        o = orders.get(i, {})
        return [{"months": p["months"], "span": p["span"]} for p in o.get("penalties", [])
                if p["kind"] == "prison" and p.get("months") is not None]

    def grounds(a):
        return sorted({c["label"] for c in cues[a] if c["cue_type"] == "ground" and c["in_grounds_summary"]})

    def result(a):
        acts = {x["action"] for x in orders.get(a, {}).get("appeal_actions", [])}
        return "파기" if "reversed" in acts else "기각" if "dismissed" in acts else "불명"

    def offense(i):
        return {(a["law"], a["article"]) for s in la[i]["steps"] if s["step"] == "offense_and_choice"
                for a in s["articles"] if not (a["law"] == "형법" and a["article"] in GENERAL)} if i in la else None

    pairs, appeals = [], {}
    by_pair = collections.defaultdict(list)
    for r in rows:
        by_pair[(r["trial_id"], r["appeal_id"])].append(r)
    for x in acc:
        t, a = x["trial_id"], x["appeal_id"]
        rs = by_pair.get((t, a), [])
        if not rs:
            continue
        aligned = [r for r in rs if r["alignment"] == "auto_single"]
        pairs.append({
            "id": rs[0]["case_pair_id"], "trial": head(t), "appeal": head(a), "link_status": x["link_status"],
            "defendants": [{"id": r["defendant_id"], "fields": r["fields"], "appeal_basis": r.get("appeal_basis"),
                            "terms": {"trial": terms(t), "appeal": terms(a)}} for r in aligned],
            "unresolved_count": len(rs) - len(aligned),
            "supreme": rs[0]["fields"]["supreme_outcome"],
            "k1": "+".join(grounds(a)) or "(항소이유 미확인)",
            "k2": f'{result(a)}·{"직권 있음" if any(c["cue_type"] == "ex_officio" for c in cues[a]) else "직권 없음"}',
        })
        if a in appeals:
            continue
        cs = sorted(cues[a], key=lambda c: c["span"][0])
        tsec, asec = offense(t), offense(a)
        appeals[a] = {
            "case_no": docs[a]["case_no"], "display_ok": docs[a].get("display_ok", True),
            "grounds": [{"label": c["label"], "origin": c["origin_hint"] or "미상", "in_summary": c["in_grounds_summary"],
                         "span": c["span"], "text": txt(a, c["sentence_span"])} for c in cs if c["cue_type"] == "ground"],
            "dispositions": [{"type": c["cue_type"], "target": (c.get("relation") or {}).get("target_label"),
                              "basis": (c.get("relation") or {}).get("basis"), "span": c["span"], "text": txt(a, c["sentence_span"])}
                             for c in cs if c["cue_type"] in ("accepted", "rejected", "not_reached", "reversal")],
            "ex_officio": [{"span": c["span"], "text": txt(a, c["sentence_span"])} for c in cs if c["cue_type"] == "ex_officio"],
            "steps": [{"step": s["step"], "label": STEP_KO.get(s["step"], s["step"]),
                       "articles": [{"law": ar["law"], "article": ar["article"],
                                     "title": (ar.get("kb") or {}).get("title"), "version_date": (ar.get("kb") or {}).get("version_date"),
                                     "kb_status": "contextual" if (ar.get("kb") or {}).get("title") else "not_in_corpus",
                                     "first_paragraph": ((ar.get("kb") or {}).get("paragraphs") or [None])[0]} for ar in s["articles"]]}
                      for s in (la[a]["steps"] if a in la else [])],
            "steps_status": "observed" if a in la else "absent_in_text",
            "factors": [{"factor": c["factor"], "label": FACTOR_KO.get(c["factor"], c["factor"]), "polarity": c["polarity_in_sentence"],
                         "span": c["span"], "text": txt(a, c["sentence_span"])} for c in sf.get(a, [])],
            "factor_status": ("observed" if sf.get(a) else
                              ("not_extracted" if any(tt in ("양형의이유", "양형이유") for tt, _, _ in docs[a]["sections"]) else "absent_in_text")),
            "statute_change": None if (tsec is None or asec is None) else
                {"removed": sorted(f"{l} 제{n}조" for l, n in tsec - asec), "added": sorted(f"{l} 제{n}조" for l, n in asec - tsec),
                 "status": "rule_extracted_unreviewed"},
        }
    # V3: section structure for every document of an accepted pair; text only when display_ok.
    documents = {}
    for i, d in docs.items():
        ok = d.get("display_ok", True)
        documents[i] = {"case_no": d["case_no"], "court": d["court"], "date": d["date"], "display_ok": ok, "length": len(d["text"]),
                        "sections": [{"title": tt, "start": st, "end": en} for tt, st, en in d["sections"]],
                        "text": d["text"] if ok else None}
    k1 = collections.Counter(p["k1"] for p in pairs)
    k2 = collections.Counter(p["k2"] for p in pairs)
    data = {"meta": {"run": str(run_dir), "note": "LOCAL prototype export. Automatic candidates, human_verified = 0.",
                     "pairs": len(pairs), "appeals": len(appeals), "k1_counts": k1, "k2_counts": k2},
            "pairs": pairs, "appeals": appeals, "documents": documents}
    out_p.write_text(json.dumps(data, ensure_ascii=False))
    print(json.dumps({"pairs": len(pairs), "appeals": len(appeals), "bytes": out_p.stat().st_size,
                      "defendant_rows": sum(len(p["defendants"]) for p in pairs),
                      "withheld_appeals": sum(1 for v in appeals.values() if not v["display_ok"])}, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:])
