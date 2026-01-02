#!/bin/bash
# DashFleet Agent Installer for Kali Linux / Debian / Ubuntu
# Run as root or with sudo

set -e

API_KEY="d2f6f9a8-3c7e-4c1f-9b0f-123456789abc"
SERVER_URL="https://dash-fleet.com"
INSTALL_DIR="/opt/dashfleet-agent"
SERVICE_NAME="dashfleet-agent"

echo "========================================"
echo "  Installation Agent DashFleet (Linux)"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERREUR: Ce script doit être exécuté en tant que root"
    echo "Utilisez: sudo bash install_dashfleet_linux.sh"
    exit 1
fi

# Get machine hostname automatically
DEFAULT_MACHINE_ID=$(hostname)

echo "Nom de machine détecté: $DEFAULT_MACHINE_ID"
read -p "Appuyez sur Entrée pour utiliser ce nom, ou tapez un autre nom: " MACHINE_ID

# Use default if empty
if [ -z "$MACHINE_ID" ]; then
    MACHINE_ID="$DEFAULT_MACHINE_ID"
fi

echo ""
echo "Installation pour: $MACHINE_ID"
echo ""

# Check and install Python if missing
echo "Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 n'est pas installé. Installation automatique..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv > /dev/null 2>&1
    echo "✅ Python3 installé"
else
    echo "✅ Python3 trouvé: $(python3 --version)"
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "Installation de pip..."
    apt-get install -y python3-pip > /dev/null 2>&1
fi

# Create directories
echo "Création des répertoires..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"

# Download files
echo "Téléchargement de fleet_agent.py..."
curl -s -L -o "$INSTALL_DIR/fleet_agent.py" \
    "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/fleet_agent.py"
if [ $? -ne 0 ]; then
    echo "ERREUR: Impossible de télécharger fleet_agent.py"
    exit 1
fi
echo "✅ fleet_agent.py téléchargé"

echo "Téléchargement de fleet_utils.py..."
curl -s -L -o "$INSTALL_DIR/fleet_utils.py" \
    "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/fleet_utils.py"
if [ $? -ne 0 ]; then
    echo "ERREUR: Impossible de télécharger fleet_utils.py"
    exit 1
fi
echo "✅ fleet_utils.py téléchargé"

# Install dependencies
echo "Installation des dépendances Python..."
pip3 install --quiet psutil requests
echo "✅ Dépendances installées"

# Create config file
echo "Création du fichier de configuration..."
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
echo "✅ Configuration créée"

# Create systemd service
echo "Création du service systemd..."
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

# Reload systemd and start service
systemctl daemon-reload
systemctl enable $SERVICE_NAME > /dev/null 2>&1
systemctl start $SERVICE_NAME

if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service démarré"
else
    echo "❌ ERREUR: Le service n'a pas démarré"
    echo "Vérifiez les logs avec: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

echo ""
echo "========================================"
echo "  Installation terminée avec succès!"
echo "========================================"
echo ""
echo "Configuration:"
echo "  - Répertoire: $INSTALL_DIR"
echo "  - Machine ID: $MACHINE_ID"
echo "  - Serveur: $SERVER_URL"
echo "  - API Key: ${API_KEY:0:8}..."
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs:       tail -f $INSTALL_DIR/logs/agent.log"
echo "  - Statut du service:   systemctl status $SERVICE_NAME"
echo "  - Redémarrer:          systemctl restart $SERVICE_NAME"
echo "  - Arrêter:             systemctl stop $SERVICE_NAME"
echo ""
echo "La machine $MACHINE_ID apparaîtra dans le dashboard dans quelques secondes:"
echo "https://dash-fleet.com/fleet"
echo ""
