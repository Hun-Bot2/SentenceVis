"""Sentencing-factor cues grounded in the 양형위원회 guideline document and found in judgments.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/annotate/sentencing_factors.py RUN_DIR [--cache data/private/pipeline/merged_criminal_cache.jsonl]

1. Grounding: each lexicon factor must occur in 양형기준의결.pdf (local PDF text index
   data/interim/pdf_pages.sqlite3). Only page locators are retained. PDF headings
   never determine factor polarity.
2. Extraction: phrases are searched only where the court is talking about sentencing:
   the 【양형의 이유】/【양형이유】 sections, or a sentence of 【이유】 that also mentions
   정상/양형/형을 정함. Each cue keeps its span and sentence span (explicit_text_cue).
   Polarity in the judgment comes from the sentence itself when it says 유리한/불리한
   정상; otherwise it is left `unstated` (no guideline polarity is inferred).
Nothing here says a factor *caused* a sentence change; it records what the court wrote.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_DB = ROOT / "data/interim/pdf_pages.sqlite3"

# factor id, guideline wording (searched in the PDF), judgment patterns, guideline group
LEXICON = [
    ("no_punishment_wish", r"처벌\s*불원", r"처벌을\s*원하지\s*(?:않|아니)|처벌\s*불원|선처를\s*(?:탄원|바라)", "행위자/기타"),
    ("settlement", r"합의", r"(?:피해자|유족)[^.]{0,20}합의(?:하였|한|가\s*이루어|되었)|합의서", "행위자/기타"),
    ("deposit", r"공탁", r"공탁(?:하였|한|금)", "행위자/기타"),
    ("damage_recovery", r"피해\s*회복", r"피해(?:를|가)?\s*(?:상당\s*부분\s*)?회복|피해\s*변제|변제하였", "행위자/기타"),
    ("remorse", r"진지한\s*반성", r"반성하(?:고|는)|뉘우치", "행위자/기타"),
    ("no_record", r"형사처벌\s*전력\s*없음", r"초범|(?:형사처벌|처벌)\s*(?:받은\s*)?전력이\s*없|전과가\s*없", "행위자/기타"),
    ("same_type_record", r"동종\s*(?:범죄|누범|전과)", r"동종\s*(?:범죄로\s*인한\s*)?(?:전과|전력|범행으로)", "행위자/기타"),
    ("repeat_offender", r"누범", r"누범", "행위자/기타"),
    ("diminished_capacity", r"심신미약", r"심신\s*미약", "행위"),
    ("surrender", r"자수", r"자수(?:하였|한)", "행위자/기타"),
    ("minor_role", r"소극\s*가담", r"소극\s*가담|가담\s*정도가\s*(?:경미|가볍)", "행위"),
    ("planned", r"계획적", r"계획적", "행위"),
    ("vulnerable_victim", r"취약한\s*피해자", r"취약한\s*피해자|(?:나이\s*)?어린\s*피해자|장애인인?\s*피해자|아동인?\s*피해자", "행위"),
    ("serious_harm", r"중한\s*상해|중대한\s*피해", r"중한\s*상해|중대한\s*피해|피해가\s*(?:크|막대)", "행위"),
    ("victim_wants_punishment", r"엄벌", r"엄벌을\s*(?:탄원|원)|엄한\s*처벌을\s*원", "행위자/기타"),
    ("accidental", r"우발적", r"우발적", "행위"),
    ("age_health_family", r"연령|건강|부양", r"고령|\d{2}세(?:를|가)?\s*넘|나이가\s*(?:많|어린)|건강(?:이|상태가)\s*(?:좋지|나쁘|악화)|지병|앓고|부양(?:하여야|해야|할)\s*(?:할\s*)?가족|부양가족", "일반"),
    # 형법 제51조(양형의 조건) wording reproduced by the court: a statutory checklist, not a specific finding
    ("art51_conditions", r"연령", r"연령\s*,\s*성행\s*,\s*지능과\s*환경", "형법 제51조"),
]
CONTEXT = re.compile(r"정상|양형|형을\s*정함|형의\s*양정|선처")
FAVOR = re.compile(r"유리한\s*정상")
DISFAVOR = re.compile(r"불리한\s*정상")


def grounding() -> dict:
    out = {}
    if not PDF_DB.exists():
        return out
    c = sqlite3.connect(f"file:{PDF_DB}?mode=ro", uri=True)
    pages = c.execute("select source_path, page, text from pages where source_path like '%양형기준의결%'").fetchall()
    for fid, gpat, _, group in LEXICON:
        hits = []
        for _, page, text in pages:
            for m in re.finditer(gpat, text):
                hits.append(page)
        out[fid] = {"guideline_pages": sorted(set(hits), key=lambda p: int(p) if str(p).isdigit() else 0)[:20],
                    "guideline_hits": len(hits), "guideline_polarity": None,
                    "guideline_polarity_note": "not inferred (PDF table layout makes heading-proximity unreliable)",
                    "guideline_grounding": "pdf" if hits else "none", "group": group,
                    "source": "data/양형기준의결.pdf (local PDF text index; page numbers as extracted)"}
    return out


def sentence_span(text: str, pos: int) -> tuple[int, int]:
    s = max(text.rfind(".", 0, pos), text.rfind("\n", 0, pos)) + 1
    e = text.find(".", pos)
    return s, (len(text) if e < 0 else e + 1)


def extract(doc: dict) -> list[dict]:
    text, cues = doc["text"], []
    zones = [(s, e, t) for t, s, e in doc["sections"] if t in ("양형의이유", "양형이유")]
    reason = [(s, e) for t, s, e in doc["sections"] if t == "이유"]
    for fid, _, jpat, _ in LEXICON:
        for zs, ze, title in zones:
            for m in re.finditer(jpat, text[zs:ze]):
                a = zs + m.start()
                cues.append((fid, a, a + len(m.group()), "sentencing_section"))
        for zs, ze in reason:
            for m in re.finditer(jpat, text[zs:ze]):
                a = zs + m.start()
                ss, se = sentence_span(text, a)
                if CONTEXT.search(text[ss:se]):
                    cues.append((fid, a, a + len(m.group()), "reason_sentence_with_sentencing_context"))
    out, seen = [], set()
    for fid, a, z, zone in sorted(cues, key=lambda x: x[1]):
        if (fid, a) in seen:
            continue
        seen.add((fid, a))
        ss, se = sentence_span(text, a)
        sent = text[ss:se]
        pol = "mitigating" if FAVOR.search(sent) and not DISFAVOR.search(sent) else "aggravating" if DISFAVOR.search(sent) and not FAVOR.search(sent) else "unstated"
        if re.search(r"(?:없|아니|않)", text[z : z + 6]) and fid not in ("no_punishment_wish", "no_record"):
            continue  # negated mention such as "합의하지 아니" / "반성하지 않"
        out.append({"doc_id": doc["source_id"], "factor": fid, "text": text[a:z], "span": [a, z], "sentence_span": [ss, se],
                    "zone": zone, "polarity_in_sentence": pol, "source_basis": "explicit_text_cue", "verification_status": "unreviewed"})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--cache", default=str(ROOT / "data/private/pipeline/merged_criminal_cache.jsonl"))
    a = ap.parse_args()
    run = Path(a.run)
    links = [json.loads(l) for l in (run / "links.jsonl").open()]
    ids = {x[k] for x in links if x["link_status"] != "auto_partial" and x.get("instance_pair", "1-2") == "1-2" for k in ("trial_id", "appeal_id")}
    g = grounding()
    (run / "sentencing_factor_lexicon.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
    cues = []
    for line in open(a.cache):
        d = json.loads(line)
        if d["source_id"] in ids:
            cues += extract(d)
    with (run / "sentencing_factors.jsonl").open("w") as f:
        for c in cues:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    by = collections.Counter(c["factor"] for c in cues)
    docs = collections.Counter(c["factor"] for c in {(c["doc_id"], c["factor"]): c for c in cues}.values())
    summary = {"docs_scanned": len(ids), "docs_with_any_factor": len({c["doc_id"] for c in cues}), "cues": len(cues),
               "by_factor": {f: {"cues": by[f], "docs": docs[f], "guideline_polarity": g.get(f, {}).get("guideline_polarity"),
                                 "guideline_pages": len(g.get(f, {}).get("guideline_pages", []))} for f, *_ in LEXICON},
               "polarity_in_sentence": dict(collections.Counter(c["polarity_in_sentence"] for c in cues)),
               "zone": dict(collections.Counter(c["zone"] for c in cues))}
    (run / "sentencing_factors_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
