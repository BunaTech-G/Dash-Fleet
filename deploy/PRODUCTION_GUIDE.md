Guide de production — DashFleet

But: décrire déploiement sûr avec gunicorn + nginx + TLS (Let's Encrypt)

1) Préparer le serveur (Ubuntu 22.04+)
- Créer un utilisateur non-root `deploy` et ajouter votre clé SSH.
- Installer dépendances :

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx git
```

2) Copier le code et préparer l'environnement

```bash
sudo mkdir -p /var/www/dashfleet
sudo chown $USER:$USER /var/www/dashfleet
rsync -av --exclude '.venv' ./ /var/www/dashfleet/
cd /var/www/dashfleet
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

3) Secrets & EnvironmentFile
- Copier `deploy/secrets.env.example` → `/var/www/dashfleet/.env` et modifier les valeurs.
- Protéger le fichier :

```bash
sudo mv deploy/secrets.env.example /var/www/dashfleet/.env
sudo chown root:www-data /var/www/dashfleet/.env
sudo chmod 640 /var/www/dashfleet/.env
```

4) systemd (gunicorn)
- Adapter `deploy/dashfleet.service` : `WorkingDirectory`, `User`, `Group`, et vérifier `EnvironmentFile` pointant sur `/var/www/dashfleet/.env`.

```bash
sudo cp deploy/dashfleet.service /etc/systemd/system/dashfleet.service
sudo systemctl daemon-reload
sudo systemctl enable --now dashfleet
sudo journalctl -u dashfleet -f
```

5) nginx
- Adapter `deploy/nginx_dashfleet.conf` (`server_name`, chemins static), puis :

```bash
sudo cp deploy/nginx_dashfleet.conf /etc/nginx/sites-available/dashfleet.conf
sudo ln -sfn /etc/nginx/sites-available/dashfleet.conf /etc/nginx/sites-enabled/dashfleet.conf
sudo nginx -t && sudo systemctl reload nginx
```

6) Certbot (Let's Encrypt)
- Obtenir certif et configurer TLS :

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

- Option manuelle (si certbot ne peut pas éditer nginx) :
  - Créer le répertoire `/var/www/dashfleet/letsencrypt` et configurer `nginx_dashfleet.conf` (voir `location /.well-known` déjà présent).
  - Exécuter `sudo certbot certonly --webroot -w /var/www/dashfleet/letsencrypt -d example.com` puis configurer `nginx` pour utiliser les certificats.

7) Vérifications post-déploiement
- Vérifier `systemctl status dashfleet` est `active (running)`.
- Vérifier logs nginx et journal systemd.
- Tester endpoints :
  - `curl -I https://example.com/api/status`
  - `curl -H "Authorization: Bearer $ACTION_TOKEN" https://example.com/api/orgs`

8) Bonnes pratiques
- Ne pas exposer le port gunicorn directement.
- Mettre en place logrotate pour `/var/log/nginx/dashfleet.*` et pour `logs/` si nécessaire.
- Prévoir snapshots/backups avant mises à jour majeures.

---
