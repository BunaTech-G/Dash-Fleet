Server-side agent hosting
-------------------------
Le serveur peut maintenant générer des liens de téléchargement sécurisés à usage unique pour l'agent. Pour créer un lien (protégé par `ACTION_TOKEN`) :
```bash
curl -X POST -H "Authorization: Bearer $ACTION_TOKEN" -H "Content-Type: application/json" \
  -d '{"ttl":3600, "path":"dist/fleet_agent.exe"}' https://votre-instance/api/agent/link
La réponse contient `link` (ex: `/download/agent/<token>`) valable pendant `ttl` secondes. L'appelant peut ensuite télécharger l'exécutable via ce lien.

Packaging & installers
----------------------
 - Chocolatey package skeleton: `packaging/chocolatey/` (nuspec + `tools/chocolateyinstall.ps1`). Placez `fleet_agent.exe` sous `packaging/chocolatey/tools/files/` et publiez avec `choco pack`.
 - MSI WiX template: `packaging/wix/DashFleet.wxs` — utilise WiX Toolset pour compiler (`candle`/`light`) et générer un MSI.

Déploiement multi-postes
------------------------
Le script PowerShell `scripts/install_windows_agent_multi.ps1` permet de pousser `fleet_agent.exe` sur plusieurs machines (PSRemoting ou partage admin C$) et de créer une tâche planifiée. Exemple :

```powershell
.\scripts\install_windows_agent_multi.ps1 -Targets @('host1','host2') -Source .\dist\fleet_agent.exe
```

# Dashboard système — README (fr)

Résumé
-------
Ce dépôt contient un petit tableau de bord système (Flask) pour afficher des métriques locales (CPU, RAM, disque, uptime) et une vue "Fleet" centralisant des rapports envoyés par des agents déployés sur des postes.

Contenu principal
-----------------
- `main.py` : serveur Flask + fonctions de collecte locale. Expose les pages et API :
  - `/` : page temps réel (index)
  - `/history` : page historique (à partir d'un CSV)
  - `/fleet` : page Fleet (vue centralisée des postes)
  - `/api/status` : retourne les métriques locales et le score de santé
  - `/api/history` : retourne l'historique lu depuis `logs/metrics.csv`
  - `/api/fleet/report` (POST) : endpoint protégé par token pour que les agents envoient leurs rapports
  - `/api/fleet` : liste des machines reportées (purge automatique des entrées expirées)

- `fleet_agent.py` : agent léger (Python) qui collecte métriques locales via `psutil` et POSTe régulièrement vers `/api/fleet/report`.

- `templates/` : templates HTML (index, history, fleet). Le template `fleet.html` contient le JS client gérant le rafraîchissement, le tri et les filtres.
- `static/` : CSS, i18n, scripts côté client.
- `logs/fleet_state.json` : fichier créé automatiquement par le serveur pour persister l'état de la flotte (best-effort). Ne pas versionner.
- `tests/` : scripts utilitaires pour vérifier la persistance et l'expiration (exécutables localement).

Variables d'environnement importantes
-----------------------------------
- `FLEET_TOKEN` : token secret partagé entre serveur et agents. Obligatoire si utilisé (protége l'endpoint `/api/fleet/report`).
- `FLEET_TTL_SECONDS` : durée (en secondes) avant qu'une entrée fleet soit considérée expirée (défaut 600).
- `ACTION_TOKEN` : token optionnel protégeant les actions sensibles exposées sur `/api/action`.
- `WEBHOOK_URL` : optional, si défini le serveur enverra un webhook en cas de santé critique.

Comment lancer localement (PowerShell)
-------------------------------------
1) Active l'environnement virtuel et place-toi dans le dossier projet :

```powershell
cd "C:\Users\SIDIBE\OneDrive\Bureau\Dashboard système"
.\.venv\Scripts\Activate.ps1
```

2) Définis le token dans la session (important pour la fenêtre serveur) :

```powershell
$env:FLEET_TOKEN="ton_token_long_et_secret"
```

3) Lancer le serveur Flask et ouvrir l'UI :

```powershell
python main.py --web
# le serveur écoutera sur http://localhost:5000
```

4) Dans une autre fenêtre PowerShell, lancer l'agent qui remonte les métriques :

```powershell
cd "C:\Users\SIDIBE\OneDrive\Bureau\Dashboard système"
.\.venv\Scripts\Activate.ps1
python fleet_agent.py --server http://localhost:5000 --token ton_token_long_et_secret --machine-id poste-01 --interval 10
```

5) Ouvre dans ton navigateur : `http://localhost:5000/fleet` pour voir la vue Fleet.

Notes sur la configuration
--------------------------
- Le serveur persiste l'état de la flotte dans `logs/fleet_state.json` afin que les machines restent visibles après redémarrage du serveur. C'est un mécanisme simple "best-effort" (pas de verrou/DB).
- Le TTL (`FLEET_TTL_SECONDS`) contrôle quand une machine passe en état "expired" côté UI. Le même TTL est exposé au client pour cohérence.
- Les actions sensibles (ex : flush DNS, restart spooler) sont protégées par `ACTION_TOKEN` si tu le définis.

Tests fournis
-------------
- `tests/test_fleet_persistence.py` : POST un rapport et vérifie que `logs/fleet_state.json` contient la machine.
- `tests/test_fleet_expiration.py` : POST un rapport, modifie le timestamp dans `logs/fleet_state.json` pour qu'il soit ancien, puis appelle `/api/fleet` et vérifie que l'entrée est listée comme expirée.

Exemples d'exécution des tests (serveur actif) :

```powershell
$env:FLEET_TOKEN="ton_token_long_et_secret"
python tests/test_fleet_persistence.py
python tests/test_fleet_expiration.py
```

Bonnes pratiques / sécurité
---------------------------
- Ne partage pas `FLEET_TOKEN` publiquement. Utilise une chaîne suffisamment longue.
- Pour la production, n'utilise pas le serveur Flask intégré (outil de dev). Préfère un WSGI (gunicorn/uvicorn) et reverse-proxy.
- Si besoin d'échelle ou de fiabilité, remplace la persistance JSON par une petite base (SQLite, Redis, etc.).

Fichiers importants à connaître
-------------------------------
- `main.py` : logique serveur et endpoints — point d'entrée principal.
- `fleet_agent.py` : agent à déployer sur postes pour remonter les métriques.
- `templates/fleet.html` : UI Fleet + JS (tri/filtre/rafraîchissement).
- `static/i18n.js` : dictionnaire de traductions (FR/EN/ES/RU) utilisé par les templates.

Prochaines améliorations possibles
---------------------------------
- Authentification + TLS pour les rapports agents.
- Remplacement du stockage JSON par une petite DB.
- Meilleure gestion des utilisateurs/roles dans l'UI.
- Notifications / alerting centralisé en cas de postes critiques.

Si tu veux, je peux :
- préparer un petit script PowerShell pour déployer l'agent sur plusieurs postes locales,
- ajouter le support TLS et un guide pour déployer en production,
- ou intégrer la persistance dans SQLite.

---

Créé automatiquement pour toi : résumé des composants, commandes et tests. Dis-moi si tu veux que j'ajoute des captures d'écran, ou un guide pas-à-pas pour déployer l'agent sur d'autres machines.
# Tableau de bord système (Python + Flask)

Surveillance CPU/RAM/Disque/uptime en mode CLI, UI web (Flask) et app desktop Tkinter. Alertes, exports CSV/JSONL, historique, sélecteur de langue (FR/EN/ES/RU), builds .exe et déploiement Render.

## Contenu du repo
- [main.py](main.py) — Lanceur CLI + app Flask (endpoints `/api/stats` et `/api/history`)
- [templates/index.html](templates/index.html) — Temps réel + sélecteur de langue
- [templates/history.html](templates/history.html) — Vue historique (courbes depuis CSV) + sélecteur de langue
- [static/style.css](static/style.css) — Style UI
- [static/i18n.js](static/i18n.js) — Translations FR/EN/ES/RU
- [desktop_app.py](desktop_app.py) — App desktop Tkinter (sans navigateur)
- [requirements.txt](requirements.txt) — Dépendances
- [readme.md](readme.md) — Ce guide
- [docs/ROADMAP.md](docs/ROADMAP.md) — Vision courte “agent santé poste” (à venir)

## Prérequis
- Python 3.10+ recommandé
- `pip` disponible

## Installation rapide
1) Créer/activer un venv (PowerShell) :
```
python -m venv .venv
.venv\Scripts\Activate
```
2) Installer les deps :
```
pip install -r requirements.txt
```

## Modes d’exécution
### CLI
```
python main.py
```
- `--interval 1.5` : changer l’intervalle (s)
- `--export-csv logs/metrics.csv` : export CSV continu
- `--export-jsonl logs/metrics.jsonl` : export JSONL continu

### UI web
```
python main.py --web
```
- `--host 0.0.0.0` : écouter partout (utile en LAN / Render)
- `--port 8000` : port custom
- `--export-csv logs/metrics.csv` et/ou `--export-jsonl logs/metrics.jsonl` : export en tâche de fond pendant que Flask tourne
- Par défaut, si rien n’est fourni, les exports vont sur le Bureau : `Desktop/metrics.csv` et `Desktop/metrics.jsonl`
- Auto-refresh ~2,5 s, badge d’alerte si seuils dépassés (CPU >= 80 %, RAM >= 90 %)

### Historique
- Générer d’abord un CSV via `--export-csv`, puis ouvrir `/history`.
- Courbes CPU/RAM/Disque, max 300 points, table des 20 dernières lignes.

### App desktop (Tkinter)
```
python desktop_app.py
```
- Rafraîchit toutes les 2 s, alertes visuelles.
- Export par défaut : `Desktop/metrics_desktop.csv` (modifiable dans l’app).

## Internationalisation
- Sélecteur de langue (FR/EN/ES/RU) sur les pages Temps réel et Historique.
- Traductions gérées dans [static/i18n.js](static/i18n.js) et persistées via `localStorage`.

## API rapide
- `/api/stats` : métriques courantes (CPU, RAM, disque, uptime, alertes)
- `/api/status` : métriques + score santé (0-100) et statut (`ok|warn|critical`)
- `/api/history?limit=200` : dernières lignes du CSV (limité à 500 côté serveur)
- `/api/action` (POST) : exécute une action approuvée locale (`flush_dns`, `restart_spooler`, `cleanup_temp`, `cleanup_teams`, `cleanup_outlook`, `collect_logs`). `ACTION_TOKEN` est obligatoire : envoyer `Authorization: Bearer <token>`.

## Exports et historique
- `--export-csv` écrit un CSV avec en-têtes (créé s’il n’existe pas).
- `--export-jsonl` écrit un JSON par ligne.
- Fichiers par défaut : Bureau (Desktop) si aucun chemin fourni.

## Déploiement Render (web)
- Build Command : `pip install -r requirements.txt`
- Start Command : `python main.py --web`
- Variables : `PORT` fourni par Render (défaut pris en compte), `HOST=0.0.0.0` si besoin.

## Construire un .exe (Windows)
1) Activer le venv :
```
.\.venv\Scripts\Activate
```
2) Installer PyInstaller :
```
python -m pip install pyinstaller
```
3) Générer :
```
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" main.py
```
- Résultat : `dist/main.exe`
- Exemple d’usage :
```
dist\main.exe --web --export-csv logs\metrics.csv
```
- Options utiles : `--icon chemin\vers\icon.ico` pour l’icône.

## Tests rapides
- CLI : `python main.py --interval 1`
- Web : `python main.py --web`
- Export + web : `python main.py --web --export-csv logs/metrics.csv`
- Historique : après génération du CSV, ouvrir `/history` (limite 300 points)

## Notes techniques
- `psutil.cpu_percent(interval=0.3)` attend un court instant pour un premier échantillon non nul.
- Le disque cible la racine du système (lecteur principal) pour des valeurs cohérentes.
- JSONL (un objet par ligne) est pratique pour les ingest pipelines et la lecture en flux.

## Valeurs à remplacer (exemples rapides)
- `(ex: http://mon-serveur:5000)` : URL où votre instance DashFleet sera accessible. Exemples : `http://localhost:5000`, `http://192.168.0.97:5000`, ou `https://dashfleet.example.com`.
- `<HOST>` : même URL que ci‑dessus, sans slash final (ex. `http://localhost:5000`).
- `FLEET_TOKEN` / `ACTION_TOKEN` : tokens secrets à définir dans les variables d'environnement sur le serveur (ne pas les versionner).
- `<API_KEY>` : clé API retournée par `POST /api/orgs` pour une organisation.

Règles rapides : utilisez HTTPS en production et ne publiez jamais vos tokens dans un README public.

## Sécurité minimale pour les actions
- Les actions `/api/action` sont prévues pour un usage local. `ACTION_TOKEN` (env) est obligatoire. Appelez avec un header `Authorization: Bearer <token>` ou un champ JSON `token`.

## Alertes webhook (optionnel)
- Définir `WEBHOOK_URL` pour envoyer une alerte lorsqu’un statut santé devient `critical` (payload JSON simple `{ "text": "..." }` compatible Slack/Teams).
- Définir `WEBHOOK_MIN_SECONDS` (défaut 300) pour le délai minimal entre deux envois.

## Suite (vision courte)
On vise un “agent santé poste” léger : score de santé, auto-remédiations simples, self-service (scripts approuvés), alertes sobres. Voir [docs/ROADMAP.md](docs/ROADMAP.md) pour le plan à étapes.

## Scripts d'installation et service
Des exemples sont fournis dans `scripts/` et `deploy/systemd/` :

- `scripts/install_systemd.sh` : script d'installation rapide pour Linux (copie dans `/opt/dashfleet`, création d'un venv et activation d'une unité systemd).
- `deploy/systemd/dashfleet.service` : fichier d'unité systemd exemple.
- `scripts/install_windows_agent.ps1` : exemple PowerShell pour installer l'agent/instance sur Windows et créer une tâche planifiée au démarrage.

Voir aussi : `scripts/migrate_fleet_to_sqlite.py` pour migrer l'ancien backup JSON vers SQLite.
