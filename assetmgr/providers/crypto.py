"""코인(암호화폐) 시세 조회 (CoinGecko 공개 API 기반, API 키 불필요)."""

from datetime import datetime, timezone

import pandas as pd
import requests

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# 지원할 코인이 늘어나면 여기에 심볼 -> CoinGecko id 매핑을 추가하세요.
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "XRP": "ripple",
    "SOL": "solana",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "MATIC": "matic-network",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "TRX": "tron",
    "LINK": "chainlink",
}


def resolve_id(symbol: str) -> str:
    key = symbol.upper()
    if key not in SYMBOL_TO_ID:
        raise ValueError(
            f"알 수 없는 코인 심볼입니다: {symbol}. "
            "assetmgr/providers/crypto.py의 SYMBOL_TO_ID에 매핑을 추가하세요."
        )
    return SYMBOL_TO_ID[key]


def fetch_crypto_history(symbol: str, vs_currency: str = "usd", days: int = 180) -> pd.Series:
    coin_id = resolve_id(symbol)
    resp = requests.get(
        f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
        params={"vs_currency": vs_currency, "days": days, "interval": "daily"},
        timeout=15,
    )
    resp.raise_for_status()
    prices = resp.json()["prices"]  # [[ms_timestamp, price], ...]
    if not prices:
        raise ValueError(f"'{symbol}' 시세 데이터를 가져오지 못했습니다.")
    index = [datetime.fromtimestamp(p[0] / 1000, tz=timezone.utc) for p in prices]
    values = [p[1] for p in prices]
    return pd.Series(values, index=index, name=symbol).dropna()


def fetch_crypto_snapshot(symbol: str, vs_currency: str = "usd") -> dict:
    history = fetch_crypto_history(symbol, vs_currency=vs_currency)
    return {"ticker": symbol, "history": history}
