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

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip);

export function HistoryPage() {
  const { data, isLoading, error } = useHistory(300);

  const chartData = {
    labels: data?.map((row) => row.timestamp.split('T')[1]?.slice(0, 5) || '') || [],
    datasets: [
      {
        label: 'CPU %',
        data: data?.map((row) => row.cpu_percent) || [],
        borderColor: '#4cd4ff',
        backgroundColor: 'rgba(76, 212, 255, 0.14)',
        tension: 0.25,
      },
      {
        label: 'RAM %',
        data: data?.map((row) => row.ram_percent) || [],
        borderColor: '#ff7a9e',
        backgroundColor: 'rgba(255, 122, 158, 0.14)',
        tension: 0.25,
      },
      {
        label: 'Disk %',
        data: data?.map((row) => row.disk_percent) || [],
        borderColor: '#ffd700',
        backgroundColor: 'rgba(255, 215, 0, 0.14)',
        tension: 0.25,
      },
    ],
  };

  const chartOptions = {
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
  };

  return (
    <div className="stack">
      <div className="section-header">
        <div>
          <div className="muted" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>History</div>
          <h1 style={{ margin: '6px 0' }}>Performance Metrics</h1>
          <p className="muted">Historical view of system metrics over time.</p>
        </div>
        <div className="muted">{data?.length || 0} samples</div>
      </div>

      {error && <div className="card status-critical">Error: {error.message}</div>}

      {isLoading ? (
        <div className="card">
          <div className="muted">Loading history...</div>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="card-title">CPU, RAM & Disk Over Time</div>
            <div style={{ height: '350px' }}>
              <Line data={chartData} options={chartOptions} />
            </div>
          </div>

          <div className="card">
            <div className="card-title">Latest Samples</div>
            {data && data.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Hostname</th>
                      <th>CPU</th>
                      <th>RAM</th>
                      <th>Disk</th>
                      <th>Uptime</th>
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
              <div className="muted">No history data available.</div>
            )}
          </div>
        </>
      )}
    </div>
  );
}