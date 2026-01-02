#!/bin/bash
# DashFleet Phase 6A & 6B Deployment Script
# Run on VPS: bash DEPLOY_VPS.sh
# Date: 2 janvier 2026

set -e

echo "🚀 DashFleet Deployment Started"
echo "=================================="

cd /opt/dashfleet

# Pull latest code
echo "📥 Pulling code from GitHub..."
git pull origin fix/pyproject-exclude

# Restart service
echo "🔄 Restarting dashfleet service..."
systemctl restart dashfleet

# Wait for service to start
sleep 3

# Check status
echo "✅ Checking service status..."
systemctl status dashfleet

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo ""
echo "📊 Dashboard available at:"
echo "   https://dash-fleet.com/fleet"
echo ""
echo "📝 Changes deployed:"
echo "   - Phase 6A: Responsive mobile design"
echo "   - Copy Machine ID button"
echo "   - Details panel (OS, Architecture, Python)"
echo "   - Export to CSV"
echo "   - Better UI: Message button, fixed filters"
echo "   - French translations"
echo ""
echo "🧪 Test the dashboard:"
echo "   1. Go to https://dash-fleet.com/fleet"
echo "   2. Click '💬 Envoyer Message' on a machine"
echo "   3. Filter by Status or Sort"
echo "   4. Test mobile (F12 → Device Emulation)"
echo ""
