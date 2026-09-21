import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from . import config, db, pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_once() -> dict:
    portfolio = config.load_portfolio()
    snapshot = pipeline.build_snapshot(portfolio)
    snapshot = pipeline.add_commentary(snapshot)

    conn = db.get_connection(config.DB_PATH)
    try:
        db.save_snapshot(conn, snapshot["generated_at"], snapshot["total_value"], snapshot)
    finally:
        conn.close()

    logger.info(
        "스냅샷 저장 완료: 총자산=%.2f, 포트폴리오 신호=%s",
        snapshot["total_value"], snapshot["portfolio_label"],
    )
    return snapshot


def main() -> None:
    logger.info("초기 스냅샷을 생성합니다...")
    run_once()

    scheduler = BlockingScheduler(timezone="Asia/Seoul")
    scheduler.add_job(run_once, "interval", minutes=config.REFRESH_INTERVAL_MINUTES)

    logger.info("스케줄러 시작: %d분마다 자동 갱신", config.REFRESH_INTERVAL_MINUTES)
    scheduler.start()


if __name__ == "__main__":
    main()
