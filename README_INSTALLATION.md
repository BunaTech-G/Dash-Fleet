README d'installation et d'usage — DashFleet

But : expliquer comment créer une organisation / générer une clé API et comment installer l'agent (Windows et Linux).

1) Pré-requis
- Avoir le serveur DashFleet en fonctionnement (python main.py) sur le serveur (ex: http://mon-serveur:5000)
- Disposer de la variable d'environnement `ACTION_TOKEN` définie sur le serveur (clé admin utilisée par l'API d'administration)

2) Créer une organisation et récupérer une clé API
- Créer une organisation (admin) :

  curl -X POST "http://<HOST>:5000/api/orgs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACTION_TOKEN" \
    -d '{"name": "MaEntreprise"}'

  Réponse attendue : JSON contenant l'`id` de l'organisation et une `api_key` initiale (conservez-la).

- Lister les organisations :

  curl -H "Authorization: Bearer $ACTION_TOKEN" "http://<HOST>:5000/api/orgs"

- Révoquer une clé API (admin) :

  curl -X POST "http://<HOST>:5000/api/keys/revoke" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACTION_TOKEN" \
    -d '{"key": "<API_KEY_TO_REVOKE>"}'

3) Installer l'agent (Windows)
- Script fourni : deploy/install_agent_windows.ps1
- One-liner (exécuter dans PowerShell en tant qu'administrateur) :

  powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://<votre-hébergement>/deploy/install_agent_windows.ps1'))"

- Commande manuelle minimale pour tester l'agent :

  .\\venv\\Scripts\\python.exe fleet_agent.py --server http://<HOST>:5000 --key <API_KEY>

4) Installer l'agent (Linux / systemd)
- Script fourni : deploy/install_agent_linux.sh
- One-liner (exécuter en root ou via sudo) :

  bash -c "$(curl -fsSL https://<votre-hébergement>/deploy/install_agent_linux.sh)" -- --server http://<HOST>:5000 --key <API_KEY>

- Le script installe un service systemd nommé `dashfleet-agent@<machine-id>` et démarre le service.

5) Format d'authentification pour l'agent
- L'agent doit envoyer l'en-tête HTTP : `Authorization: Bearer <API_KEY>` sur les requêtes vers `/api/fleet/report`.

6) Endpoints utiles
- POST /api/fleet/report : envoyer un rapport (agent)
- GET /api/fleet : récupérer l'état (admin)
- POST /api/fleet/reload : forcer le serveur à recharger les backups (admin)
- POST /api/orgs : créer organisation (admin)
- GET /api/orgs : lister organisations (admin)
- POST /api/keys/revoke : révoquer clé (admin)

7) Remarques opérationnelles
- `ACTION_TOKEN` protège les endpoints d'administration. Ne l'exposez pas publiquement.
- En production, déployer derrière nginx + gunicorn et activer TLS (certbot).
- Pour débogage local, assurez-vous que le serveur écoute sur 127.0.0.1:5000 et que les scripts utilisent la bonne URL et la bonne clé.

Fichiers utiles dans le dépôt :
- deploy/install_agent_windows.ps1
- deploy/install_agent_linux.sh
- deploy/dashfleet.service (exemple systemd)

---
Si vous voulez, je peux :
- ajuster ce README (ajouter exemples concrets),
- générer un petit script `create_org.sh` qui fait automatiquement les appels curl,
- ou corriger le test qui a échoué (`tests/test_fleet_expiration.py`) pour qu'il passe avec la configuration actuelle.
