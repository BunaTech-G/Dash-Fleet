# Checklist de mise en production — DashFleet

Cette checklist rassemble les étapes minimales à valider avant et après le déploiement sur un VPS.

## Avant déploiement (local)
- [ ] Exécuter tous les tests locaux (`tests/*.py`) et corriger les erreurs.
- [ ] Lancer un agent local et vérifier la page `/fleet` et `/api/status`.
- [ ] Remplir `deploy/secrets.env.example` et tester l'application avec ces valeurs localement.
- [ ] Ajouter `requirements.txt` et vérifier l'environnement virtuel fonctionne.

## Provisionner le VPS
- [ ] Créer le VPS (Hetzner / DigitalOcean / OVH) avec Ubuntu 22.04+.
- [ ] Configurer un utilisateur non-root et ajouter la clé SSH.
- [ ] Mettre à jour le système : `sudo apt update && sudo apt upgrade -y`.
- [ ] Configurer le pare-feu (UFW) :
  - `sudo ufw allow OpenSSH`
  - `sudo ufw allow 80,443/tcp`
  - `sudo ufw enable`

## Déploiement du code
- [ ] Copier le projet dans `/var/www/dashfleet` (ou chemin choisi).
- [ ] Créer un virtualenv et installer les dépendances :

```bash
python3 -m venv /var/www/dashfleet/.venv
/var/www/dashfleet/.venv/bin/pip install -r /var/www/dashfleet/requirements.txt
```

- [ ] Créer `/var/www/dashfleet/.env` (ou `EnvironmentFile`) avec `FLEET_TOKEN`, `ACTION_TOKEN`, etc., permissions `640`.
- [ ] Adapter `deploy/dashfleet.service` : `WorkingDirectory`, `Environment` (pointant vers `.env` si utilisé), chemin `ExecStart` vers le venv.
- [ ] Copier le fichier systemd, recharger systemd et démarrer :

```bash
sudo cp deploy/dashfleet.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dashfleet
sudo journalctl -u dashfleet -f
```

## Reverse proxy & TLS
- [ ] Adapter `deploy/nginx_dashfleet.conf` : remplacer `server_name` et chemins statiques.
- [ ] Activer le site nginx et recharger :

```bash
sudo cp deploy/nginx_dashfleet.conf /etc/nginx/sites-available/dashfleet.conf
sudo ln -sfn /etc/nginx/sites-available/dashfleet.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

- [ ] Obtenir les certificats Let's Encrypt (Certbot) :

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d example.com -d www.example.com
```

## Post-déploiement — vérifications
- [ ] Vérifier que `systemctl status dashfleet` est `active (running)`.
- [ ] Tester endpoints protégés : `/api/status`, `/api/fleet` (GET), `/api/fleet/report` (POST avec `FLEET_TOKEN`).
- [ ] Lancer un agent de test externe pour s'assurer que `logs/fleet_state.json` se met à jour.
- [ ] Examiner les logs (`journalctl -u dashfleet`, `/var/log/nginx/dashfleet.*`).

## Sécurité & opérations
- [ ] Ne pas exposer le port interne WSGI (8000) directement au public — nginx reverse-proxy uniquement.
- [ ] Stocker `FLEET_TOKEN` et `ACTION_TOKEN` hors du dépôt, avec permissions restreintes.
- [ ] Configurer logrotate pour `logs/fleet_state.json` si nécessaire, ou migrer vers SQLite/Redis.
- [ ] Mettre en place sauvegarde régulière du répertoire `logs/` et de la configuration.

## Monitoring & alerting
- [ ] Ajouter simple health-check script qui appelle `/api/status` et signale via webhook ou systemd timer.
- [ ] (Optionnel) Ajouter métriques Prometheus export ou simple uptime monitor externe.

## Rollback rapide
- [ ] Garder un snapshot ou image du VPS avant la mise en production.
- [ ] Procédure de rollback :
  1. `sudo systemctl stop dashfleet`
  2. Restaurer les fichiers depuis snapshot/backup
  3. `sudo systemctl start dashfleet`

## Checklist finale avant bascule DNS
- [ ] Le staging fonctionne et répond correctement.
- [ ] Certificat TLS valide en staging (si possible).
- [ ] Backups et monitoring en place.
- [ ] Règles de pare-feu configurées (80/443 ouvertes seulement).
- [ ] Documenter les accès SSH et les personnes responsables.

---
Garde ce document vivant : coche les étapes à mesure que tu les valides.

## Valeurs à remplacer (rapide)
- `<HOST>` / `(ex: http://mon-serveur:5000)` : URL où DashFleet sera exposé (local ou public).
- `FLEET_TOKEN` / `ACTION_TOKEN` : tokens secrets à fournir via `.env` ou `EnvironmentFile` pour systemd.
- `<API_KEY>` : clé API pour les agents, fournie par `POST /api/orgs`.
