"""월간 리포트 글 → 숏폼 세로 영상(mp4). 같은 facts를 쓰므로 블로그와 숫자가 항상 일치한다."""
import json
import shutil
from pathlib import Path

from . import analyze, assets, db, learn, motion, qa, render, tts
from .config import ROOT
from .write import SHORTS_SCENES

VIDEO_DIR = ROOT / "videos"


def plan(conn, cfg) -> list:
    """아직 영상이 없는 월간 리포트. 최신 월, 거래 많은 순."""
    rows = conn.execute(
        """SELECT p.* FROM posts p LEFT JOIN videos v ON v.slug = p.slug
           WHERE p.kind = 'gu_monthly' AND v.slug IS NULL
           ORDER BY json_extract(p.charts, '$[0].ym') DESC, p.trade_count DESC"""
    ).fetchall()
    return rows[: cfg["shorts"]["max_per_run"]]


def check_script(script: dict, facts: dict, cfg: dict) -> list[str]:
    problems = []
    allowed = qa._allowed_numbers(facts)
    texts = {"title": script["title"], "description": script["description"],
             "hashtags": " ".join(script["hashtags"])}
    for k in SHORTS_SCENES:
        texts[f"{k}.headline"] = script["scenes"][k]["headline"]
        texts[f"{k}.narration"] = script["scenes"][k]["narration"]
    for name, text in texts.items():
        for key in qa.PLACEHOLDER.findall(text):
            if key not in facts:
                problems.append(f"{name}: 존재하지 않는 플레이스홀더 {{{{{key}}}}}")
        for num in qa.DIGITS.findall(qa.PLACEHOLDER.sub("", text)):
            if num not in allowed and num.replace(",", "") not in allowed:
                problems.append(f"{name}: 근거 없는 숫자 '{num}' 직접 기재")
    if problems:
        return problems  # 아래 길이 검사는 치환이 가능해야 함
    for k in SHORTS_SCENES:
        n = len(qa.fill(script["scenes"][k]["narration"], facts))
        if n > cfg["shorts"]["max_narration_chars"]:
            problems.append(f"{k}.narration: 너무 김 ({n}자)")
        if not n:
            problems.append(f"{k}.narration: 비어 있음")
        if len(qa.fill(script["scenes"][k]["headline"], facts)) > 20:
            problems.append(f"{k}.headline: 20자 초과")
    if len(qa.fill(script["title"], facts)) > 70:
        problems.append("title: 70자 초과")
    joined = " ".join(texts.values())
    for phrase in cfg["quality"]["banned_phrases"]:
        if phrase in joined:
            problems.append(f"금지 표현 포함: '{phrase}'")
    return problems


def produce(conn, cfg, writer, post, out_dir: Path = VIDEO_DIR) -> tuple[bool, list[str]]:
    facts = json.loads(post["facts_json"])
    spec = json.loads(post["charts"])[0]
    work = out_dir / f"_{post['slug']}"
    work.mkdir(parents=True, exist_ok=True)
    try:
        playbook = learn.load()
        variant = learn.choose(playbook, post["slug"])
        script, problems, feedback = None, [], None
        for _ in range(2):
            script = writer.write_shorts(facts, feedback, learn.guidance(playbook, variant))
            problems = check_script(script, facts, cfg)
            if not problems:
                break
            feedback = problems
        if problems:
            db.log_rejection(conn, "video:" + post["slug"], problems)
            return False, problems

        m = analyze.gu_monthly(conn, spec["sgg"], spec["gu"], spec["ym"], facts["as_of"])
        trend = m["trend"] if m else []

        s = cfg["shorts"]
        site = cfg["site"]
        # 1) 음성을 먼저 만들어 장면 길이를 정한다
        parts, total = [], 0.0
        for i, k in enumerate(SHORTS_SCENES):
            sc = script["scenes"][k]
            narration = qa.fill(sc["narration"], facts)
            audio = work / f"{i}.mp3"
            secs = tts.speak(narration, audio, s["tts_provider"], s["voice"]) + 0.35
            parts.append((k, qa.fill(sc["headline"], facts), narration, audio, secs))
            total += secs
        if total > s["max_seconds"]:
            problems = [f"영상 길이 {total:.1f}초 > {s['max_seconds']}초"]
            db.log_rejection(conn, "video:" + post["slug"], problems)
            return False, problems

        # 2) 공개 사진 배경 (실험 변수 photo=on 이고 조건에 맞는 사진이 있을 때만)
        theme = motion.THEMES[variant["theme"]]
        photo, credit_short, credit_full = None, None, None
        if variant["photo"] == "on" and s.get("public_photos", True):
            path, credit_short, credit_full = assets.region_photo(conn, writer, facts["region"], work)
            photo = motion.load_photo(path, theme)
        variant["photo"] = "on" if photo is not None else "off"   # 실제로 쓴 값으로 기록

        # 3) 장면별 모션 렌더
        segments, offset = [], 0.0
        for i, (k, headline, narration, audio, secs) in enumerate(parts):
            scene = motion.Scene(k, headline, narration, facts, trend, theme, site["title"], site["base_url"], secs,
                                 photo_bg=photo if k in ("hook", "outro") else None,
                                 credit=credit_short if (photo is not None and k == "hook") else None,
                                 intro=i > 0)
            if i == 0:
                scene.frame(secs - 0.1, 0.0).save(out_dir / f"{post['slug']}.jpg", quality=90)  # 썸네일 후보
            seg = work / f"{i}.mp4"
            motion.render_scene(scene, audio, seg, offset, total)
            segments.append(seg)
            offset += secs

        out = out_dir / f"{post['slug']}.mp4"
        render.concat(segments, out)

        post_url = f"{site['base_url']}/posts/{post['slug']}/"
        tags = [qa.fill(t, facts).lstrip("#") for t in script["hashtags"]][:5]
        title = qa.fill(script["title"], facts)[:90] + " #Shorts"
        desc = (qa.fill(script["description"], facts)
                + f"\n\n단지별 상세 표: {post_url}"
                + "\n자료: 국토교통부 실거래가 공개시스템. 정보 제공 목적이며 투자 권유가 아닙니다."
                + (f"\n{credit_full}" if photo is not None and credit_full else "")
                + "\n\n" + " ".join("#" + t.replace(" ", "") for t in tags))
        ts = db.now_iso()
        conn.execute(
            """INSERT OR REPLACE INTO videos (slug, title, description, tags, seconds, status,
                   created_at, updated_at, variant) VALUES (?, ?, ?, ?, ?, 'rendered', ?, ?, ?)""",
            (post["slug"], title, desc, json.dumps(tags, ensure_ascii=False), round(total, 1), ts, ts,
             json.dumps(variant, ensure_ascii=False)))
        conn.commit()
        return True, []
    finally:
        shutil.rmtree(work, ignore_errors=True)
