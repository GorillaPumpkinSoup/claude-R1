"""규칙 기반 신호 산출. 예측/추천이 아니라 정량 지표를 정성 라벨로 요약하는 것뿐이다."""

SIGNAL_STRONG = "강세"
SIGNAL_NEUTRAL = "중립"
SIGNAL_WEAK = "약세"


def score_asset(indicators: dict) -> dict:
    price = indicators["price"]
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    rsi14 = indicators.get("rsi14")
    momentum20 = indicators.get("momentum20")

    score = 0
    reasons: list[str] = []

    if ma20 is not None:
        if price > ma20:
            score += 1
            reasons.append("현재가가 20일 이평선 위")
        else:
            score -= 1
            reasons.append("현재가가 20일 이평선 아래")

    if ma60 is not None:
        if price > ma60:
            score += 1
            reasons.append("현재가가 60일 이평선 위")
        else:
            score -= 1
            reasons.append("현재가가 60일 이평선 아래")

    if rsi14 is not None:
        if rsi14 >= 70:
            score -= 1
            reasons.append(f"RSI {rsi14:.0f} 과매수 구간")
        elif rsi14 <= 30:
            score += 1
            reasons.append(f"RSI {rsi14:.0f} 과매도 구간")

    if momentum20 is not None:
        if momentum20 > 0.05:
            score += 1
            reasons.append(f"20일 모멘텀 +{momentum20 * 100:.1f}%")
        elif momentum20 < -0.05:
            score -= 1
            reasons.append(f"20일 모멘텀 {momentum20 * 100:.1f}%")

    if score >= 2:
        label = SIGNAL_STRONG
    elif score <= -2:
        label = SIGNAL_WEAK
    else:
        label = SIGNAL_NEUTRAL

    return {"score": score, "label": label, "reasons": reasons}


def label_for_score(score: float) -> str:
    if score >= 0.5:
        return SIGNAL_STRONG
    if score <= -0.5:
        return SIGNAL_WEAK
    return SIGNAL_NEUTRAL
