import { useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import { useVisibleSeverities } from "../hooks/useVisibleSeverities";
import { formatClock } from "../preferences/cybershieldPreferences";
import type { Scope, Severidad } from "../types";
import { SeverityBadge } from "../components/SeverityBadge";

const scopeClass: Record<Scope, string> = { BLOCKED: "ok", REACHED: "wn", IMPACT: "er" };

export default function EventsPage() {
  const ctx = useOutletContext<CyberShieldCtx>();
  const visible = useVisibleSeverities();
  const [sev, setSev] = useState<"" | Severidad>("");
  const [scope, setScope] = useState<"" | Scope>("");
  const rows = useMemo(() => ctx.events.filter((e) => visible.has(e.severidad) &&
    (!sev || e.severidad === sev) && (!scope || e.scope === scope)).slice(0, 200),
    [ctx.events, sev, scope, visible]);
  const hiddenCount = ctx.events.filter((e) => !visible.has(e.severidad)).length;
  return (
    <>
      <div className="h">
        <div><h1>Eventos</h1><div className="mu">Telemetría normalizada recibida por CyberShield.</div></div>
        <div className="acts">
          <select className="sel" value={sev} onChange={(e) => setSev(e.target.value as "" | Severidad)}>
            <option value="">Toda severidad visible</option><option>NORMAL</option><option>WARNING</option><option>HIGH</option><option>CRITICAL</option>
          </select>
          <select className="sel" value={scope} onChange={(e) => setScope(e.target.value as "" | Scope)}>
            <option value="">Todo scope</option><option>BLOCKED</option><option>REACHED</option><option>IMPACT</option>
          </select>
        </div>
      </div>
      {ctx.demo && <div className="demo">DATOS SIMULADOS · El backend no respondió desde el inicio de la sesión.</div>}
      {hiddenCount > 0 && <div className="cfg-filter-note" role="status">Filtro personal: {hiddenCount} eventos ocultos. La detección continúa activa.</div>}
      <div className="tw"><table><thead><tr><th>Hora</th><th>Tipo</th><th>Origen</th><th>Servidor</th><th>Severidad</th><th>Scope</th><th>Estado</th></tr></thead>
        <tbody>{rows.map((e) => <tr key={String(e.id)}><td className="mono">{e.createdAt ? formatClock(e.createdAt) : e.fecha}</td><td>{e.tipo.replaceAll("_", " ")}</td><td className="mono">{e.origen}</td><td>{e.serverName ?? (e.serverId != null ? `#${e.serverId}` : "—")}</td><td><SeverityBadge value={e.severidad} /></td><td>{e.scope ? <span className={`sv ${scopeClass[e.scope]}`}>{e.scope}</span> : <span className="mu">—</span>}</td><td className="mu">● {e.estado}</td></tr>)}</tbody>
      </table></div>
      {!rows.length && <div className="card mu">No hay eventos para mostrar con estos filtros.</div>}
    </>
  );
}
