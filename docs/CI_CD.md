CI / CD (GitHub Actions) — DashFleet

Ce dépôt contient un workflow (/.github/workflows/ci-deploy.yml) qui :
- exécute les tests (`pytest`) sur `push` vers `main`;
- construit un package (`python -m build`) et publie l'artefact `dist/*`;
- permet un déploiement manuel (`workflow_dispatch`) qui SCP les artefacts vers un serveur et redémarre le service `dashfleet`.

Secrets GitHub (à configurer dans Settings → Secrets):
- `SSH_PRIVATE_KEY` : clé privée SSH (PEM) utilisée pour se connecter au serveur.
- `SERVER_HOST` : adresse IP ou hostname du serveur.
- `SERVER_USER` : utilisateur SSH (ex. `deploy`).
- `SERVER_PORT` : port SSH (optionnel, défaut 22).
- `REMOTE_PATH` : chemin distant où déposer les artefacts (ex. `/var/www/dashfleet/releases`).

Notes et recommandations :
- La job `deploy` ne s'exécute qu'en dispatch manuel (sécurité). Vous pouvez restreindre davantage par règles de protection de branche.
- Assurez-vous que le serveur accepte l'authentification par clé et que l'utilisateur a les droits nécessaires pour écrire `REMOTE_PATH` et redémarrer `dashfleet` via `sudo` (configurez `/etc/sudoers.d` si besoin sans mot de passe pour la commande `systemctl restart dashfleet`).
- Ce workflow réalise une copie simple des artefacts ; adaptez-le pour un déploiement plus complet (rsync d'un repo, extraction, migrations SQL, maintenance page, rollback, etc.).

Exécuter un déploiement manuel :
- Ouvrez l'onglet Actions → CI & Deploy → Run workflow, sélectionnez la branche `main` et lancez.

Sécurité :
- Ne stockez pas de secrets en clair dans le repo. Utilisez les GitHub Secrets et des utilisateurs avec droits limités côté serveur.
