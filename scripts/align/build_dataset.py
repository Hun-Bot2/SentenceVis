"""Build the private SentenScope pipeline snapshot from AI-Hub criminal judgments.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/align/build_dataset.py data/private/pipeline/<NEW_RUN_DIR>

Writes (refuses an existing directory):
    documents.jsonl   one row per criminal source judgment used (text kept private)
    links.jsonl       appeal↔trial link candidates with every check
    orders.jsonl      parsed 【주문】 per document in a link (rule_extracted)
    defendants.jsonl  defendant rows per accepted link (auto_single or needs_review)
    paths.jsonl       explicit reasoning cues from appeal 【이유】 (see extract_paths)
    summary.json      counts at every unit, by status
Nothing here is human-verified; every record carries verification_status.
"""
from __future__ import annotations

import collections
import re
import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "annotate"))

from corpus import Corpus  # noqa: E402
from extract_paths import extract_paths  # noqa: E402
from link_pairs import build_links  # noqa: E402
from parse_order import parse_order, single_defendant  # noqa: E402

ACCEPTED = ("auto_strict", "auto_alias")


def supreme_outcome(doc: dict) -> dict:
    """Procedural outcome of a 대법원 상고심 judgment from its 【주문】 (rule_extracted)."""
    import re
    sec = section(doc, "주문")
    if not sec:
        return {"actions": [], "issues": ["no_order_section"]}
    body = doc["text"][sec[0]:sec[1]]
    acts = []
    for m in re.finditer(r"원심판결(?:\s*중\s*([^.]*?)에\s*대한\s*(?:[가-힣]+\s*)?부분)?\s*을\s*파기하고[^.]*?(환송|이송)", body):
        acts.append({"action": "reversed_" + ("remanded" if m.group(2) == "환송" else "transferred"),
                     "scope": (m.group(1) or "all").strip(), "span": [sec[0] + m.start(), sec[0] + m.end()]})
    for m in re.finditer(r"([^.]*?)상고(?:를|는)?\s*(?:모두\s*|각\s*)?기각", body):
        pre = m.group(1)
        by = "쌍방" if ("검사" in pre and "피고인" in pre) else "검사" if "검사" in pre else "피고인" if "피고인" in pre else "unspecified"
        acts.append({"action": "dismissed", "by": by, "scope": pre.strip(), "span": [sec[0] + m.start(), sec[0] + m.end()]})
    return {"actions": acts, "issues": [] if acts else ["no_parse"], "source_basis": "rule_extracted", "verification_status": "unreviewed"}


def section(doc: dict, title: str) -> tuple[int, int] | None:
    for t, s, e in doc["sections"]:
        if t == title:
            return s, e
    return None


def load_docs(cache: Path | None) -> list[dict]:
    if cache and cache.exists():
        return [json.loads(line) for line in cache.read_text().splitlines()]
    c = Corpus()
    out = []
    for r in c.criminal_rows():
        j = c.load(r)
        out.append(
            {
                "source_id": j.source_id,
                "case_no": j.case_no,
                "court": j.court,
                "date": j.decision_date,
                "cat": j.category,
                "case_name": j.case_name,
                "text": j.text,
                "sections": [[s.title, s.start, s.end] for s in j.sections],
                "locator": j.locator,
            }
        )
    c.close()
    return out


def order_of(doc: dict) -> dict:
    sec = section(doc, "주문")
    if not sec:
        return {"issues": ["no_order_section"], "penalties": [], "suspensions": [], "appeal_actions": []}
    o = asdict(parse_order(doc["text"][sec[0] : sec[1]]))
    for group in ("penalties", "suspensions", "appeal_actions", "partial_outcomes"):
        for rec in o[group]:
            rec["span"] = [rec["span"][0] + sec[0], rec["span"][1] + sec[0]]
    hdr = section(doc, "피고인")
    o["single_defendant"] = single_defendant(
        doc["text"][hdr[0] : hdr[1]] if hdr else "", doc["text"][sec[0] : sec[1]]
    )
    return o


def outcome_for(order: dict, label: str) -> dict:
    """Penalties and suspension that name `label` or everyone ('*')."""
    pens = [p for p in order["penalties"] if label in p["defendants"] or "*" in p["defendants"]]
    susp = [s for s in order["suspensions"] if label in s["defendants"] or "*" in s["defendants"]]
    prison = [p for p in pens if p["kind"] in ("prison", "confinement")]
    return {
        "kinds": sorted({p["kind"] for p in pens}),
        "prison_months": prison[0]["months"] if len(prison) == 1 and prison[0]["kind"] == "prison" else None,
        "confinement_months": prison[0]["months"] if len(prison) == 1 and prison[0]["kind"] == "confinement" else None,
        "multi_term": len(prison) > 1,
        "fine_won": [p["fine_won"] for p in pens if p["kind"] == "fine"],
        "suspension_months": susp[0]["months"] if susp else None,
        "suspension_partial": susp[0].get("partial") if susp else None,
        "spans": [p["span"] for p in pens] + [s["span"] for s in susp],
    }


# Value-status vocabulary (docs/specs/DATA.md §결측 상태). Every displayed value carries
# exactly one status so that "no value" is never left as a bare null/empty list.
STATUSES = {
    "observed": "주문 원문에 명시된 값 (span 있음)",
    "derived": "원문 규칙으로 유도한 값 (예: 항소기각 → 원심 형 유지)",
    "absent_in_text": "주문을 해석했으나 해당 조항이 없음 (예: 집행유예 조항 없음). 파서 누락 가능성은 검증 대상",
    "not_applicable": "이 피고인의 형 종류에는 해당 항목이 없음 (벌금·무죄·금고 등)",
    "not_scalar": "값은 있으나 하나의 수로 만들 수 없음 (복수 형)",
    "not_extracted": "원문은 있으나 자동 추출 실패",
    "unresolved": "공동피고인 대응 등 사람 검토 전이라 값을 배정하지 않음",
    "not_in_corpus": "관련 판결이 로컬 AI-Hub 자료에 없음 (해당 절차가 없었다는 뜻이 아님)",
    "withheld": "자료는 있으나 개인정보 보호를 위해 원문 표시 보류",
}


def fv(value, status: str, reason: str | None = None, spans=None) -> dict:
    assert status in STATUSES, status
    out = {"value": value, "status": status}
    if reason:
        out["reason"] = reason
    if spans:
        out["spans"] = spans
    return out


def side_fields(o: dict, derived: bool) -> dict:
    ok = "derived" if derived else "observed"
    kinds = set(o.get("kinds", []))
    custodial = kinds & {"prison", "confinement"}
    if o["prison_months"] is not None:
        prison = fv(o["prison_months"], ok, spans=o.get("spans"))
    elif o.get("multi_term"):
        prison = fv(None, "not_scalar", "multi_term", o.get("spans"))
    elif o.get("confinement_months") is not None:
        prison = fv(None, "not_applicable", "confinement")
    elif kinds and not custodial:
        prison = fv(None, "not_applicable", "+".join(sorted(kinds)))
    else:
        prison = fv(None, "not_extracted", "no_parse")
    if o.get("suspension_months") is not None and o.get("suspension_partial"):
        susp = fv(o["suspension_months"], "not_scalar", f"partial_suspension:{o['suspension_partial']}", o.get("spans"))
    elif o.get("suspension_months") is not None:
        susp = fv(o["suspension_months"], ok, spans=o.get("spans"))
    elif custodial and prison["status"] in ("observed", "derived", "not_scalar"):
        susp = fv(None, "absent_in_text", "no_suspension_clause_found")
    elif kinds and not custodial:
        susp = fv(None, "not_applicable", "+".join(sorted(kinds)))
    else:
        susp = fv(None, "not_extracted", "no_parse")
    return {"prison_months": prison, "suspension_months": susp,
            "confinement_months": fv(o["confinement_months"], ok) if o.get("confinement_months") is not None else fv(None, "not_applicable" if kinds else "not_extracted")}


def supreme_field(entries: list) -> dict:
    if not entries:
        return fv(None, "not_in_corpus", "no_linked_supreme_judgment_in_aihub")
    acts = [a for e in entries for a in e.get("actions", [])]
    if not acts:
        return fv(None, "not_extracted", "supreme_order_unparsed")
    return fv([{"action": a["action"], "scope": a.get("scope", ""), "supreme_id": e["supreme_id"]} for e in entries for a in e["actions"]], "observed")


def defendant_rows(link: dict, trial: dict, appeal: dict, ot: dict, oa: dict) -> list[dict]:
    base = {
        "case_pair_id": f"{link['trial_id'][:12]}__{link['appeal_id'][:12]}",
        "trial_id": link["trial_id"],
        "appeal_id": link["appeal_id"],
        "link_status": link["link_status"],
        "source_basis": "rule_extracted",
        "verification_status": "unreviewed",
    }
    if not (ot.get("single_defendant") and oa.get("single_defendant")):
        labels = sorted(set(ot.get("defendant_labels", [])) | set(oa.get("defendant_labels", [])), key=int) or ["?"]
        unresolved = {k: fv(None, "unresolved", "co_defendant_alignment") for k in ("prison_months", "suspension_months", "confinement_months")}
        return [dict(base, defendant_id=f"{base['case_pair_id']}#{lab}", alignment="needs_review",
                     trial_label=lab, appeal_label=None, fields={"trial": dict(unresolved), "appeal": dict(unresolved)})
                for lab in labels]
    t = outcome_for(ot, "*")
    a = outcome_for(oa, "*")
    appeal_basis = "appeal_order"
    actions = {x["action"] for x in oa.get("appeal_actions", [])}
    if not a["kinds"] and "dismissed" in actions and "reversed" not in actions:
        a = dict(t, spans=[x["span"] for x in oa["appeal_actions"]])
        appeal_basis = "appeal_dismissal_derived"
    v1 = t["prison_months"] is not None and a["prison_months"] is not None and not (t["multi_term"] or a["multi_term"])
    reason = None if v1 else (
        "multi_term" if t["multi_term"] or a["multi_term"] else
        "non_prison_kind" if (t["kinds"] or a["kinds"]) else "no_parse")
    return [dict(base, defendant_id=f"{base['case_pair_id']}#1", alignment="auto_single",
                 trial_label="*", appeal_label="*", trial=t, appeal=a, appeal_basis=appeal_basis,
                 appeal_actions=oa.get("appeal_actions", []), v1_eligible=v1, v1_excluded_reason=reason,
                 fields={"trial": side_fields(t, False), "appeal": side_fields(a, appeal_basis == "appeal_dismissal_derived")})]


def main(out_dir: str, cache: str | None = None) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    docs = load_docs(Path(cache) if cache else None)
    by_id = {d["source_id"]: d for d in docs}
    links, unmatched = build_links(docs, include_supreme=True)
    links = [asdict(x) for x in links]
    accepted = [x for x in links if x["link_status"] in ACCEPTED and x["instance_pair"] == "1-2"]
    supreme_links = [x for x in links if x["link_status"] in ACCEPTED and x["instance_pair"] == "2-3"]
    supreme_by_appeal: dict = collections.defaultdict(list)
    for x in supreme_links:
        supreme_by_appeal[x["trial_id"]].append({"supreme_id": x["appeal_id"], "case_no": by_id[x["appeal_id"]]["case_no"],
                                                 "date": by_id[x["appeal_id"]]["date"], **supreme_outcome(by_id[x["appeal_id"]])})
    used = {x["trial_id"] for x in accepted} | {x["appeal_id"] for x in accepted}
    orders = {sid: order_of(by_id[sid]) for sid in used}
    rows: list[dict] = []
    for link in accepted:
        new = defendant_rows(link, by_id[link["trial_id"]], by_id[link["appeal_id"]],
                             orders[link["trial_id"]], orders[link["appeal_id"]])
        for r in new:
            # 대법원 outcome is attached per case pair; per-defendant scope is not resolved
            r["supreme"] = supreme_by_appeal.get(link["appeal_id"], [])
            r["display_ok"] = bool(by_id[link["trial_id"]].get("display_ok", True) and by_id[link["appeal_id"]].get("display_ok", True))
            r["fields"]["supreme_outcome"] = supreme_field(r["supreme"])
            r["fields"]["source_text"] = {side: fv(link[f"{side}_id"], "observed" if by_id[link[f"{side}_id"]].get("display_ok", True) else "withheld",
                                                     None if by_id[link[f"{side}_id"]].get("display_ok", True) else "unmasked_names_in_115_copy")
                                          for side in ("trial", "appeal")}
        rows += new
    unpaired = []
    for u in unmatched:
        a = by_id.get(u["appeal_id"])
        if not a or not re.match(r"^\d{2,4}노", a["case_no"]):
            continue
        oa = order_of(a)
        unpaired.append({"appeal_id": a["source_id"], "case_no": a["case_no"], "court": a["court"], "date": a["date"],
                         "reason": u["reason"], "priors": [p.get("raw") for p in u.get("priors", [])],
                         "fields": {"trial_judgment": fv(None, "not_in_corpus" if u["reason"] == "no_trial_doc_in_corpus" else "not_extracted", u["reason"]),
                                    "appeal_order_parsed": fv(not oa.get("issues"), "observed" if not oa.get("issues") else "not_extracted"),
                                    "supreme_outcome": supreme_field(supreme_by_appeal.get(a["source_id"], [])),
                                    "source_text": fv(a["source_id"], "observed" if a.get("display_ok", True) else "withheld")}})
    appeals = sorted({x["appeal_id"] for x in accepted})
    paths = []
    for aid in appeals:
        paths += extract_paths(by_id[aid])

    def dump(name: str, items) -> None:
        with (out / name).open("w") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")

    used |= {x["appeal_id"] for x in supreme_links}
    dump("documents.jsonl", ({k: by_id[s][k] for k in ("source_id", "case_no", "court", "date", "cat", "case_name", "sections")}
                             | {"locator": by_id[s].get("locator"), "display_ok": by_id[s].get("display_ok", True),
                                "copies": by_id[s].get("copies")} for s in sorted(used)))
    dump("links.jsonl", links)
    dump("unmatched_appeals.jsonl", unmatched)
    dump("orders.jsonl", ({"source_id": k, **v} for k, v in sorted(orders.items())))
    dump("defendants.jsonl", rows)
    dump("unpaired_appeals.jsonl", unpaired)
    dump("paths.jsonl", paths)
    year = lambda sid: by_id[sid]["date"][:4]  # noqa: E731
    summary = {
        "criminal_source_documents": len(docs),
        "appeal_documents": sum(1 for d in docs if "노" in d["case_no"]),
        "corpus_sources": collections.Counter((d.get("locator") or {}).get("dataset", "12") for d in docs),
        "link_candidates": collections.Counter(f'{x["instance_pair"]}:{x["link_status"]}' for x in links),
        "supreme_links_accepted": len(supreme_links),
        "case_pairs_with_supreme": sum(1 for x in accepted if x["appeal_id"] in supreme_by_appeal),
        "supreme_actions": collections.Counter(a["action"] for v in supreme_by_appeal.values() for s_ in v for a in s_["actions"]),
        "defendant_rows_display_ok": sum(1 for r in rows if r.get("display_ok")),
        "accepted_links": len(accepted),
        "accepted_links_by_basis": collections.Counter(x["basis"] for x in accepted),
        "accepted_appeals": len(appeals),
        "accepted_appeals_by_year": dict(sorted(collections.Counter(year(a) for a in appeals).items())),
        "unmatched_appeals": collections.Counter(u["reason"] for u in unmatched),
        "defendant_rows": collections.Counter(r["alignment"] for r in rows),
        "v1_eligible_rows": sum(1 for r in rows if r.get("v1_eligible")),
        "v1_excluded": collections.Counter(r.get("v1_excluded_reason") for r in rows if r["alignment"] == "auto_single" and not r["v1_eligible"]),
        "appeal_basis": collections.Counter(r.get("appeal_basis") for r in rows if r["alignment"] == "auto_single"),
        "path_cues": collections.Counter(p["cue_type"] for p in paths),
        "appeals_with_any_path_cue": len({p["appeal_id"] for p in paths}),
        "field_status": {
            path: dict(collections.Counter(get(r) for r in rows))
            for path, get in {
                "trial.prison_months": lambda r: r["fields"]["trial"]["prison_months"]["status"],
                "trial.suspension_months": lambda r: r["fields"]["trial"]["suspension_months"]["status"],
                "appeal.prison_months": lambda r: r["fields"]["appeal"]["prison_months"]["status"],
                "appeal.suspension_months": lambda r: r["fields"]["appeal"]["suspension_months"]["status"],
                "supreme_outcome": lambda r: r["fields"]["supreme_outcome"]["status"],
                "source_text.trial": lambda r: r["fields"]["source_text"]["trial"]["status"],
                "source_text.appeal": lambda r: r["fields"]["source_text"]["appeal"]["status"],
            }.items()
        },
        "unpaired_appeals": {"total": len(unpaired), "by_trial_status": dict(collections.Counter(u["fields"]["trial_judgment"]["status"] for u in unpaired)),
                             "supreme": dict(collections.Counter(u["fields"]["supreme_outcome"]["status"] for u in unpaired)),
                             "source_text": dict(collections.Counter(u["fields"]["source_text"]["status"] for u in unpaired))},
        "status_vocabulary": STATUSES,
        "human_verified": 0,
        "note": "All counts are automatic (rule_extracted, unreviewed). Not verified observations.",
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
