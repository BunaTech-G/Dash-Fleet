export type Lang = 'fr' | 'en';

const dictionaries: Record<Lang, Record<string, string>> = {
  fr: {
    live: 'Temps réel',
    history: 'Historique',
    fleet: 'Fleet',
    help: 'Aide',
    actions: 'Actions approuvées',
    health: 'Santé',
    lastMeasure: 'Dernière mesure',
    refresh: 'Rafraîchir',
    systemMetrics: 'Métriques système',
    statusOk: 'OK',
    statusWarn: 'Avertissement',
    statusCritical: 'Critique',
    statusExpired: 'Expiré',
    machines: 'Machines',
    filters: 'Filtres',
    sort: 'Trier',
    byScore: 'Score',
    byRecent: 'Récence',
    adminTokens: 'Tokens de téléchargement',
    helpTitle: 'Aide et intégration',
  },
  en: {
    live: 'Live',
    history: 'History',
    fleet: 'Fleet',
    help: 'Help',
    actions: 'Approved actions',
    health: 'Health',
    lastMeasure: 'Latest reading',
    refresh: 'Refresh',
    systemMetrics: 'System metrics',
    statusOk: 'OK',
    statusWarn: 'Warning',
    statusCritical: 'Critical',
    statusExpired: 'Expired',
    machines: 'Machines',
    filters: 'Filters',
    sort: 'Sort',
    byScore: 'Score',
    byRecent: 'Recent',
    adminTokens: 'Download tokens',
    helpTitle: 'Help & onboarding',
  },
};

export function getLabel(key: string, lang: Lang): string {
  return dictionaries[lang][key] || key;
}

export function getInitialLang(): Lang {
  const stored = localStorage.getItem('dash_lang');
  if (stored === 'fr' || stored === 'en') return stored;
  return 'fr';
}
