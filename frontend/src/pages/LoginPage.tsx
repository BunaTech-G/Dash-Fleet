import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const { serverLogin, setApiKey, loading, error } = useAuth();
  const [key, setKey] = useState('');
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim()) return;
    const ok = await serverLogin(key.trim());
    if (ok) navigate('/');
  };

  const storeLocal = () => {
    if (!key.trim()) return;
    setApiKey(key.trim());
    navigate('/');
  };

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Connexion</div>
          <h1 style={{ margin: '6px 0' }}>Authentification</h1>
          <p className="muted">Échanger une clé API contre une session serveur ou la stocker localement.</p>
        </div>
      </div>
      <div className="card" style={{ maxWidth: 520 }}>
        <form onSubmit={submit} className="stack" style={{ gap: 12 }}>
          <label className="muted" htmlFor="api-key">Clé API</label>
          <input id="api-key" className="input" value={key} onChange={(e) => setKey(e.target.value)} placeholder="xxxx" />
          <div className="controls">
            <button type="submit" className="button" disabled={loading}>Session serveur</button>
            <button type="button" className="button ghost" onClick={storeLocal}>Stocker côté client</button>
          </div>
          {error && <div className="card status-critical">{error}</div>}
        </form>
      </div>
    </div>
  );
}
