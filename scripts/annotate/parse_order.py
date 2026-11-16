"""Rule-based parser for 【주문】 (disposition) of Korean criminal judgments.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Outputs are `rule_extracted` and `unreviewed`. Design constraints from
AGENTS.md / VALIDATION.md:
  * 징역/금고 months and 집행유예 are separate fields; never merged.
  * 벌금, 무죄, 면소, 공소기각 are kinds, never converted to 0 months.
  * One defendant with several separate prison terms -> `multi_term`, no sum.
  * Defendant labels are document-internal aliases (피고인, 피고인 1 …).
Every value keeps the [start, end) span of the clause it came from, as
offsets into the 주문 body (caller adds the section start offset).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

NUM = r"\d+"
DEF_LABEL = re.compile(r"피고인(?:들)?(?:\s*(?:\d+|[A-Z가-힣]\s*\(.*?\)))?")
TERM = re.compile(r"(징역|금고)\s*(?:(\d+)\s*년)?\s*(?:(\d+)\s*(?:개월|월))?")
FINE = re.compile(r"벌금\s*([\d,억만천원\s]+?원)")
SUSP = re.compile(r"(\d+)\s*년(?:\s*(\d+)\s*(?:개월|월))?\s*간\s*(?:위\s*)?(?:각\s*)?(?:그\s*)?(?:징역|금고)?형(?:의|에\s*대한|에\s*대하여)\s*(?:그\s*)?집행을\s*유예")
ENUM = re.compile(r"^\s*(?:(?:\d+|[가-하])\s*\.\s*)+")
LIST_RE = re.compile(r"피고인(?:들)?\s*((?:\d+\s*(?:\([^)]*\))?\s*[,，및와과\s]*)+)")


def won(text: str) -> int | None:
    t = re.sub(r"[\s,원]", "", text)
    total = 0
    m = re.fullmatch(r"(?:(\d+)억)?(?:(\d+)만)?(\d+)?", t)
    if not m or not any(m.groups()):
        return None
    eok, man, rest = (int(g) if g else 0 for g in m.groups())
    total = eok * 100_000_000 + man * 10_000 + rest
    return total


def labels_in(text: str) -> list[str]:
    """Defendant labels named at the start of a clause: ['1','2'] or ['*'] (all / sole)."""
    m = LIST_RE.match(text.strip())
    if m and re.search(r"\d", m.group(1)):
        nums = re.findall(r"(?<!\()\b(\d+)\b(?![^()]*\))", m.group(1))
        return nums or ["*"]
    return ["*"]


@dataclass
class Penalty:
    defendants: list[str]  # ['*'] = all defendants named collectively / sole defendant
    kind: str  # prison | confinement | fine | acquittal | dismissal | exemption
    months: int | None = None
    fine_won: int | None = None
    span: list[int] = field(default_factory=list)


@dataclass
class Order:
    penalties: list[Penalty] = field(default_factory=list)
    suspensions: list[dict] = field(default_factory=list)  # {defendants, months, span}
    appeal_actions: list[dict] = field(default_factory=list)  # {action, scope, span}
    partial_outcomes: list[dict] = field(default_factory=list)  # 일부 무죄/면소/공소기각
    defendant_labels: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    source_basis: str = "rule_extracted"
    verification_status: str = "unreviewed"


def _clauses(body: str):
    """Split on sentence ends and 에, separators while keeping offsets."""
    start = 0
    for m in re.finditer(r"(?:처한다|기각한다|파기한다|유예한다|무죄|면소|기각|명한다|한다)\s*[.。]|[.。]\s*(?=\d+\.|[가-하]\.)|(?<=에)\s*,", body):
        yield start, m.end()
        start = m.end()
    if start < len(body):
        yield start, len(body)


def parse_order(body: str) -> Order:
    o = Order()
    o.defendant_labels = sorted(set(re.findall(r"피고인\s*(\d+)", body)), key=int)
    for cs, ce in _clauses(body):
        clause = body[cs:ce]
        flat = re.sub(r"\s+", " ", clause)
        # appellate actions
        for m in re.finditer(r"원심판결(?:\s*중\s*([^.]*?)에\s*대한\s*부분)?\s*을\s*파기", clause):
            o.appeal_actions.append({"action": "reversed", "scope": (m.group(1) or "all").strip(), "span": [cs + m.start(), cs + m.end()]})
        for m in re.finditer(r"([^.]*?)항소(?:를|는)?\s*(?:모두\s*|각\s*)?기각", clause):
            who = "검사" if "검사" in m.group(1) else ("피고인" if "피고인" in m.group(1) else "unspecified")
            if "검사" in m.group(1) and "피고인" in re.sub(r"검사의\s*피고인", "", m.group(1)):
                who = "쌍방"
            o.appeal_actions.append({"action": "dismissed", "by": who, "scope": m.group(1).strip(), "span": [cs + m.start(), cs + m.end()]})
        # suspension
        sm = SUSP.search(clause)
        if sm:
            months = int(sm.group(1)) * 12 + int(sm.group(2) or 0)
            target = labels_in(re.sub(r"^\s*다만\s*,?\s*", "", ENUM.sub("", flat))) if re.search(r"피고인\s*\d", flat[: flat.find("집행")]) else ["*"]
            rec = {"defendants": target, "months": months, "span": [cs + sm.start(), cs + sm.end()]}
            part = re.search(r"형\s*중\s*([^,.]*?)에\s*한하여", flat)
            if part:  # suspension attached to only part of the sentence
                rec["partial"] = part.group(1).strip()
            o.suspensions.append(rec)
            continue
        # sentences
        if "처한다" in clause or re.search(r"(징역|금고|벌금)[^.]*에\s*,?$", clause.strip()):
            who = labels_in(ENUM.sub("", flat))
            terms = list(TERM.finditer(clause))
            for t in terms:
                if not (t.group(2) or t.group(3)):
                    continue
                kind = "prison" if t.group(1) == "징역" else "confinement"
                months = int(t.group(2) or 0) * 12 + int(t.group(3) or 0)
                o.penalties.append(Penalty(who, kind, months=months, span=[cs + t.start(), cs + t.end()]))
            for f in FINE.finditer(clause):
                o.penalties.append(Penalty(who, "fine", fine_won=won(f.group(1)), span=[cs + f.start(), cs + f.end()]))
            if "형의 선고를 유예" in flat:
                o.issues.append("sentence_deferred")
        # outcomes without a penalty
        for m in re.finditer(r"(?:공소사실\s*중\s*[^.]*?(?:의\s*점|부분)(?:은|는)\s*)?(?:각\s*)?(무죄|면소|공소\s*를?\s*기각)", clause):
            pre = clause[max(0, m.start() - 40) : m.start()]
            partial = "공소사실 중" in re.sub(r"\s+", " ", clause[: m.end()])
            rec = {"kind": {"무죄": "acquittal", "면소": "exemption"}.get(m.group(1), "dismissal"), "span": [cs + m.start(), cs + m.end()]}
            if partial:
                o.partial_outcomes.append(rec)
            elif re.search(r"피고인", clause[: m.start()]) or "피고인" in pre:
                o.penalties.append(Penalty(labels_in(flat), rec["kind"], span=rec["span"]))
    # one defendant with two separate prison terms (separate 형 for 경합범 분리)
    by_def: dict[str, int] = {}
    for p in o.penalties:
        if p.kind in ("prison", "confinement"):
            for d in p.defendants:
                by_def[d] = by_def.get(d, 0) + 1
    if any(v > 1 for v in by_def.values()):
        o.issues.append("multi_term")
    if not o.penalties and not o.appeal_actions:
        o.issues.append("no_parse")
    return o


def single_defendant(body_header: str, order_body: str) -> bool:
    """True when neither the 피고인 header nor the 주문 names numbered or plural defendants."""
    text = body_header + order_body
    return not re.search(r"피고인\s*\d|피고인들|피고인\s*[A-Z]\b", text)
