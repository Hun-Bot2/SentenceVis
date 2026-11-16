"""Link appellate (항소심) criminal judgments to first-instance (원심) judgments.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Rule (documented in docs/specs/VALIDATION.md §3, run 2026-11-16):
  1. Parse the appeal's 【원심판결】 into court, decision date, case numbers.
     Abbreviated lists such as `2002고합534,589,605(병합)` are expanded only
     when the shorthand keeps the same year+type prefix; such links carry
     basis `abbrev_expanded` so their accuracy can be measured separately.
  2. Candidate trial docs: compacted case number equals a parsed number,
     or equals one of the numbers in the trial doc's own compound case number.
  3. Each candidate gets three independent checks: court_equal (normalized
     exact equality, no substring rule), date_equal, date_order (trial
     decided before appeal). No court alias table is applied.
  4. link_status = auto_strict when all three checks pass, else
     auto_partial with the failed checks listed. Neither status is a
     verified link; human review sets verification_status.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from corpus import compact

CASE_RE = re.compile(r"(\d{2,4})\s*(고[가-힣]{0,2}|노|초[가-힣]?|도)\s*(\d+)(-\d+)?")
DATE_RE = re.compile(r"(\d{2,4})\s*\.\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\.?")
APPEAL_RE = re.compile(r"^\d{2,4}노\d+")
SUPREME_RE = re.compile(r"^\d{2,4}도\d+")


def normalize_court(name: str) -> str:
    c = compact(name)
    c = c.replace("지법", "지방법원").replace("고법", "고등법원").replace("가법", "가정법원").replace("행법", "행정법원")
    return c


def full_year(y: str) -> str:
    if len(y) == 4:
        return y
    n = int(y)
    return f"{1900 + n if n >= 40 else 2000 + n}"


@dataclass
class PriorRef:
    raw: str
    court: str = ""
    date: str = ""  # YYYYMMDD
    case_nos: list[str] = field(default_factory=list)
    abbreviated: list[str] = field(default_factory=list)  # expanded from shorthand
    parse_issues: list[str] = field(default_factory=list)


def expand_case_list(text: str) -> tuple[list[str], list[str]]:
    """Return (explicit numbers, numbers expanded from shorthand lists)."""
    explicit: list[str] = []
    expanded: list[str] = []
    for m in CASE_RE.finditer(text):
        year, kind, num, suffix = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        explicit.append(f"{year}{kind}{num}{suffix}")
        # shorthand continuation: ",589,605" directly after the match keeps
        # the same year and type; a following full number stops the loop.
        pos = m.end()
        while True:
            t = re.match(r"\s*[,，、]\s*(\d+)(-\d+)?(?=\s*[,，、(）)\s]|$|\s*판결)", text[pos:])
            if not t:
                break
            expanded.append(f"{year}{kind}{t.group(1)}{t.group(2) or ''}")
            pos += t.end()
    return explicit, [e for e in expanded if e not in explicit]


def parse_prior(raw: str) -> PriorRef:
    ref = PriorRef(raw=re.sub(r"\s+", " ", raw).strip())
    # "제1원심판결 ： 광주지법 …" heading prefix; "200 1. 1. 10." stray space inside a year
    text = re.sub(r"^제\s*\d+\s*원심판결\s*[:：]?\s*", "", ref.raw)
    text = re.sub(r"(?<!\d)(\d{3}) (\d)(?=\s*\.)", r"\1\2", text)
    text = text.lstrip(":： ")
    d = DATE_RE.search(text)
    if d:
        ref.date = f"{full_year(d.group(1))}{int(d.group(2)):02d}{int(d.group(3)):02d}"
        court_part = text[: d.start()]
    else:
        ref.parse_issues.append("no_date")
        court_part = text.split("(")[0]
    court_part = re.sub(r"^제\s*1\s*심", "", court_part).strip(" (:：")
    ref.court = court_part.strip()
    if not ref.court:
        ref.parse_issues.append("no_court")
    ref.case_nos, ref.abbreviated = expand_case_list(text)
    if not ref.case_nos:
        ref.parse_issues.append("no_case_no")
    return ref


def split_priors(raw: str) -> list[str]:
    """Split a 【원심판결】 body listing several judgments ("1. … 판결 / 2. … 판결")."""
    text = re.sub(r"\s+", " ", raw).strip()
    text = re.sub(r"제\s*\d+\s*원심판결\s*[:：]?", " / ", text)
    parts = re.split(r"(?<=판결)\s*[,/]?\s*|\s/\s", text)
    out = []
    for part in parts:
        part = re.sub(r"^\d+\s*\.\s*", "", part.strip(" ,/)"))
        if re.search(r"\d", part):
            out.append(part)
    return out or [text]


# The only court alias applied: 서울지방법원 was reorganized into
# 서울중앙지방법원 on 2004-02-09; documents of that period use either name.
COURT_ALIASES = {frozenset({"서울지방법원", "서울중앙지방법원"})}


def court_alias(a: str, b: str) -> bool:
    return frozenset({normalize_court(a), normalize_court(b)}) in COURT_ALIASES


def own_numbers(case_no: str) -> set[str]:
    explicit, expanded = expand_case_list(case_no)
    return {compact(x) for x in explicit + expanded}


@dataclass
class Link:
    appeal_id: str
    trial_id: str
    appeal_case_no: str
    trial_case_no: str
    matched_number: str
    basis: str  # explicit | abbrev_expanded
    court_equal: bool
    court_alias: bool
    date_equal: bool
    date_order: bool
    link_status: str  # auto_strict | auto_alias | auto_partial
    failed_checks: list[str]
    prior_raw: str
    prior_index: int
    prior_count: int
    prior_span: list[int]
    verification_status: str = "unreviewed"
    instance_pair: str = "1-2"  # 1-2: first instance -> appeal; 2-3: appeal -> Supreme Court (도)


def build_links(docs: list[dict], include_supreme: bool = False) -> tuple[list[Link], list[dict]]:
    """include_supreme also links 대법원 상고심(도) judgments to the 항소심(노) judgment
    named in their 【원심판결】, with the same three checks (instance_pair '2-3')."""
    """docs: cache rows with source_id, case_no, court, date, text, sections."""
    index: dict[str, list[dict]] = {}
    for d in docs:
        for n in own_numbers(d["case_no"]) or {compact(d["case_no"])}:
            index.setdefault(n, []).append(d)
    links: list[Link] = []
    unmatched: list[dict] = []
    for a in docs:
        is_appeal = bool(APPEAL_RE.match(compact(a["case_no"])))
        is_supreme = include_supreme and bool(SUPREME_RE.match(compact(a["case_no"])))
        if not (is_appeal or is_supreme):
            continue
        sec = next((s for s in a["sections"] if s[0] == "원심판결"), None)
        if not sec:
            unmatched.append({"appeal_id": a["source_id"], "reason": "no_prior_section"})
            continue
        priors = split_priors(a["text"][sec[1] : sec[2]])
        found = False
        seen: set[tuple[str, int]] = set()
        for pi, piece in enumerate(priors):
            ref = parse_prior(piece)
            numbers = [(n, "explicit") for n in ref.case_nos] + [(n, "abbrev_expanded") for n in ref.abbreviated]
            for n, basis in numbers:
                for t in index.get(compact(n), []):
                    if t["source_id"] == a["source_id"] or (t["source_id"], pi) in seen:
                        continue
                    t_appeal = bool(APPEAL_RE.match(compact(t["case_no"])))
                    if is_appeal and (t_appeal or SUPREME_RE.match(compact(t["case_no"]))):
                        continue
                    if is_supreme and not t_appeal:
                        continue
                    seen.add((t["source_id"], pi))
                    ce = bool(ref.court) and normalize_court(t["court"]) == normalize_court(ref.court)
                    ca = not ce and bool(ref.court) and court_alias(t["court"], ref.court)
                    de = bool(ref.date) and t["date"] == ref.date
                    do = bool(t["date"]) and t["date"] <= a["date"]
                    failed = [k for k, ok in (("court_equal", ce or ca), ("date_equal", de), ("date_order", do)) if not ok]
                    status = "auto_partial" if failed else ("auto_alias" if ca else "auto_strict")
                    links.append(
                        Link(
                            appeal_id=a["source_id"],
                            trial_id=t["source_id"],
                            appeal_case_no=a["case_no"],
                            trial_case_no=t["case_no"],
                            matched_number=n,
                            basis=basis,
                            court_equal=ce,
                            court_alias=ca,
                            date_equal=de,
                            date_order=do,
                            link_status=status,
                            failed_checks=failed,
                            prior_raw=ref.raw,
                            prior_index=pi,
                            prior_count=len(priors),
                            prior_span=[sec[1], sec[2]],
                            instance_pair="2-3" if is_supreme else "1-2",
                        )
                    )
                    found = True
        if not found:
            unmatched.append(
                {"appeal_id": a["source_id"], "reason": "no_trial_doc_in_corpus",
                 "priors": [asdict(parse_prior(p)) for p in priors]}
            )
    return links, unmatched
