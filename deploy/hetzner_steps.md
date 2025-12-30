# Playbook Hetzner — Déploiement DashFleet (pas d'exécution automatique)

Ce document décrit pas-à-pas comment provisionner et déployer DashFleet sur Hetzner. Il est informatif : n'exécute pas tout d'un coup si tu veux vérifier manuellement.

1) Créer le serveur

- Via l'interface web Hetzner : Servers → Create Server → Ubuntu 22.04, type CX11 (ou supérieur), ajoute ta clé SSH.
- Via `hcloud` CLI :

```bash
hcloud server create --name dashfleet --type cx11 --image ubuntu-22.04 --ssh-key <key-name>
```

2) Connexion et préparation

```bash
ssh root@<IP>
apt update && apt upgrade -y
adduser deploy
usermod -aG sudo deploy
```

3) Pare-feu

```bash
apt install -y ufw
ufw allow OpenSSH
ufw allow http
ufw allow https
ufw enable
```

4) Installer dépendances système

```bash
apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
```

5) Déployer le code

- Cloner le repo ou copier via rsync/scp.

```bash
cd /var/www
git clone <repo-url> dashfleet
chown -R deploy:www-data dashfleet
```

6) Virtualenv & dépendances

```bash
sudo -u deploy python3 -m venv /var/www/dashfleet/.venv
/var/www/dashfleet/.venv/bin/pip install -U pip
/var/www/dashfleet/.venv/bin/pip install -r /var/www/dashfleet/requirements.txt
```

7) Secrets

Créer `/var/www/dashfleet/.env` d'après `deploy/secrets.env.example`, protéger les permissions.

8) systemd & gunicorn

- Adapter `deploy/dashfleet.service` (WorkingDirectory, User=deploy, EnvironmentFile). Copier dans `/etc/systemd/system/` puis :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dashfleet
sudo journalctl -u dashfleet -f
```

9) nginx & TLS

- Adapter `deploy/nginx_dashfleet.conf` (server_name, alias static path) puis :

```bash
sudo cp deploy/nginx_dashfleet.conf /etc/nginx/sites-available/dashfleet.conf
sudo ln -sfn /etc/nginx/sites-available/dashfleet.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d example.com -d www.example.com
```

10) Post-implantation

- Tester API et UI, vérifier `logs/fleet_state.json`, configurer backup.

Notes Hetzner spécifiques
- Snapshots et backups disponibles dans le panel — prendre snapshot avant bascule DNS.
- Pour coûts et types, CX11 est suffisant pour staging. Pour production avec +agents, privilégier 2GB+.
