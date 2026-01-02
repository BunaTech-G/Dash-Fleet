# 🔨 Phase 2 Refactoring - En Cours

**Date:** 2 janvier 2026  
**Branche:** `fix/pyproject-exclude`  
**Priorité:** 🟡 MOYENNE

---

## ✅ Complété

### 1. **Centralisé PyInstaller .spec Files** ✅
- **Commit:** `9872441`
- **Nouveau:** `deploy/specs/` folder avec 4 specs centralisées
- **Specs créés:**
  - `server.spec` - Flask server
  - `agent.spec` - Fleet agent (avec paths relatifs portables)
  - `desktop-gui.spec` - Desktop GUI (windowless)
  - `desktop-cli.spec` - Desktop CLI (console)
- **Mis à jour:** `build_agent_exe.ps1` pour utiliser spec centralisé
- **Documentation:** `deploy/specs/README.md`

**Bénéfices:**
- ✅ Une source de vérité pour les specs
- ✅ Paths relatifs portables (fonctionne sur toutes machines)
- ✅ Noms binaires cohérents (`dashfleet-*`)
- ✅ Facile à maintenir et découvrir

---

## ⏳ En Attente

### 2. **Restructurer scripts/ vs deploy/**
**Impact:** Organisation, trouvabilité  
**Effort:** 🟢 Faible

```bash
# Avant: Scripts éparpillés
scripts/install_agent_linux.sh          # ❌ Ancien
scripts/install_agent_windows_service.ps1  # ❌ Ancien
deploy/install_dashfleet_linux.sh       # ✅ Nouveau
deploy/install_dashfleet_oneliner.ps1   # ✅ Nouveau

# Après: Source unique de vérité
deploy/                                 # Seule source
  - install_dashfleet_linux_oneliner.sh
  - install_dashfleet_oneliner.ps1
  - ... (etc)
```

**Action:** Supprimer `scripts/install*.sh` et `scripts/install*.ps1`

### 3. **Centraliser Validation Marshmallow**
**Impact:** Maintenabilité, testabilité  
**Effort:** 🟡 Moyen

**Créer:** `schemas.py` avec tous les Marshmallow schemas

```python
# Avant: Dispersé dans main.py
class ReportSchema(Schema): ...
class MetricsSchema(Schema): ...

# Après: Centralisé
from schemas import ReportSchema, MetricsSchema
```

### 4. **Ajouter Tests Unitaires (pytest)**
**Impact:** Confiance code, regression  
**Effort:** 🟡 Moyen

```bash
tests/
  - unit/
    - test_fleet_utils.py       # fleet_utils functions
    - test_health_score.py      # health calculation
    - test_fleet_agent.py       # agent collection
  - integration/
    - test_api_endpoints.py     # API validation
```

### 5. **Documentation API (Swagger/OpenAPI)**
**Impact:** Découverte, intégration  
**Effort:** 🟡 Moyen

```yaml
# Générer depuis Flask docstrings
swagger:
  definitions:
    FleetReport:
      properties:
        machine_id: { type: string }
        report: { type: object }
```

---

## 📊 Phase 2 Status

| Tâche | Status | Commit | Effort |
|-------|--------|--------|--------|
| Centraliser .spec files | ✅ DONE | `9872441` | 🟢 30min |
| Restructurer scripts/ | ⏳ TODO | - | 🟢 20min |
| Centraliser Marshmallow | ⏳ TODO | - | 🟡 45min |
| Ajouter pytest tests | ⏳ TODO | - | 🟡 60min |
| Swagger docs | ⏳ TODO | - | 🟡 45min |

**Temps restant Phase 2:** ~3h (2-3 jours)

---

## 🎯 Prochaine Action

→ **Structurer scripts/ vs deploy/** (tâche rapide, haute valeur)

Supprimer:
```bash
rm scripts/install_agent_linux.sh
rm scripts/install_agent_windows_service.ps1
rm scripts/install_windows_agent_multi.ps1
rm scripts/install_windows_agent.ps1
```

Garder structuré dans deploy/ seulement.

---

## 📚 Historique Phase 2

1. **Centralisé .spec files** (commit `9872441`)
   - 4 specs créés dans `deploy/specs/`
   - Paths relatifs portables
   - Updated build script

---

**Phase 2 Progress: 20% (1/5 tâches)**
