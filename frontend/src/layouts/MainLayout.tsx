import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useTheme } from '../hooks/useTheme';
import { getInitialLang, getLabel, Lang } from '../i18n';
import { useAuth } from '../hooks/useAuth';

export function MainLayout() {
  const [theme, setTheme] = useTheme();
  const [lang, setLang] = useState<Lang>(() => getInitialLang());
  const navigate = useNavigate();
  const { apiKey, setApiKey, logout } = useAuth();

  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark');

  const handleApiKey = () => {
    const k = window.prompt('Clé API (Bearer)');
    if (!k) return;
    setApiKey(k.trim());
  };

  return (
    <div className="app-shell">
      <div className="topbar">
        <div className="brand">
          <div className="brand-mark">DF</div>
          <div>
            <div className="muted" style={{ fontSize: 12, letterSpacing: '0.08em' }}>DashFleet</div>
            <strong>Dashboard</strong>
          </div>
        </div>
        <div className="controls">
          <select className="input" value={lang} onChange={(e) => { const v = e.target.value as Lang; setLang(v); localStorage.setItem('dash_lang', v); }}>
            <option value="fr">FR</option>
            <option value="en">EN</option>
          </select>
          <button className="button ghost small" onClick={toggleTheme}>{theme === 'dark' ? 'Mode clair' : 'Mode sombre'}</button>
          <button className="button ghost small" onClick={() => navigate('/login')}>Login</button>
          <button className="button ghost small" onClick={handleApiKey}>{apiKey ? 'Clé chargée' : 'Clé API'}</button>
          <button className="button ghost small" onClick={() => { logout(); navigate('/'); }}>Logout</button>
        </div>
      </div>

      <nav className="main-nav" aria-label="Navigation principale">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>{getLabel('live', lang)}</NavLink>
        <NavLink to="/fleet" className={({ isActive }) => (isActive ? 'active' : '')}>{getLabel('fleet', lang)}</NavLink>
        <NavLink to="/history" className={({ isActive }) => (isActive ? 'active' : '')}>{getLabel('history', lang)}</NavLink>
        <NavLink to="/help" className={({ isActive }) => (isActive ? 'active' : '')}>{getLabel('help', lang)}</NavLink>
        <NavLink to="/admin/tokens" className={({ isActive }) => (isActive ? 'active' : '')}>{getLabel('adminTokens', lang)}</NavLink>
      </nav>

      <Outlet context={{ lang }} />
    </div>
  );
}
