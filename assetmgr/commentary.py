"""규칙 기반 지표/신호를 바탕으로 Claude API가 참고용 시장 해설을 생성한다."""

import json
import os

import anthropic

SYSTEM_PROMPT = (
    "당신은 개인 자산관리 대시보드의 시장 해설가입니다. "
    "제공되는 정량 지표(이동평균, RSI, 모멘텀, 변동성)와 규칙 기반 신호를 바탕으로 "
    "현재 시장 상황과 포트폴리오 배분 상태를 한국어로 간결하게 설명하세요. "
    "이것은 투자 자문이 아니라 참고용 코멘트이며, 확정적인 매수/매도 지시나 "
    "미래 수익 예측을 하지 않습니다. 출력은 4~6문장, 불릿 없이 자연스러운 문단으로 작성하세요."
)


def generate_commentary(snapshot: dict) -> str:
    client = anthropic.Anthropic()
    model = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

    payload = {
        "portfolio_score": snapshot["portfolio_score"],
        "portfolio_label": snapshot["portfolio_label"],
        "allocation_pct": snapshot["allocation_pct"],
        "assets": [
            {
                "label": a["label"],
                "class": a["class"],
                "signal": a.get("signal", {}).get("label"),
                "reasons": a.get("signal", {}).get("reasons"),
                "change_1d_pct": a.get("indicators", {}).get("change_1d_pct"),
            }
            for a in snapshot["assets"]
            if not a.get("error")
        ],
    }
    user_content = (
        "다음은 이번 시각의 포트폴리오 스냅샷입니다. "
        "이 데이터를 근거로 참고용 시장 해설을 작성해주세요.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": user_content}],
    )
    return next((b.text for b in response.content if b.type == "text"), "")
