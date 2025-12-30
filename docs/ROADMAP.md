# Roadmap courte : agent santé poste + auto-remédiation + self-service

Objectif : un agent léger pour postes (Windows d’abord) qui mesure la santé, applique des remédiations sûres, propose des scripts self-service, et envoie des alertes sobres. Architecture simple, déploiement rapide, sans empiler des stacks lourdes.

## 1) Agent local minimal (POC)
- Collecte : CPU/RAM/Disque, uptime, état services clés (spooler, réseau, VPN client), état AV/EDR, statut Windows Update.
- Score santé 0-100 (vert/orange/rouge) avec seuils simples (ex. CPU<80%, RAM<90%, disque<90%, update récent, AV OK, services up).
- Endpoint local JSON (http://127.0.0.1:port/status) qui expose métriques + score.
- Logs locaux, pas d’auto-remédiation encore.

## 2) UI locale + self-service
- Réutiliser l’UI Flask existante pour afficher le score santé et un badge coloré.
- Ajouter un panneau “Actions approuvées” (scripts whitelists) :
  - Flush DNS, restart spooler, clear caches (Temp, Teams/Outlook), relancer service VPN.
- Bouton “Collecter un zip de logs” (diag réseau, services, events basiques).

## 3) Auto-remédiations légères
- Déclenchement conditionnel :
  - Disque >90% → cleanup léger (temp) limité.
  - Spooler down → restart.
  - Cache Teams/Outlook trop gros → purge soft.
- Sécurité : whitelists, pas d’exécution arbitraire, journaliser chaque action.

## 4) Alertes sobres
- Webhook Teams/Slack/Email quand score passe en rouge ou reste orange > N heures.
- Debounce/antispam, fenêtre de maintenance pour éviter le bruit planifié.

## 5) Mode centralisé (optionnel)
- Petit backend (Flask/FastAPI) qui reçoit les rapports de plusieurs agents.
- Tableau multi-postes, filtres par score, export CSV/JSON.
- Auth token/API, pas d’exposition publique sans proxy/ACL.

## 6) Durcissement et packaging
- Service Windows (nssm ou service Python), scripts signés/whitelistés, config fichier ou ENV.
- Installers : binaire unique (PyInstaller/Go), ou MSI minimal.
- Paramètres : intervalle collecte, seuils, actions auto, endpoints d’alerte.

## 7) Nice-to-have
- Thème clair/sombre pour l’UI.
- Internationalisation déjà prête (FR/EN/ES/RU) à étendre.
- Export Prometheus (option) si besoin d’intégration existante.

## Prochaines actions proposées
1) Ajouter au code un score santé et un endpoint local `/status`.
2) Étendre l’UI actuelle pour afficher ce score et un panneau d’actions approuvées (self-service).
3) Coder 2-3 auto-remédiations sûres (cleanup temp, restart spooler, flush DNS) avec journalisation.
4) Ajouter un webhook Teams/Slack simple pour les alertes rouge.

## Valeurs à remplacer (rapide)
- `(ex: http://mon-serveur:5000)` / `<HOST>` : URL où DashFleet sera accessible. Exemples : `http://localhost:5000` (local), `http://192.168.0.97:5000` (LAN) ou `https://dashfleet.example.com` (production).
- `FLEET_TOKEN` / `ACTION_TOKEN` : tokens secrets, à définir en variables d'environnement ou via un fichier `.env` sécurisé. Ne pas les committer.
- `<API_KEY>` : clé API fournie par `POST /api/orgs` pour une organisation.
