"""Read AI-Hub criminal source judgments with hash-checked provenance.

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md. Reads originals read-only; never extracts
ZIP paths to disk. Text offsets are Unicode code points into `text`, the
판례내용 HTML with tags replaced by newlines and entities unescaped (same
convention as the 2026-11-16 temporal-scope audit).
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/private/inventory/2026-11-13-v4/catalog.sqlite"
CRIMINAL = ("형사", "형사A", "형사B")
SECTION_RE = re.compile(r"【([^】]+)】")


def compact(value: object) -> str:
    """NFC + remove all whitespace. Used only for comparison keys."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", str(value or "")))


@dataclass
class Section:
    title: str  # compacted title, e.g. 주문, 이유, 원심판결
    start: int  # body start offset (after 】)
    end: int  # body end offset (exclusive)


@dataclass
class Judgment:
    source_id: str
    case_no: str
    court: str
    decision_date: str  # YYYYMMDD
    category: str
    case_name: str
    text: str
    sections: list[Section]
    locator: dict = field(default_factory=dict)

    def section(self, title: str) -> Section | None:
        for s in self.sections:
            if s.title == title:
                return s
        return None

    def body(self, title: str) -> str:
        s = self.section(title)
        return self.text[s.start : s.end] if s else ""


def to_text(raw_html: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "\n", raw_html or ""))


def split_sections(text: str) -> list[Section]:
    marks = list(SECTION_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append(Section(compact(m.group(1)), m.end(), end))
    return out


class Corpus:
    """Lazy, hash-verified reader for source (원천) documents."""

    def __init__(self, catalog: Path = CATALOG, root: Path = ROOT):
        self.root = root
        self.db = sqlite3.connect(f"file:{catalog}?mode=ro", uri=True)
        self.db.row_factory = sqlite3.Row
        self._zips: dict[Path, zipfile.ZipFile] = {}

    def criminal_rows(self, subset: str = "general") -> list[dict]:
        q = (
            "select d.*, a.relative_path, a.sha256 as archive_sha256 from documents d "
            "join archives a using(archive_id) where a.role='source' and a.subset=? "
            f"and d.category in ({','.join('?' * len(CRIMINAL))}) order by d.source_id"
        )
        return [dict(r) for r in self.db.execute(q, (subset, *CRIMINAL))]

    def _zip(self, rel: str, sha: str) -> zipfile.ZipFile:
        p = self.root / "data" / rel
        if p not in self._zips:
            if hashlib.sha256(p.read_bytes()).hexdigest() != sha:
                raise ValueError(f"archive hash mismatch: {rel}")
            self._zips[p] = zipfile.ZipFile(p)
        return self._zips[p]

    def load(self, row: dict) -> Judgment:
        z = self._zip(row["relative_path"], row["archive_sha256"])
        info = z.infolist()[row["member_index"]]
        if info.filename != row["member_path"]:
            raise ValueError(f"member path mismatch: {row['source_id']}")
        raw = z.read(info)
        if hashlib.sha256(raw).hexdigest() != row["member_sha256"]:
            raise ValueError(f"member hash mismatch: {row['source_id']}")
        obj = json.loads(raw)["PrecService"]
        text = to_text(obj.get("판례내용", ""))
        return Judgment(
            source_id=row["source_id"],
            case_no=row["case_no"] or "",
            court=row["court"] or "",
            decision_date=re.sub(r"\D", "", row["decision_date"] or ""),
            category=row["category"] or "",
            case_name=obj.get("사건명", "") or "",
            text=text,
            sections=split_sections(text),
            locator={
                "archive": row["relative_path"],
                "archive_sha256": row["archive_sha256"],
                "member_index": row["member_index"],
                "member_sha256": row["member_sha256"],
            },
        )

    def close(self) -> None:
        for z in self._zips.values():
            z.close()
        self.db.close()
