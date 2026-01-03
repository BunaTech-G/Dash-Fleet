import { useMemo, useState } from 'react';
import { useFleet, getEntryStatus, getEntryScore } from '../hooks/useFleet';

const TTL_SECONDS = parseInt(import.meta.env.VITE_FLEET_TTL || '600', 10);

type StatusFilter = 'all' | 'ok' | 'warn' | 'critical' | 'expired';
type SortKey = 'score_desc' | 'score_asc' | 'last_desc' | 'last_asc';

export function FleetPage() {
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [sort, setSort] = useState<SortKey>('score_desc');
  const { data, isLoading, error } = useFleet();

  const filtered = useMemo(() => {
    const list = data || [];
    const now = Date.now() / 1000;
    let next = list;

    if (filter !== 'all') {
      next = list.filter((e) => {
        const status = getEntryStatus(e);
        if (filter === 'expired') return status === 'expired';
        return status === filter && now - e.ts <= TTL_SECONDS;
      });
    }

    next = [...next].sort((a, b) => {
      const sa = getEntryScore(a);
      const sb = getEntryScore(b);
      switch (sort) {
        case 'score_asc':
          return sa - sb;
        case 'last_desc':
          return b.ts - a.ts;
        case 'last_asc':
          return a.ts - b.ts;
        case 'score_desc':
        default:
          return sb - sa;
      }
    });
    return next;
  }, [data, filter, sort]);

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Flotte</div>
          <h1 style={{ margin: '6px 0' }}>Santé de la flotte</h1>
          <p className="muted">Vue centralisée des machines qui rapportent des métriques.</p>
        </div>
        <div className="muted">{data?.length || 0} machine{(data?.length || 0) > 1 ? 's' : ''}</div>
      </div>

      <div className="card">
        <div className="controls" style={{ marginBottom: 10, display: 'flex', gap: '10px' }}>
          <label className="muted">
            Statut
            <select className="input" value={filter} onChange={(e) => setFilter(e.target.value as StatusFilter)}>
              <option value="all">Tout</option>
              <option value="ok">OK</option>
              <option value="warn">Avertissement</option>
              <option value="critical">Critique</option>
              <option value="expired">Expiré</option>
            </select>
          </label>
          <label className="muted">
            Trier
            <select className="input" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
              <option value="score_desc">Score (décroissant)</option>
              <option value="score_asc">Score (croissant)</option>
              <option value="last_desc">Dernier (récent)</option>
              <option value="last_asc">Dernier (ancien)</option>
            </select>
          </label>
        </div>

        {isLoading && <div className="muted">Chargement...</div>}
        {error && <div className="card status-critical">Erreur : {error.message}</div>}
        {!isLoading && !error && filtered.length === 0 && (
          <div className="empty">Aucune machine ne rapporte. Déployez un agent qui envoie des données à /api/fleet/report.</div>
        )}}

        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
          {filtered.map((entry) => {
            const report: any = entry.report || {};
            const health = report.health || { score: 0, status: 'ok' };
            const status = getEntryStatus(entry);
            const lastTime = new Date(entry.ts * 1000).toLocaleString();
            const expired = status === 'expired';

            return (
              <article key={entry.id} className={`card tight status-${status}`}>
                <div className="card-title">{entry.hostname || entry.id}</div>
                <div className="flex" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="card-value">{health.score}/100</div>
                  <span className={`badge ${status}`}>{status.toUpperCase()}</span>
                </div>
                <p className="card-meta">
                  CPU {report.cpu_percent?.toFixed?.(1) ?? '--'}% · RAM {report.ram_percent?.toFixed?.(1) ?? '--'}% · Disque {report.disk_percent?.toFixed?.(1) ?? '--'}%
                </p>
                <p className="card-meta">Disponibilité {report.uptime_hms || '--'}</p>
                <p className="card-meta muted">
                  Dernier : {lastTime} · {entry.client || 'inconnu'} {expired ? '⚠️' : ''}
                </p>
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}
