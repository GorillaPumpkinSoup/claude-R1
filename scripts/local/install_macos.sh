#!/usr/bin/env bash
# macOS: launchd 에이전트로 assetmgr.scheduler를 로그인 시 자동 시작 + 항상 재시작되게 등록한다.
# 로컬 PC에서 1회만 실행하면 된다: bash scripts/local/install_macos.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="$(command -v python3)"
LABEL="com.assetmgr.scheduler"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"

if [ ! -f "${REPO_DIR}/config/portfolio.yaml" ]; then
  echo "config/portfolio.yaml이 없습니다. 먼저 아래처럼 보유 내역 파일을 만드세요:" >&2
  echo "  cp ${REPO_DIR}/config/portfolio.example.yaml ${REPO_DIR}/config/portfolio.yaml" >&2
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "${REPO_DIR}/data"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        <string>-m</string>
        <string>assetmgr.scheduler</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${REPO_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${REPO_DIR}/data/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>${REPO_DIR}/data/scheduler.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "설치 완료. 로그인할 때마다 자동으로 시작되고, 종료되면 자동 재시작됩니다."
echo "로그 확인: tail -f ${REPO_DIR}/data/scheduler.log"
echo "중지하려면: launchctl unload ${PLIST_PATH}"
echo "완전히 제거하려면: launchctl unload ${PLIST_PATH} && rm ${PLIST_PATH}"
