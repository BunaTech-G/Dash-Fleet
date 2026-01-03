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
  const [actionMsg, setActionMsg] = useState<string>('Ready');
  const historyRef = useRef<ChartPoint[]>([]);
  const { data, isFetching, error } = useStats();

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
      plugins: { legend: { labels: { color: '#9db1c5' } } },
      scales: {
        x: { ticks: { color: '#9db1c5' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: {
          ticks: { color: '#9db1c5' },
          grid: { color: 'rgba(255,255,255,0.05)' },
          suggestedMin: 0,
          suggestedMax: 100,
        },
      },
    }),
    []
  );

  const healthClass = data ? `status-${data.health?.status || 'ok'}` : '';

  const triggerAction = async (action: string) => {
    try {
      setActionMsg('Running...');
      const resp = await runAction(action);
      setActionMsg(resp.message || 'OK');
      setTimeout(() => setActionMsg('Ready'), 2000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error';
      setActionMsg(msg);
      setTimeout(() => setActionMsg('Ready'), 3000);
    }
  };

  const placeholder = '—';

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Live</div>
          <h1 style={{ margin: '6px 0' }}>System Dashboard</h1>
          <p className="muted">CPU, RAM, Disk and Uptime updated every 2.5s.</p>
        </div>
        <div className={`badge ${data?.alert_active ? 'critical' : 'ok'}`}>
          {data?.alert_active ? 'High Load' : 'Healthy'}
        </div>
      </div>

      <div className="grid stats">
        <div className={`card ${healthClass}`}>
          <div className="card-title">Health Score</div>
          <div className="card-value">{data?.health?.score ?? placeholder}/100</div>
          <p className="card-meta">
            {data?.health?.status?.toUpperCase() ?? placeholder}
          </p>
        </div>

        <div className="card">
          <div className="card-title">CPU</div>
          <div className="card-value">{data?.cpu_percent?.toFixed?.(1) ?? placeholder}%</div>
          <p className="card-meta">CPU {data?.health?.components?.cpu ?? placeholder}</p>
        </div>

        <div className="card">
          <div className="card-title">Memory</div>
          <div className="card-value">{data?.ram_percent?.toFixed?.(1) ?? placeholder}%</div>
          <p className="card-meta">
            {data?.ram_used_gib?.toFixed?.(2) ?? placeholder}/{data?.ram_total_gib?.toFixed?.(2) ?? placeholder} GiB
          </p>
        </div>

        <div className="card">
          <div className="card-title">Disk</div>
          <div className="card-value">{data?.disk_percent?.toFixed?.(1) ?? placeholder}%</div>
          <p className="card-meta">
            {data?.disk_used_gib?.toFixed?.(2) ?? placeholder}/{data?.disk_total_gib?.toFixed?.(2) ?? placeholder} GiB
          </p>
        </div>

        <div className="card">
          <div className="card-title">Uptime</div>
          <div className="card-value">{data?.uptime_hms ?? placeholder}</div>
          <p className="card-meta">{data?.hostname ?? 'Unknown'}</p>
        </div>

        <div className="card">
          <div className="card-title">Status</div>
          <div style={{ fontSize: '0.9em', color: '#9db1c5', lineHeight: 1.6 }}>
            {isFetching ? '⏳ Fetching...' : '✓ Updated'}
            <br />
            <span style={{ fontSize: '0.85em' }}>{actionMsg}</span>
          </div>
        </div>
      </div>

      {error && <div className="card status-critical">Error: {error.message}</div>}

      <div className="card">
        <div className="card-title">CPU & RAM Over Time</div>
        <div style={{ height: '250px' }}>
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>

      <div className="card">
        <div className="card-title">System Actions</div>
        <p className="muted" style={{ marginBottom: '10px' }}>
          Run maintenance tasks on this system.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px' }}>
          <button className="button" onClick={() => triggerAction('flush_dns')}>
            Flush DNS
          </button>
          <button className="button" onClick={() => triggerAction('restart_spooler')}>
            Restart Spooler
          </button>
          <button className="button" onClick={() => triggerAction('cleanup_temp')}>
            Cleanup Temp
          </button>
          <button className="button" onClick={() => triggerAction('cleanup_teams')}>
            Cleanup Teams
          </button>
          <button className="button" onClick={() => triggerAction('cleanup_outlook')}>
            Cleanup Outlook
          </button>
          <button className="button" onClick={() => triggerAction('collect_logs')}>
            Collect Logs
          </button>
        </div>
      </div>
    </div>
  );
}