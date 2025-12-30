# Playbook DigitalOcean — Déploiement DashFleet (pas d'exécution automatique)

Étapes pour créer un Droplet et déployer DashFleet.

1) Créer le Droplet
- Via UI : Marketplace → Ubuntu 22.04, choisir 1GB/1vCPU (pour staging) ou 2GB pour production.
- Ajouter ta clé SSH.

2) Connexion et préparation

```bash
ssh root@<IP>
apt update && apt upgrade -y
adduser deploy
usermod -aG sudo deploy
```

3) Pare-feu

```bash
apt install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

4) Installer dépendances

```bash
apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
```

5) Déploiement du code, virtualenv, service et nginx
- Identique aux étapes Hetzner ci-dessus (cloner repo, créer venv, copier unit systemd, config nginx, certbot).

6) DO tips
- Utilise les snapshots DO avant les changements majeurs.
- Pour backups automatisés, active l'option Backups dans le panneau (coût en plus).
