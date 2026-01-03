export function HelpPage() {
  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Aide</div>
          <h1 style={{ margin: '6px 0' }}>Déploiement et intégration</h1>
          <p className="muted">Rappels rapides pour brancher les agents et vérifier les API.</p>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        <div className="card">
          <h3>1. Déployer l'agent</h3>
          <ol>
            <li>Télécharger ou builder l'agent (dist/fleet_agent.exe).</li>
            <li>Lancer avec <code>--server http://host:5000 --token FLEET_TOKEN</code>.</li>
            <li>Machine_id par défaut = hostname (visible dans la Fleet).</li>
          </ol>
        </div>
        <div className="card">
          <h3>2. API clés</h3>
          <ul>
            <li><strong>/api/status</strong> : live host</li>
            <li><strong>/api/history?limit=300</strong> : courbes CSV</li>
            <li><strong>/api/fleet</strong> : inventaire multi-agents</li>
            <li><strong>/api/action</strong> : actions locales (protégé ACTION_TOKEN)</li>
          </ul>
        </div>
        <div className="card">
          <h3>3. Auth</h3>
          <p>Clé API échangée contre cookie session via /api/login. Possibilité de stocker localement si besoin (Bearer).</p>
          <p>Les routes Fleet et History exigent la même clé ou session.</p>
        </div>
        <div className="card">
          <h3>4. Tokens de téléchargement</h3>
          <p>Créer des liens one-shot pour l'agent via l'onglet Tokens (ACTION_TOKEN requis).</p>
        </div>
      </div>
    </div>
  );
}
