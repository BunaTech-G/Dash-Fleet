// Small client-side helper to store an API key in sessionStorage and add it to fetch requests.
function setApiKey(key) { sessionStorage.setItem('api_key', key); updateAuthUI(); }
function getApiKey() { return sessionStorage.getItem('api_key'); }
function clearApiKey() { sessionStorage.removeItem('api_key'); updateAuthUI(); }

function authFetch(url, opts = {}) {
  opts = opts || {};
  opts.headers = opts.headers || {};
  const key = getApiKey();
  if (key) opts.headers['Authorization'] = 'Bearer ' + key;
  return fetch(url, opts);
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
