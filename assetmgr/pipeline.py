"""보유 자산 -> 시세 조회 -> 지표/신호 계산 -> (선택) LLM 해설까지 한 번에 수행."""

import os
from datetime import datetime, timezone

from . import commentary as commentary_mod
from .indicators import compute_indicators
from .providers import crypto, stocks
from .signals import label_for_score, score_asset

CLASS_LABELS = {
    "stock": "주식",
    "crypto": "코인",
}


def _build_asset_entry(asset_class: str, ticker: str, label: str, quantity: float, history) -> dict:
    indicators = compute_indicators(history)
    signal = score_asset(indicators)
    value = indicators["price"] * quantity
    return {
        "class": asset_class,
        "ticker": ticker,
        "label": label,
        "quantity": quantity,
        "price": indicators["price"],
        "value": value,
        "indicators": indicators,
        "signal": signal,
        "error": None,
    }


def build_snapshot(portfolio: dict) -> dict:
    assets = []
    total_value = 0.0
    weighted_score = 0.0

    for item in portfolio.get("stocks", []) or []:
        ticker = item["ticker"]
        label = item.get("label", ticker)
        quantity = float(item["quantity"])
        try:
            data = stocks.fetch_stock_snapshot(ticker)
            entry = _build_asset_entry("stock", ticker, label, quantity, data["history"])
            assets.append(entry)
            total_value += entry["value"]
            weighted_score += entry["signal"]["score"] * entry["value"]
        except Exception as exc:  # 개별 종목 실패가 전체 스냅샷을 막지 않도록
            assets.append({
                "class": "stock", "ticker": ticker, "label": label,
                "quantity": quantity, "error": str(exc),
            })

    for item in portfolio.get("crypto", []) or []:
        symbol = item["symbol"]
        label = item.get("label", symbol)
        quantity = float(item["quantity"])
        try:
            data = crypto.fetch_crypto_snapshot(symbol)
            entry = _build_asset_entry("crypto", symbol, label, quantity, data["history"])
            assets.append(entry)
            total_value += entry["value"]
            weighted_score += entry["signal"]["score"] * entry["value"]
        except Exception as exc:
            assets.append({
                "class": "crypto", "ticker": symbol, "label": label,
                "quantity": quantity, "error": str(exc),
            })

    portfolio_score = weighted_score / total_value if total_value > 0 else 0.0

    allocation_value: dict[str, float] = {}
    for a in assets:
        if a.get("error"):
            continue
        allocation_value[a["class"]] = allocation_value.get(a["class"], 0.0) + a["value"]
    allocation_pct = {
        k: (v / total_value * 100 if total_value else 0.0) for k, v in allocation_value.items()
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_value": total_value,
        "portfolio_score": portfolio_score,
        "portfolio_label": label_for_score(portfolio_score),
        "allocation_value": allocation_value,
        "allocation_pct": allocation_pct,
        "assets": assets,
    }


def add_commentary(snapshot: dict) -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        snapshot["commentary"] = None
        snapshot["commentary_error"] = "ANTHROPIC_API_KEY가 설정되지 않아 LLM 해설을 건너뛰었습니다."
        return snapshot
    try:
        snapshot["commentary"] = commentary_mod.generate_commentary(snapshot)
        snapshot["commentary_error"] = None
    except Exception as exc:
        snapshot["commentary"] = None
        snapshot["commentary_error"] = str(exc)
    return snapshot
