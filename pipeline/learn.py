"""성과 평가 → 개선안 → 다음 콘텐츠에 반영하는 학습 고리.

1) 실험: 영상마다 실험 변수(테마·도입부 유형·사진 배경)를 가중치에 따라 고른다 (choose).
2) 평가: 게시 후 2일이 지난 영상의 조회수를 채널별 중앙값으로 나눈 상대 점수로 본다 (score).
3) 개선: 변수 값별 평균 점수로 가중치를 고친다. 표본이 3개 미만인 값은 계속 시험한다.
        일주일에 한 번 Claude가 상·하위 영상을 비교해 제목·도입부 교훈을 뽑는다 (update).
4) 적용: 가중치와 교훈은 data/playbook.json 에 저장되고, 다음 대본 지침과 렌더 설정에 들어간다 (guidance).
"""
import hashlib
import json
import random
import statistics
from datetime import datetime, timedelta, timezone

from . import metrics
from .config import DATA_DIR

PLAYBOOK = DATA_DIR / "playbook.json"
MIN_AGE_DAYS = 2
MIN_SAMPLES = 3

DIMS = {
    "theme": ["midnight", "ember", "paper", "forest"],
    "hook": ["question", "number", "contrast"],
    "photo": ["on", "clip"],   # on=공개 사진, clip=무료 스톡 영상 (둘 다 실패할 때만 그라데이션 off)
}
HOOK_GUIDE = {
    "question": "hook 장면은 시청자가 답을 궁금해할 질문으로 시작하세요.",
    "number": "hook 장면은 이번 달 가장 눈에 띄는 수치(플레이스홀더)를 첫 마디에 말하며 시작하세요.",
    "contrast": "hook 장면은 서로 엇갈리는 두 사실(예: 거래는 늘었는데 중위가는 내림)을 대비시켜 시작하세요. "
                "facts에서 실제로 엇갈릴 때만 쓰고, 아니면 핵심 한 줄로 시작하세요.",
}
LESSON_SCHEMA = {
    "type": "object",
    "properties": {"lessons": {"type": "array", "items": {"type": "string"}}},
    "required": ["lessons"], "additionalProperties": False,
}


def load() -> dict:
    if PLAYBOOK.exists():
        pb = json.loads(PLAYBOOK.read_text(encoding="utf-8"))
    else:
        pb = {}
    pb.setdefault("weights", {})
    for dim, vals in DIMS.items():
        w = pb["weights"].setdefault(dim, {})
        for v in vals:
            w.setdefault(v, 1.0)
    pb.setdefault("lessons", [])
    pb.setdefault("lessons_at", None)
    pb.setdefault("history", [])
    return pb


def save(pb: dict) -> None:
    PLAYBOOK.write_text(json.dumps(pb, ensure_ascii=False, indent=1), encoding="utf-8")


def choose(pb: dict, slug: str) -> dict:
    """slug로 고정된 난수로 실험 변수 조합을 고른다 (같은 글은 다시 만들어도 같은 조합)."""
    rng = random.Random(int(hashlib.sha256(slug.encode()).hexdigest()[:12], 16))
    out = {}
    for dim, vals in DIMS.items():
        w = [max(0.05, float(pb["weights"][dim].get(v, 1.0))) for v in vals]
        out[dim] = rng.choices(vals, weights=w, k=1)[0]
    return out


def guidance(pb: dict, variant: dict) -> str:
    lines = [HOOK_GUIDE[variant["hook"]]]
    if pb.get("lessons"):
        lines.append("지금까지 성과 분석에서 얻은 교훈 (숫자 규칙·금지 표현 규칙이 항상 우선):")
        lines += [f"- {x}" for x in pb["lessons"][:6]]
    return "\n".join(lines)


def score(conn) -> dict:
    """slug → 상대 점수(1.0 = 그 채널의 보통). 조회수가 없는 채널은 좋아요+댓글로 본다."""
    metrics._ensure(conn)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MIN_AGE_DAYS)).isoformat()
    per_platform: dict = {}
    for r in conn.execute(
            """SELECT m.slug, m.platform, m.views, m.likes, m.comments, m.retention FROM metrics m
               JOIN videos v ON v.slug = m.slug
               WHERE v.created_at <= ? AND m.day = (SELECT MAX(day) FROM metrics x
                                                    WHERE x.slug = m.slug AND x.platform = m.platform)""",
            (cutoff,)):
        val = r["views"] if r["views"] is not None else (r["likes"] or 0) + (r["comments"] or 0)
        if r["retention"] is not None and r["views"] is not None:
            val = r["views"] * (0.5 + r["retention"] / 100)   # 끝까지 본 비율이 높을수록 가산
        per_platform.setdefault(r["platform"], {})[r["slug"]] = val
    rel: dict = {}
    for plat, vals in per_platform.items():
        if len(vals) < 2:
            continue
        med = statistics.median(vals.values())
        for slug, v in vals.items():
            rel.setdefault(slug, []).append((v + 1) / (med + 1))
    return {s: round(statistics.mean(x), 3) for s, x in rel.items()}


def update(conn, writer_factory=None) -> dict:
    """가중치를 다시 계산하고, 주 1회 교훈을 갱신한다. 요약을 돌려준다."""
    pb = load()
    scores = score(conn)
    rows = {r["slug"]: r for r in conn.execute("SELECT slug, title, variant FROM videos WHERE variant IS NOT NULL")}
    stats: dict = {d: {} for d in DIMS}
    for slug, sc in scores.items():
        if slug not in rows:
            continue
        var = json.loads(rows[slug]["variant"])
        for d in DIMS:
            if var.get(d) in DIMS[d]:
                stats[d].setdefault(var[d], []).append(sc)
    for d, vals in DIMS.items():
        for v in vals:
            xs = stats[d].get(v, [])
            pb["weights"][d][v] = round(min(2.5, max(0.4, statistics.mean(xs))), 2) if len(xs) >= MIN_SAMPLES else 1.0
    summary = {"scored": len(scores), "weights": pb["weights"],
               "samples": {d: {v: len(x) for v, x in s.items()} for d, s in stats.items()}}

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    due = not pb["lessons_at"] or pb["lessons_at"] < week_ago
    if writer_factory and due and len(scores) >= 8:
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        def line(slug, sc):
            t = conn.execute("SELECT title, variant FROM videos WHERE slug = ?", (slug,)).fetchone()
            return f"- 점수 {sc} | {t['title']} | {t['variant'] or ''}" if t else None
        table = "\n".join(filter(None, [line(s, sc) for s, sc in ranked[:6]] + ["…"]
                                 + [line(s, sc) for s, sc in ranked[-6:]]))
        system = ("당신은 부동산 데이터 숏폼 채널의 성과 분석가입니다. 아래는 영상별 상대 성과(1.0이 보통)와 제목, "
                  "실험 변수입니다. 상위와 하위를 비교해 다음 영상의 제목과 도입부에 바로 적용할 수 있는 구체적인 "
                  "교훈을 최대 5개 쓰세요. 표본이 적어 확실하지 않은 것은 쓰지 마세요. "
                  "낚시성 표현, 투자 권유, 가격 전망 단정은 교훈으로 쓸 수 없습니다. 숫자를 직접 쓰지 말고 원칙만 쓰세요.")
        try:
            res = writer_factory()._call(system, table, LESSON_SCHEMA, "medium", 2000)
            pb["lessons"] = [str(x)[:200] for x in res.get("lessons", [])][:5]
            pb["lessons_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            summary["lessons_updated"] = True
        except Exception as e:
            summary["lessons_error"] = f"{type(e).__name__}"
    pb["history"] = (pb["history"] + [{"at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                       "scored": len(scores), "weights": json.loads(json.dumps(pb["weights"]))}])[-30:]
    pb["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save(pb)
    summary["lessons"] = pb["lessons"]
    return summary
