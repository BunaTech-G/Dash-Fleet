# Agent Python Mini-MDM

## Fonctionnalités
- Collecte CPU, RAM, disque, uptime
- Envoi des métriques au serveur Flask via API REST
- Authentification par token (FLEET_TOKEN)
- Journalisation locale dans agent.log
- Configuration par arguments ou variables d’environnement

## Utilisation

```bash
python fleet_agent.py --server http://127.0.0.1:5000 --token VOTRE_TOKEN
```

## Test unitaire

```bash
python test_fleet_agent.py
```

## Sécurité
- Le token n’est jamais affiché dans les logs
- Les erreurs sont journalisées

## Dépendances
- psutil
