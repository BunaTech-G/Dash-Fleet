# Tableau de bord système (Python + Flask)

Petit projet pédagogique qui surveille CPU, RAM, disque et uptime en mode CLI et via une mini interface web Flask. Les mesures viennent de `psutil` et des alertes se déclenchent si CPU >= 80 % ou RAM >= 90 %.

## Contenu
- [main.py](main.py) — Lanceur CLI et app Flask
- [templates/index.html](templates/index.html) — Interface web temps réel
- [templates/history.html](templates/history.html) — Vue historique (courbes depuis CSV)
- [static/style.css](static/style.css) — Style du tableau de bord
- [requirements.txt](requirements.txt) — Dépendances Python

## Prérequis
- Python 3.10+ recommandé
- `pip` disponible

## Installation
1) Créer et activer un environnement virtuel (PowerShell Windows) :
```
python -m venv .venv
.venv\Scripts\Activate
```

2) Installer les dépendances :
```
pip install -r requirements.txt
```

## Exécution (mode CLI)
Afficher les métriques dans le terminal toutes les 2 secondes :
```
python main.py
```

Options :
- `--interval 1.5` — changer l’intervalle de rafraîchissement (secondes)
- `--export-csv logs/metrics.csv` — ajouter les mesures dans un CSV (utile pour /history)
- `--export-jsonl logs/metrics.jsonl` — ajouter les mesures en JSON Lines

Arrêt : `Ctrl+C`.

## Exécution (interface web)
Lancer l’UI Flask sur http://127.0.0.1:5000 :
```
python main.py --web
```

Options :
- `--host 0.0.0.0` — écouter sur toutes les interfaces
- `--port 8000` — port personnalisé
- `--export-csv logs/metrics.csv` — (optionnel) lance un export en tâche de fond en plus de l’UI
- `--export-jsonl logs/metrics.jsonl` — (optionnel) export JSONL en tâche de fond
- Par défaut (si tu n’indiques rien) les exports vont dans ton Bureau : `Desktop/metrics.csv` et `Desktop/metrics.jsonl`

La page se met à jour automatiquement toutes les ~2,5 s. Un badge rouge apparaît en cas d’alerte.

## Ce que fait le code
- Récupère CPU, RAM, disque et uptime avec `psutil` ([main.py](main.py))
- Formate l’uptime en `HH:MM:SS` et convertit les bytes en GiB pour la lisibilité
- Déclenche des alertes selon les seuils CPU/RAM et les affiche en CLI + web
- Expose un endpoint JSON `/api/stats` réutilisable ([main.py](main.py))
- Propose des exports CSV/JSONL pour analyser plus tard ([main.py](main.py))
- Fournit une vue historique `/history` qui lit `logs/metrics.csv` et trace les courbes CPU/RAM/Disque
- Permet de lancer l’UI Flask + un export CSV/JSONL en même temps (un seul processus)
- Fournit une app desktop Tkinter sans navigateur ([desktop_app.py](desktop_app.py))

## Notes rapides pour apprendre
- `psutil.cpu_percent(interval=0.3)` attend un court instant pour éviter de renvoyer 0 au premier appel.
- L’usage disque cible la racine de votre OS (lecteur principal sous Windows) pour des valeurs stables.
- Le format JSONL (un objet JSON par ligne) est pratique pour les logs en continu et lisible par de nombreux outils.

## Tester le projet
- CLI : `python main.py --interval 1` puis solliciter CPU/RAM pour voir les alertes s’activer.
- Web : `python main.py --web`, ouvrir le navigateur et vérifier que les valeurs se rafraîchissent.
- Exports : `python main.py --export-csv logs/out.csv --export-jsonl logs/out.jsonl`, laisser tourner 5+ échantillons puis ouvrir les fichiers pour vérifier les entêtes/lignes.
- Web + export dans un seul process : `python main.py --web --export-csv logs/metrics.csv`
- Historique : après avoir généré `logs/metrics.csv` via `--export-csv` (en CLI ou avec l’option ci-dessus), ouvrir `/history` pour afficher les courbes (max 300 points).

## Idées suivantes
- Ajouter un service Windows ou un unit systemd pour faire tourner l’exporteur en continu.
- Packager en image Docker avec endpoints de healthcheck.

## App desktop (sans navigateur)
```
python desktop_app.py
```
- Rafraîchit toutes les 2 s, alerte visuelle si seuils CPU/RAM dépassés.
- Exporte par défaut vers Desktop/metrics_desktop.csv (modifiable dans le champ de l’app).
- Fenêtre native Tkinter (aucun navigateur requis).

## Construire un .exe (Windows)
1) Active l’environnement :
```
.\.venv\Scripts\Activate
```
2) Installe PyInstaller :
```
python -m pip install pyinstaller
```
3) Génère l’exécutable :
```
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" main.py
```
Le .exe se trouvera dans `dist/main.exe`. Copie le dossier `dist` (qui contient `main.exe`) n’importe où et lance-le en double-cliquant ou en ligne de commande :
```
dist\main.exe --web --export-csv logs\metrics.csv
```
Notes :
- L’option `--add-data` est essentielle pour embarquer templates et static.
- Tu peux ajouter une icône avec `--icon chemin\vers\icone.ico`.
- Si tu partages l’exécutable, rappelle qu’il écoute par défaut sur 127.0.0.1:5000.
