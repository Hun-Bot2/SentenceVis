"""Cross-validate AI-Hub datasets against each other (data-to-data checks).

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/ingest/aihub_crosscheck.py data/private/aihub_scan/<scan_dir>

Input: members.jsonl and texts/ from aihub_scan.py. Output (same dir):
crosscheck.json (all rates) and crosscheck_mismatches.jsonl (every
disagreement with both values, for review). No legal judgment is made; these
checks only test whether independent AI-Hub records agree with each other.

A  label ↔ source inside a dataset (12: serial; 115: case number; 019: file name)
B  the same law.go.kr precedent (판례일련번호) delivered in several files/datasets
C  019 human annotation of the original judgment (org*) ↔ 【원심판결】 in the full text
D  019 annotation ↔ automatic trial↔appeal links built on the merged corpus
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/align"))
from corpus import split_sections  # noqa: E402
from link_pairs import build_links, normalize_court, own_numbers, parse_prior, split_priors  # noqa: E402

CRIMINAL_115 = ("형사",)


def rate(k: int, n: int) -> dict:
    return {"agree": k, "n": n, "rate": round(k / n, 4) if n else None}


def main(scan: str) -> None:
    d = Path(scan)
    M = [json.loads(x) for x in (d / "members.jsonl").open()]
    mism = (d / "crosscheck_mismatches.jsonl").open("w")
    res: dict = {}

    def miss(check: str, **kw) -> None:
        mism.write(json.dumps({"check": check, **kw}, ensure_ascii=False) + "\n")

    def compare(check: str, a: dict, b: dict, fields: list[str], key) -> dict:
        out = {}
        for f in fields:
            va, vb = a.get(f) or "", b.get(f) or ""
            if f == "court":
                va, vb = normalize_court(va), normalize_court(vb)
            ok = va == vb
            out[f] = ok
            if not ok:
                miss(check, key=key, field=f, a=va, b=vb, a_member=a["member"], b_member=b["member"])
        return out

    def tally(check: str, pairs: list[tuple[dict, dict]], fields: list[str], key) -> dict:
        agg = collections.Counter()
        for a, b in pairs:
            for f, ok in compare(check, a, b, fields, key(a)).items():
                agg[f] += ok
        return {f: rate(agg[f], len(pairs)) for f in fields}

    # ---- A1: dataset 12 label ↔ source by serial
    src12 = {r["serial"]: r for r in M if r["dataset"] == "12" and r.get("kind") == "precedent_fulltext"}
    lab12 = [r for r in M if r["dataset"] == "12" and r.get("kind") == "label_info"]
    pairs = [(l, src12[l["serial"]]) for l in lab12 if l["serial"] in src12]
    res["A1_12_label_source"] = {"labels": len(lab12), "sources_fulltext": len(src12), "joined_by_serial": len(pairs),
                                 "fields": tally("A1", pairs, ["case_no", "court", "date"], lambda r: r["serial"])}
    # ---- A2: dataset 115 label ↔ TS/VS precedent by case number
    ts115 = [r for r in M if r["dataset"] == "115" and r.get("kind") == "precedent_fulltext" and "/01.원천데이터/" in r["archive"]]
    by_case = collections.defaultdict(list)
    for r in ts115:
        by_case[r["case_no"]].append(r)
    lab115 = [r for r in M if r["dataset"] == "115" and r.get("kind") == "label_info"]
    pairs, ambiguous, unmatched = [], 0, 0
    for l in lab115:
        c = by_case.get(l["case_no"], [])
        c2 = [x for x in c if x["date"] == l["date"]] or c
        if len(c2) == 1:
            pairs.append((l, c2[0]))
        elif c2:
            ambiguous += 1
        else:
            unmatched += 1
    res["A2_115_label_source"] = {"labels": len(lab115), "sources_TS_VS": len(ts115), "joined_unique": len(pairs),
                                  "ambiguous": ambiguous, "unmatched": unmatched,
                                  "fields": tally("A2", pairs, ["court", "date"], lambda r: r["case_no"])}
    # ---- A3: dataset 019 annotation ↔ XML full text by file stem
    xml019 = {Path(r["member"]).stem: r for r in M if r["dataset"] == "019" and r.get("kind") == "xml_fulltext" and "판결문" in r["archive"]}
    ann019 = [r for r in M if r["dataset"] == "019" and r.get("kind") == "annotated_judgment"]
    pairs = [(a, xml019[Path(a["member"]).stem]) for a in ann019 if Path(a["member"]).stem in xml019]
    res["A3_019_annotation_xml"] = {"annotations": len(ann019), "xml_judgments": len(xml019), "joined_by_file": len(pairs),
                                    "fields": tally("A3", pairs, ["case_no"], lambda r: r["case_no"]),
                                    "xml_header_court_date_extracted": sum(1 for _, x in pairs if x.get("court") and x.get("date"))}
    # ---- B: same precedent serial across files/datasets
    groups = collections.defaultdict(list)
    for r in M:
        if r.get("kind") == "precedent_fulltext":
            groups[r["serial"]].append(r)
    multi = {s: g for s, g in groups.items() if len(g) > 1}
    where = collections.Counter("+".join(sorted({("12" if r["dataset"] == "12" else ("115-SbL" if "SbL" in r["archive"] else "115-TS")) for r in g})) for g in multi.values())
    agg, text_same, n = collections.Counter(), 0, 0
    for s, g in multi.items():
        base = g[0]
        for other in g[1:]:
            n += 1
            for f, ok in compare("B", base, other, ["case_no", "court", "date", "category"], s).items():
                agg[f] += ok
            same = base["text_sha"] == other["text_sha"]
            text_same += same
            if not same:
                miss("B", key=s, field="text_sha", a=base["text_len"], b=other["text_len"], a_member=base["member"], b_member=other["member"])
    res["B_same_serial"] = {"distinct_serials": len(groups), "serials_in_multiple_files": len(multi), "where": dict(where),
                            "comparisons": n, "fields": {f: rate(agg[f], n) for f in ["case_no", "court", "date", "category"]},
                            "text_identical": rate(text_same, n)}
    # ---- unique criminal corpus (12 ∪ 115), first file per serial, texts loaded
    crim = {}
    for s, g in groups.items():
        r = sorted(g, key=lambda x: (x["dataset"] != "12", x["archive"]))[0]
        if r.get("category") in CRIMINAL_115:
            crim[s] = r
    need = {r["sha256"]: s for s, r in crim.items()}
    docs = {}
    for ds in ("12", "115"):
        for line in (d / "texts" / f"{ds}.jsonl").open():
            t = json.loads(line)
            s = need.get(t["sha256"])
            if s and s not in docs:
                r = crim[s]
                docs[s] = {"source_id": f"{r['dataset']}:{s}", "case_no": r["case_no"], "court": r["court"], "date": r["date"],
                           "text": t["text"], "sections": [[x.title, x.start, x.end] for x in split_sections(t["text"])]}
    res["criminal_corpus"] = {"unique_serials": len(crim), "texts_loaded": len(docs),
                              "by_dataset_of_first_copy": dict(collections.Counter(r["dataset"] for r in crim.values()))}
    # ---- C: 019 org annotation ↔ 【원심판결】 of the same judgment
    by_key = collections.defaultdict(list)
    for x in docs.values():
        by_key[(x["case_no"], x["date"])].append(x)
    ann_crim = [a for a in ann019 if a.get("category") == "2" and (a.get("org_case_no") or a.get("org_court"))]
    import re as _re
    c_found = c_case = c_court = c_date = 0
    for a in ann_crim:
        key = (_re.sub(r"^\(.*?\)", "", a["case_no"]), a["date"])
        hit = by_key.get(key)
        if not hit:
            continue
        doc = hit[0]
        sec = next((s for s in doc["sections"] if s[0] == "원심판결"), None)
        if not sec:
            continue
        c_found += 1
        refs = [parse_prior(p) for p in split_priors(doc["text"][sec[1]:sec[2]])]
        nums = {n for r in refs for n in r.case_nos + r.abbreviated}
        org_nums = set(_re.findall(r"\d{2,4}[가-힣]{1,3}\d+(?:-\d+)?", a["org_case_no"]))
        ok_case = bool(org_nums & nums)
        ok_court = any(normalize_court(r.court) == normalize_court(a["org_court"]) for r in refs)
        ok_date = any(r.date == a["org_date"] for r in refs)
        c_case += ok_case; c_court += ok_court; c_date += ok_date
        if not (ok_case and ok_court and ok_date):
            miss("C", key=a["case_no"], field="org_vs_prior", a={"org_case_no": a["org_case_no"], "org_court": a["org_court"], "org_date": a["org_date"]},
                 b=[{"court": r.court, "date": r.date, "case_nos": r.case_nos + r.abbreviated} for r in refs], a_member=a["member"], b_member=doc["source_id"])
    res["C_019_org_vs_prior_section"] = {"criminal_annotations_with_org": len(ann_crim), "matched_to_fulltext_with_prior": c_found,
                                         "case_no": rate(c_case, c_found), "court": rate(c_court, c_found), "date": rate(c_date, c_found)}
    # ---- D: 019 org annotation ↔ automatic links on merged corpus
    links, _ = build_links(list(docs.values()))
    acc = [l for l in links if l.link_status in ("auto_strict", "auto_alias")]
    by_appeal = collections.defaultdict(list)
    for l in acc:
        by_appeal[l.appeal_id].append(l)
    trial_meta = {x["source_id"]: x for x in docs.values()}
    d_n = d_agree = d_missed_present = d_missed_absent = 0
    org_index = {(x["case_no"]) for x in docs.values()}
    for a in ann_crim:
        key = (_re.sub(r"^\(.*?\)", "", a["case_no"]), a["date"])
        hit = by_key.get(key)
        if not hit or "노" not in key[0]:
            continue
        ls = by_appeal.get(hit[0]["source_id"], [])
        org_nums = set(_re.findall(r"\d{2,4}[가-힣]{1,3}\d+(?:-\d+)?", a["org_case_no"]))
        if ls:
            d_n += 1
            ok = any((own_numbers(trial_meta[l.trial_id]["case_no"]) & org_nums) and trial_meta[l.trial_id]["date"] == a["org_date"] for l in ls)
            d_agree += ok
            if not ok:
                miss("D", key=a["case_no"], field="link_vs_org", a=sorted(org_nums), b=[trial_meta[l.trial_id]["case_no"] for l in ls], a_member=a["member"], b_member=hit[0]["source_id"])
        elif any(org_nums & own_numbers(c) for c in org_index):
            d_missed_present += 1
            miss("D", key=a["case_no"], field="org_trial_in_corpus_but_not_linked", a=sorted(org_nums), b=None, a_member=a["member"], b_member=hit[0]["source_id"])
        else:
            d_missed_absent += 1
    res["D_019_org_vs_links"] = {"merged_corpus_links": dict(collections.Counter(l.link_status for l in links)),
                                 "accepted_links": len(acc), "accepted_appeals": len(by_appeal),
                                 "appeals_with_019_annotation_and_link": d_n, "link_agrees_with_019": rate(d_agree, d_n),
                                 "019_trial_in_corpus_but_not_linked": d_missed_present, "019_trial_not_in_corpus": d_missed_absent}
    mism.close()
    (d / "crosscheck.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
