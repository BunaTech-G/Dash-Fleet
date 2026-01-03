import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip,
} from 'chart.js';
import { fetchHistory, fetchStatus, HistoryRow, StatusPayload } from '../services/api';
import { getStoredApiKey } from '../hooks/useAuth';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip);

export function HistoryPage() {
  const apiKey = getStoredApiKey();
  const { data: history, isLoading, error } = useQuery<HistoryRow[], Error>(['history', apiKey], () => fetchHistory(300, apiKey));
  const { data: status } = useQuery<StatusPayload, Error>(['status-health', apiKey], () => fetchStatus(apiKey), { staleTime: 5000 });

  const chartData = useMemo(() => {
    const labels = (history || []).map((r) => r.timestamp.split('T')[1]?.slice(0, 8) || r.timestamp);
    return {
      labels,
      datasets: [
        { label: 'CPU %', data: (history || []).map((r) => r.cpu_percent), borderColor: '#4cd4ff', backgroundColor: 'rgba(76,212,255,0.12)', tension: 0.25 },
        { label: 'RAM %', data: (history || []).map((r) => r.ram_percent), borderColor: '#ff7a9e', backgroundColor: 'rgba(255,122,158,0.12)', tension: 0.25 },
        { label: 'Disque %', data: (history || []).map((r) => r.disk_percent), borderColor: '#3fd1a4', backgroundColor: 'rgba(63,209,164,0.12)', tension: 0.25 },
      ],
    };
  }, [history]);

  const chartOptions = useMemo(() => ({
    responsive: true,
    plugins: { legend: { labels: { color: '#9db1c5' } } },
    scales: {
      x: { ticks: { color: '#9db1c5' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#9db1c5' }, grid: { color: 'rgba(255,255,255,0.05)' }, suggestedMin: 0, suggestedMax: 100 },
    },
  }), []);

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Historique</div>
          <h1 style={{ margin: '6px 0' }}>Courbes CPU / RAM / Disque</h1>
          <p className="muted">Affiche les points enregistrés dans logs/metrics.csv (jusqu'à 300 derniers).</p>
        </div>
        <div className="muted">{history?.length || 0} points</div>
      </div>

      <div className="card">
        <Line height={260} data={chartData} options={chartOptions} />
      </div>

      <div className="section-header">
        <h2 style={{ margin: 0 }}>Santé actuelle</h2>
        <div className={`badge ${status?.health?.status || 'ok'}`}>
          {status ? `${status.health.score}/100` : '—'}
        </div>
      </div>
      <div className={`card ${status ? `status-${status.health.status}` : ''}`}>
        <p className="card-meta">{status?.timestamp || '—'}</p>
      </div>

      <div className="section-header">
        <h2 style={{ margin: 0 }}>Dernières entrées</h2>
        <div className="muted">Heure locale</div>
      </div>
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Timestamp</th><th>CPU</th><th>RAM</th><th>Disque</th><th>Uptime</th>
            </tr>
          </thead>
          <tbody>
            {(history || []).slice(-30).reverse().map((row) => (
              <tr key={row.timestamp}>
                <td>{row.timestamp}</td>
                <td>{row.cpu_percent.toFixed(1)}%</td>
                <td>{row.ram_percent.toFixed(1)}%</td>
                <td>{row.disk_percent.toFixed(1)}%</td>
                <td>{row.uptime_hms || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!history?.length && !isLoading && <div className="muted" style={{ marginTop: 8 }}>Aucun historique. Lance un export CSV.</div>}
      </div>

      {isLoading && <div className="muted">Chargement...</div>}
      {error && <div className="card status-critical">{error.message}</div>}
    </div>
  );
}
