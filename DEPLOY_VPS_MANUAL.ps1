# DashFleet Phase 6A & 6B Deployment - Manual VPS Guide
# Date: 2 janvier 2026

Write-Host "🚀 DashFleet Phase 6A & 6B Deployment Guide" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 MANUAL DEPLOYMENT STEPS (SSH into VPS first):" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  SSH into VPS:" -ForegroundColor White
Write-Host "   ssh root@83.150.218.175" -ForegroundColor Gray
Write-Host ""

Write-Host "2️⃣  Navigate to DashFleet:" -ForegroundColor White
Write-Host "   cd /opt/dashfleet" -ForegroundColor Gray
Write-Host ""

Write-Host "3️⃣  Pull latest code:" -ForegroundColor White
Write-Host "   git pull origin fix/pyproject-exclude" -ForegroundColor Gray
Write-Host ""

Write-Host "4️⃣  Restart service:" -ForegroundColor White
Write-Host "   systemctl restart dashfleet" -ForegroundColor Gray
Write-Host ""

Write-Host "5️⃣  Verify service is running:" -ForegroundColor White
Write-Host "   systemctl status dashfleet" -ForegroundColor Gray
Write-Host ""

Write-Host "6️⃣  Check logs:" -ForegroundColor White
Write-Host "   tail -f logs/api.log" -ForegroundColor Gray
Write-Host ""

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Changes deployed:" -ForegroundColor Green
Write-Host "   ✓ Phase 6A: Responsive mobile design" -ForegroundColor Green
Write-Host "   ✓ Copy Machine ID button (📋)" -ForegroundColor Green
Write-Host "   ✓ Details panel (OS, Architecture, Python)" -ForegroundColor Green
Write-Host "   ✓ Export to CSV (📥)" -ForegroundColor Green
Write-Host "   ✓ Better UI: Message button, fixed filters" -ForegroundColor Green
Write-Host "   ✓ French translations" -ForegroundColor Green
Write-Host ""

Write-Host "🧪 After deployment, test:" -ForegroundColor Yellow
Write-Host "   1. Go to https://dash-fleet.com/fleet" -ForegroundColor Gray
Write-Host "   2. Click '💬 Envoyer Message' on a machine" -ForegroundColor Gray
Write-Host "   3. Filter by Status or Sort" -ForegroundColor Gray
Write-Host "   4. Click 📋 to copy Machine ID" -ForegroundColor Gray
Write-Host "   5. Click '▼ Détails système' to expand" -ForegroundColor Gray
Write-Host "   6. Click 📥 'Exporter CSV'" -ForegroundColor Gray
Write-Host "   7. Test mobile (F12 → Device Emulation → 512px)" -ForegroundColor Gray
Write-Host ""

Write-Host "📊 Dashboard URL:" -ForegroundColor Blue
Write-Host "   https://dash-fleet.com/fleet" -ForegroundColor Cyan
Write-Host ""

Write-Host "💾 Git Commits Pushed:" -ForegroundColor Blue
Write-Host "   - b1f4dbd: UI improvements (filters, message button)" -ForegroundColor Gray
Write-Host "   - d686ac3: Phase 6A deployment guide" -ForegroundColor Gray
Write-Host "   - 5bd1bac: Responsive mobile + Fleet enhancements" -ForegroundColor Gray
Write-Host ""

Write-Host "Press Enter when deployment is complete on VPS..." -ForegroundColor Yellow
Read-Host
