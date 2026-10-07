import { useEffect, useState } from "react";
import { Check, ChevronDown, ChevronUp, Loader2, Search, X } from "lucide-react";
import type { Incidente } from "../types";
import { SeverityBadge } from "../components/SeverityBadge";

const statusClass = (estado: string) => {
  if (estado === "Resuelto") return "ok";
  if (estado === "Investigando") return "wn";
  return "pd";
};

export function IncidentsView({
  list,
  selId,
  setSelId,
  onInvestigate,
  onResolve,
}: {
  list: Incidente[];
  selId: string | null;
  setSelId: (v: string) => void;
  onInvestigate: (incident: Incidente) => Promise<boolean>;
  onResolve: (incident: Incidente) => Promise<boolean>;
}) {
  const [q, setQ] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<Incidente | null>(null);
  const [showGuide, setShowGuide] = useState(false);

  const shown = list.filter((i) =>
    (i.titulo + i.id + i.origen).toLowerCase().includes(q.toLowerCase()),
  );
  const sel = list.find((i) => i.id === selId) || shown[0];
  const abiertos = list.filter((i) => i.estado !== "Resuelto").length;

  useEffect(() => {
    setShowGuide(false);
  }, [sel?.id]);

  const investigate = async (incident: Incidente) => {
    if (busyId) return;
    setBusyId(incident.id);
    const ok = await onInvestigate(incident);
    setBusyId(null);
    if (ok) setShowGuide(true);
  };

  const resolve = async () => {
    if (!confirm || busyId) return;
    setBusyId(confirm.id);
    const ok = await onResolve(confirm);
    setBusyId(null);
    if (ok) {
      setConfirm(null);
      setShowGuide(true);
    }
  };

  return (
    <>
      <div className="h">
        <div>
          <h1>Incidentes</h1>
          <div className="mu">Revisa las alertas, investiga su origen y prioriza la respuesta.</div>
        </div>
        <span className="sv er">{abiertos} incidentes abiertos</span>
      </div>

      <div className="inp" style={{ maxWidth: 420 }}>
        <Search size={16} color="#8a9bb0" />
        <input
          placeholder="Buscar por ID, tipo de evento o IP..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      <div className="inc">
        <div className="il">
          <div className="mu">{shown.length} resultados</div>
          {shown.map((i) => (
            <button
              key={i.id}
              className={`ic ${sel?.id === i.id ? "on" : ""}`}
              onClick={() => setSelId(i.id)}
            >
              <div className="row" style={{ padding: 0 }}>
                <span className="mono"><SeverityBadge value={i.severidad} /> {i.id}</span>
                <span className="mono mu">{i.detectado?.split("·")[1]}</span>
              </div>
              <b style={{ display: "block", margin: "8px 0 2px" }}>{i.titulo}</b>
              <div className="mu" style={{ fontSize: 13 }}>{i.resumen}</div>
              <div className="row" style={{ padding: "8px 0 0" }}>
                <span className="mono">⌖ {i.origen}</span>
                <span className={`sv ${statusClass(i.estado)}`}>● {i.estado}</span>
              </div>
            </button>
          ))}
          {!shown.length && <div className="card mu">No se encontraron incidentes.</div>}
        </div>

        {sel && (
          <div className="card incident-detail">
            <div className="row" style={{ padding: 0 }}>
              <span className="eyebrow">{sel.id} / Detalle</span>
              <SeverityBadge value={sel.severidad} />
            </div>

            <h2 style={{ margin: "10px 0" }}>{sel.titulo}</h2>
            <span className={`sv ${statusClass(sel.estado)}`}>● {sel.estado}</span>
            <p className="mu">{sel.resumen}</p>

            <div className="kv">
              {[
                ["IP de origen", sel.origen],
                ["Servidor afectado", sel.servidor],
                ["Servicio / puerto", sel.servicio],
                ["Detectado", sel.detectado],
                ["Asignado a", sel.asignado],
                ["Regla", sel.regla],
              ].map(([k, v]) => (
                <div key={k}>
                  <small>{k}</small>
                  <span className="mono">{v}</span>
                </div>
              ))}
            </div>

            <div className="reco">
              <b>Recomendación</b>
              {sel.reco}
            </div>

            {(sel.estado === "Investigando" || sel.estado === "Resuelto" || showGuide) && (
              <div className="investigation-guide">
                <button className="guide-toggle" onClick={() => setShowGuide((v) => !v)}>
                  <span>Guía de investigación</span>
                  {showGuide ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {showGuide && (
                  <div className="guide-content">
                    <b>Qué revisar</b>
                    <ol>
                      {sel.investigationSteps.map((step, index) => (
                        <li key={`${sel.id}-step-${index}`}>{step}</li>
                      ))}
                    </ol>
                    <b>Criterio de resolución</b>
                    <p className="mu">{sel.resolutionCriteria}</p>
                  </div>
                )}
              </div>
            )}

            <div className="incident-actions">
              {sel.estado === "Pendiente" && (
                <button
                  className="btn sm"
                  style={{ flex: 1 }}
                  disabled={busyId === sel.id}
                  onClick={() => investigate(sel)}
                >
                  {busyId === sel.id ? (
                    <><Loader2 size={14} className="spin" /> Investigando…</>
                  ) : (
                    "Investigar"
                  )}
                </button>
              )}

              {sel.estado === "Investigando" && (
                <button
                  className="btn sm gh"
                  style={{ flex: 1 }}
                  disabled={busyId === sel.id}
                  onClick={() => setConfirm(sel)}
                >
                  <Check size={14} /> Marcar resuelto
                </button>
              )}

              {sel.estado === "Resuelto" && (
                <div className="resolved-note">✓ Incidente cerrado</div>
              )}
            </div>
          </div>
        )}
      </div>

      {confirm && (
        <div className="ov" onClick={() => !busyId && setConfirm(null)}>
          <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <div className="row" style={{ padding: 0 }}>
              <h3 style={{ border: 0, margin: 0, padding: 0 }}>¿Marcar incidente como resuelto?</h3>
              <button
                className="lnk"
                style={{ marginLeft: "auto", color: "var(--mu)" }}
                disabled={Boolean(busyId)}
                onClick={() => setConfirm(null)}
                aria-label="Cerrar"
              >
                <X size={18} />
              </button>
            </div>
            <p className="mu">
              El incidente {confirm.id} cambiará a Resuelto. La guía seguirá disponible como evidencia de investigación.
            </p>
            <div className="modal-actions">
              <button className="btn sm gh" disabled={Boolean(busyId)} onClick={() => setConfirm(null)}>
                Cancelar
              </button>
              <button className="btn sm resolve" disabled={Boolean(busyId)} onClick={resolve}>
                {busyId ? <><Loader2 size={14} className="spin" /> Procesando…</> : "Marcar resuelto"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
