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
import { useHistory } from '../hooks/useHistory';
import { useOutletContext } from 'react-router-dom';
import { getLabel, Lang } from '../i18n';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip);

export function HistoryPage() {
  const { lang } = useOutletContext<{ lang: Lang }>();
  const { data, isLoading, error } = useHistory(300);

  // Détecter le thème actuel
  const isDark = !document.body.classList.contains('light');
  const textColor = isDark ? '#8b98aa' : '#4a5568';
  const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.08)';

  const chartData = {
    labels: data?.map((row) => row.timestamp.split('T')[1]?.slice(0, 5) || '') || [],
    datasets: [
      {
        label: 'CPU %',
        data: data?.map((row) => row.cpu_percent) || [],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.25,
      },
      {
        label: 'RAM %',
        data: data?.map((row) => row.ram_percent) || [],
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        tension: 0.25,
      },
      {
        label: 'Disk %',
        data: data?.map((row) => row.disk_percent) || [],
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.25,
      },
    ],
  };

  const chartOptions = {
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
  };

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Historique</div>
          <h1 style={{ margin: '6px 0' }}>Métriques de performance</h1>
          <p className="muted">Vue historique des métriques système au fil du temps.</p>
        </div>
        <div className="muted">{data?.length || 0} échantillon{(data?.length || 0) > 1 ? 's' : ''}</div>
      </div>

      {error && <div className="card status-critical">Erreur : {error.message}</div>}

      {isLoading ? (
        <div className="card">
          <div className="muted">Chargement de l'historique...</div>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="card-title">CPU, RAM et Disque dans le temps</div>
            <div style={{ height: '350px' }}>
              <Line data={chartData} options={chartOptions} />
            </div>
          </div>

          <div className="card">
            <div className="card-title">Derniers échantillons</div>
            {data && data.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Horodatage</th>
                      <th>Nom d'hôte</th>
                      <th>CPU</th>
                      <th>RAM</th>
                      <th>Disque</th>
                      <th>Disponibilité</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...data].reverse().slice(0, 50).map((row, idx) => (
                      <tr key={idx}>
                        <td style={{ fontSize: '0.85em' }}>{row.timestamp}</td>
                        <td>{row.hostname || 'unknown'}</td>
                        <td>{row.cpu_percent.toFixed(1)}%</td>
                        <td>{row.ram_percent.toFixed(1)}%</td>
                        <td>{row.disk_percent.toFixed(1)}%</td>
                        <td>{row.uptime_hms || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="muted">{getLabel('noHistory', lang)}</div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
