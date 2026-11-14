"""자동 품질 게이트: 사람 검수 대신 규칙 검사 + (선택) Claude 2차 검수."""
import re

PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
MARKER = re.compile(r"\[\[(CHART|TABLE:[a-z0-9_]+)\]\]")
DIGITS = re.compile(r"\d+(?:[.,]\d+)*")
# 설명에 자연스럽게 쓰일 수 있는 고정 상수 (평 환산, 소형 기준, 신고기한)
ALWAYS_OK = {"3.3", "60", "30"}

REQUIRED_MARKERS = {
    "gu_monthly": {"CHART", "TABLE:top10"},
    "complex": {"CHART", "TABLE:areas", "TABLE:recent"},
}


def _allowed_numbers(facts: dict) -> set[str]:
    ok = set(ALWAYS_OK)
    for v in facts.values():
        for d in DIGITS.findall(str(v)):
            ok.add(d)
            ok.add(d.replace(",", ""))
            ok.update(re.split(r"[.,-]", d))
    return ok


def check(kind: str, draft: dict, facts: dict, cfg: dict) -> list[str]:
    problems = []
    texts = {"title": draft["title"], "description": draft["description"], "body": draft["body_md"]}
    for i, qa in enumerate(draft["faq"]):
        texts[f"faq{i}"] = qa["question"] + " " + qa["answer"]

    allowed = _allowed_numbers(facts)
    for name, text in texts.items():
        for key in PLACEHOLDER.findall(text):
            if key not in facts:
                problems.append(f"{name}: 존재하지 않는 플레이스홀더 {{{{{key}}}}}")
        stripped = MARKER.sub("", PLACEHOLDER.sub("", text))
        for num in DIGITS.findall(stripped):
            if num not in allowed and num.replace(",", "") not in allowed:
                problems.append(f"{name}: 근거 없는 숫자 '{num}' 직접 기재")

    body = draft["body_md"]
    markers = MARKER.findall(body)
    for m in REQUIRED_MARKERS[kind]:
        n = markers.count(m)
        if n != 1:
            problems.append(f"body: 마커 [[{m}]] {n}회 (정확히 1회 필요)")

    prose = MARKER.sub("", PLACEHOLDER.sub("값", body))
    if len(prose) < cfg["quality"]["min_chars"]:
        problems.append(f"body: 분량 부족 ({len(prose)}자 < {cfg['quality']['min_chars']}자)")
    if len(re.findall(r"^##\s", body, flags=re.M)) < 3:
        problems.append("body: 소제목(##) 3개 미만")

    all_text = " ".join(texts.values())
    for phrase in cfg["quality"]["banned_phrases"]:
        if phrase in all_text:
            problems.append(f"금지 표현 포함: '{phrase}'")

    if not (10 <= len(draft["title"]) <= 80):
        problems.append(f"title 길이 이상 ({len(draft['title'])}자)")
    if not (40 <= len(draft["description"]) <= 200):
        problems.append(f"description 길이 이상 ({len(draft['description'])}자)")
    if len(draft["faq"]) < 2:
        problems.append("faq 2개 미만")
    return problems


def fill(text: str, facts: dict) -> str:
    return PLACEHOLDER.sub(lambda m: str(facts[m.group(1)]), text)


def render(draft: dict, facts: dict, tables: dict, chart_url: str, chart_alt: str) -> dict:
    """플레이스홀더 치환 + 표/차트 삽입 + FAQ/출처 부착. 최종 마크다운을 반환."""
    body = fill(draft["body_md"], facts)

    def marker(m):
        tag = m.group(1)
        if tag == "CHART":
            return f"![{chart_alt}]({chart_url})"
        return "\n" + tables[tag.split(":", 1)[1]] + "\n"

    body = MARKER.sub(marker, body)
    faq = [{"question": fill(q["question"], facts), "answer": fill(q["answer"], facts)}
           for q in draft["faq"]]
    body += "\n\n## 자주 묻는 질문\n\n" + "\n\n".join(
        f"**Q. {q['question']}**\n\nA. {q['answer']}" for q in faq)
    body += (
        "\n\n---\n\n"
        f"*자료: 국토교통부 실거래가 공개시스템(공공데이터포털 API), {facts['as_of']} 수집 기준. "
        "해제(취소)된 거래는 제외했으며, 신고 기한(계약 후 30일) 내 추가 신고로 수치가 바뀔 수 있습니다. "
        "이 글은 공개 데이터를 정리한 정보이며 투자 권유가 아닙니다.*"
    )
    return {
        "title": fill(draft["title"], facts),
        "description": fill(draft["description"], facts),
        "tags": [fill(t, facts) for t in draft["tags"]][:6],
        "body_md": body,
        "faq": faq,
    }
