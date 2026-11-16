"""Rule tests for the SentenScope extraction pipeline (synthetic strings only).

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/align"))
sys.path.insert(0, str(ROOT / "scripts/annotate"))
sys.path.insert(0, str(ROOT / "scripts/statutes"))

from extract_paths import extract_paths  # noqa: E402
from link_pairs import build_links, court_alias, parse_prior, split_priors  # noqa: E402
from metrics import wilson  # noqa: E402
from parse_order import parse_order, single_defendant  # noqa: E402


def pen(order):
    return [(p.defendants, p.kind, p.months, p.fine_won) for p in order.penalties]


class OrderTests(unittest.TestCase):
    def test_prison_and_suspension_are_separate(self):
        o = parse_order("원심판결을 파기한다. 피고인을 징역 2년 6월에 처한다. 다만, 이 판결확정일로부터 4년간 위 형의 집행을 유예한다.")
        self.assertEqual(pen(o), [(["*"], "prison", 30, None)])
        self.assertEqual(o.suspensions[0]["months"], 48)
        self.assertEqual(o.appeal_actions[0]["action"], "reversed")

    def test_suspension_phrase_variants(self):
        for phrase in ("위 형에 대한 집행을 유예", "위 징역형의 집행을 유예", "위 각 형의 집행을 유예"):
            o = parse_order(f"피고인을 징역 1년 6월에 처한다. 다만, 이 판결이 확정된 날로부터 3년간 {phrase}한다.")
            self.assertEqual(o.suspensions[0]["months"], 36, phrase)

    def test_numbered_defendants_and_fines(self):
        o = parse_order("피고인 1을 징역 10월에,피고인 2(대법원 및 제2심판결의 피고인 1)를 벌금 5,000,000원에,"
                        "피고인 3,4를 각 벌금 1,000,000원에 각 처한다. 다만,피고인 1에 대하여는 이 판결 확정일부터 2년간 위 형의 집행을 유예한다.")
        self.assertEqual(pen(o), [(["1"], "prison", 10, None), (["2"], "fine", None, 5_000_000), (["3", "4"], "fine", None, 1_000_000)])
        self.assertEqual(o.suspensions[0]["defendants"], ["1"])

    def test_fine_never_becomes_zero_months(self):
        o = parse_order("피고인을 벌금 3,000,000원에 처한다.")
        self.assertEqual(pen(o), [(["*"], "fine", None, 3_000_000)])

    def test_korean_unit_amount(self):
        o = parse_order("피고인 3을 징역 2년 및 벌금 6억 5,320만 원에 처한다.")
        self.assertIn((["3"], "fine", None, 653_200_000), pen(o))

    def test_acquittal_and_partial_acquittal(self):
        self.assertEqual(pen(parse_order("피고인은 무죄.")), [(["*"], "acquittal", None, None)])
        o = parse_order("피고인들을 각 징역 1년 2월에 처한다. 이 사건 공소사실 중 특수절도미수의 점은 각 무죄.")
        self.assertEqual(len(o.partial_outcomes), 1)
        self.assertEqual(pen(o), [(["*"], "prison", 14, None)])

    def test_dismissal_party(self):
        self.assertEqual(parse_order("검사의 항소를 기각한다.").appeal_actions[0]["by"], "검사")
        self.assertEqual(parse_order("피고인들의 항소를 모두 기각한다.").appeal_actions[0]["by"], "피고인")

    def test_multi_term_flag(self):
        o = parse_order("피고인을 판시 제1죄에 대하여 징역 8월에, 판시 제2죄에 대하여 징역 4월에 처한다.")
        self.assertIn("multi_term", o.issues)

    def test_single_defendant(self):
        self.assertTrue(single_defendant(" 피고인 ", "피고인을 징역 1년에 처한다."))
        self.assertFalse(single_defendant(" 1. 피고인 1 2. 피고인 2", "피고인들을 각 징역 1년에 처한다."))


class LinkTests(unittest.TestCase):
    def test_parse_prior_and_abbreviation(self):
        r = parse_prior("서울지방법원 2002. 12. 27. 선고 2002고합534,589,605(병합) 판결")
        self.assertEqual((r.court, r.date), ("서울지방법원", "20021227"))
        self.assertEqual(r.case_nos, ["2002고합534"])
        self.assertEqual(r.abbreviated, ["2002고합589", "2002고합605"])

    def test_two_digit_year(self):
        self.assertEqual(parse_prior("수원지법 여주지원 2000. 6. 13. 선고 99고단1293 판결").case_nos, ["99고단1293"])

    def test_split_priors(self):
        parts = split_priors("1. 서울중앙지방법원 2008. 4. 17. 선고 2007고합1408 판결, 2. 서울중앙지방법원 2008. 7. 4. 선고 2008고합606 판결")
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[1].startswith("서울중앙지방법원 2008. 7. 4."))

    def test_court_alias_is_only_seoul_reorganization(self):
        self.assertTrue(court_alias("서울지법", "서울중앙지방법원"))
        self.assertFalse(court_alias("수원지방법원", "수원지방법원 여주지원"))

    def _doc(self, sid, case_no, court, date, prior=None):
        text = f"【주문】 x 【원심판결】 {prior} 【이유】 y" if prior else "【주문】 x"
        sections = []
        import re
        marks = list(re.finditer(r"【([^】]+)】", text))
        for i, m in enumerate(marks):
            sections.append([m.group(1), m.end(), marks[i + 1].start() if i + 1 < len(marks) else len(text)])
        return {"source_id": sid, "case_no": case_no, "court": court, "date": date, "text": text, "sections": sections}

    def test_same_number_other_court_is_partial(self):
        appeal = self._doc("A", "2006노1", "서울고등법원", "20061208", "춘천지방법원 강릉지원 2006. 5. 15. 선고 2005고합87 판결")
        right = self._doc("T1", "2005고합87", "춘천지방법원 강릉지원", "20060515")
        wrong = self._doc("T2", "2005고합87", "의정부지방법원", "20050819")
        links, _ = build_links([appeal, right, wrong])
        status = {x.trial_id: x.link_status for x in links}
        self.assertEqual(status, {"T1": "auto_strict", "T2": "auto_partial"})


class PathTests(unittest.TestCase):
    def test_cues_and_relation(self):
        body = ("\n1. 항소이유의 요지\n피고인은 원심의 사실오인 및 양형부당을 주장한다.\n"
                "2. 판단\n가. 사실오인 주장에 대하여\n피고인의 위 주장은 이유 없다.\n"
                "나. 직권판단\n직권으로 살피건대, 원심판결은 더 이상 유지될 수 없다.\n")
        text = "【이유】" + body
        doc = {"source_id": "A", "text": text, "sections": [["이유", 4, len(text)]]}
        cues = extract_paths(doc)
        kinds = [(c["cue_type"], c["label"]) for c in cues]
        self.assertIn(("ground", "사실오인"), kinds)
        self.assertIn(("ground", "양형부당"), kinds)
        self.assertIn(("rejected", "rejected"), kinds)
        self.assertIn(("ex_officio", "직권"), kinds)
        rej = next(c for c in cues if c["cue_type"] == "rejected")
        self.assertEqual(rej["relation"]["target_label"], "사실오인")
        self.assertEqual(rej["relation"]["basis"], "rule_proximity")
        for c in cues:
            self.assertEqual(text[c["span"][0]:c["span"][1]], c["text"])
            self.assertEqual(c["verification_status"], "unreviewed")


class MetricTests(unittest.TestCase):
    def test_wilson_known_values(self):
        w = wilson(34, 40)
        self.assertAlmostEqual(w["lo"], 0.7093, places=3)
        self.assertAlmostEqual(w["hi"], 0.9294, places=3)
        self.assertIsNone(wilson(0, 0)["p"])


if __name__ == "__main__":
    unittest.main()


class CrossCheckHelperTests(unittest.TestCase):
    def test_date8_dotted_and_dashed(self):
        sys.path.insert(0, str(ROOT / "scripts/ingest"))
        from aihub_scan import date8
        self.assertEqual(date8("2011. 12. 9."), "20111209")
        self.assertEqual(date8("2012-02-26"), "20120226")
        self.assertEqual(date8("20111209"), "20111209")
        self.assertEqual(date8("2016893"), "")

    def test_court_abbreviations(self):
        from link_pairs import normalize_court
        self.assertEqual(normalize_court("서울가법"), normalize_court("서울가정법원"))
        self.assertEqual(normalize_court("서울행법"), normalize_court("서울행정법원"))

    def test_prior_prefix_and_year_space(self):
        parts = split_priors("제 1원심판결 ： 광주지법 2001. 4. 26. 선고 2000고합540 판결 제2원심판결 ： 광주지법 2000. 12. 21. 선고 2000고단4421 판결")
        self.assertEqual([(parse_prior(p).court, parse_prior(p).date) for p in parts],
                         [("광주지법", "20010426"), ("광주지법", "20001221")])
        r = parse_prior("서울지법 동부지원 200 1. 1. 10. 선고 2000고단1841 판결")
        self.assertEqual((r.date, r.case_nos), ("20010110", ["2000고단1841"]))


class RecoveryAndKbTests(unittest.TestCase):
    def test_recover_zip_without_central_directory(self):
        import io as _io
        import zipfile as _zf
        sys.path.insert(0, str(ROOT / "scripts/ingest"))
        from aihub_scan import recover_local_entries
        buf = _io.BytesIO()
        with _zf.ZipFile(buf, "w", _zf.ZIP_DEFLATED) as z:
            z.writestr("a/1.json", '{"x": 1}')
            z.writestr("a/2.json", '{"y": "' + "가" * 500 + '"}')
        raw = buf.getvalue()
        cut = raw[: raw.rfind(b"PK\x01\x02")]  # drop central directory, keep all entries
        got = [(n, b, note) for _, n, b, note in recover_local_entries(cut)]
        self.assertEqual([n for n, _, _ in got], ["a/1.json", "a/2.json"])
        self.assertEqual(got[0][1], b'{"x": 1}')
        self.assertTrue(all(note == "recovered" for *_, note in got))
        second = raw.find(b"PK\x03\x04", 4)
        inside = raw[: second + 30 + len("a/2.json") + 3]  # cut inside the 2nd entry's deflate data
        notes = [note for *_, note in recover_local_entries(inside)]
        self.assertEqual(notes, ["recovered", "truncated"])

    def test_nt_literal_unescape(self):
        sys.path.insert(0, str(ROOT / "scripts/ingest"))
        from kb_scan import NT, literal, unesc
        line = '<http://www.law.go.kr/decree/\\uC870/_1> <http://x/name> "\\uC81C198\\uC870"^^<http://www.w3.org/2001/XMLSchema#string> .'
        m = NT.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(unesc(m.group(1)), "<http://www.law.go.kr/decree/조/_1>")
        self.assertEqual(literal(m.group(3)), "제198조")

    def test_kb_article_key(self):
        sys.path.insert(0, str(ROOT / "scripts/ingest"))
        from kb_crosscheck import art_key
        self.assertEqual(art_key("민법 제396조"), ("민법", "396"))
        self.assertEqual(art_key("형법 제37조의2"), ("형법", "37-2"))
        self.assertIsNone(art_key(""))


class SupremeTests(unittest.TestCase):
    def _doc(self, sid, case_no, court, date, prior=None, order="x"):
        import re as _re
        text = f"【주문】 {order} 【원심판결】 {prior} 【이유】 y" if prior else f"【주문】 {order}"
        marks = list(_re.finditer(r"【([^】]+)】", text))
        secs = [[m.group(1), m.end(), marks[i + 1].start() if i + 1 < len(marks) else len(text)] for i, m in enumerate(marks)]
        return {"source_id": sid, "case_no": case_no, "court": court, "date": date, "text": text, "sections": secs}

    def test_supreme_links_only_to_appeal_docs(self):
        sup = self._doc("S", "2006도3302", "대법원", "20061013", "광주지법 2006. 4. 26. 선고 2006노97 판결")
        app = self._doc("A", "2006노97", "광주지방법원", "20060426")
        links, _ = build_links([sup, app], include_supreme=True)
        self.assertEqual([(x.trial_id, x.appeal_id, x.instance_pair, x.link_status) for x in links], [("A", "S", "2-3", "auto_strict")])
        self.assertEqual(build_links([sup, app])[0], [])  # default keeps 1-2 only

    def test_supreme_outcome_partial_reversal_and_dismissal(self):
        sys.path.insert(0, str(ROOT / "scripts/align"))
        from build_dataset import supreme_outcome
        doc = self._doc("S", "2004도45", "대법원", "20070125",
                        order="원심판결 중 피고인 1, 피고인 2에 대한 유죄 부분을 파기하고, 이 부분 사건을 서울중앙지방법원 합의부에 환송한다. 피고인 4의 상고를 기각한다.")
        acts = [(a["action"], a.get("scope")) for a in supreme_outcome(doc)["actions"]]
        self.assertEqual(acts, [("reversed_remanded", "피고인 1, 피고인 2"), ("dismissed", "피고인 4의")])


class StatusTests(unittest.TestCase):
    def test_partial_suspension_phrase(self):
        o = parse_order("피고인을 징역 1년 6월에 처한다. 다만, 이 판결 확정일부터 위 형 중 징역 1년에 한하여 3년간 그 형의 집행을 유예한다.")
        self.assertEqual(o.suspensions[0]["months"], 36)
        self.assertEqual(o.suspensions[0]["partial"], "징역 1년")

    def test_side_fields_never_bare_null(self):
        sys.path.insert(0, str(ROOT / "scripts/align"))
        from build_dataset import STATUSES, outcome_for, side_fields
        cases = {
            "피고인을 징역 2년에 처한다.": ("observed", "absent_in_text"),
            "피고인을 벌금 3,000,000원에 처한다.": ("not_applicable", "not_applicable"),
            "피고인은 무죄.": ("not_applicable", "not_applicable"),
            "피고인을 징역 2년에 처한다. 다만, 이 판결 확정일부터 3년간 위 형의 집행을 유예한다.": ("observed", "observed"),
            "피고인을 판시 제1죄에 대하여 징역 8월에, 판시 제2죄에 대하여 징역 4월에 처한다.": ("not_scalar", "absent_in_text"),
        }
        from dataclasses import asdict
        for text, (p_status, s_status) in cases.items():
            f = side_fields(outcome_for(asdict(parse_order(text)), "*"), False)
            self.assertEqual((f["prison_months"]["status"], f["suspension_months"]["status"]), (p_status, s_status), text)
            for v in f.values():
                self.assertIn(v["status"], STATUSES)


class ContextExtractionTests(unittest.TestCase):
    def _doc(self, sections):
        text, secs = "", []
        for title, body in sections:
            text += f"【{title}】"
            s = len(text)
            text += body
            secs.append([title, s, len(text)])
        return {"source_id": "D", "date": "20060101", "text": text, "sections": secs}

    def test_law_application_steps_and_carry_over(self):
        from law_application import parse
        doc = self._doc([("법령의 적용".replace(" ", ""), "1. 범죄사실에 대한 해당법조 및 형의 선택 형법 제329조(징역형 선택) 1. 경합범가중 각 형법 제37조 전단, 제38조 제1항 제2호 1. 작량감경 형법 제53조, 제55조 제1항 제3호")])
        r = parse(doc)
        steps = [(s["step"], [(a["law"], a["article"]) for a in s["articles"]]) for s in r["steps"] if s["articles"]]
        self.assertEqual(steps, [("offense_and_choice", [("형법", "329")]),
                                 ("concurrent_aggravation", [("형법", "37"), ("형법", "38")]),
                                 ("discretionary_mitigation", [("형법", "53"), ("형법", "55")])])

    def test_sentencing_factor_negation_and_context(self):
        from sentencing_factors import extract
        doc = self._doc([("이유", "피고인이 잘못을 반성하고 있는 점 등 유리한 정상을 참작한다. 피해자와 합의하지 아니한 점은 불리한 정상이다. 피고인은 반성하고 있다.")])
        got = [(c["factor"], c["polarity_in_sentence"]) for c in extract(doc)]
        self.assertIn(("remorse", "mitigating"), got)
        self.assertEqual(sum(1 for f, _ in got if f == "remorse"), 1)  # 3rd sentence lacks sentencing context
        self.assertNotIn("settlement", [f for f, _ in got])  # negated


class LawNameTests(unittest.TestCase):
    def _parse(self, body):
        import law_application as L
        L.KNOWN_LAWS.update({"성폭력범죄의처벌및피해자보호등에관한법률", "형법", "저작권법", "상법"})
        r = L.parse({"source_id": "x", "date": "20060101", "text": "【법령의적용】" + body, "sections": [["법령의적용", 7, 7 + len(body)]]})
        return [(a["law"], a["article"]) for st in r["steps"] for a in st["articles"]]

    def test_heading_not_part_of_law_name(self):
        self.assertEqual(self._parse("1. 경합범의 처리 형법 제37조 전단, 제38조 제1항 제2호"), [("형법", "37"), ("형법", "38")])

    def test_long_name_with_mit(self):
        self.assertEqual(self._parse("성폭력범죄의 처벌 및 피해자보호 등에 관한 법률 제5조 제2항"),
                         [("성폭력범죄의처벌및피해자보호등에관한법률", "5")])

    def test_parenthetical_between_name_and_article(self):
        self.assertEqual(self._parse("구 저작권법(2006. 12. 28. 법률 제8101호로 전부 개정되기 전의 것) 제97조의5"), [("저작권법", "97-5")])

    def test_same_law_and_middle_dot(self):
        self.assertEqual(self._parse("각 형법 제347조, 같은 법 제30조, ·상법 제628조"), [("형법", "347"), ("형법", "30"), ("상법", "628")])
