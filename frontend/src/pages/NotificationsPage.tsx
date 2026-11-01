import { useOutletContext } from "react-router-dom";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import { SeverityBadge } from "../components/SeverityBadge";
import { timeAgo } from "../utils/format";

export default function NotificationsPage() {
  const ctx = useOutletContext<CyberShieldCtx>();

  return (
    <>
      <div className="h">
        <div>
          <h1>Notificaciones</h1>
          <div className="mu">
            Avisos generados por incidentes HIGH y CRITICAL.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="notification-list">
          {ctx.notifications.map((n) => {
            const incident = ctx.incidents.find(
              (i) =>
                i.backendId ===
                Number(n.incident_id),
            );

            const correlatedCount =
              incident?.correlatedEventsCount ?? 1;

            return (
              <div
                className="notification-row"
                key={n.id}
              >
                <SeverityBadge
                  value={n.severity}
                />

                <div className="notification-message">
                  <b>{n.message}</b>

                  <small className="mu">
                    Incidente {n.incident_id}
                    {" · "}
                    {correlatedCount}{" "}
                    {correlatedCount === 1
                      ? "evento asociado"
                      : "eventos correlacionados"}
                    {" · "}
                    {timeAgo(n.created_at)}
                  </small>
                </div>

                <span
                  className={`sv ${
                    n.status === "pending"
                      ? "wn"
                      : "ok"
                  }`}
                >
                  {n.status}
                </span>
              </div>
            );
          })}

          {!ctx.notifications.length && (
            <div className="mu">
              No hay notificaciones registradas.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
