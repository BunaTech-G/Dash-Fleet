# Déploiement (extrait)

Remplace les chemins et valeurs entre <> avant l'utilisation.

Exemple d'étapes (Ubuntu 22.04):

```bash
# Copier le projet sur le serveur, par ex. /var/www/dashfleet
sudo mkdir -p /var/www/dashfleet
sudo chown $USER:$USER /var/www/dashfleet
rsync -av --exclude '.venv' ./ /var/www/dashfleet/

# Créer un virtualenv et installer dépendances
python3 -m venv /var/www/dashfleet/.venv
/var/www/dashfleet/.venv/bin/pip install -U pip
/var/www/dashfleet/.venv/bin/pip install flask psutil gunicorn

# Tester localement
/var/www/dashfleet/.venv/bin/gunicorn -w 3 -b 127.0.0.1:8000 main:app

# Installer le service systemd
sudo cp deploy/dashfleet.service /etc/systemd/system/dashfleet.service
sudo systemctl daemon-reload
sudo systemctl enable --now dashfleet

# Configurer nginx (remplacer example.com)
sudo cp deploy/nginx_dashfleet.conf /etc/nginx/sites-available/dashfleet.conf
sudo ln -s /etc/nginx/sites-available/dashfleet.conf /etc/nginx/sites-enabled/dashfleet.conf
sudo nginx -t && sudo systemctl reload nginx

# Obtenir certbot/Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
```

Notes:
- Adapte `WorkingDirectory` et `Environment` dans `dashfleet.service`.
- Définit `FLEET_TOKEN` dans l'environnement systemd (ou utilise un fichier `.env` sécurisé).
- Pour sécurité, active TLS via certbot et reverse-proxy.
