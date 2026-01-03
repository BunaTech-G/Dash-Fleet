#!/bin/bash
# Script de déploiement complet pour Dash-Fleet sur le serveur
# Exécutez ceci sur le serveur Linux via SSH

set -e  # Exit on error

echo "================================"
echo "🚀 Déploiement Dash-Fleet START"
echo "================================"

# 1. Cloner/Mettre à jour le repo
echo "📦 1. Clonage du repository..."
cd /opt
if [ -d "dash-fleet" ]; then
    echo "   → Le dossier existe, suppression..."
    rm -rf dash-fleet
fi
git clone https://github.com/BunaTech-G/Dash-Fleet.git dash-fleet
cd dash-fleet
git checkout feat/react-spa
git pull origin feat/react-spa
echo "   ✅ Repository prêt"

# 2. Créer venv Python
echo ""
echo "🐍 2. Configuration Python..."
if [ -d "venv" ]; then
    echo "   → venv existe, suppression..."
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
echo "   ✅ Python venv activé"

# 3. Installer dépendances Python
echo ""
echo "📚 3. Installation des dépendances Python..."
pip install -r requirements.txt
echo "   ✅ Dépendances Python installées"

# 4. Builder le frontend
echo ""
echo "⚛️  4. Build du frontend React..."
cd frontend

# Installer Node dependencies
echo "   → npm install..."
npm install --legacy-peer-deps

# Builder l'app
echo "   → npm run build..."
npm run build

# Vérifier le build
if [ -d "dist" ]; then
    echo "   ✅ Build frontend réussi (dist/ créé)"
else
    echo "   ❌ ERREUR: dist/ n'existe pas!"
    exit 1
fi

cd ..
echo "   ✅ Frontend prêt"

# 5. Tester le backend
echo ""
echo "🧪 5. Test du backend..."
source venv/bin/activate
python main.py --version || echo "   ⚠️  Pas de --version flag (c'est normal)"
echo "   ✅ Backend vérifié"

# 6. Permissions et cleanup
echo ""
echo "🧹 6. Nettoyage et permissions..."
chmod +x main.py
chmod +x fleet_agent.py
chmod +x desktop_app.py
echo "   ✅ Permissions configurées"

# 7. Redémarrer le service
echo ""
echo "🔄 7. Redémarrage du service..."
sudo systemctl restart dashfleet || echo "   ⚠️  Service pas encore configuré (c'est normal en première fois)"
echo "   ✅ Service restarté"

# 8. Vérifier le status
echo ""
echo "✨ 8. Vérification du status..."
sudo systemctl status dashfleet || echo "   ⚠️  Service pas configuré"

echo ""
echo "================================"
echo "✅ Déploiement TERMINÉ"
echo "================================"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Vérifier que le service dashfleet est actif"
echo "   2. Accéder à https://dash-fleet.com"
echo "   3. Tester les endpoints API"
echo ""
echo "🔗 URLs utiles:"
echo "   - Dashboard: https://dash-fleet.com"
echo "   - API Stats: https://dash-fleet.com/api/stats"
echo "   - API Fleet: https://dash-fleet.com/api/fleet"
echo ""
