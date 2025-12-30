#!/usr/bin/env bash
set -euo pipefail

# Deploy script for DashFleet (adjust variables below)
# Usage (on server as root or via sudo):
#   sudo ./deploy.sh

APP_USER=www-data
APP_GROUP=www-data
APP_DIR=/var/www/dashfleet
REPO_DIR=$(pwd)
VENV_DIR=${APP_DIR}/.venv
SERVICE_SRC=${REPO_DIR}/deploy/dashfleet.service
NGINX_SRC=${REPO_DIR}/deploy/nginx_dashfleet.conf
ENV_FILE=${APP_DIR}/.env
DOMAIN=example.com  # <-- replace with your domain

echo "Starting deploy (APP_DIR=${APP_DIR})"

if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root. Use sudo." >&2
  exit 2
fi

mkdir -p ${APP_DIR}
chown ${SUDO_USER:-root}:${APP_GROUP} ${APP_DIR}
echo "Copying project files to ${APP_DIR} (excludes .venv)"
rsync -a --delete --exclude '.venv' --exclude 'deploy' ${REPO_DIR}/ ${APP_DIR}/

echo "Creating virtualenv at ${VENV_DIR}"
python3 -m venv ${VENV_DIR}
${VENV_DIR}/bin/pip install -U pip
if [ -f ${APP_DIR}/requirements.txt ]; then
  ${VENV_DIR}/bin/pip install -r ${APP_DIR}/requirements.txt
else
  ${VENV_DIR}/bin/pip install flask psutil gunicorn
fi

echo "Creating environment file ${ENV_FILE} (edit values)"
cat > ${ENV_FILE} <<EOF
# DashFleet environment
FLEET_TOKEN=change_me_long_random
ACTION_TOKEN=change_me_optional
HOST=127.0.0.1
PORT=8000
WEBHOOK_URL=
FLEET_TTL_SECONDS=600
EOF
chown ${APP_USER}:${APP_GROUP} ${ENV_FILE}
chmod 640 ${ENV_FILE}

echo "Installing systemd service"
if [ -f "${SERVICE_SRC}" ]; then
  cp "${SERVICE_SRC}" /etc/systemd/system/dashfleet.service
  sed -i "s|/var/www/dashfleet|${APP_DIR}|g" /etc/systemd/system/dashfleet.service || true
  systemctl daemon-reload
  systemctl enable --now dashfleet
else
  echo "Warning: ${SERVICE_SRC} not found, skipping service install"
fi

echo "Installing nginx site"
if [ -f "${NGINX_SRC}" ]; then
  cp "${NGINX_SRC}" /etc/nginx/sites-available/dashfleet.conf
  ln -snf /etc/nginx/sites-available/dashfleet.conf /etc/nginx/sites-enabled/dashfleet.conf
  nginx -t && systemctl reload nginx
else
  echo "Warning: ${NGINX_SRC} not found, skipping nginx config"
fi

echo "Obtaining TLS cert via Certbot (requires domain DNS to point to this server)"
echo "Run: certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"

echo "Deploy finished. Check service: systemctl status dashfleet"
echo "Edit ${ENV_FILE} to change secrets and restart: systemctl restart dashfleet"
