# 자산관리 대시보드 (개인용 MVP)

주식(국내/해외) + 코인 보유 현황을 한곳에서 추적하고, 매시간 자동으로 규칙 기반
지표와 LLM 참고 해설을 갱신해서 보여주는 개인용 대시보드입니다.

**중요:** 이 시스템은 매수/매도를 실행하지 않고, 확정적인 투자 자문을 제공하지
않습니다. 규칙 기반 지표(이동평균, RSI, 모멘텀)를 계산하고, 그 지표를 바탕으로
Claude API가 참고용 해설을 생성할 뿐입니다. 모든 투자 판단과 책임은 본인에게
있습니다.

## 구조

```
config/portfolio.example.yaml   보유 자산 정의 예시 (복사해서 portfolio.yaml로 사용)
assetmgr/
  providers/stocks.py            국내·해외 주식 시세 (yfinance, API 키 불필요)
  providers/crypto.py            코인 시세 (CoinGecko 공개 API, API 키 불필요)
  indicators.py                  이동평균/RSI/변동성/모멘텀 계산
  signals.py                     지표 -> 강세/중립/약세 규칙 기반 라벨
  commentary.py                  Claude API로 참고용 시장 해설 생성 (선택)
  pipeline.py                    위 단계를 묶어 스냅샷 1건을 생성
  scheduler.py                   매시간(기본) 자동 갱신 + DB 저장
  db.py                          스냅샷 히스토리 SQLite 저장
dashboard/app.py                 Streamlit 대시보드 (DB에서 읽어서 보여주기만 함)
scripts/run_once.py              스케줄러 없이 스냅샷 1회 생성 (테스트용)
```

자산군은 채권·부동산도 추가할 수 있게 설계되어 있습니다 (`providers/`에 새
provider 파일을 추가하고 `pipeline.py`에 루프를 하나 더 추가하면 됩니다). 다만
채권·부동산은 무료 실시간 시세 API가 마땅치 않아 1차 버전에서는 제외했습니다.

## 설치

```bash
pip install -r requirements.txt
cp config/portfolio.example.yaml config/portfolio.yaml   # 보유 내역으로 수정
cp .env.example .env                                      # 필요시 값 채우기
```

`config/portfolio.yaml`을 본인의 실제 보유 종목/수량으로 수정하세요. 코인은
`assetmgr/providers/crypto.py`의 `SYMBOL_TO_ID`에 등록된 심볼만 지원하며, 없는
코인은 매핑을 추가해야 합니다.

LLM 시장 해설을 켜려면 `.env`에 `ANTHROPIC_API_KEY`를 채우세요. 키가 없으면
지표/신호는 정상적으로 계산되고, 해설란만 "건너뜀"으로 표시됩니다.

## 실행

**1) 스냅샷 1회 생성 (테스트)**

```bash
python scripts/run_once.py
```

**2) 매시간 자동 갱신 (백그라운드 프로세스로 계속 실행)**

```bash
python -m assetmgr.scheduler
```

주기는 `.env`의 `REFRESH_INTERVAL_MINUTES`로 조절합니다(기본 60분). 서버에
계속 띄워두려면 `systemd`, `pm2`, `tmux`, 또는 `cron + run_once.py` 중 편한
방식으로 상시 실행하세요. 이 리포지토리 자체는 배포/호스팅 설정을 포함하지
않습니다.

**3) 대시보드 보기**

```bash
streamlit run dashboard/app.py
```

대시보드는 DB에 쌓인 최신 스냅샷과 히스토리를 읽어서 보여주기만 하며, 자체적으로
시세를 조회하지 않습니다. 스케줄러(2번)가 갱신을 담당합니다.

## 비용 참고

- 주식(yfinance)·코인(CoinGecko) 시세는 무료 공개 API라 비용이 들지 않습니다.
- LLM 해설은 매시간 Claude API를 호출하므로 하루 24회, 한 달 약 720회 호출됩니다.
  기본 모델은 `claude-opus-5`이며, 비용을 낮추려면 `.env`의 `CLAUDE_MODEL`을
  `claude-sonnet-5` 또는 `claude-haiku-4-5`로 바꾸세요.

## 알려진 제약 (이번 세션 검증 환경)

이 세션의 원격 실행 환경은 아웃바운드 네트워크 정책상 `finance.yahoo.com`,
`api.coingecko.com` 접근이 막혀 있어 실제 시세로는 테스트하지 못했습니다.
대신 합성(가짜) 가격 데이터로 지표 계산 -> 신호 산출 -> DB 저장 -> Streamlit
대시보드 렌더링까지 전체 파이프라인이 정상 동작하는 것을 확인했습니다. 본인의
PC나 일반적인 네트워크 환경에서 실행하면 실제 시세로 정상 동작할 것입니다.

## 다음 단계로 고려할 것들

- 채권/부동산 자산군 추가 (provider + pipeline 루프 추가)
- 국내 브로커 API(예: 한국투자증권 OpenAPI) 연동으로 실제 보유내역 자동 동기화
- 알림(가격 급변, 신호 전환 시 텔레그램/이메일 알림)
- 여러 사람이 쓰는 서비스로 확장하려면 인증, 사용자별 데이터 분리, 법적 검토
  (투자자문업 규제 등)가 별도로 필요합니다.
