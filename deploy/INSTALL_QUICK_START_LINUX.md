# DashFleet Agent - Installation Rapide Linux (All-in-One)

Installer l'agent DashFleet sur **Kali Linux, Debian ou Ubuntu** en une seule commande.

## Prérequis
- Kali Linux, Debian 11+, ou Ubuntu 20.04+
- `sudo` ou accès root
- Accès Internet
- `curl` ou `wget`

## Installation (One-Liner)

### Méthode 1 : Directement depuis GitHub (recommandée)

Ouvre un terminal et exécute :

```bash
curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux_oneliner.sh | sudo bash -s -- -k d2f6f9a8-3c7e-4c1f-9b0f-123456789abc
```

Remplace `d2f6f9a8-3c7e-4c1f-9b0f-123456789abc` par ton **API Key** réelle.

### Méthode 2 : Avec nom de machine personnalisé

```bash
curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux_oneliner.sh | sudo bash -s -- -k d2f6f9a8-3c7e-4c1f-9b0f-123456789abc -m kali-machine-01
```

### Méthode 3 : Télécharger et exécuter

```bash
wget https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux_oneliner.sh
sudo bash install_dashfleet_linux_oneliner.sh -k d2f6f9a8-3c7e-4c1f-9b0f-123456789abc
```

## Ce que fait le script

1. ✅ Vérifie les droits root
2. ✅ Installe Python3/pip (si absent)
3. ✅ Crée `/opt/dashfleet-agent/`
4. ✅ Télécharge `fleet_agent.py` et `fleet_utils.py` depuis GitHub
5. ✅ Installe les dépendances : `psutil`, `requests`
6. ✅ Génère `config.json` avec ton token + hostname réel
7. ✅ Crée un service systemd `dashfleet-agent`
8. ✅ Lance le service immédiatement

## Vérifications après installation

### Voir le statut du service
```bash
systemctl status dashfleet-agent
```

### Voir les 10 derniers logs
```bash
tail -f /opt/dashfleet-agent/logs/agent.log
```

### Voir les machines sur le dashboard
```bash
curl -s https://dash-fleet.com/api/fleet/public | jq .
```

## Dashboard
Accès : https://dash-fleet.com/fleet

La machine apparaîtra dans les **30 secondes** après l'installation.

## Gestion du service

### Démarrer
```bash
sudo systemctl start dashfleet-agent
```

### Arrêter
```bash
sudo systemctl stop dashfleet-agent
```

### Redémarrer
```bash
sudo systemctl restart dashfleet-agent
```

### Voir les logs en temps réel
```bash
sudo journalctl -u dashfleet-agent -f
```

### Désactiver au démarrage
```bash
sudo systemctl disable dashfleet-agent
```

### Réactiver au démarrage
```bash
sudo systemctl enable dashfleet-agent
```

## Désinstallation

```bash
sudo systemctl stop dashfleet-agent
sudo systemctl disable dashfleet-agent
sudo rm -rf /opt/dashfleet-agent
sudo rm /etc/systemd/system/dashfleet-agent.service
sudo systemctl daemon-reload
```

## Paramètres

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `-k` | Obligatoire | Clé d'authentification (token API) |
| `-m` | `hostname` | Nom de la machine |
| `-s` | `https://dash-fleet.com` | URL du serveur DashFleet |
| `-d` | `/opt/dashfleet-agent` | Répertoire d'installation |

## Exemples

### Installation sur plusieurs serveurs (Ansible, etc.)

```bash
# Boucle simple
for host in server1 server2 server3; do
  ssh root@$host "curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux_oneliner.sh | bash -s -- -k d2f6f9a8-3c7e-4c1f-9b0f-123456789abc -m $host"
done
```

### Installation avec mot de passe sudo

Si `sudo` demande un mot de passe :

```bash
sudo bash -c 'curl -sSL https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_linux_oneliner.sh | bash -s -- -k d2f6f9a8-3c7e-4c1f-9b0f-123456789abc'
```

## Windows

Pour Windows :

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_dashfleet_oneliner.ps1" -OutFile "$env:TEMP\install.ps1"; & "$env:TEMP\install.ps1" -ApiKey "d2f6f9a8-3c7e-4c1f-9b0f-123456789abc"
```

Voir [INSTALL_QUICK_START.md](INSTALL_QUICK_START.md) pour plus de détails.

## Dépannage

### Python3 n'est pas trouvé
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip
```

### Le service ne démarre pas
```bash
sudo journalctl -u dashfleet-agent -n 20
```

### Logs du service
```bash
sudo tail -100 /opt/dashfleet-agent/logs/agent.log
```

### Tester manuellement
```bash
cd /opt/dashfleet-agent
python3 fleet_agent.py --config config.json
```

## Support

- Config : `/opt/dashfleet-agent/config.json`
- Logs : `/opt/dashfleet-agent/logs/agent.log`
- Service : `dashfleet-agent` (systemd)
- Journal : `sudo journalctl -u dashfleet-agent`
