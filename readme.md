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
- `/api/action` (POST) : exécute une action approuvée locale (`flush_dns`, `restart_spooler`, `cleanup_temp`, `cleanup_teams`, `cleanup_outlook`, `collect_logs`). Optionnellement protégée par `ACTION_TOKEN`.

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

## Sécurité minimale pour les actions
- Les actions `/api/action` sont prévues pour un usage local. Si besoin, définir `ACTION_TOKEN` (env) et appeler avec un header `Authorization: Bearer <token>`.

## Alertes webhook (optionnel)
- Définir `WEBHOOK_URL` pour envoyer une alerte lorsqu’un statut santé devient `critical` (payload JSON simple `{ "text": "..." }` compatible Slack/Teams).
- Définir `WEBHOOK_MIN_SECONDS` (défaut 300) pour le délai minimal entre deux envois.

## Suite (vision courte)
On vise un “agent santé poste” léger : score de santé, auto-remédiations simples, self-service (scripts approuvés), alertes sobres. Voir [docs/ROADMAP.md](docs/ROADMAP.md) pour le plan à étapes.
