// Types and interfaces for DashFleet
export type HealthStatus = 'ok' | 'warn' | 'critical';

export interface HealthScore {
  score: number;
  status: HealthStatus;
  components?: {
    cpu: number;
    ram: number;
    disk: number;
  };
}

export interface SystemStats {
  timestamp: string;
  hostname: string;
  cpu_percent: number;
  ram_percent: number;
  ram_used_gib: number;
  ram_total_gib: number;
  disk_percent: number;
  disk_used_gib: number;
  disk_total_gib: number;
  uptime_seconds: number;
  uptime_hms: string;
  alerts: {
    cpu: boolean;
    ram: boolean;
  };
  alert_active: boolean;
  health?: HealthScore;
}

export interface HistoryRow {
  timestamp: string;
  hostname: string;
  cpu_percent: number;
  ram_percent: number;
  disk_percent: number;
  uptime_hms: string;
}

export interface FleetEntry {
  id: string;
  hostname: string;
  ts: number;
  client?: string;
  report: SystemStats | Record<string, any>;
}

export interface FleetResponse {
  count: number;
  data: FleetEntry[];
}

export interface HistoryResponse {
  count: number;
  data: HistoryRow[];
}
