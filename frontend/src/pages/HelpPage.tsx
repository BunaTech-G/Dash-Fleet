export function HelpPage() {
  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Aide</div>
          <h1 style={{ margin: '6px 0' }}>Déploiement de l'agent et intégration</h1>
          <p className="muted">Référence rapide pour déployer des agents et utiliser l'API.</p>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        <div className="card">
          <h3>1. Déployer l'agent</h3>
          <ol>
            <li>Téléchargez ou compilez l'agent (dist/fleet_agent.exe)</li>
            <li>Exécutez : <code>fleet_agent.exe --server http://localhost:5000</code></li>
            <li>L'ID de la machine par défaut est le nom d'hôte (visible dans l'onglet Flotte)</li>
            <li>L'agent rapporte à /api/fleet/report toutes les 30 secondes</li>
          </ol>
        </div>

        <div className="card">
          <h3>2. Endpoints principaux</h3>
          <ul>
            <li><strong>GET /api/stats</strong> - Statistiques système actuelles</li>
            <li><strong>GET /api/status</strong> - Stats + score de santé</li>
            <li><strong>GET /api/fleet</strong> - Toutes les machines de la flotte</li>
            <li><strong>GET /api/history?limit=300</strong> - Données historiques CSV</li>
            <li><strong>POST /api/fleet/report</strong> - L'agent rapporte les métriques</li>
            <li><strong>POST /api/action</strong> - Exécuter des actions système</li>
          </ul>
        </div>

        <div className="card">
          <h3>3. Sans authentification</h3>
          <p>Cette version simplifiée n'a pas de connexion, de clés API ou d'organisations.</p>
          <p>Tous les endpoints sont publics. À utiliser uniquement dans des réseaux de confiance.</p>
        </div>

        <div className="card">
          <h3>4. Actions système</h3>
          <p>Tâches de maintenance Windows uniquement :</p>
          <ul>
            <li>flush_dns - Vider le cache DNS</li>
            <li>restart_spooler - Redémarrer le spooler d'impression</li>
            <li>cleanup_temp - Nettoyer les fichiers temporaires</li>
            <li>cleanup_teams - Nettoyer le cache Teams</li>
            <li>cleanup_outlook - Nettoyer le cache Outlook</li>
            <li>collect_logs - Collecter les journaux de diagnostic</li>
          </ul>
        </div>

        <div className="card">
          <h3>5. Variables d'environnement</h3>
          <ul>
            <li><strong>HOST</strong> - Hôte Flask (défaut : 0.0.0.0)</li>
            <li><strong>PORT</strong> - Port Flask (défaut : 5000)</li>
            <li><strong>FLEET_TTL_SECONDS</strong> - Expiration des entrées de flotte (défaut : 600)</li>
            <li><strong>WEBHOOK_URL</strong> - Envoyer des alertes par webhook en cas de santé critique</li>
          </ul>
        </div>

        <div className="card">
          <h3>6. Exécution du tableau de bord</h3>
          <ul>
            <li><strong>Mode web :</strong> <code>python main.py --web</code> (ouvre le navigateur automatiquement)</li>
            <li><strong>Mode CLI :</strong> <code>python main.py</code> (sortie terminal)</li>
            <li><strong>Export :</strong> <code>--export-csv ~/metrics.csv</code></li>
          </ul>
        </div>
      </div>

      <div className="card">
        <h3>Pages du tableau de bord</h3>
        <p><strong>Temps réel :</strong> Métriques en temps réel, score de santé, actions système</p>
        <p><strong>Flotte :</strong> Toutes les machines connectées, statut, scores de santé</p>
        <p><strong>Historique :</strong> Graphiques historiques à partir des journaux CSV</p>
        <p><strong>Aide :</strong> Cette page</p>
      </div>

      <div className="card">
        <h3>Format de rapport de l'agent</h3>
        <pre style={{ fontSize: '0.85em', overflow: 'auto', maxHeight: '300px' }}>
{`POST /api/fleet/report
{
  "machine_id": "DESKTOP-ABC123",
  "hostname": "DESKTOP-ABC123",
  "report": {
    "timestamp": "2025-01-03T14:30:45.123456",
    "hostname": "DESKTOP-ABC123",
    "cpu_percent": 45.2,
    "ram_percent": 62.5,
    "ram_used_gib": 8.5,
    "ram_total_gib": 16.0,
    "disk_percent": 72.1,
    "disk_used_gib": 360.0,
    "disk_total_gib": 500.0,
    "uptime_seconds": 864000,
    "uptime_hms": "240:00:00",
    "alerts": { "cpu": false, "ram": false },
    "alert_active": false,
    "health": {
      "score": 78,
      "status": "ok",
      "components": { "cpu": 90, "ram": 75, "disk": 65 }
    }
  }
}`}
        </pre>
      </div>
    </div>
  );
}
