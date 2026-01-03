import { useEffect, useMemo, useRef, useState } from 'react';
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
import { fetchStatus, runAction, StatusPayload } from '../services/api';
import { useLang } from '../hooks/useLang';
import { useAuth, getStoredApiKey } from '../hooks/useAuth';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip);

const MAX_POINTS = 60;

type SeriesPoint = { label: string; cpu: number; ram: number };

export function LivePage() {
  const lang = useLang();
  const { apiKey } = useAuth();
  const [actionMsg, setActionMsg] = useState<string>('Prêt');
  const historyRef = useRef<SeriesPoint[]>([]);

  const { data, isFetching, error } = useQuery<StatusPayload, Error>(
    ['status', apiKey],
    () => fetchStatus(apiKey || getStoredApiKey()),
    { refetchInterval: 2500 }
  );

  useEffect(() => {
    if (!data) return;
    const label = data.timestamp.split('T')[1]?.slice(0, 8) || data.timestamp;
    historyRef.current = [...historyRef.current, { label, cpu: data.cpu_percent, ram: data.ram_percent }].slice(-MAX_POINTS);
  }, [data]);

  const labels = historyRef.current.map((p) => p.label);
  const chartData = {
    labels,
    datasets: [
      {
        label: 'CPU %',
        data: historyRef.current.map((p) => p.cpu),
        borderColor: '#4cd4ff',
        backgroundColor: 'rgba(76, 212, 255, 0.14)',
        tension: 0.25,
      },
      {
        label: 'RAM %',
        data: historyRef.current.map((p) => p.ram),
        borderColor: '#ff7a9e',
        backgroundColor: 'rgba(255, 122, 158, 0.14)',
        tension: 0.25,
      },
    ],
  };

  const chartOptions = useMemo(() => ({
    responsive: true,
    plugins: { legend: { labels: { color: '#9db1c5' } } },
    scales: {
      x: { ticks: { color: '#9db1c5' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#9db1c5' }, grid: { color: 'rgba(255,255,255,0.05)' }, suggestedMin: 0, suggestedMax: 100 },
    },
  }), []);

  const healthClass = data ? `status-${data.health?.status || 'ok'}` : '';

  const triggerAction = async (action: string) => {
    try {
      setActionMsg('Exécution...');
      const resp = await runAction(action, apiKey || getStoredApiKey());
      setActionMsg(resp.message || 'OK');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erreur';
      setActionMsg(msg);
    }
  };

  const placeholder = '—';

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Live</div>
          <h1 style={{ margin: '6px 0' }}>Tableau de bord</h1>
          <p className="muted">CPU, mémoire, disque et uptime rafraîchis toutes les 2.5s.</p>
        </div>
        <div className={`badge ${data?.alert_active ? 'critical' : 'ok'}`}>
          {data?.alert_active ? 'Alerte charge' : 'Tout va bien'}
        </div>
      </div>

      <div className="grid stats">
        <div className={`card ${healthClass}`}>
          <div className="card-title">Santé</div>
          <div className="card-value">{data ? `${data.health?.score ?? 0}/100` : placeholder}</div>
          <p className="card-meta">{data?.health?.status || 'en attente'}</p>
        </div>
        <div className={`card ${data?.alerts?.cpu ? 'status-critical' : ''}`}>
          <div className="card-title">CPU</div>
          <div className="card-value">{data ? `${data.cpu_percent.toFixed(1)}%` : placeholder}</div>
          <p className="card-meta">Seuil 80%</p>
        </div>
        <div className={`card ${data?.alerts?.ram ? 'status-warn' : ''}`}>
          <div className="card-title">RAM</div>
          <div className="card-value">{data ? `${data.ram_percent.toFixed(1)}%` : placeholder}</div>
          <p className="card-meta">{data ? `${data.ram_used_gib.toFixed(1)} / ${data.ram_total_gib.toFixed(1)} GiB` : '—'}</p>
        </div>
        <div className="card">
          <div className="card-title">Disque</div>
          <div className="card-value">{data ? `${data.disk_percent.toFixed(1)}%` : placeholder}</div>
          <p className="card-meta">{data ? `${data.disk_used_gib.toFixed(1)} / ${data.disk_total_gib.toFixed(1)} GiB` : '—'}</p>
        </div>
        <div className="card">
          <div className="card-title">Uptime</div>
          <div className="card-value">{data?.uptime_hms || placeholder}</div>
          <p className="card-meta">Depuis le boot</p>
        </div>
      </div>

      <div className="section-header" style={{ marginTop: 20 }}>
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Tendance</div>
          <h2 style={{ margin: 0 }}>CPU / RAM</h2>
        </div>
        <div className="muted">{isFetching ? 'Mise à jour...' : data?.timestamp || ''}</div>
      </div>
      <div className="card">
        <Line height={260} data={chartData} options={chartOptions} />
      </div>

      <div className="section-header">
        <h2 style={{ margin: 0 }}>Actions approuvées</h2>
        <div className="muted">Exécutées localement côté hôte</div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        {['flush_dns', 'restart_spooler', 'cleanup_temp', 'cleanup_teams', 'cleanup_outlook', 'collect_logs'].map((a) => (
          <button key={a} className="button ghost" onClick={() => triggerAction(a)}>{a}</button>
        ))}
      </div>
      <div className="muted" style={{ marginTop: 8 }}>{actionMsg}</div>

      <div className="section-header">
        <h2 style={{ margin: 0 }}>Dernière mesure</h2>
        <div className="muted">{data?.timestamp || '—'}</div>
      </div>
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Métrique</th><th>Valeur</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>CPU</td><td>{data ? `${data.cpu_percent.toFixed(1)}%` : placeholder}</td></tr>
            <tr><td>RAM</td><td>{data ? `${data.ram_percent.toFixed(1)}% (${data.ram_used_gib.toFixed(1)}/${data.ram_total_gib.toFixed(1)} GiB)` : placeholder}</td></tr>
            <tr><td>Disque</td><td>{data ? `${data.disk_percent.toFixed(1)}% (${data.disk_used_gib.toFixed(1)}/${data.disk_total_gib.toFixed(1)} GiB)` : placeholder}</td></tr>
            <tr><td>Uptime</td><td>{data?.uptime_hms || placeholder}</td></tr>
          </tbody>
        </table>
      </div>

      {error && <div className="card status-critical">Erreur: {error.message}</div>}
    </div>
  );
}
