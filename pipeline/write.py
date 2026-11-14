"""Claude로 글 초안을 쓰고 2차 검수한다."""
import json
import os

ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "body_md": {"type": "string"},
        "faq": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"question": {"type": "string"}, "answer": {"type": "string"}},
                "required": ["question", "answer"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "description", "tags", "body_md", "faq"],
    "additionalProperties": False,
}

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean"},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["approved", "issues"],
    "additionalProperties": False,
}

SYSTEM = """당신은 한국 부동산 실거래 데이터를 해설하는 데이터 저널리스트입니다.
독자는 집을 사고팔거나 시세를 확인하려는 일반인입니다. 정확하고, 읽기 쉽고, 실제로 도움이 되는 글을 씁니다.

## 숫자 규칙 (가장 중요)
- 글에 들어가는 모든 수치·금액·비율·건수·날짜는 반드시 제공된 facts의 플레이스홀더 {{키}} 로만 씁니다.
  예: "이번 달 거래는 {{trade_count}}로 전월({{prev_count}}) 대비 {{count_change}} 변했습니다."
- facts에 없는 숫자를 직접 쓰거나 계산하거나 추정하지 마세요. 아라비아 숫자를 직접 타이핑하지 마세요.
- facts 값이 "비교 불가"나 "자료 없음"이면 해당 비교는 언급하지 않거나 "비교할 자료가 아직 없다"고만 씁니다.
- 제목(title)과 설명(description)에도 같은 규칙이 적용됩니다.

## 구성 규칙
- body_md는 마크다운입니다. ## 소제목을 3~5개 사용하고, 첫 문단은 핵심 요약입니다.
- 지정된 표 마커(예: [[TABLE:top10]])와 [[CHART]] 마커를 본문의 적절한 위치에 각각 정확히 한 번, 독립된 줄로 넣습니다.
- 표와 차트를 그대로 반복하지 말고, 그 안에서 읽어낼 수 있는 의미를 해설합니다.
- 본문 분량은 표를 제외하고 1,200~2,000자 정도.
- 출처·면책 문구는 시스템이 자동으로 붙이므로 쓰지 않습니다.

## 금지
- 매수·매도 권유, 가격 전망 단정("오를 것", "지금이 기회"), 과장·낚시성 표현.
- 데이터로 확인할 수 없는 원인 단정(정책·금리 등 외부 요인은 "~일 수 있다" 수준으로만, 또는 언급하지 않음).
- 특정 단지 비방.

## 기타
- title: 검색 의도를 반영한 자연스러운 제목, 60자 이내.
- description: 검색 결과에 보일 요약, 80~150자.
- tags: 3~6개.
- faq: 독자가 궁금해할 질문 3개와 답. 답에도 숫자 규칙 적용.
"""

SHORTS_SCENES = ["hook", "volume", "price", "top_deal", "busy", "outro"]

_scene = {
    "type": "object",
    "properties": {"headline": {"type": "string"}, "narration": {"type": "string"}},
    "required": ["headline", "narration"],
    "additionalProperties": False,
}
SHORTS_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "scenes": {
            "type": "object",
            "properties": {k: _scene for k in SHORTS_SCENES},
            "required": SHORTS_SCENES,
            "additionalProperties": False,
        },
    },
    "required": ["title", "description", "hashtags", "scenes"],
    "additionalProperties": False,
}

SHORTS_SYSTEM = """당신은 부동산 데이터 숏폼(세로 영상, 약 40초) 대본 작가입니다.
화면에는 시스템이 숫자 카드와 차트를 그리고, 당신은 장면별 짧은 제목(headline)과 내레이션(narration)을 씁니다.

## 숫자 규칙 (가장 중요)
- 모든 수치·금액·비율·건수·날짜는 facts 플레이스홀더 {{키}} 로만 씁니다. 아라비아 숫자를 직접 쓰지 마세요.
- facts 값이 "비교 불가"/"자료 없음"이면 그 비교는 말하지 않습니다.

## 장면 (순서 고정)
- hook: 첫 2초에 시선을 끄는 질문이나 핵심 한 줄 (지역·월 언급)
- volume: 거래 건수와 전월 대비 변화
- price: 중위 거래가와 변화 (화면에 월별 추이 차트가 나옴)
- top_deal: 이번 달 최고가 거래 단지·면적·금액
- busy: 거래가 많았던 단지들 또는 동
- outro: "단지별 표는 블로그에서 확인하세요" 취지의 마무리 (구독 권유는 한 마디 이하)

## 형식
- narration: 장면당 한두 문장, 숫자를 채웠을 때 60자 안팎. 구어체, 또박또박 읽히는 문장.
- headline: 화면 상단 큰 글씨, 15자 이내.
- title: 유튜브 제목 60자 이내, 끝에 #Shorts 를 붙이지 마세요(시스템이 붙임).
- description: 2~3문장 요약. hashtags: 3~5개, # 없이.
- 매수·매도 권유, 가격 전망 단정, 과장·낚시 표현 금지.
"""

KIND_GUIDE = {
    "gu_monthly": "구 단위 월간 아파트 매매 실거래 리포트입니다. 사용할 마커: [[TABLE:top10]], [[CHART]] (월별 거래량·중위가 추이).",
    "complex": "개별 아파트 단지의 실거래가 정리 페이지입니다. 사용할 마커: [[TABLE:areas]], [[TABLE:recent]], [[CHART]] (거래 시점별 가격 분포).",
}


class WriterError(RuntimeError):
    pass


def _user_prompt(kind: str, facts: dict) -> str:
    lines = [f"- {{{{{k}}}}} = {v}" for k, v in facts.items()]
    return (f"{KIND_GUIDE[kind]}\n\n사용 가능한 facts (플레이스홀더 = 현재 값):\n"
            + "\n".join(lines)
            + "\n\n위 규칙에 따라 글을 작성하세요.")


class ClaudeWriter:
    def __init__(self, model: str, effort: str = "medium"):
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise WriterError("ANTHROPIC_API_KEY 환경변수가 없습니다.")
        self.client = anthropic.Anthropic(max_retries=4)
        self.model = model
        self.effort = effort
        self.usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}

    def _call(self, system: str, user: str, schema: dict, effort: str, max_tokens: int) -> dict:
        resp = self.client.beta.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        )
        for k in self.usage:
            self.usage[k] += getattr(resp.usage, k, 0) or 0
        if resp.stop_reason == "refusal":
            raise WriterError("모델이 요청을 거절했습니다.")
        if resp.stop_reason == "max_tokens":
            raise WriterError("출력이 max_tokens에서 잘렸습니다.")
        text = next((b.text for b in resp.content if b.type == "text"), None)
        if not text:
            raise WriterError("응답에 텍스트가 없습니다.")
        return json.loads(text)

    def write(self, kind: str, facts: dict, feedback: list[str] | None = None) -> dict:
        user = _user_prompt(kind, facts)
        if feedback:
            user += ("\n\n이전 초안이 자동 검수에서 아래 이유로 반려되었습니다. 모두 고쳐서 다시 쓰세요:\n- "
                     + "\n- ".join(feedback))
        return self._call(SYSTEM, user, ARTICLE_SCHEMA, self.effort, 16000)

    def write_shorts(self, facts: dict, feedback: list[str] | None = None) -> dict:
        user = ("사용 가능한 facts (플레이스홀더 = 현재 값):\n"
                + "\n".join(f"- {{{{{k}}}}} = {v}" for k, v in facts.items())
                + "\n\n규칙에 따라 숏폼 대본을 작성하세요.")
        if feedback:
            user += "\n\n이전 대본이 아래 이유로 반려되었습니다. 모두 고치세요:\n- " + "\n- ".join(feedback)
        return self._call(SHORTS_SYSTEM, user, SHORTS_SCHEMA, self.effort, 8000)

    def review(self, rendered_md: str, facts: dict) -> dict:
        system = (
            "당신은 부동산 데이터 기사 편집장입니다. 발행 전 최종 검수를 합니다. "
            "다음 중 하나라도 있으면 approved=false 로 하고 issues에 구체적으로 적으세요: "
            "(1) facts와 모순되는 서술이나 수치 해석 오류(예: 감소를 증가로 표현), "
            "(2) 매수·매도 권유나 가격 전망 단정, (3) 근거 없는 원인 단정, "
            "(4) 문장이 깨지거나 같은 내용이 반복되어 읽기 어려움, (5) 사실과 다른 일반 상식. "
            "사소한 문체 취향은 문제로 삼지 마세요."
        )
        user = ("facts:\n" + json.dumps(facts, ensure_ascii=False, indent=1)
                + "\n\n검수할 글:\n" + rendered_md)
        return self._call(system, user, REVIEW_SCHEMA, "low", 4000)


class FakeWriter:
    """API 키 없이 파이프라인 전체를 시험하기 위한 가짜 작성기."""

    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}

    def write(self, kind: str, facts: dict, feedback: list[str] | None = None) -> dict:
        if kind == "gu_monthly":
            body = (
                "{{month}} {{region}} 아파트 매매는 {{trade_count}}가 신고되었습니다. "
                "중위 거래가는 {{median_price}}이며 전월 대비 {{median_change}} 변동했습니다.\n\n"
                "## 거래량과 가격 흐름\n\n"
                + "이 구간은 시험용 문장입니다. 거래량과 중위 가격의 움직임을 함께 살펴봅니다. " * 12
                + "\n\n[[CHART]]\n\n## 고가 거래 상위 단지\n\n"
                "가장 비싸게 거래된 곳은 {{top_apt}} {{top_area}}로 {{top_price}}였습니다.\n\n[[TABLE:top10]]\n\n"
                "## 지역별 특징\n\n"
                + "거래가 가장 많았던 동은 {{top_umd}}({{top_umd_count}})입니다. 시험용 문장을 이어 씁니다. " * 10
            )
            title = "{{month}} {{region}} 아파트 실거래 리포트: 거래 {{trade_count}}"
        else:
            body = (
                "{{apt}}({{region}} {{umd}})의 실거래는 {{trade_count}}가 확인됩니다.\n\n"
                "## 주력 평형 시세\n\n"
                + "가장 많이 거래된 {{main_area}}의 중위 거래가는 {{main_median}}입니다. 시험용 문장입니다. " * 10
                + "\n\n[[TABLE:areas]]\n\n## 가격 흐름\n\n[[CHART]]\n\n"
                + "최근 거래는 {{latest_date}} {{latest_price}}입니다. 시험용 문장을 조금 더 길게 이어 씁니다. " * 14
                + "\n\n## 최근 거래 내역\n\n[[TABLE:recent]]\n"
            )
            title = "{{apt}} 실거래가 정리 ({{region}} {{umd}})"
        return {
            "title": title,
            "description": "{{region}} 아파트 실거래 데이터를 국토교통부 공개 자료로 정리했습니다. 거래 건수, 중위 가격, 최고가 거래를 한눈에 확인하세요.",
            "tags": ["실거래가", facts.get("region", "서울")],
            "body_md": body,
            "faq": [{"question": "자료 출처는 어디인가요?",
                     "answer": "국토교통부 실거래가 공개 자료이며 {{as_of}} 기준입니다."}] * 3,
        }

    def write_shorts(self, facts: dict, feedback: list[str] | None = None) -> dict:
        s = lambda h, n: {"headline": h, "narration": n}  # noqa: E731
        return {
            "title": "{{month}} {{region}} 아파트 거래 {{trade_count}}, 최고가는?",
            "description": "{{region}} 아파트 실거래를 정리했습니다. 단지별 표는 블로그에서 확인하세요.",
            "hashtags": ["실거래가", "부동산", "{{region}}"],
            "scenes": {
                "hook": s("{{region}} 실거래", "{{month}} {{region}} 아파트, 얼마에 거래됐을까요?"),
                "volume": s("거래량", "거래는 {{trade_count}}로 전월보다 {{count_change}} 변했습니다."),
                "price": s("중위 거래가", "중위 거래가는 {{median_price}}, 전월 대비 {{median_change}}입니다."),
                "top_deal": s("최고가 거래", "최고가는 {{top_apt}} {{top_area}}, {{top_price}}였습니다."),
                "busy": s("거래 많은 단지", "거래가 가장 많은 단지는 {{busy1_apt}}였습니다."),
                "outro": s("자세한 표는 블로그", "단지별 상세 표는 블로그에서 확인하세요."),
            },
        }

    def review(self, rendered_md: str, facts: dict) -> dict:
        return {"approved": True, "issues": []}
