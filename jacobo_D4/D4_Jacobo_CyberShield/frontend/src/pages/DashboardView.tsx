/* BACKEND_GISS: servidores/servidoresOnline/servidoresOffline/eventos/incidentes/criticos/estado <- getDashboard() + listas · lista <- getEvents() · serie <- se calcula de eventos por minuto · stats1s/stats60s <- getEventStats() · notifications <- getNotifications(). Todo llega por useCyberShieldData(). */
import { Activity, Bell, Crosshair, Server, ShieldAlert, WifiOff } from "lucide-react";
import type { Evento, EventStats, NotificationItem, Scope } from "../types";
import { SeverityBadge } from "../components/SeverityBadge";
import { Chart } from "../components/Chart";
import { SimBanner } from "../components/SimBanner";
import { timeAgo } from "../utils/format";

const scopeClass: Record<Scope, string> = {
  BLOCKED: "ok",
  REACHED: "wn",
  IMPACT: "er",
};

export function DashboardView({ d, simulate }: { d: any; simulate: () => void }) {
  const stats1s = d.stats1s as EventStats | null;
  const stats60s = d.stats60s as EventStats | null;
  const notifications = (d.notifications ?? []) as NotificationItem[];

  const blocked = stats60s?.by_scope.BLOCKED ?? 0;
  const reached = stats60s?.by_scope.REACHED ?? 0;
  const impact = stats60s?.by_scope.IMPACT ?? 0;
  const totalScope = blocked + reached + impact;
  const pct = (n: number) => (totalScope ? Math.round((n / totalScope) * 100) : 0);

  return (
    <>
      <div className="h">
        <div>
          <h1>Dashboard</h1>
          <div className="mu">Monitoreo de eventos, incidentes, alcance y notificaciones de CyberShield.</div>
        </div>
        <button className="btn sm" onClick={simulate}><Crosshair size={16} />Simular escenario HIGH</button>
      </div>

      <SimBanner demo={Boolean(d.demo)} stale={Boolean(d.stale)} />

      <div className="interpretation-note"><ShieldAlert size={16} /><span><b>Lectura operativa:</b> una alerta o técnica MITRE representa evidencia para investigar; no equivale automáticamente a un ataque confirmado.</span></div>

      <div className="g4">
        <div className="card kpi">
          <div className="t">Eventos / segundo <Activity size={16} /></div>
          <b>{stats1s?.total_events ?? 0}</b>
          <small className="mu">Ventana móvil de 1 s</small>
        </div>
        <div className="card kpi">
          <div className="t">Eventos / minuto <Activity size={16} /></div>
          <b>{stats60s?.total_events ?? 0}</b>
          <small className="mu">Ventana móvil de 60 s</small>
        </div>
        <div className="card kpi">
          <div className="t">Incidentes abiertos <ShieldAlert size={16} color="#f58b97" /></div>
          <b>{d.incidentes}</b>
          <small className="mu">Críticos: {d.criticos}</small>
        </div>
        <div className="card kpi">
          <div className="t">Servidores online <Server size={16} /></div>
          <b>{d.servidoresOnline}</b>
          <small className="mu">Offline: {d.servidoresOffline}</small>
        </div>
      </div>

      <div className="g2">
        <div className="card">
          <div className="h"><b>Resultado de eventos</b><span className="mu">Últimos 60 s</span></div>
          <div className="scope-grid">
            {(["BLOCKED", "REACHED", "IMPACT"] as Scope[]).map((scope) => {
              const value = stats60s?.by_scope[scope] ?? 0;
              return (
                <div className="scope-item" key={scope}>
                  <span className={`sv ${scopeClass[scope]}`}>{scope}</span>
                  <b>{value}</b>
                  <small className="mu">{pct(value)}%</small>
                </div>
              );
            })}
          </div>
          <div className="mu" style={{ marginTop: 12, fontSize: 12 }}>
            BLOCKED = detenido · REACHED = llegó sin impacto confirmado · IMPACT = efecto comprobado.
          </div>
        </div>

        <div className="card">
          <div className="h">
            <b>Eventos por minuto</b>
            <span className="mu">Histórico calculado con <code>created_at</code></span>
          </div>
          <Chart data={d.serie} />
        </div>
      </div>

      <div className="g2">
        <div className="card">
          <div className="h"><b>Principales orígenes</b><span className="mu">60 s</span></div>
          <div className="mini-list">
            {(stats60s?.by_source ?? []).slice(0, 6).map((item) => (
              <div className="mini-row" key={item.source_ip ?? "sin-origen"}>
                <span className="mono">{item.source_ip ?? "Sin origen"}</span><b>{item.count}</b>
              </div>
            ))}
            {!stats60s?.by_source.length && <div className="mu">Sin eventos en esta ventana.</div>}
          </div>
        </div>
        <div className="card">
          <div className="h"><b>Tipos de evento</b><span className="mu">60 s</span></div>
          <div className="mini-list">
            {(stats60s?.by_type ?? []).slice(0, 6).map((item) => (
              <div className="mini-row" key={item.event_type}>
                <span>{item.event_type.replaceAll("_", " ")}</span><b>{item.count}</b>
              </div>
            ))}
            {!stats60s?.by_type.length && <div className="mu">Sin eventos en esta ventana.</div>}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="h">
          <div><b>Notificaciones</b><div className="mu">Generadas por incidentes HIGH y CRITICAL.</div></div>
          <Bell size={18} color="var(--ac)" />
        </div>
        <div className="notification-list">
          {notifications.slice(0, 5).map((n) => (
            <div className="notification-row" key={n.id}>
              <SeverityBadge value={n.severity} />
              <div className="notification-message"><b>{n.message}</b><small className="mu">Incidente {n.incident_id} · {timeAgo(n.created_at)}</small></div>
              <span className={`sv ${n.status === "pending" ? "wn" : "ok"}`}>{n.status}</span>
            </div>
          ))}
          {!notifications.length && <div className="mu"><WifiOff size={14} style={{ verticalAlign: -2 }} /> No hay notificaciones registradas.</div>}
        </div>
      </div>

      <h3 style={{ margin: 0 }}>Eventos recientes</h3>
      <div className="tw">
        <table>
          <thead><tr><th>Hora</th><th>Tipo</th><th>Origen</th><th>Servidor</th><th>Severidad</th><th>Scope</th><th>Estado</th></tr></thead>
          <tbody>
            {d.lista.slice(0, 10).map((e: Evento) => (
              <tr key={e.id}>
                <td className="mono">{e.fecha}</td>
                <td>{e.tipo.replaceAll("_", " ")}</td>
                <td className="mono">{e.origen}</td>
                <td>{e.serverName ?? (e.serverId != null ? `#${e.serverId}` : "—")}</td>
                <td><SeverityBadge value={e.severidad} /></td>
                <td>{e.scope ? <span className={`sv ${scopeClass[e.scope]}`}>{e.scope}</span> : <span className="mu">—</span>}</td>
                <td className="mu">● {e.estado}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
