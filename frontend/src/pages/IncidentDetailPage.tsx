import { Link, useOutletContext, useParams } from "react-router-dom";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import { SeverityBadge } from "../components/SeverityBadge";
import { MitreTechniqueCard } from "../components/mitre/MitreTechniqueCard";

export default function IncidentDetailPage() {
  const { id } = useParams();
  const ctx = useOutletContext<CyberShieldCtx>();
  const inc = ctx.incidents.find((i) => i.id === id || String(i.backendId) === id);
  if (!inc) return <><Link to="/incidents" className="lnk">← Volver a incidentes</Link><div className="card mu">Incidente no encontrado.</div></>;
  return (
    <>
      <Link to="/incidents" className="lnk">← Volver a incidentes</Link>
      <div className="card" style={{ marginTop: 12 }}>
        <div className="row" style={{ padding: 0 }}><span className="eyebrow">{inc.id} / Detalle</span><SeverityBadge value={inc.severidad} /></div>
        <h1 style={{ marginBottom: 6 }}>{inc.titulo}</h1><p className="mu">{inc.resumen}</p>
        <Link
  to={`/incidents/${inc.backendId}/evidence`}
  className="btn"
  style={{
    display: "inline-block",
    marginTop: 10,
    marginBottom: 14,
  }}
>
  Ver evidencia de respuesta
</Link>
        <div className="kv3"><div><small>Estado</small><b>{inc.estado}</b></div><div><small>Origen</small><b className="mono">{inc.origen}</b></div><div><small>Servidor</small><b>{inc.servidor}</b></div><div><small>Detectado</small><b>{inc.detectado}</b></div></div>
        <div className="detail-section"><div className="section-label">Clasificación técnica</div><MitreTechniqueCard techniques={inc.mitre ?? []} /></div>
        <div className="reco response-panel">
  <b>Respuesta de CyberShield</b>

  {inc.responseAction ? (
    <div
      className="kv3"
      style={{ marginTop: 10 }}
    >
      <div>
        <small>Acción</small>
        <b className="mono">
          {inc.responseAction.action_type}
        </b>
      </div>

      <div>
        <small>Objetivo</small>
        <b className="mono">
          {inc.responseAction.target ?? "—"}
        </b>
      </div>

      <div>
        <small>Estado</small>
        <b>
          {inc.responseAction.status}
        </b>
      </div>

      <div>
        <small>Reversible</small>
        <b>
          {inc.responseAction.reversible
            ? "Sí"
            : "No"}
        </b>
      </div>
    </div>
  ) : (
    <span className="mu">
      Sin acción de respuesta registrada.
    </span>
  )}
</div>
        <div className="reco recommendation-panel"><b>Recomendación</b><span>{inc.reco}</span></div>
        <div className="investigation-guide detail-section"><div className="guide-content" style={{ display: "block" }}><b>Qué revisar</b><ol>{inc.investigationSteps.map((s, idx) => <li key={idx}>{s}</li>)}</ol><b>Criterio de resolución</b><p className="mu">{inc.resolutionCriteria}</p></div></div>
      </div>
    </>
  );
}
