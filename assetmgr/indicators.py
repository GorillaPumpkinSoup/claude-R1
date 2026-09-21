"""가격 시계열로부터 정량 지표를 계산한다. 예측이 아닌 현재 상태 요약 지표들이다."""

import numpy as np
import pandas as pd


def moving_average(series: pd.Series, window: int) -> float | None:
    if len(series) < window:
        return None
    return float(series.rolling(window).mean().iloc[-1])


def rsi(series: pd.Series, window: int = 14) -> float | None:
    if len(series) < window + 1:
        return None
    delta = series.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean().iloc[-1]
    avg_loss = loss.rolling(window).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    return float(100 - (100 / (1 + avg_gain / avg_loss)))


def volatility(series: pd.Series, window: int = 20) -> float | None:
    if len(series) < window + 1:
        return None
    returns = series.pct_change().dropna()
    return float(returns.rolling(window).std().iloc[-1] * np.sqrt(252))


def momentum(series: pd.Series, window: int = 20) -> float | None:
    if len(series) <= window:
        return None
    return float(series.iloc[-1] / series.iloc[-window] - 1)


def compute_indicators(series: pd.Series) -> dict:
    price = float(series.iloc[-1])
    change_1d_pct = float(series.iloc[-1] / series.iloc[-2] - 1) if len(series) > 1 else None
    return {
        "price": price,
        "change_1d_pct": change_1d_pct,
        "ma20": moving_average(series, 20),
        "ma60": moving_average(series, 60),
        "rsi14": rsi(series, 14),
        "volatility20": volatility(series, 20),
        "momentum20": momentum(series, 20),
    }
