// Small client-side helper to store an API key in sessionStorage and add it to fetch requests.
function setApiKey(key) { sessionStorage.setItem('api_key', key); updateAuthUI(); }
function getApiKey() { return sessionStorage.getItem('api_key'); }
function clearApiKey() { sessionStorage.removeItem('api_key'); updateAuthUI(); }

function authFetch(url, opts = {}) {
  opts = opts || {};
  opts.headers = opts.headers || {};
  const key = getApiKey();
  if (key) opts.headers['Authorization'] = 'Bearer ' + key;
  return fetch(url, opts).then((resp) => {
    if (resp.status === 401 || resp.status === 403) {
      showAuthError(resp.status === 401 ? 'Unauthorized (401) — clé invalide ou manquante' : 'Forbidden (403) — accès refusé');
      return Promise.reject(resp);
    }
    return resp;
  });
}

function updateAuthUI() {
  const logged = !!getApiKey();
  const loginBtn = document.getElementById('loginApiKeyBtn');
  const logoutBtn = document.getElementById('logoutApiKeyBtn');
  const status = document.getElementById('apiKeyStatus');
  if (loginBtn) loginBtn.style.display = logged ? 'none' : 'inline';
  if (logoutBtn) logoutBtn.style.display = logged ? 'inline' : 'none';
  if (status) status.textContent = logged ? 'Clé chargée' : 'Non connecté';
}

document.addEventListener('DOMContentLoaded', () => {
  const loginBtn = document.getElementById('loginApiKeyBtn');
  const logoutBtn = document.getElementById('logoutApiKeyBtn');
  if (loginBtn) loginBtn.addEventListener('click', () => {
    const k = prompt('Entrez la clé API :');
    if (k) setApiKey(k.trim());
  });
  if (logoutBtn) logoutBtn.addEventListener('click', () => clearApiKey());
  updateAuthUI();
});

function showAuthError(message) {
  const existing = document.getElementById('auth-error-banner');
  if (existing) {
    existing.textContent = message;
    return;
  }
  const banner = document.createElement('div');
  banner.id = 'auth-error-banner';
  banner.style.position = 'fixed';
  banner.style.top = '0';
  banner.style.left = '0';
  banner.style.right = '0';
  banner.style.background = '#f87171';
  banner.style.color = 'white';
  banner.style.padding = '8px 12px';
  banner.style.zIndex = '9999';
  banner.style.fontWeight = '600';
  banner.textContent = message;
  const btn = document.createElement('button');
  btn.textContent = '×';
  btn.style.float = 'right';
  btn.style.marginRight = '8px';
  btn.style.background = 'transparent';
  btn.style.color = 'white';
  btn.style.border = 'none';
  btn.style.fontSize = '18px';
  btn.style.cursor = 'pointer';
  btn.addEventListener('click', () => banner.remove());
  banner.appendChild(btn);
  document.body.appendChild(banner);
}
