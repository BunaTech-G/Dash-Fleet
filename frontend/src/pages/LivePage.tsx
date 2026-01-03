import { useEffect, useMemo, useRef, useState } from 'react';
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
import { useStats } from '../hooks/useStats';
import { runAction } from '../services/api';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip);

const MAX_POINTS = 60;

interface ChartPoint {
  label: string;
  cpu: number;
  ram: number;
}

export function LivePage() {
  const [actionMsg, setActionMsg] = useState<string>('Prêt');
  const historyRef = useRef<ChartPoint[]>([]);
  const { data, isFetching, error } = useStats();

  // Détecter le thème actuel
  const isDark = !document.body.classList.contains('light');
  const textColor = isDark ? '#9db1c5' : '#4a5568';
  const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.08)';

  useEffect(() => {
    if (!data) return;
    const label = data.timestamp.split('T')[1]?.slice(0, 8) || data.timestamp;
    historyRef.current = [
      ...historyRef.current,
      { label, cpu: data.cpu_percent, ram: data.ram_percent },
    ].slice(-MAX_POINTS);
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

  const chartOptions = useMemo(
    () => ({
      responsive: true,
      plugins: { legend: { labels: { color: textColor } } },
      scales: {
        x: { ticks: { color: textColor }, grid: { color: gridColor } },
        y: {
          ticks: { color: textColor },
          grid: { color: gridColor },
          suggestedMin: 0,
          suggestedMax: 100,
        },
      },
    }),
    [textColor, gridColor]
  );

  const healthClass = data ? `status-${data.health?.status || 'ok'}` : '';

  const triggerAction = async (action: string) => {
    try {
      setActionMsg('En cours...');
      const resp = await runAction(action);
      setActionMsg(resp.message || 'OK');
      setTimeout(() => setActionMsg('Prêt'), 2000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erreur';
      setActionMsg(msg);
      setTimeout(() => setActionMsg('Prêt'), 3000);
    }
  };

  const placeholder = '—';

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Temps réel</div>
          <h1 style={{ margin: '6px 0' }}>Tableau de bord système</h1>
          <p className="muted">CPU, RAM, Disque et Disponibilité mis à jour toutes les 2.5s.</p>
        </div>
        <div className={`badge ${data?.alert_active ? 'critical' : 'ok'}`}>
          {data?.alert_active ? 'Charge élevée' : 'En bonne santé'}
        </div>
      </div>

      <div className="grid stats">
        <div className={`card ${healthClass}`}>
          <div className="card-title">Score de santé</div>
          <div className="card-value">{data?.health?.score ?? placeholder}/100</div>
          <p className="card-meta">
            {data?.health?.status?.toUpperCase() ?? placeholder}
          </p>
        </div>

        <div className="card">
          <div className="card-title">CPU</div>
          <div className="card-value">{data?.cpu_percent?.toFixed?.(1) ?? placeholder}%</div>
          <p className="card-meta">Score CPU {data?.health?.components?.cpu ?? placeholder}</p>
        </div>

        <div className="card">
          <div className="card-title">Mémoire</div>
          <div className="card-value">{data?.ram_percent?.toFixed?.(1) ?? placeholder}%</div>
          <p className="card-meta">
            {data?.ram_used_gib?.toFixed?.(2) ?? placeholder}/{data?.ram_total_gib?.toFixed?.(2) ?? placeholder} Gio
          </p>
        </div>

        <div className="card">
          <div className="card-title">Disque</div>
          <div className="card-value">{data?.disk_percent?.toFixed?.(1) ?? placeholder}%</div>
          <p className="card-meta">
            {data?.disk_used_gib?.toFixed?.(2) ?? placeholder}/{data?.disk_total_gib?.toFixed?.(2) ?? placeholder} Gio
          </p>
        </div>

        <div className="card">
          <div className="card-title">Disponibilité</div>
          <div className="card-value">{data?.uptime_hms ?? placeholder}</div>
          <p className="card-meta">{data?.hostname ?? 'Inconnu'}</p>
        </div>

        <div className="card">
          <div className="card-title">Statut</div>
          <div style={{ fontSize: '0.9em', color: 'var(--muted)', lineHeight: 1.6 }}>
            {isFetching ? '⏳ Chargement...' : '✓ Mis à jour'}
            <br />
            <span style={{ fontSize: '0.85em' }}>{actionMsg}</span>
          </div>
        </div>
      </div>

      {error && <div className="card status-critical">Erreur : {error.message}</div>}

      <div className="card">
        <div className="card-title">CPU et RAM dans le temps</div>
        <div style={{ height: '250px' }}>
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>

      <div className="card">
        <div className="card-title">Actions système</div>
        <p className="muted" style={{ marginBottom: '10px' }}>
          Exécuter des tâches de maintenance sur ce système.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px' }}>
          <button className="button" onClick={() => triggerAction('flush_dns')}>
            Vider DNS
          </button>
          <button className="button" onClick={() => triggerAction('restart_spooler')}>
            Redémarrer Spooler
          </button>
          <button className="button" onClick={() => triggerAction('cleanup_temp')}>
            Nettoyer Temp
          </button>
          <button className="button" onClick={() => triggerAction('cleanup_teams')}>
            Nettoyer Teams
          </button>
          <button className="button" onClick={() => triggerAction('cleanup_outlook')}>
            Nettoyer Outlook
          </button>
          <button className="button" onClick={() => triggerAction('collect_logs')}>
            Collecter Logs
          </button>
        </div>
      </div>
    </div>
  );
}
