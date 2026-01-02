#!/bin/bash
# One-liner DashFleet Agent installer (Linux - Kali/Debian/Ubuntu)
# Usage:
#   curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux_oneliner.sh | bash -s -- -k YOUR_TOKEN
#   OR
#   bash <(curl -s https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux_oneliner.sh) -k YOUR_TOKEN

set -e

API_KEY=""
SERVER_URL="https://dash-fleet.com"
INSTALL_DIR="/opt/dashfleet-agent"
SERVICE_NAME="dashfleet-agent"

# Parse arguments
while getopts "k:s:d:m:" opt; do
  case $opt in
    k) API_KEY="$OPTARG" ;;
    s) SERVER_URL="$OPTARG" ;;
    d) INSTALL_DIR="$OPTARG" ;;
    m) MACHINE_ID="$OPTARG" ;;
  esac
done

# Default machine ID
if [ -z "$MACHINE_ID" ]; then
  MACHINE_ID=$(hostname)
fi

# Validate token
if [ -z "$API_KEY" ]; then
  echo "ERREUR: API Key obligatoire"
  echo "Usage: $0 -k YOUR_API_KEY [-m MACHINE_NAME]"
  exit 1
fi

echo "========================================"
echo "  DashFleet Agent Installation (Linux)"
echo "========================================"
echo ""
echo "Configuration:"
echo "  Machine: $MACHINE_ID"
echo "  Serveur: $SERVER_URL"
echo "  Repertoire: $INSTALL_DIR"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then 
  echo "ERREUR: Ce script doit etre execute en tant que root"
  echo "Utilisez: sudo bash <script>"
  exit 1
fi

# Check and install Python3
echo "Verification de Python3..."
if ! command -v python3 &> /dev/null; then
  echo "Installation de Python3..."
  apt-get update -qq > /dev/null 2>&1
  apt-get install -y python3 python3-pip > /dev/null 2>&1
  echo "✅ Python3 installe"
else
  echo "✅ Python3 trouve: $(python3 --version)"
fi

# Install pip if missing
if ! command -v pip3 &> /dev/null; then
  echo "Installation de pip3..."
  apt-get install -y python3-pip > /dev/null 2>&1
fi

# Create directories
echo "Creation des repertoires..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"

# Download fleet_agent.py
echo "Telechargement de fleet_agent.py..."
curl -s -L -o "$INSTALL_DIR/fleet_agent.py" \
  "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/fleet_agent.py" || {
  echo "ERREUR: Impossible de telecharger fleet_agent.py"
  exit 1
}
echo "✅ fleet_agent.py telecharge"

# Download fleet_utils.py
echo "Telechargement de fleet_utils.py..."
curl -s -L -o "$INSTALL_DIR/fleet_utils.py" \
  "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/fleet_utils.py" || {
  echo "ERREUR: Impossible de telecharger fleet_utils.py"
  exit 1
}
echo "✅ fleet_utils.py telecharge"

# Install dependencies
echo "Installation des dependances Python..."
pip3 install --quiet psutil requests 2>/dev/null || {
  echo "ERREUR: Impossible d'installer les dependances"
  exit 1
}
echo "✅ Dependances installes"

# Create config file (proper JSON)
echo "Creation du fichier de configuration..."
cat > "$INSTALL_DIR/config.json" << EOF
{
    "server": "$SERVER_URL",
    "path": "/api/fleet/report",
    "token": "$API_KEY",
    "interval": 30,
    "machine_id": "$MACHINE_ID",
    "log_file": "$INSTALL_DIR/logs/agent.log"
}
EOF
echo "✅ Configuration creee"

# Create systemd service
echo "Creation du service systemd..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=DashFleet Monitoring Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/fleet_agent.py --config $INSTALL_DIR/config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable $SERVICE_NAME > /dev/null 2>&1
systemctl start $SERVICE_NAME

if systemctl is-active --quiet $SERVICE_NAME; then
  echo "✅ Service demarrE"
else
  echo "❌ ERREUR: Le service n'a pas demarrE"
  journalctl -u $SERVICE_NAME -n 10
  exit 1
fi

# Verify
echo ""
echo "========================================"
echo "  Installation reussie !"
echo "========================================"
echo ""
echo "Configuration:" 
echo "  Agent: $INSTALL_DIR/fleet_agent.py"
echo "  Config: $INSTALL_DIR/config.json"
echo "  Logs: $INSTALL_DIR/logs/agent.log"
echo "  Service: $SERVICE_NAME"
echo ""
echo "Commandes utiles:"
echo "  Statut:   systemctl status $SERVICE_NAME"
echo "  Logs:     tail -f $INSTALL_DIR/logs/agent.log"
echo "  Restart:  systemctl restart $SERVICE_NAME"
echo "  Stop:     systemctl stop $SERVICE_NAME"
echo ""
echo "Dashboard: $SERVER_URL/fleet"
echo ""
echo "L'agent se lancera automatiquement au demarrage et envoie les metriques toutes les 30 secondes."
