"""Split 【법령의 적용】 into the court's own sentencing steps and resolve cited articles.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/annotate/law_application.py RUN_DIR [--articles data/private/statutes/kb_articles.jsonl]

* Steps are the headings the court writes (해당법조·형의 선택, 경합범가중, 작량감경,
  집행유예 …). Text between two headings belongs to the earlier step.
* Articles: "<법명> 제N조(의M) [제K항]" with the last named law carried forward for
  bare "제N조" and for 같은 법/동법. Every article keeps its span.
* Resolution: (law, article) → AI-Hub KB article (title, paragraphs, version date).
  The KB holds one version per law, so `kb.version_relation` says whether that version
  is dated after the decision (text may differ) — it is context, never the applied text.
Outputs RUN_DIR/law_application.jsonl and law_application_summary.json.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STEPS = [
    ("offense_and_choice", r"범죄사실에\s*대한\s*해당\s*법조|해당\s*법조|형의\s*선택"),
    ("imaginative_concurrence", r"상상적\s*경합"),
    ("repeat_aggravation", r"누범\s*가중"),
    ("concurrent_aggravation", r"경합범\s*(?:가중|처리)"),
    ("legal_mitigation", r"법률상\s*감경|(?:심신미약|미수|자수|종범)\s*감경"),
    ("discretionary_mitigation", r"작량\s*감경|정상참작\s*감경"),
    ("suspension", r"집행\s*유예"),
    ("probation_service", r"보호관찰|사회봉사|수강명령"),
    ("detention_credit", r"미결\s*구금\s*일수(?:의)?\s*(?:산입|통산)|미결구금일수"),
    ("workhouse", r"노역장\s*유치"),
    ("provisional_payment", r"가납\s*명령"),
    ("confiscation", r"몰수|추징"),
]
HEAD = re.compile("|".join(f"(?P<{k}>{p})" for k, p in STEPS))
# Article numbers are found first; the law name is read from a short window before each
# number (anchored at its end), which avoids catastrophic backtracking on long Hangul runs
# (2026-11-16: the earlier single regex with nested repetition hung on real judgments).
ART_NO = re.compile(r"제\s*(?P<no>\d+)\s*조(?:\s*의\s*(?P<br>\d+))?(?:\s*제\s*(?P<para>\d+)\s*항)?")
PAREN_TAIL = re.compile(r"\([^()]*(?:\([^()]*\)[^()]*)*\)\s*$")
LAW_TAIL = re.compile(r"(?P<law>(?:구\s*)?[가-힣ㆍ·][가-힣ㆍ·\s]{0,60}?(?:법률|특례법|법))\s*$")
SAME_TAIL = re.compile(r"(?:같은\s*법|동법)\s*$")


def law_before(seg: str, pos: int) -> tuple[str | None, bool]:
    """(law name or None, is_same_law_reference) for the text just before an article number."""
    w = seg[max(0, pos - 90):pos].rstrip()
    w = PAREN_TAIL.sub("", w).rstrip()
    if SAME_TAIL.search(w):
        return None, True
    m = LAW_TAIL.search(w)
    return (m.group("law").split(",")[-1].strip() if m else None), False
# Headings and connective words that can precede a law name inside 【법령의 적용】 (2026-11-16 fix:
# "경합범의처리형법", "각형법" were read as law names).
LEAD = re.compile(r"^(?:(?:범죄사실에대한)?해당법조(?:및형의선택)?|형의선택|경합범(?:의처리|가중|처리)?|상상적경합|누범가중|법률상감경|작량감경|정상참작감경|"
                  r"집행유예|보호관찰|사회봉사(?:명령)?|수강명령|미결구금일수(?:의)?(?:산입|통산)|노역장유치|가납명령|몰수|추징|선택형|각각|각|모두|및|또는|이상|판시)+")
KNOWN_LAWS: set[str] = set()  # filled from the KB article index in main()


def norm_law(name: str) -> str:
    n = re.sub(r"\s+", "", name or "")
    n = re.sub(r"^[·ㆍ,]+", "", n)
    n = re.sub(r"^구", "", n)
    n = LEAD.sub("", n)
    n = re.sub(r"^구", "", n)
    # prefer the longest known law name that the string ends with (keeps names containing 및)
    for k in sorted(KNOWN_LAWS, key=len, reverse=True):
        if n.endswith(k):
            return k
    return n


def parse(doc: dict) -> dict | None:
    sec = [(s, e) for t, s, e in doc["sections"] if t == "법령의적용"]
    if not sec:
        return None
    s0, s1 = sec[0]
    text = doc["text"]
    body = text[s0:s1]
    heads = [(m.start(), m.end(), m.lastgroup) for m in HEAD.finditer(body)]
    if not heads or heads[0][0] > 0:
        heads.insert(0, (0, 0, "unlabeled"))
    steps, law = [], None
    for i, (hs, he, label) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(body)
        seg = body[he:end]
        arts = []
        for m in ART_NO.finditer(seg):
            raw_law, same = law_before(seg, m.start())
            if raw_law and not same:
                law = norm_law(raw_law)
            if not law:
                continue
            no = m.group("no") + (f"-{m.group('br')}" if m.group("br") else "")
            arts.append({"law": law, "article": no, "paragraph": m.group("para"),
                         "span": [s0 + he + m.start(), s0 + he + m.end()]})
        steps.append({"step": label, "heading": body[hs:he], "span": [s0 + hs, s0 + end], "articles": arts})
    return {"doc_id": doc["source_id"], "date": doc["date"], "steps": steps,
            "source_basis": "explicit_text", "verification_status": "unreviewed"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--cache", default=str(ROOT / "data/private/pipeline/merged_criminal_cache.jsonl"))
    ap.add_argument("--articles", default=str(ROOT / "data/private/statutes/kb_articles.jsonl"))
    a = ap.parse_args()
    run = Path(a.run)
    kb = {}
    for line in open(a.articles):
        r = json.loads(line)
        KNOWN_LAWS.add(re.sub(r"\s+", "", r["law"]))
    for line in open(a.articles):
        r = json.loads(line)
        kb[(norm_law(r["law"]), r["article"])] = r
    links = [json.loads(l) for l in (run / "links.jsonl").open()]
    ids = {x[k] for x in links if x["link_status"] != "auto_partial" and x.get("instance_pair", "1-2") == "1-2" for k in ("trial_id", "appeal_id")}
    rows, step_c, art_c, res_c, per_step = [], collections.Counter(), 0, collections.Counter(), collections.defaultdict(collections.Counter)
    for line in open(a.cache):
        d = json.loads(line)
        if d["source_id"] not in ids:
            continue
        r = parse(d)
        if not r:
            continue
        for st in r["steps"]:
            step_c[st["step"]] += 1
            for ar in st["articles"]:
                art_c += 1
                k = kb.get((ar["law"], ar["article"]))
                if k:
                    rel = "kb_version_after_decision" if k["version_date"] > d["date"] else "kb_version_on_or_before_decision"
                    ar["kb"] = {"title": k["title"], "version_date": k["version_date"], "version_relation": rel,
                                "paragraphs": k["paragraphs"], "source_basis": "contextual"}
                    res_c["resolved"] += 1
                    per_step[st["step"]][f'{ar["law"]} {k["title"]}'] += 1
                else:
                    ar["kb"] = {"status": "not_in_corpus", "reason": "law/article not in KB (132 laws, one version each)"}
                    res_c["not_in_kb"] += 1
        rows.append(r)
    with (run / "law_application.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"docs_with_section": len(rows), "docs_scanned": len(ids), "steps": dict(step_c.most_common()),
               "articles_cited": art_c, "resolution": dict(res_c),
               "top_kb_article_per_step": {s: c.most_common(3) for s, c in per_step.items()},
               "note": "step→article association is counted from the judgments, not assumed."}
    (run / "law_application_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
