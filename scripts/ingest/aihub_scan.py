"""Full member-level scan of every local AI-Hub archive (datasets 12, 019, 114, 115).

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/ingest/aihub_scan.py data/private/aihub_scan/<NEW_DIR>

Reads every member of every ZIP read-only (no extraction to disk) and writes
one row per member to members.jsonl: dataset, archive, member, bytes, sha256,
format, parse status, schema signature and the identity fields each format
carries (serial, case number, court, date, category). For full-text formats
it stores a hash of the whitespace-free text (for cross-dataset equality) and
the text itself only in texts/<dataset>.jsonl inside the private output dir.
Unreadable archives are recorded with the count of local file headers found.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import html
import io
import json
import re
import sys
import unicodedata
import struct
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DATASETS = {"12": "12.판결서 익명처리 데이터", "019": "019.법률, 규정 (판결서, 약관 등) 텍스트 분석 데이터",
            "114": "114.법률 지식기반 관계 데이터", "115": "115.법률-규정 텍스트 분석 데이터_고도화_상황에 따른 판례 데이터"}


def nows(s: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", s or ""))


def date8(s) -> str:
    """'2011. 12. 9.' / '2011-12-09' / '20111209' -> '20111209'; anything else -> ''."""
    t = str(s or "").strip()
    m = re.fullmatch(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})\D*", t)
    if m:
        return f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}"
    d = re.sub(r"\D", "", t)
    return d if len(d) == 8 else ""


def sig(obj) -> str:
    if isinstance(obj, dict):
        return "{" + ",".join(sorted(obj.keys())) + "}"
    if isinstance(obj, list):
        return "[" + (sig(obj[0]) if obj else "") + "]"
    return type(obj).__name__


def prec_text(t: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "\n", t or ""))


def recover_local_entries(raw: bytes):
    """Yield (index, name, bytes|None, note) by walking local file headers of a ZIP
    whose central directory is missing (truncated download). Deflate streams are
    decompressed until their own end marker, so data descriptors are not needed.
    A member cut off by the truncation yields bytes=None with note 'truncated'."""
    pos, i = 0, 0
    while True:
        pos = raw.find(b"PK\x03\x04", pos)
        if pos < 0 or pos + 30 > len(raw):
            return
        (_, _, flags, method, _, _, _, csize, _, nlen, xlen) = struct.unpack("<IHHHHHIIIHH", raw[pos:pos + 30])
        name_b = raw[pos + 30:pos + 30 + nlen]
        name = name_b.decode("utf-8" if flags & 0x800 else "cp437", "replace")
        start = pos + 30 + nlen + xlen
        try:
            if method == 8:
                d = zlib.decompressobj(-15)
                data = d.decompress(raw[start:])
                if not d.eof:
                    yield i, name, None, "truncated"
                    return
                end = len(raw) - len(d.unused_data)
            elif method == 0 and csize:
                data, end = raw[start:start + csize], start + csize
            else:
                data, end = b"", start
            yield i, name, data, "recovered"
        except zlib.error as e:
            yield i, name, None, f"zlib_error:{e}"
            end = start
        i += 1
        pos = max(end, pos + 4)


def parse_member(ds: str, name: str, b: bytes) -> tuple[dict, str | None]:
    """Return (identity fields, full text or None)."""
    ext = Path(name).suffix.lower()
    out: dict = {"format": ext.lstrip(".")}
    if ext == ".json":
        o = json.loads(b.decode("utf-8-sig"))
        out["schema"] = sig(o)
        if isinstance(o, dict) and "PrecService" in o:  # dataset 12 source wrapper
            o = o["PrecService"]
        if isinstance(o, dict) and "재결요지" in o and "판례내용" not in o:
            out.update(kind="admin_appeal_decision", case_no=nows(o.get("사건번호")), court=nows(o.get("재결청")),
                       date=date8(o.get("의결일자")), category=o.get("재결구분명") or "")
            return out, None
        if isinstance(o, dict) and "question" in o and "answer" in o:
            out["kind"] = "qa_pair"
            return out, None
        if isinstance(o, dict) and "clauseArticle" in o:
            out["kind"] = "terms_clause"
            return out, None
        if isinstance(o, dict) and "판례내용" in o:  # law.go.kr precedent record
            text = prec_text(o.get("판례내용"))
            out.update(kind="precedent_fulltext", serial=str(o.get("판례일련번호") or o.get("판례정보일련번호") or ""), case_no=nows(o.get("사건번호")),
                       court=nows(o.get("법원명")), date=date8(o.get("선고일자")), category=o.get("사건종류명") or "",
                       case_name=o.get("사건명") or "", has_prior="【원심판결】" in text, text_len=len(text),
                       ref_articles=nows(re.sub(r"【참조조문】", "", o.get("참조조문") or "")),
                       text_sha=hashlib.sha256(nows(text).encode()).hexdigest())
            return out, text
        info = o.get("info") if isinstance(o, dict) else None
        if isinstance(info, dict) and "caseNo" in info:
            out.update(kind="label_info", serial=str(info.get("caseNoID") or info.get("id") or ""), case_no=nows(info.get("caseNo")),
                       court=nows(info.get("courtNm")), date=date8(info.get("judmnAdjuDe")),
                       category=str(info.get("caseClass") or (o.get("Class_info") or {}).get("class_name") or info.get("caseField") or ""),
                       case_name=info.get("caseNm") or "")
            if "org" in o:  # dataset 019 structured annotation
                org = o.get("org") or {}
                out.update(kind="annotated_judgment", org_court=nows(org.get("orgJdgmnCourtNm")), org_date=date8(org.get("orgJdgmnAdjuDe")),
                           org_case_no=nows(org.get("orgJdgmnCaseNo")),
                           n_claims=len((o.get("assrs") or {}).get("acusrAssrs") or []) + len((o.get("assrs") or {}).get("dedatAssrs") or []),
                           n_court_reasons=len((o.get("dcss") or {}).get("courtDcss") or []))
            return out, None
        if isinstance(info, dict) and "Precedent" in info:  # dataset 114
            p = info.get("Precedent") or {}
            out.update(kind="relation_triples", doc_type=info.get("DocType"), precedent_keys=sig(p),
                       case_no=nows(str(p.get("CaseNum") or p.get("caseNo") or "")), court=nows(str(p.get("CourtName") or p.get("courtNm") or "")),
                       n_triples=len(o.get("Triple") or []), n_entities=len(o.get("Entities") or []))
            return out, None
        out["kind"] = "other_json"
        return out, None
    if ext == ".xml":
        try:
            root = ET.fromstring(b)
            f = root.find("file")
            text = (f.findtext("cn") if f is not None else "") or ""
            fname = (f.findtext("name") if f is not None else "") or ""
            category = (f.findtext("category") if f is not None else "") or ""
            out["xml_parse"] = "strict"
        except (ET.ParseError, LookupError, ValueError) as e:
            # Lenient recovery: take CDATA bodies of <category>, <name>, <cn>; a truncated
            # <cn> is kept up to the end of the file and flagged.
            t = b.decode("utf-8", "replace")
            # also handles damaged files whose quotes/brackets were stripped: <!CDATA ... >
            grab = lambda tag: re.search(rf"<{tag}>\s*<!\s*\[?\s*CDATA\s*\[?(.*?)(?:\]\]>|\]?\s*>\s*</{tag}>|$)", t, re.S)  # noqa: E731
            m_cn, m_nm, m_cat = grab("cn"), grab("name"), grab("category")
            if m_cn:
                text, fname, category = m_cn.group(1), (m_nm.group(1) if m_nm else ""), (m_cat.group(1) if m_cat else "")
                out["xml_parse"] = "lenient"
            else:
                # Last resort for files whose markup is corrupted or absent: keep the whole
                # decoded file as text; case number from the member file name.
                text, fname, category = t, Path(name).stem, ""
                out["xml_parse"] = "raw_text"
            out["xml_error"] = str(e)[:120]
            out["xml_truncated"] = (not re.search(r"</cn>", t[m_cn.start():])) if m_cn else None
        head = re.sub(r"\s+", " ", text[:600])
        hm = re.search(r"([가-힣]+(?:지방|고등|가정|행정|특허)?법원(?:\s*[가-힣]+지원)?|대법원),\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.", head)
        out.update(kind="xml_fulltext", schema="xml:file{category,cn,name}", category=category.strip(),
                   case_no=nows(re.sub(r"\.pdf$", "", fname.strip())),
                   court=nows(hm.group(1)) if hm else "", date=f"{hm.group(2)}{int(hm.group(3)):02d}{int(hm.group(4)):02d}" if hm else "",
                   text_len=len(text), text_sha=hashlib.sha256(nows(text).encode()).hexdigest())
        return out, text
    if ext == ".csv":
        rows = list(csv.reader(io.StringIO(b.decode("utf-8-sig", "replace"))))
        out.update(kind="csv_pairs", schema=f"csv:{len(rows[0]) if rows else 0}cols", n_rows=len(rows))
        return out, None
    out["kind"] = "unknown"
    return out, None


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    (out / "texts").mkdir(mode=0o700)
    members = (out / "members.jsonl").open("w")
    texts = {ds: (out / "texts" / f"{ds}.jsonl").open("w") for ds in DATASETS}
    summary: dict = {"archives": [], "by_dataset": {}}
    for ds, folder in DATASETS.items():
        counts = collections.Counter()
        for zp in sorted((ROOT / "data" / folder).rglob("*.zip")):
            rel = str(zp.relative_to(ROOT / "data"))
            raw = zp.read_bytes()
            arch = {"dataset": ds, "archive": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            try:
                z = zipfile.ZipFile(io.BytesIO(raw))
            except zipfile.BadZipFile as e:
                arch.update(status="central_directory_missing", error=str(e), local_headers=raw.count(b"PK\x03\x04"))
                n_ok = n_bad = n_trunc = 0
                for i, nm, b, note in recover_local_entries(raw):
                    if nm.endswith("/") or nm.endswith(".DS_Store"):
                        continue
                    if b is None:
                        n_trunc += 1
                        members.write(json.dumps({"dataset": ds, "archive": rel, "member_index": i, "member": nm, "parse": "error",
                                                  "error": note, "recovery": "local_header"}, ensure_ascii=False) + "\n")
                        continue
                    row = {"dataset": ds, "archive": rel, "member_index": i, "member": nm, "bytes": len(b),
                           "sha256": hashlib.sha256(b).hexdigest(), "recovery": "local_header"}
                    try:
                        fields, text = parse_member(ds, nm, b)
                        row.update(fields, parse="ok"); n_ok += 1
                        if text is not None:
                            texts[ds].write(json.dumps({"sha256": row["sha256"], "text": text}, ensure_ascii=False) + "\n")
                    except Exception as e2:
                        row.update(parse="error", error=f"{type(e2).__name__}: {str(e2)[:120]}"); n_bad += 1
                    members.write(json.dumps(row, ensure_ascii=False) + "\n")
                    counts[f"kind:{row.get('kind', 'parse_error')}"] += 1
                arch.update(members_recovered=n_ok, members_error=n_bad, members_truncated=n_trunc)
                summary["archives"].append(arch)
                counts["recovered_archives"] += 1
                counts["members_ok"] += n_ok
                counts["members_error"] += n_bad + n_trunc
                continue
            n_ok = n_bad = 0
            for i, info in enumerate(z.infolist()):
                if info.is_dir() or info.filename.endswith(".DS_Store") or "/__MACOSX/" in info.filename:
                    continue
                b = z.read(info)
                row = {"dataset": ds, "archive": rel, "member_index": i, "member": info.filename, "bytes": len(b),
                       "sha256": hashlib.sha256(b).hexdigest()}
                try:
                    fields, text = parse_member(ds, info.filename, b)
                    row.update(fields, parse="ok")
                    n_ok += 1
                    if text is not None:
                        texts[ds].write(json.dumps({"sha256": row["sha256"], "text": text}, ensure_ascii=False) + "\n")
                except Exception as e:  # recorded, never silently dropped
                    row.update(parse="error", error=f"{type(e).__name__}: {str(e)[:120]}")
                    n_bad += 1
                members.write(json.dumps(row, ensure_ascii=False) + "\n")
                counts[f"kind:{row.get('kind', 'parse_error')}"] += 1
            arch.update(status="ok", members_ok=n_ok, members_error=n_bad)
            summary["archives"].append(arch)
            counts["members_ok"] += n_ok
            counts["members_error"] += n_bad
        summary["by_dataset"][ds] = dict(counts)
    members.close()
    for f in texts.values():
        f.close()
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary["by_dataset"], ensure_ascii=False, indent=2))
    print("unreadable:", [a for a in summary["archives"] if a.get("status") == "unreadable"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
