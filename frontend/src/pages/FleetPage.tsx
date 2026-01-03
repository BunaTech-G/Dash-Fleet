import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchFleet, FleetEntry } from '../services/api';
import { useLang } from '../hooks/useLang';
import { getStoredApiKey } from '../hooks/useAuth';

const TTL_SECONDS = parseInt(import.meta.env.VITE_FLEET_TTL || '600', 10);

type StatusFilter = 'all' | 'ok' | 'warn' | 'critical' | 'expired';
type SortKey = 'score_desc' | 'score_asc' | 'last_desc' | 'last_asc';

function entryStatus(entry: FleetEntry): 'ok' | 'warn' | 'critical' | 'expired' {
  const now = Date.now() / 1000;
  if (now - entry.ts > TTL_SECONDS) return 'expired';
  const status = (entry.report as any)?.health?.status || 'ok';
  return status;
}

function score(entry: FleetEntry): number {
  return (entry.report as any)?.health?.score ?? 0;
}

export function FleetPage() {
  const lang = useLang();
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [sort, setSort] = useState<SortKey>('score_desc');
  const apiKey = getStoredApiKey();

  const { data, isLoading, error } = useQuery<FleetEntry[], Error>(
    ['fleet', apiKey],
    () => fetchFleet(apiKey),
    { refetchInterval: 5000 }
  );

  const filtered = useMemo(() => {
    const list = data || [];
    const now = Date.now() / 1000;
    let next = list;
    if (filter !== 'all') {
      next = list.filter((e) => {
        const status = entryStatus(e);
        if (filter === 'expired') return status === 'expired';
        return status === filter && now - e.ts <= TTL_SECONDS;
      });
    }

    next = [...next].sort((a, b) => {
      const sa = score(a);
      const sb = score(b);
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
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Fleet</div>
          <h1 style={{ margin: '6px 0' }}>Santé des postes</h1>
          <p className="muted">Vue centrale des machines reportées par les agents.</p>
        </div>
        <div className="muted">{data?.length || 0} machines</div>
      </div>

      <div className="card">
        <div className="controls" style={{ marginBottom: 10 }}>
          <label className="muted">Statut
            <select className="input" value={filter} onChange={(e) => setFilter(e.target.value as StatusFilter)}>
              <option value="all">Tous</option>
              <option value="ok">OK</option>
              <option value="warn">Warn</option>
              <option value="critical">Critique</option>
              <option value="expired">Expiré</option>
            </select>
          </label>
          <label className="muted">Trier
            <select className="input" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
              <option value="score_desc">Score (desc)</option>
              <option value="score_asc">Score (asc)</option>
              <option value="last_desc">Dernier (récent)</option>
              <option value="last_asc">Dernier (ancien)</option>
            </select>
          </label>
        </div>

        {isLoading && <div className="muted">Chargement...</div>}
        {error && <div className="card status-critical">{error.message}</div>}
        {!isLoading && !error && filtered.length === 0 && (
          <div className="empty">Aucune machine reportée. Déployer un agent qui POST sur /api/fleet/report avec FLEET_TOKEN.</div>
        )}

        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          {filtered.map((entry) => {
            const report: any = entry.report || {};
            const health = report.health || { score: 0, status: 'ok' };
            const status = entryStatus(entry);
            const last = new Date(entry.ts * 1000).toLocaleString();
            const expired = status === 'expired';
            return (
              <article key={`${entry.org_id || 'org'}-${entry.id}`} className={`card tight status-${status}`}>
                <div className="card-title">{entry.id || 'Machine'}</div>
                <div className="flex" style={{ justifyContent: 'space-between' }}>
                  <div className="card-value">{health.score}/100</div>
                  <span className={`badge ${status}`}>{status.toUpperCase()}</span>
                </div>
                <p className="card-meta">CPU {report.cpu_percent?.toFixed?.(1) ?? '--'}% · RAM {report.ram_percent?.toFixed?.(1) ?? '--'}% · Disk {report.disk_percent?.toFixed?.(1) ?? '--'}%</p>
                <p className="card-meta">Uptime {report.uptime_hms || '--'}</p>
                <p className="card-meta muted">Dernier : {last} · {entry.client || 'client inconnu'} {expired ? '⚠️' : ''}</p>
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}
