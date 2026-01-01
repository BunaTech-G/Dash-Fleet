#!/usr/bin/env bash
set -euo pipefail

SERVER_URL=${SERVER_URL:-"https://mon-serveur-mdm.example.com"}
FLEET_TOKEN=${FLEET_TOKEN:-"REMPLACER_PAR_FLEET_TOKEN"}
INTERVAL_SECONDS=${INTERVAL_SECONDS:-30}
INSTALL_DIR=${INSTALL_DIR:-"/opt/mini-mdm-agent"}
SERVICE_NAME=${SERVICE_NAME:-"mini-mdm-agent"}

if [[ $EUID -ne 0 ]]; then
  echo "Exécutez en root (sudo)." >&2
  exit 1
fi

install_path="$INSTALL_DIR"
logs_path="$install_path/logs"
config_path="$install_path/config.json"
agent_path="$install_path/fleet_agent.py"
venv_path="$install_path/venv"

mkdir -p "$logs_path"
cp "$(dirname "$0")/../fleet_agent.py" "$agent_path"

python3 -m venv "$venv_path"
"$venv_path/bin/pip" install --upgrade pip
"$venv_path/bin/pip" install psutil requests

cat > "$config_path" <<EOF
{
  "server": "$SERVER_URL",
  "path": "/api/fleet/report",
  "token": "$FLEET_TOKEN",
  "interval": $INTERVAL_SECONDS,
  "machine_id": "",
  "log_file": "$logs_path/agent.log"
}
EOF

unit_path="/etc/systemd/system/${SERVICE_NAME}.service"
cat > "$unit_path" <<EOF
[Unit]
Description=Mini MDM Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$install_path
ExecStart=$venv_path/bin/python $agent_path --config $config_path
Restart=always
RestartSec=5
StandardOutput=append:$logs_path/agent.log
StandardError=append:$logs_path/agent.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

systemctl status "$SERVICE_NAME" --no-pager
