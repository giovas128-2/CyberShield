import { useOutletContext } from "react-router-dom";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import { useVisibleSeverities } from "../hooks/useVisibleSeverities";
import { SeverityBadge } from "../components/SeverityBadge";
import { timeAgo } from "../utils/format";

export default function NotificationsPage() {
  const ctx = useOutletContext<CyberShieldCtx>();
  const visible = useVisibleSeverities();
  const filtered = ctx.notifications.filter((n) => visible.has(n.severity));
  const hiddenCount = ctx.notifications.length - filtered.length;

  return (
    <>
      <div className="h"><div><h1>Notificaciones</h1><div className="mu">Avisos del backend asociados a incidentes; no se eliminan al filtrar.</div></div></div>
      {hiddenCount > 0 && <div className="cfg-filter-note" role="status">Filtro personal: {hiddenCount} notificaciones ocultas. Telegram y el backend no se modifican.</div>}
      <div className="card">
        <div className="notification-list">
          {filtered.map((n) => {
            const incident = ctx.incidents.find((i) => i.backendId === Number(n.incident_id));
            const count = incident?.correlatedEventsCount ?? 1;
            return (
              <div className="notification-row" key={n.id}>
                <SeverityBadge value={n.severity} />
                <div className="notification-message">
                  <b>{n.message}</b>
                  <small className="mu">Incidente {n.incident_id} · {count} {count === 1 ? "evento asociado" : "eventos correlacionados"} · {timeAgo(n.created_at)}</small>
                </div>
                <span className={`sv ${n.status === "pending" ? "wn" : n.status === "failed" ? "er" : "ok"}`}>{n.status}</span>
              </div>
            );
          })}
          {!filtered.length && <div className="mu">No hay notificaciones para las severidades seleccionadas.</div>}
        </div>
      </div>
    </>
  );
}
