# Release v0.0.1

Date: 2025-12-30

Résumé
- Migration de la persistance JSON vers SQLite (`data/fleet.db`) avec sauvegarde JSON conservée.
- Auth multi‑tenant : tables `organizations` et `api_keys` + vérification côté serveur.
- Sessions serveur : endpoints `/api/login` et `/api/logout` (cookie `dashfleet_sid`, HTTP-only).
- Client : UI de login API-key avec option d'échange serveur (`serverLogin`) et amélioration du toast d'erreur.
- Installateurs : exemples `deploy/systemd/dashfleet.service` et `scripts/install_systemd.sh`.
- Windows : script de construction PyInstaller et script d'installation `scripts/install_windows_agent.ps1`.
- Packaging : distributions Python générées (`dist/*.whl`, `dist/*.tar.gz`) et agent Windows (`dist/fleet_agent.exe`).
- Tests : intégration exécutée localement (3 tests passés).

Notes de migration
- Le script `scripts/migrate_fleet_to_sqlite.py` importe l'état JSON et conserve une copie dans `logs/fleet_state.json`.

Instructions rapides
1. Installer et configurer l'environnement virtuel Python.
2. Exporter `ACTION_TOKEN` avant d'exécuter le serveur pour les opérations admin.
3. Pour créer automatiquement la release GitHub (si `gh` est configuré) :
   ``gh release create v0.0.1 dist/dashfleet-0.0.1-py3-none-any.whl dist/dashfleet-0.0.1.tar.gz dist/fleet_agent.exe --title "v0.0.1" --notes-file RELEASE_NOTES.md``

Remerciements
- Travail préparatoire et corrections diverses pour linting, packaging et UX.
 
Assets publiés
- Wheel: https://github.com/BunaTech-G/Dashboard/releases/download/v0.0.1/dashfleet-0.0.1-py3-none-any.whl
- Source (tar.gz): https://github.com/BunaTech-G/Dashboard/releases/download/v0.0.1/dashfleet-0.0.1.tar.gz
- Agent Windows: https://github.com/BunaTech-G/Dashboard/releases/download/v0.0.1/fleet_agent.exe
 - Agent Windows: https://github.com/BunaTech-G/Dashboard/releases/download/v0.0.1/fleet_agent.exe

# Release v0.0.2

Date: 2025-12-30

Résumé
- Ajout d'un workflow GitHub Actions CI (`.github/workflows/ci.yml`) qui exécute lint, tests et build.
- Correction : affichage de la page de login avant la page principale lorsque l'utilisateur n'a pas de session.
- Ajout d'un thread de nettoyage des sessions expirées et option `PUBLIC_READ` (variable d'environnement) pour affichage public en lecture seule.
- Publication de la release v0.0.2 (artefacts `dist/*`).

Assets publiés v0.0.2
- Release page: https://github.com/BunaTech-G/Dashboard/releases/tag/v0.0.2
