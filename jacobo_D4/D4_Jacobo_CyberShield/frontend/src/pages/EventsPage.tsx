/* BACKEND_GISS: ctx.events <- getEvents() (Evento.id/createdAt/tipo/origen/severidad/estado/scope/serverId/serverName) · ctx.servers <- getServers() para nombrar el servidor. */
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import type { Scope, Severidad } from "../types";
import { SeverityBadge } from "../components/SeverityBadge";

const scopeClass: Record<Scope, string> = { BLOCKED: "ok", REACHED: "wn", IMPACT: "er" };

export default function EventsPage() {
  const ctx = useOutletContext<CyberShieldCtx>();
  const [sev, setSev] = useState<"" | Severidad>("");
  const [scope, setScope] = useState<"" | Scope>("");
  const rows = useMemo(() => ctx.events.filter((e) => (!sev || e.severidad === sev) && (!scope || e.scope === scope)).slice(0, 200), [ctx.events, sev, scope]);
  return (
    <>
      <div className="h">
        <div><h1>Eventos</h1><div className="mu">Telemetría normalizada recibida por CyberShield.</div></div>
        <div className="acts">
          <select className="sel" value={sev} onChange={(e) => setSev(e.target.value as "" | Severidad)}>
            <option value="">Toda severidad</option><option>NORMAL</option><option>WARNING</option><option>HIGH</option><option>CRITICAL</option>
          </select>
          <select className="sel" value={scope} onChange={(e) => setScope(e.target.value as "" | Scope)}>
            <option value="">Todo scope</option><option>BLOCKED</option><option>REACHED</option><option>IMPACT</option>
          </select>
        </div>
      </div>
      {ctx.demo && <div className="demo">DATOS SIMULADOS · Frontend desacoplado: datos del mock local.</div>}
      <div className="tw"><table><thead><tr><th>Hora</th><th>Tipo</th><th>Origen</th><th>Servidor</th><th>Severidad</th><th>Scope</th><th>Estado</th></tr></thead>
        <tbody>{rows.map((e) => <tr key={String(e.id)}><td className="mono">{e.fecha}</td><td>{e.tipo.replaceAll("_", " ")}</td><td className="mono">{e.origen}</td><td>{e.serverName ?? (e.serverId != null ? `#${e.serverId}` : "—")}</td><td><SeverityBadge value={e.severidad} /></td><td>{e.scope ? <span className={`sv ${scopeClass[e.scope]}`}>{e.scope}</span> : <span className="mu">—</span>}</td><td className="mu">● {e.estado}</td></tr>)}</tbody>
      </table></div>
      {!rows.length && <div className="card mu">No hay eventos para mostrar con estos filtros.</div>}
    </>
  );
}
