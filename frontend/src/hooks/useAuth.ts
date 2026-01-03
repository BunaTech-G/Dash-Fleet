import { useCallback, useState } from 'react';

const STORAGE_KEY = 'api_key';

export function getStoredApiKey(): string | null {
  return sessionStorage.getItem(STORAGE_KEY);
}

export function useAuth() {
  const [apiKey, setApiKeyState] = useState<string | null>(() => getStoredApiKey());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setApiKey = useCallback((next: string | null) => {
    if (next) {
      sessionStorage.setItem(STORAGE_KEY, next);
      setApiKeyState(next);
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
      setApiKeyState(null);
    }
  }, []);

  const serverLogin = useCallback(async (key: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: key }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Connexion refusée');
      }
      // session cookie is set by server, clear local key to prefer cookie
      setApiKey(null);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur inconnue';
      setError(message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [setApiKey]);

  const logout = useCallback(async () => {
    setApiKey(null);
    try {
      await fetch('/api/logout', { method: 'POST' });
    } catch (err) {
      // ignore
    }
  }, [setApiKey]);

  return { apiKey, setApiKey, serverLogin, logout, loading, error };
}
