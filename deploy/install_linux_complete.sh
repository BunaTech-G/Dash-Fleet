#!/usr/bin/env bash
# ============================================================
# INSTALLATION AGENT DASHFLEET - LINUX
# ============================================================
# Exécuter en tant que root: sudo bash install_linux_complete.sh

set -euo pipefail

# Configuration
SERVER_URL="${SERVER_URL:-https://dash-fleet.com}"
API_KEY="${API_KEY:-VOTRE_API_KEY_ICI}"  # À récupérer depuis le dashboard
INTERVAL_SECONDS="${INTERVAL_SECONDS:-30}"
INSTALL_DIR="${INSTALL_DIR:-/opt/dashfleet-agent}"
SERVICE_NAME="dashfleet-agent"

echo "========================================"
echo "  Installation Agent DashFleet"
echo "========================================"

# Vérifier les droits root
if [[ $EUID -ne 0 ]]; then
  echo "ERREUR: Ce script doit être exécuté en tant que root (sudo)." >&2
  exit 1
fi

# Créer les répertoires
echo "Création des répertoires..."
mkdir -p "$INSTALL_DIR/logs"

# Télécharger les fichiers
echo "Téléchargement de fleet_agent.py..."
curl -sSL "https://raw.githubusercontent.com/BunaTech-G/Dashboard-syst-me-/fix/pyproject-exclude/fleet_agent.py" -o "$INSTALL_DIR/fleet_agent.py"

echo "Téléchargement de fleet_utils.py..."
curl -sSL "https://raw.githubusercontent.com/BunaTech-G/Dashboard-syst-me-/fix/pyproject-exclude/fleet_utils.py" -o "$INSTALL_DIR/fleet_utils.py"

# Installer Python et dépendances
echo "Installation des dépendances Python..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv -qq
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip -q
fi

# Créer l'environnement virtuel
echo "Création de l'environnement virtuel..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install psutil requests --quiet

# Générer machine_id
MACHINE_ID=$(hostname -s)
echo "Machine ID: $MACHINE_ID"

# Créer le fichier de configuration
echo "Création du fichier de configuration..."
cat > "$INSTALL_DIR/config.json" <<EOF
{
  "server": "$SERVER_URL",
  "path": "/api/fleet/report",
  "token": "$API_KEY",
  "interval": $INTERVAL_SECONDS,
  "machine_id": "$MACHINE_ID",
  "log_file": "$INSTALL_DIR/logs/agent.log"
}
EOF

# Créer le service systemd
echo "Création du service systemd..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=DashFleet Monitoring Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/fleet_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd et démarrer le service
echo "Activation et démarrage du service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# Attendre 2 secondes et vérifier le statut
sleep 2
STATUS=$(systemctl is-active "$SERVICE_NAME")

echo ""
echo "========================================"
echo "  Installation terminée!"
echo "========================================"
echo ""
echo "Configuration:"
echo "  - Répertoire: $INSTALL_DIR"
echo "  - Machine ID: $MACHINE_ID"
echo "  - Serveur: $SERVER_URL"
echo "  - Intervalle: $INTERVAL_SECONDS secondes"
echo ""
echo "Service: $SERVICE_NAME"
echo "Statut: $STATUS"
echo ""
echo "Commandes utiles:"
echo "  systemctl status $SERVICE_NAME    # Voir le statut"
echo "  journalctl -u $SERVICE_NAME -f    # Voir les logs en temps réel"
echo "  systemctl restart $SERVICE_NAME   # Redémarrer"
echo "  tail -f $INSTALL_DIR/logs/agent.log  # Logs de l'agent"
