#!/usr/bin/env bash
# Install DashFleet as a systemd service (Linux)
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Exécutez en root: sudo ./install_systemd.sh"
  exit 1
fi

INSTALL_DIR="/opt/dashfleet"
SERVICE_FILE="/etc/systemd/system/dashfleet.service"

mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install "./$INSTALL_DIR"

cp deploy/systemd/dashfleet.service "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable dashfleet.service
systemctl start dashfleet.service

echo "DashFleet installé et démarré. Logs: journalctl -u dashfleet.service -f"
