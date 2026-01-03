import { Outlet, NavLink } from 'react-router-dom';
import { useState } from 'react';
import { useTheme } from '../hooks/useTheme';
import { getInitialLang, getLabel, Lang } from '../i18n';

export function MainLayout() {
  const [theme, setTheme] = useTheme();
  const [lang, setLang] = useState<Lang>(() => getInitialLang());

  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark');

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
          <select 
            className="input" 
            value={lang} 
            onChange={(e) => { 
              const v = e.target.value as Lang; 
              setLang(v); 
              localStorage.setItem('dash_lang', v); 
            }}
          >
            <option value="fr">FR</option>
            <option value="en">EN</option>
          </select>
          <button className="button ghost small" onClick={toggleTheme}>
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </div>

      <nav className="main-nav" aria-label="Main navigation">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
          {getLabel('live', lang)}
        </NavLink>
        <NavLink to="/fleet" className={({ isActive }) => (isActive ? 'active' : '')}>
          {getLabel('fleet', lang)}
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => (isActive ? 'active' : '')}>
          {getLabel('history', lang)}
        </NavLink>
        <NavLink to="/help" className={({ isActive }) => (isActive ? 'active' : '')}>
          {getLabel('help', lang)}
        </NavLink>
      </nav>

      <main className="main-content">
        <Outlet context={{ lang }} />
      </main>
    </div>
  );
}
