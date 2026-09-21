import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

PORTFOLIO_FILE = os.environ.get("PORTFOLIO_FILE", "config/portfolio.yaml")
DB_PATH = os.environ.get("DB_PATH", "data/portfolio.db")
REFRESH_INTERVAL_MINUTES = int(os.environ.get("REFRESH_INTERVAL_MINUTES", "60"))


def load_portfolio(path: str | None = None) -> dict:
    path = path or PORTFOLIO_FILE
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"포트폴리오 파일을 찾을 수 없습니다: {path}\n"
            "config/portfolio.example.yaml을 복사해서 실제 보유 내역으로 채워주세요:\n"
            f"  cp config/portfolio.example.yaml {path}"
        )
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
