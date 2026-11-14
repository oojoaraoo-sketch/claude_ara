import tempfile
import unittest
from datetime import date
from pathlib import Path

from pipeline import collect, db, generate, qa, site
from pipeline.config import load_config
from pipeline.demo import make_trades
from pipeline.write import FakeWriter

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header>
<body><items>
<item><aptNm>테스트아파트</aptNm><dealAmount>  82,500</dealAmount><excluUseAr>84.97</excluUseAr>
<floor>12</floor><buildYear>2008</buildYear><dealYear>2026</dealYear><dealMonth>10</dealMonth>
<dealDay>3</dealDay><umdNm>역삼동</umdNm><jibun>123</jibun><aptSeq>11680-111</aptSeq>
<cdealType> </cdealType><dealingGbn>중개거래</dealingGbn></item>
<item><aptNm>취소아파트</aptNm><dealAmount>50,000</dealAmount><excluUseAr>59.9</excluUseAr>
<floor>3</floor><buildYear>1999</buildYear><dealYear>2026</dealYear><dealMonth>10</dealMonth>
<dealDay>5</dealDay><umdNm>역삼동</umdNm><jibun>9</jibun><cdealType>O</cdealType></item>
</items><numOfRows>10</numOfRows><pageNo>1</pageNo><totalCount>2</totalCount></body></response>"""


class CollectTest(unittest.TestCase):
    def test_parse(self):
        rows, total = collect.parse_items(SAMPLE_XML, "11680")
        self.assertEqual(total, 2)
        self.assertEqual(rows[0]["price"], 82500)
        self.assertEqual(rows[0]["deal_date"], "2026-10-03")
        self.assertEqual(rows[0]["canceled"], 0)
        self.assertEqual(rows[1]["canceled"], 1)

    def test_auth_error(self):
        xml = ("<OpenAPI_ServiceResponse><cmmMsgHeader><returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR"
               "</returnAuthMsg></cmmMsgHeader></OpenAPI_ServiceResponse>")
        with self.assertRaises(collect.CollectError):
            collect.parse_items(xml, "11680")

    def test_recent_months(self):
        self.assertEqual(collect.recent_months(3, date(2026, 2, 10)), ["202602", "202601", "202512"])


class QATest(unittest.TestCase):
    cfg = load_config()
    facts = {"region": "강남구", "trade_count": "120건", "median_price": "25억 3,000만원", "as_of": "2026-11-14"}

    def draft(self, body, title="강남구 아파트 거래 {{trade_count}} 정리 리포트"):
        filler = "\n\n## 소제목 하나\n\n## 소제목 둘\n\n## 소제목 셋\n\n" + "충분한 분량의 해설 문장입니다. " * 80
        return {"title": title, "description": "강남구 아파트 실거래 데이터를 정리했습니다. 거래 건수와 중위 가격을 확인하세요.",
                "tags": ["강남구"], "body_md": body + filler + "\n\n[[CHART]]\n\n[[TABLE:top10]]\n",
                "faq": [{"question": "출처?", "answer": "국토교통부 {{as_of}}"}] * 3}

    def test_clean_passes(self):
        self.assertEqual(qa.check("gu_monthly", self.draft("거래는 {{trade_count}}입니다."), self.facts, self.cfg), [])

    def test_raw_number_rejected(self):
        p = qa.check("gu_monthly", self.draft("거래는 135건으로 늘었습니다."), self.facts, self.cfg)
        self.assertTrue(any("135" in x for x in p))

    def test_number_from_facts_allowed(self):
        self.assertEqual(qa.check("gu_monthly", self.draft("거래 120건."), self.facts, self.cfg), [])

    def test_unknown_placeholder(self):
        p = qa.check("gu_monthly", self.draft("{{made_up}}"), self.facts, self.cfg)
        self.assertTrue(any("made_up" in x for x in p))

    def test_banned_phrase(self):
        p = qa.check("gu_monthly", self.draft("지금 사야 합니다."), self.facts, self.cfg)
        self.assertTrue(any("금지" in x for x in p))

    def test_render_fills(self):
        out = qa.render(self.draft("거래 {{trade_count}}"), self.facts, {"top10": "|a|"}, "/c.png", "alt")
        self.assertIn("거래 120건", out["body_md"])
        self.assertNotIn("{{", out["body_md"])
        self.assertIn("![alt](/c.png)", out["body_md"])


class EndToEndTest(unittest.TestCase):
    def test_demo_pipeline(self):
        cfg = load_config()
        with tempfile.TemporaryDirectory() as tmp:
            conn = db.connect(Path(tmp) / "t.db")
            today = date(2026, 11, 14)
            db.upsert_trades(conn, make_trades(["11680", "11650"], today=today))
            jobs = generate.plan(conn, cfg, today)
            self.assertTrue(jobs)
            for job in jobs:
                ok, problems = generate.produce(conn, cfg, FakeWriter(), job, "2026-11-14")
                self.assertTrue(ok, problems)
            # 같은 데이터로 다시 계획하면 할 일이 줄어야 함 (중복 생성 방지)
            again = {j["slug"] for j in generate.plan(conn, cfg, today)}
            self.assertFalse(again & {j["slug"] for j in jobs})
            out = Path(tmp) / "public"
            n = site.build(conn, cfg, out)
            self.assertEqual(n, len(jobs))
            self.assertTrue((out / "sitemap.xml").exists())
            html = (out / "posts" / jobs[0]["slug"] / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("{{", html)
            conn.close()


class ShortsTest(unittest.TestCase):
    def test_script_check_and_render(self):
        from pipeline import shorts
        cfg = load_config()
        cfg["shorts"]["tts_provider"] = "silent"
        with tempfile.TemporaryDirectory() as tmp:
            conn = db.connect(Path(tmp) / "t.db")
            today = date(2026, 11, 14)
            db.upsert_trades(conn, make_trades(["11680"], today=today))
            for job in generate.plan(conn, cfg, today):
                if job["kind"] == "gu_monthly":
                    generate.produce(conn, cfg, FakeWriter(), job, "2026-11-14")
            posts = shorts.plan(conn, cfg)
            self.assertTrue(posts)
            facts = __import__("json").loads(posts[0]["facts_json"])

            bad = FakeWriter().write_shorts(facts)
            bad["scenes"]["volume"]["narration"] = "거래가 777건 늘었습니다."
            self.assertTrue(any("777" in p for p in shorts.check_script(bad, facts, cfg)))
            self.assertEqual(shorts.check_script(FakeWriter().write_shorts(facts), facts, cfg), [])

            ok, problems = shorts.produce(conn, cfg, FakeWriter(), posts[0], Path(tmp) / "v")
            self.assertTrue(ok, problems)
            self.assertTrue((Path(tmp) / "v" / f"{posts[0]['slug']}.mp4").stat().st_size > 10000)
            v = conn.execute("SELECT * FROM videos").fetchone()
            self.assertTrue(v["title"].endswith("#Shorts"))
            self.assertIn("/posts/", v["description"])
            self.assertLessEqual(v["seconds"], cfg["shorts"]["max_seconds"])
            # 이미 영상이 있는 글은 다시 계획되지 않음
            self.assertNotIn(posts[0]["slug"], [p["slug"] for p in shorts.plan(conn, cfg)])
            conn.close()


if __name__ == "__main__":
    unittest.main()
