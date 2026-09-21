"""국내/해외 주식 시세 조회 (yfinance 기반, API 키 불필요)."""

import pandas as pd
import yfinance as yf


def fetch_stock_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.Series:
    hist = yf.Ticker(ticker).history(period=period, interval=interval)
    if hist.empty:
        raise ValueError(f"'{ticker}' 시세 데이터를 가져오지 못했습니다. 티커를 확인하세요.")
    return hist["Close"].dropna()


def fetch_stock_snapshot(ticker: str) -> dict:
    history = fetch_stock_history(ticker)
    return {"ticker": ticker, "history": history}
