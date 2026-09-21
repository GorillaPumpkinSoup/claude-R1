#!/usr/bin/env bash
# Linux: systemd --user 서비스로 assetmgr.scheduler를 로그인 시 자동 시작 + 항상 재시작되게 등록한다.
# 로컬 PC에서 1회만 실행하면 된다: bash scripts/local/install_linux.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="$(command -v python3)"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_PATH="${SERVICE_DIR}/assetmgr-scheduler.service"

if [ ! -f "${REPO_DIR}/config/portfolio.yaml" ]; then
  echo "config/portfolio.yaml이 없습니다. 먼저 아래처럼 보유 내역 파일을 만드세요:" >&2
  echo "  cp ${REPO_DIR}/config/portfolio.example.yaml ${REPO_DIR}/config/portfolio.yaml" >&2
  exit 1
fi

mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=Asset Manager Hourly Scheduler
After=network-online.target

[Service]
Type=simple
WorkingDirectory=${REPO_DIR}
ExecStart=${PYTHON_BIN} -m assetmgr.scheduler
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now assetmgr-scheduler.service
loginctl enable-linger "$USER" 2>/dev/null || echo "참고: loginctl enable-linger 실패 - 로그아웃하면 서비스가 멈출 수 있습니다."

echo "설치 완료."
echo "상태 확인: systemctl --user status assetmgr-scheduler.service"
echo "로그 확인: journalctl --user -u assetmgr-scheduler.service -f"
echo "중지하려면: systemctl --user disable --now assetmgr-scheduler.service"
