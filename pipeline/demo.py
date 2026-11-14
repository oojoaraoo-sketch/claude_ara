"""API 키 없이 시험할 때 쓰는 가상 거래 데이터. 실제 사이트에는 절대 쓰지 않는다."""
import hashlib
import random
from datetime import date

from .collect import recent_months

APTS = [("가람마을1단지", "역삼동", 2004), ("푸른숲아파트", "대치동", 1999), ("한빛타워", "도곡동", 2015),
        ("새솔마을", "개포동", 2010), ("은행나무단지", "일원동", 1993), ("느티나무아파트", "수서동", 2008)]


def make_trades(sgg_codes: list[str], months: int = 13, seed: int = 7, today: date | None = None) -> list[dict]:
    rnd = random.Random(seed)
    rows = []
    for sgg in sgg_codes:
        for i, ym in enumerate(reversed(recent_months(months, today))):
            for _ in range(rnd.randint(25, 45)):
                name, umd, by = rnd.choice(APTS)
                area = rnd.choice([59.97, 84.95, 114.8])
                price = int((area * 1500 + i * 300 + rnd.randint(-8000, 8000)) // 10 * 10)
                day = rnd.randint(1, 28)
                row = {"sgg_cd": sgg, "umd": umd, "apt_seq": f"{sgg}-{name}", "apt_name": name,
                       "jibun": "1", "area": area, "floor": rnd.randint(1, 25), "build_year": by,
                       "deal_date": f"{ym[:4]}-{ym[4:]}-{day:02d}", "deal_ym": ym, "price": price,
                       "canceled": 1 if rnd.random() < 0.03 else 0, "dealing_type": "중개거래"}
                key = f"{sgg}|{name}|{area}|{row['floor']}|{row['deal_date']}|{price}|{rnd.random()}"
                row["id"] = hashlib.sha1(key.encode()).hexdigest()[:20]
                rows.append(row)
    return rows
