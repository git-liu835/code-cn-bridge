import React, { useState, useEffect, createContext, useContext } from 'react';
import { HashRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Models from './pages/Models';
import Settings from './pages/Settings';
import Logs from './pages/Logs';
import About from './pages/About';
import StatusBar from './components/StatusBar';
import { api } from './services/api';
import { t, Lang } from './i18n';

// ── Theme & Language Context ───────────────────────────────────

export type ThemeName = 'dark' | 'light' | 'blue' | 'green' | 'purple' | 'warm';

interface AppContextType {
  theme: ThemeName;
  setTheme: (t: ThemeName) => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  tl: (key: Parameters<typeof t>[0]) => string;
}
export const AppContext = createContext<AppContextType>(null!);
export const useApp = () => useContext(AppContext);

function loadSetting<T>(key: string, fallback: T): T {
  try {
    const v = localStorage.getItem(`code-bridge:${key}`);
    return v ? JSON.parse(v) : fallback;
  } catch { return fallback; }
}

function saveSetting(key: string, val: unknown) {
  localStorage.setItem(`code-bridge:${key}`, JSON.stringify(val));
}

// ── App Component ──────────────────────────────────────────────

const App: React.FC = () => {
  const [proxyRunning, setProxyRunning] = useState(false);
  const [requestCount, setRequestCount] = useState(0);
  const [theme, _setTheme] = useState<ThemeName>(() => loadSetting('theme', 'dark'));
  const [lang, _setLang] = useState<Lang>(() => loadSetting('lang', 'zh'));

  const setTheme = (t: ThemeName) => { _setTheme(t); saveSetting('theme', t); };
  const setLang = (l: Lang) => { _setLang(l); saveSetting('lang', l); };

  // 应用主题到 document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await api.getStatus();
        setProxyRunning(status.running);
        setRequestCount(status.stats?.request_count ?? 0);
      } catch {
        setProxyRunning(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const ctx: AppContextType = { theme, setTheme, lang, setLang, tl: (k) => t(k, lang) };

  return (
    <HashRouter>
      <AppContext.Provider value={ctx}>
        <AppInner proxyRunning={proxyRunning} requestCount={requestCount} />
      </AppContext.Provider>
    </HashRouter>
  );
};

const AppInner: React.FC<{ proxyRunning: boolean; requestCount: number }> = ({ proxyRunning, requestCount }) => {
  const { tl } = useApp();
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-brand">
          <span className="header-logo">&#9653;</span>
          <span className="header-title">{tl('app.title')}</span>
        </div>
        <div className="header-status">
          <span className={`status-dot ${proxyRunning ? 'running' : 'stopped'}`} />
          <span className="status-text">{proxyRunning ? tl('app.running') : tl('app.stopped')}</span>
        </div>
      </header>

      <div className="app-body">
        <nav className="sidebar">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">&#9632;</span> {tl('nav.dashboard')}
          </NavLink>
          <NavLink to="/models" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">&#9881;</span> {tl('nav.models')}
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">&#9776;</span> {tl('nav.settings')}
          </NavLink>
          <NavLink to="/logs" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">&#9776;</span> {tl('nav.logs')}
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">&#9432;</span> {tl('nav.about')}
          </NavLink>
        </nav>

        <main className="content">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/models" element={<Models />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>

      <StatusBar proxyRunning={proxyRunning} port={8765} requestCount={requestCount} />
    </div>
  );
};

export default App;
