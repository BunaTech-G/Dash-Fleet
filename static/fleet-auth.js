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
    const msg = existing.querySelector('.message');
    if (msg) msg.textContent = message;
    existing.classList.remove('hide');
    clearTimeout(existing._hideTimer);
    existing._hideTimer = setTimeout(() => existing.classList.add('hide'), 6000);
    return;
  }
  const banner = document.createElement('div');
  banner.id = 'auth-error-banner';
  banner.className = 'auth-error-banner';
  banner.innerHTML = `<div class="message">${message}</div><button class="close" aria-label="Close">×</button>`;
  const btn = banner.querySelector('.close');
  btn.addEventListener('click', () => banner.remove());
  document.body.appendChild(banner);
  // trigger entrance animation
  requestAnimationFrame(() => banner.classList.add('show'));
  banner._hideTimer = setTimeout(() => banner.classList.add('hide'), 6000);
}
