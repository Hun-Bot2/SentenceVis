"""Extract explicit reasoning cues from an appellate judgment's 【이유】.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Scope (user decision 2026-11-16): only relations the court states in the
text. Each cue is a literal phrase with its [start, end) span and the
enclosing sentence span. Cue types:
  ground     항소이유 keyword inside a 항소이유 요지 block (사실오인, 법리오해, 양형부당, …)
  origin     who raised it (피고인 / 검사) when the block heading or sentence names them
  ex_officio the court raising an issue itself (직권으로 …)
  accepted   "이유 있다"   rejected "이유 없다"   not_reached 판단 생략 phrases
  reversal   the sentence that states why the 원심판결 is reversed (… 파기)
A `relation` links a disposition cue to the nearest preceding ground or
ex_officio cue in the same numbered block; basis is `rule_proximity`, so it
is a proposal for human review, never a court finding by itself.
"""
from __future__ import annotations

import re

GROUNDS = {
    "사실오인": r"사실\s*오인",
    "법리오해": r"법리\s*오해",
    "양형부당": r"양형\s*부당|형이\s*너무\s*(?:무거워|가벼워)|형(?:의\s*양정)?이\s*(?:과중|과경|부당)",
    "심신장애": r"심신\s*(?:장애|미약|상실)",
    "채증법칙": r"채증\s*법칙",
    "절차위반": r"소송\s*절차의?\s*법령\s*위반|공소장\s*변경",
}
DISPOSITIONS = {
    "accepted": r"(?:주장|항소|논지)?(?:은|는)?\s*이유\s*있(?:다|고|으므로)",
    "rejected": r"(?:주장|항소|논지)?(?:은|는)?\s*이유\s*없(?:다|고|으므로)|받아들이지\s*(?:아니|않)",
    "not_reached": r"(?:에\s*대한\s*)?판단(?:을)?\s*생략|나아가\s*(?:살펴|판단할)\s*필요\s*(?:없이|가\s*없)|판단하지\s*아니",
}
EX_OFFICIO = r"직권으로\s*(?:살펴|살피건대|보건대|판단|본다)|직권\s*판단|직권\s*파기"
REVERSAL = r"원심판결(?:\s*중[^.。]{0,40}부분)?(?:은|을)\s*(?:더\s*이상\s*)?(?:유지될\s*수\s*없|파기)"
HEADING = re.compile(r"(?m)^\s*(?:\d+|[가-하]|\(\d+\)|\([가-하]\))\s*[.)]\s*[^\n]{0,40}$")
YOJI = re.compile(r"항소\s*이유(?:의)?\s*요지|항소\s*이유\s*요지|항소이유에\s*대한\s*판단|항소이유의\s*요지")


def _sentence(text: str, pos: int) -> list[int]:
    s = max(text.rfind(".", 0, pos), text.rfind("\n", 0, pos)) + 1
    e = text.find(".", pos)
    return [s, len(text) if e == -1 else e + 1]


def _blocks(text: str, start: int, end: int) -> list[tuple[int, int, str]]:
    marks = [(m.start() + start, m.group().strip()) for m in HEADING.finditer(text[start:end])]
    out = []
    for i, (s, h) in enumerate(marks):
        out.append((s, marks[i + 1][0] if i + 1 < len(marks) else end, h))
    if not out or out[0][0] > start:
        out.insert(0, (start, out[0][0] if out else end, ""))
    return out


def extract_paths(doc: dict) -> list[dict]:
    sec = next((s for s in doc["sections"] if s[0] == "이유"), None)
    if not sec:
        return []
    text, (s0, s1) = doc["text"], (sec[1], sec[2])
    cues: list[dict] = []
    in_yoji = False
    for b0, b1, heading in _blocks(text, s0, s1):
        block = text[b0:b1]
        if heading:
            in_yoji = bool(YOJI.search(heading)) or (in_yoji and not re.search(r"판단|직권", heading))
        origin = "검사" if re.search(r"검사", heading) else ("피고인" if re.search(r"피고인", heading) else None)

        def add(kind: str, label: str, m: re.Match, **extra) -> None:
            a, z = b0 + m.start(), b0 + m.end()
            sent = _sentence(text, a)
            org = origin
            if org is None:
                st = text[sent[0] : a]
                org = "검사" if "검사" in st else ("피고인" if "피고인" in st else None)
            cues.append({
                "appeal_id": doc["source_id"], "cue_type": kind, "label": label,
                "text": text[a:z], "span": [a, z], "sentence_span": sent,
                "block_heading": heading, "block_span": [b0, b1], "origin_hint": org,
                "in_grounds_summary": in_yoji or bool(YOJI.search(text[max(s0, a - 300) : a])),
                "source_basis": "explicit_text_cue", "verification_status": "unreviewed", **extra,
            })

        for label, pat in GROUNDS.items():
            for m in re.finditer(pat, block):
                add("ground", label, m)
        for m in re.finditer(EX_OFFICIO, block):
            add("ex_officio", "직권", m)
        for label, pat in DISPOSITIONS.items():
            for m in re.finditer(pat, block):
                add(label, label, m)
        for m in re.finditer(REVERSAL, block):
            add("reversal", "파기", m)
    cues.sort(key=lambda c: c["span"][0])
    # proximity relations: disposition -> nearest preceding ground/ex_officio in same block
    for i, c in enumerate(cues):
        if c["cue_type"] not in ("accepted", "rejected", "not_reached", "reversal"):
            continue
        for p in reversed(cues[:i]):
            if p["block_span"] != c["block_span"]:
                break
            if p["cue_type"] in ("ground", "ex_officio"):
                c["relation"] = {"target_span": p["span"], "target_label": p["label"], "basis": "rule_proximity"}
                break
    return cues
