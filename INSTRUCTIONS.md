# 📋 DashFleet - Instructions & Règles du Projet

## 🎯 Principes Fondamentaux

### Philosophie du Projet
- **Simplicité avant tout** : L'utilisateur lance juste l'exe, c'est tout
- **Zéro configuration manuelle** : La machine se détecte toute seule
- **Pratique d'abord** : Les données doivent être utiles et visibles
- **Pas de perte de données** : Garder l'historique des machines
- **Transparence** : Voir ce qui se passe (online/offline/deleted)

---

## 🚀 Flux de Déploiement Simplifié

### Pour une Nouvelle Machine

**Une seule commande :**
```powershell
Invoke-WebRequest -Uri "https://github.com/BunaTech-G/Dash-Fleet/raw/fix/pyproject-exclude/deploy/agent_binaries/fleet_agent.exe" -OutFile "C:\Program Files\DashFleet\dashfleet-agent.exe"

& 'C:\Program Files\DashFleet\dashfleet-agent.exe' --token api_a7ee4957ca1640e180802c256fdf
```

**C'est tout.** L'exe fait le reste :
- ✅ Récupère le nom de la machine automatiquement
- ✅ Récupère l'architecture (x86 / x64 / ARM)
- ✅ Vérifie la version Python (si applicable)
- ✅ Récupère l'OS automatiquement
- ✅ Récupère le Hardware ID
- ✅ Se connecte au serveur
- ✅ Envoie les métriques toutes les 30 secondes
- ✅ Crée la tâche planifiée (optionnel)

**Pas de manipulation manuelle. Aucune.**

---

## 📊 Statuts des Machines

### États Possibles

| Statut | Signification | Couleur | Action |
|--------|---------------|---------|--------|
| **ONLINE** | Machine qui envoie des métriques | 🟢 Vert | Voir détails |
| **OFFLINE** | Machine n'a pas envoyer de données depuis 10 min | 🟡 Jaune | Relancer ou supprimer |
| **DELETED** | Machine supprimée par l'utilisateur | ⚫ Gris | Restaurer ou effacer définitivement |

### Gestion des Machines

**Supprimer une machine :**
```
1. Cliquer sur le bouton "Supprimer" de la machine
2. Confirmation : "Êtes-vous sûr ?"
3. Machine marquée DELETED (elle reste visible mais grisée)
4. Peut être restaurée ou supprimée définitivement
```

**Restaurer une machine supprimée :**
```
1. Cliquer sur le bouton "Restaurer" sur une machine DELETED
2. Machine revient en ONLINE/OFFLINE selon son état
```

**Supprimer définitivement :**
```
1. Sur une machine DELETED
2. Cliquer "Supprimer définitivement"
3. Confirmation finale
4. Machine disparaît complètement de la base de données
```

---

## 📝 Informations Affichées par Machine

### Obligatoires (doivent être remplis)
- **Machine ID** : Nom de la machine (ex: OSIDIBE-PC)
- **OS** : Windows 10, Ubuntu 22.04, etc. (récupéré automatiquement)
- **Architecture** : x86, x64, ARM (récupéré automatiquement)
- **Python Version** : 3.9, 3.11, etc. (si applicable)
- **Hardware ID** : UUID unique de la machine
- **Statut** : ONLINE / OFFLINE / DELETED
- **Dernière mise à jour** : Timestamp du dernier rapport

### Métriques (en temps réel)
- **CPU** : % utilisation
- **RAM** : % utilisée + GB utilisés / GB totaux
- **Disk** : % utilisé + GB utilisés / GB totaux
- **Health Score** : 0-100 (basé sur les 3 métriques)
- **Uptime** : Temps depuis le dernier démarrage

---

## 💬 Fonctionnalités à Implémenter

### Messages & Notifications ❌ (À faire)
- [ ] Envoyer un message à une machine
- [ ] Exécuter une commande à distance
- [ ] Redémarrer une machine
- [ ] Arrêter une machine
- [ ] Recevoir les notifications d'alerte

### Tableau de Bord (Dashboard) ✅ (Fait)
- [x] Afficher toutes les machines
- [x] Filtrer par statut
- [x] Trier par colonne
- [x] Voir les détails
- [x] Graphiques temps réel
- [x] Historique des métriques

---

## 🔧 Règles de Codage

### Code Exécutable (fleet_agent.py)
```python
# ✅ DOIT
- Récupérer automatiquement le nom de la machine
- Récupérer automatiquement l'architecture
- Récupérer automatiquement l'OS
- Récupérer automatiquement le Python version
- Récupérer automatiquement le Hardware ID

# ❌ NE DOIT PAS DEMANDER À L'UTILISATEUR:
- Le nom de la machine
- L'architecture
- L'OS
- La version Python
- L'Hardware ID
```

### Serveur (main.py)
```python
# ✅ DOIT
- Stocker tous les champs (OS, arch, Python, HW ID)
- Marquer le statut (ONLINE/OFFLINE/DELETED)
- Garder l'historique complet
- Supporter les messages et actions
- Vérifier la validité des données
```

### API Endpoints
```
GET  /api/fleet              - Lister les machines (auth required)
GET  /api/fleet/public       - Lister les machines (public)
POST /api/fleet/report       - Recevoir les métriques (agent)
DELETE /api/fleet/{id}       - Supprimer une machine
POST /api/fleet/{id}/restore - Restaurer une machine
POST /api/fleet/{id}/message - Envoyer un message
POST /api/fleet/{id}/action  - Exécuter une action
```

---

## 🗄️ Schéma Base de Données

```sql
-- Machines avec TOUTES les infos
CREATE TABLE fleet (
    id TEXT PRIMARY KEY,  -- "org_id:machine_id"
    org_id TEXT,
    machine_id TEXT,
    report JSON,          -- Les métriques
    
    -- Infos détectées automatiquement:
    os TEXT,              -- "Windows 10", "Ubuntu 22.04"
    architecture TEXT,    -- "x86", "x64", "ARM"
    python_version TEXT,  -- "3.11.4"
    hardware_id TEXT,     -- UUID unique
    
    -- Statuts:
    status TEXT,          -- "ONLINE", "OFFLINE", "DELETED"
    ts REAL,              -- Timestamp dernière mise à jour
    
    -- Soft delete:
    deleted_at REAL,      -- Timestamp suppression (NULL si actif)
    
    FOREIGN KEY (org_id) REFERENCES organizations(id)
);
```

---

## 📋 Checklist de Déploiement

Avant de déployer une nouvelle version :

- [ ] L'exe récupère automatiquement le nom de la machine
- [ ] L'exe récupère automatiquement l'OS
- [ ] L'exe récupère automatiquement l'architecture
- [ ] L'exe récupère automatiquement la version Python
- [ ] L'exe récupère automatiquement le Hardware ID
- [ ] Les données sont stockées dans la base de données
- [ ] Le statut passe à ONLINE quand des données arrivent
- [ ] Le statut passe à OFFLINE après 10 minutes sans données
- [ ] Les machines DELETED restent visibles mais grisées
- [ ] On peut restaurer une machine DELETED
- [ ] On peut supprimer définitivement une machine DELETED
- [ ] Confirmation avant suppression
- [ ] Les métriques s'affichent en temps réel
- [ ] Le Health Score se calcule correctement
- [ ] Pas de champs vides (N/A) - tout doit être rempli

---

## 🔐 Sécurité

### Authentification
- API Key Bearer token pour tous les endpoints
- Validée contre la table `api_keys`
- Organisées par `org_id`

### Autorisation
- Chaque org ne voit que ses machines
- Suppression et actions limitées au propriétaire
- Admin peut tout faire

### Données Sensibles
- Config.json contient la clé API (fichier local)
- Logs stockés localement
- Pas de transmission de mots de passe
- HTTPS obligatoire en production

---

## 📞 Exemple Complet de Déploiement

### 1. Générer une clé API (admin)
```bash
ssh root@83.150.218.175
cd /opt/dashfleet
python3 << 'EOF'
import sqlite3, uuid, time
conn = sqlite3.connect('data/fleet.db')
c = conn.cursor()
org_id = 'prod-' + str(uuid.uuid4())[:8]
api_key = 'api_' + str(uuid.uuid4()).replace('-', '')[:28]
c.execute('INSERT INTO organizations (id, name) VALUES (?, ?)', (org_id, 'Production'))
c.execute('INSERT INTO api_keys (key, org_id, created_at, revoked) VALUES (?, ?, ?, 0)',
          (api_key, org_id, time.time()))
conn.commit()
print(f'API_KEY={api_key}')
EOF
```

### 2. Sur la machine client (Windows)
```powershell
# Télécharger
Invoke-WebRequest -Uri "https://github.com/BunaTech-G/Dash-Fleet/raw/fix/pyproject-exclude/deploy/agent_binaries/fleet_agent.exe" `
  -OutFile "C:\Program Files\DashFleet\dashfleet-agent.exe"

# Lancer avec juste la clé API
& 'C:\Program Files\DashFleet\dashfleet-agent.exe' `
  --server https://dash-fleet.com `
  --token api_xxxxxxx

# C'est tout ! L'exe fait le reste
```

### 3. Vérifier sur le dashboard
```
Aller à: https://dash-fleet.com/fleet/public
Chercher votre machine par nom
Voir les métriques en temps réel
```

---

## 🎓 Ce Qu'On DOIT Avoir

### Fonctionnalités Critiques (Non-Négociables)
1. ✅ Détection automatique du nom de machine
2. ✅ Détection automatique de l'OS
3. ✅ Détection automatique de l'architecture
4. ✅ Détection automatique du Python version
5. ✅ Détection automatique du Hardware ID
6. ✅ Statuts ONLINE/OFFLINE/DELETED
7. ✅ Soft delete (machines supprimées restent visibles)
8. ✅ Confirmation avant suppression
9. ✅ Restauration possible
10. ❌ Messages et actions (À implémenter)

### Data Quality
- ✅ Pas de champs N/A ou vides
- ✅ Toutes les données remplies automatiquement
- ✅ Synchronisation temps réel
- ✅ Historique complet conservé

---

## 🚀 Roadmap Prochaines Étapes

1. **Corriger l'exe** : Récupérer automatiquement OS, arch, Python, HW ID
2. **Implémenter les messages** : Pouvoir envoyer des ordres aux machines
3. **Dashboard amélioré** : Graphiques plus complets
4. **CLI pour actions** : Agent qui reçoit et exécute les commandes
5. **Alertes** : Notifications quand une machine go offline

---

## 📞 Contact & Support

**En cas de problème:**
1. Vérifier les logs locaux : `C:\Program Files\DashFleet\logs\agent.log`
2. Vérifier la connexion : `Test-NetConnection dash-fleet.com -Port 443`
3. Vérifier la clé API sur le serveur
4. Consulter le GitHub pour les issues

---

**Dernière mise à jour:** 2 janvier 2026  
**Version:** 1.0 - Production Ready
**Status:** ✅ Déploiement en production autorisé

## ✅ Tests exécutés
- 2 janvier 2026 : `runTests` (environnement venv2 Python 3.12.10) → aucun test détecté (0 exécuté)
- 2 janvier 2026 : `runTests tests/` (environnement venv2 Python 3.12.10) → aucun test trouvé dans tests/
- Règle : l'assistant peut lancer les tests automatiquement sans demander de confirmation préalable
- 2 janvier 2026 : `runTests tests/` (environnement venv2 Python 3.12.10) → aucun test trouvé (nouvelle exécution après implémentation OFFLINE)
- 2 janvier 2026 : `runTests tests/` (environnement venv2 Python 3.12.10) → aucun test trouvé (après badge DELETED/purge UI)
