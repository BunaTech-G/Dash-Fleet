# GitHub Actions Configuration

## Workflows disponibles

### 1. CI (Intégration Continue)
**Fichier** : [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

**Déclenchement** :
- Push sur `main`, `master`, `fix/pyproject-exclude`
- Pull requests vers ces branches

**Jobs** :
- `lint` : Vérification flake8 avec config `.flake8`
- `test` : Lancement serveur Flask + pytest
- `build` : Construction package Python

**Variables d'environnement requises** : Aucune (tout en local)

---

### 2. CI & Deploy
**Fichier** : [`.github/workflows/ci-deploy.yml`](.github/workflows/ci-deploy.yml)

**Déclenchement** :
- Push sur `fix/pyproject-exclude`
- Pull requests vers `fix/pyproject-exclude`
- Manuel via `workflow_dispatch`

**Jobs** : Identique à CI + préparation artifacts

---

### 3. Deploy to VPS
**Fichier** : [`.github/workflows/deploy-vps.yml`](.github/workflows/deploy-vps.yml)

**Déclenchement** :
- Push sur `fix/pyproject-exclude` (auto)
- Manuel via `workflow_dispatch` (option restart only)

**Secrets requis** :
- `VPS_SSH_PRIVATE_KEY` : Clé SSH privée pour connexion root@83.150.218.175

**Actions** :
1. Backup de l'état actuel
2. Git pull origin fix/pyproject-exclude
3. Installation dépendances (venv)
4. Migrations DB si nécessaire
5. Restart service `dashfleet`
6. Health check sur `/api/status`

**Configuration VPS** :
```bash
# Ajouter la clé publique sur le VPS
ssh root@83.150.218.175
mkdir -p ~/.ssh
echo "VOTRE_CLE_PUBLIQUE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

### 4. Build Agent Executables
**Fichier** : [`.github/workflows/build-agents.yml`](.github/workflows/build-agents.yml)

**Déclenchement** :
- Push sur `fix/pyproject-exclude` modifiant `fleet_agent.py`, `fleet_agent_windows_tray.py`, `fleet_utils.py`
- Release GitHub publiée
- Manuel via `workflow_dispatch`

**Jobs** :
- `build-windows` : Génère `fleet_agent.exe` et `fleet_agent_tray.exe` (avec systray)
- `build-linux` : Génère `fleet_agent` (binaire Linux)
- `release-assets` : Upload automatique sur GitHub Releases

**Artifacts** :
- `windows-agents/fleet_agent.exe` (console)
- `windows-agents/fleet_agent_tray.exe` (avec icône système)
- `linux-agent/fleet_agent` (binaire statique)

---

### 5. Security Scan
**Fichier** : [`.github/workflows/security.yml`](.github/workflows/security.yml)

**Déclenchement** :
- Push sur `fix/pyproject-exclude` ou `main`
- Pull requests
- Hebdomadaire (lundi 00:00 UTC)
- Manuel via `workflow_dispatch`

**Jobs** :
- `dependency-scan` : Safety (CVE dépendances) + Bandit (code Python)
- `code-quality` : Pylint + Radon (complexité cyclomatique)
- `secrets-scan` : TruffleHog (détection secrets dans historique Git)

**Rapports générés** :
- `security-reports/safety-report.json`
- `security-reports/bandit-report.json`
- `quality-reports/pylint-report.json`

---

### 6. Update Deployment Scripts
**Fichier** : [`.github/workflows/update-deploy-scripts.yml`](.github/workflows/update-deploy-scripts.yml)

**Déclenchement** :
- Push sur `fix/pyproject-exclude` modifiant `deploy/**`
- Manuel via `workflow_dispatch`

**Secrets requis** :
- `VPS_SSH_PRIVATE_KEY`

**Actions** :
1. Sync scripts `deploy/` vers VPS (`/var/www/dashfleet-deploy`)
2. Remplacement URLs GitHub (main → fix/pyproject-exclude)
3. Permissions exécution (chmod +x)
4. Test accessibilité via `https://dash-fleet.com/deploy/`

---

## Configuration des secrets GitHub

### Ajouter VPS_SSH_PRIVATE_KEY

1. **Générer paire de clés SSH** (si inexistante) :
```bash
ssh-keygen -t ed25519 -C "github-actions@dashfleet" -f ~/.ssh/dashfleet_deploy
```

2. **Copier clé publique sur VPS** :
```bash
ssh-copy-id -i ~/.ssh/dashfleet_deploy.pub root@83.150.218.175
```

3. **Ajouter clé privée dans GitHub** :
- Aller sur https://github.com/BunaTech-G/Dashboard-syst-me-/settings/secrets/actions
- Cliquer "New repository secret"
- Nom : `VPS_SSH_PRIVATE_KEY`
- Valeur : Contenu de `~/.ssh/dashfleet_deploy` (clé PRIVÉE entière)

4. **Tester manuellement** :
```bash
ssh -i ~/.ssh/dashfleet_deploy root@83.150.218.175 "systemctl status dashfleet"
```

---

## Exemples d'utilisation

### Déploiement automatique
```bash
# Sur votre machine locale
git checkout fix/pyproject-exclude
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin fix/pyproject-exclude
# → Déclenche automatiquement ci.yml + deploy-vps.yml
```

### Restart service sans deploy
1. Aller sur GitHub Actions
2. Sélectionner "Deploy to VPS"
3. Cliquer "Run workflow"
4. Cocher "Restart only"
5. Cliquer "Run workflow"

### Build manuel des agents
1. Aller sur GitHub Actions
2. Sélectionner "Build Agent Executables"
3. Cliquer "Run workflow"
4. Télécharger artifacts dans "Summary" du run

### Créer une release avec agents
```bash
git tag v1.2.3
git push origin v1.2.3
# → Déclenche build-agents.yml avec upload automatique sur release
```

---

## Dépannage

### Erreur "Host key verification failed"
```bash
# Sur runner GitHub, ajouter VPS aux known_hosts
ssh-keyscan -H 83.150.218.175 >> ~/.ssh/known_hosts
```

### Erreur "Permission denied (publickey)"
- Vérifier que `VPS_SSH_PRIVATE_KEY` contient TOUTE la clé (y compris `-----BEGIN OPENSSH PRIVATE KEY-----`)
- Vérifier clé publique sur VPS : `cat ~/.ssh/authorized_keys`

### Health check échoue après deploy
```bash
# Sur VPS
sudo systemctl status dashfleet
sudo journalctl -u dashfleet -n 50 --no-pager
# Vérifier logs applicatifs
tail -f /opt/dashfleet/logs/api.log
```

### Tests échouent en CI
```bash
# Lancer localement avec mêmes variables d'environnement
export SECRET_KEY=ci-secret
export ALLOW_DEV_INSECURE=1
export FLEET_TOKEN=ci-fleet-token
python main.py --web --host localhost --port 5000 &
pytest -v tests
```

---

## Badges GitHub Actions

Ajouter dans `README.md` :

```markdown
[![CI](https://github.com/BunaTech-G/Dashboard-syst-me-/actions/workflows/ci.yml/badge.svg)](https://github.com/BunaTech-G/Dashboard-syst-me-/actions/workflows/ci.yml)
[![Deploy](https://github.com/BunaTech-G/Dashboard-syst-me-/actions/workflows/deploy-vps.yml/badge.svg)](https://github.com/BunaTech-G/Dashboard-syst-me-/actions/workflows/deploy-vps.yml)
[![Security](https://github.com/BunaTech-G/Dashboard-syst-me-/actions/workflows/security.yml/badge.svg)](https://github.com/BunaTech-G/Dashboard-syst-me-/actions/workflows/security.yml)
```

---

## Maintenance

### Mise à jour versions Actions
Surveiller dépréciations GitHub Actions :
- `actions/checkout@v4` → `v5` quand disponible
- `actions/setup-python@v5` → `v6`
- `actions/upload-artifact@v4` → `v5`

### Mise à jour Python
Changer `PYTHON_VERSION: "3.11"` → `"3.12"` dans tous les workflows quand migration validée.

### Ajout nouveaux tests
Modifier `.github/workflows/ci.yml` :
```yaml
- name: Run tests
  run: pytest -v tests --cov=. --cov-report=xml
```
