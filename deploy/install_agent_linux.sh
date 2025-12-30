#!/usr/bin/env bash
# Install DashFleet agent on Linux (systemd)
# Usage: sudo ./install_agent_linux.sh ORG_KEY
set -euo pipefail
ORG_KEY=${1:-}
AGENT_DIR=${2:-/opt/dashfleet}
if [[ -z "$ORG_KEY" ]]; then
  echo "Usage: sudo ./install_agent_linux.sh <ORG_KEY> [target_dir]"
  exit 1
fi
mkdir -p "$AGENT_DIR"
# Copy agent file (assumes script run from repo root)
cp ./fleet_agent.py "$AGENT_DIR/"
cat > "$AGENT_DIR/agent.conf" <<EOF
ORG_KEY=$ORG_KEY
EOF

# Create systemd service
SERVICE_PATH=/etc/systemd/system/dashfleet-agent.service
cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=DashFleet Agent
After=network.target

[Service]
Type=simple
Environment=ORG_KEY=$ORG_KEY
ExecStart=/usr/bin/env python3 $AGENT_DIR/fleet_agent.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now dashfleet-agent

echo "DashFleet agent installed and started."
