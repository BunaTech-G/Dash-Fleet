import { useEffect, useState } from 'react';
import { createToken, deleteToken, fetchTokens } from '../services/api';
import { getStoredApiKey } from '../hooks/useAuth';

export function AdminTokensPage() {
  const [actionToken, setActionToken] = useState('');
  const [path, setPath] = useState('dist/fleet_agent.exe');
  const [ttl, setTtl] = useState(3600);
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const apiKey = getStoredApiKey();

  const load = async () => {
    if (!actionToken) { setError('ACTION_TOKEN requis'); return; }
    try {
      setError(null);
      const res = await fetchTokens(actionToken, apiKey || undefined);
      setItems(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    }
  };

  useEffect(() => { if (actionToken) load(); }, [actionToken]);

  const create = async () => {
    try {
      setError(null);
      await createToken({ path, ttl }, actionToken, apiKey || undefined);
      await load();
      alert('Token créé');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    }
  };

  const remove = async (token: string) => {
    try {
      await deleteToken(token, actionToken, apiKey || undefined);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    }
  };

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Admin</div>
          <h1 style={{ margin: '6px 0' }}>Tokens de téléchargement</h1>
          <p className="muted">Gérer les liens éphémères pour l'agent.</p>
        </div>
        <div className="controls">
          <input className="input" placeholder="ACTION_TOKEN" value={actionToken} onChange={(e) => setActionToken(e.target.value)} />
          <button className="button ghost" onClick={load}>Actualiser</button>
        </div>
      </div>

      {error && <div className="card status-critical">{error}</div>}

      <div className="card" style={{ display: 'grid', gap: 10 }}>
        <div className="controls">
          <input className="input" value={path} onChange={(e) => setPath(e.target.value)} style={{ flex: 1 }} />
          <input className="input" type="number" value={ttl} onChange={(e) => setTtl(parseInt(e.target.value, 10) || 3600)} style={{ width: 120 }} />
          <button className="button" onClick={create}>Créer</button>
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Token</th><th>Path</th><th>Créé</th><th>Expire</th><th>Used</th><th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.token_masked}>
                <td>{it.token_masked}</td>
                <td>{it.path}</td>
                <td>{new Date(it.created_at * 1000).toLocaleString()}</td>
                <td>{it.expires_at ? new Date(it.expires_at * 1000).toLocaleString() : 'never'}</td>
                <td>{it.used ? 'oui' : 'non'}</td>
                <td><button className="button ghost small" onClick={() => remove(it.token)}>Supprimer</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && <div className="muted">Aucun token</div>}
      </div>
    </div>
  );
}
