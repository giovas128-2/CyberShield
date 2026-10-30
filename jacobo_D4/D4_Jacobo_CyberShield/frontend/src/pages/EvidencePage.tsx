import { Link, useParams, useSearchParams } from "react-router-dom";
import { AlertTriangle, ChevronLeft, FileText, RotateCcw } from "lucide-react";
import { DetectionPanel } from "../components/evidence/DetectionPanel";
import { DefensiveCommandPanel } from "../components/evidence/DefensiveCommandPanel";
import { MockStateSwitcher } from "../components/evidence/MockStateSwitcher";
import { getEvidenceResult, normalizeIncidentCode, parseAttack } from "../mocks/evidenceMock";

/* Ruta: /incidents/:id/evidence. SIN backend: los datos salen de getEvidenceResult() (src/mocks/evidenceMock.ts).
   BACKEND_GISS: sustituir getEvidenceResult(id, estado) por la lectura real (ver PASOS_PARA_GISS.md); los componentes solo reciben `ev` por props.
   El estado del mock se guarda en la URL (?estado=detected|responding|contained|failed|escalated&ataque=brute_force|ransomware) para que recargar reconstruya la misma pantalla. */
export default function EvidencePage() {
  const { id = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const estado = params.get("estado");
  const ataque = parseAttack(params.get("ataque"));
  const result = getEvidenceResult(id, estado, ataque); // BACKEND_GISS: result <- servicio real de evidencia (loading | ready | empty | error)
  const code = normalizeIncidentCode(id);
  const pick = (e: string) => setParams({ estado: e, ataque }, { replace: true });
  const pickAttack = (a: string) => setParams({ estado: estado ?? "contained", ataque: a }, { replace: true });
  const current = estado ?? "contained";
  return (
    <>
      <div className="h">
        <div>
          <div className="eyebrow">{code} / Evidencia</div>
          <h1>Evidencia de protección / Respuesta real</h1>
          <div className="mu">Monitoreo del ataque y comandos defensivos ejecutados para proteger la empresa.</div>
        </div>
        <Link className="ab" to={`/incidents/${id}`}><ChevronLeft size={14} />Volver al incidente</Link>
      </div>
      <MockStateSwitcher current={current} attack={ataque} onPick={pick} onAttack={pickAttack} />
      {result.phase === "ready" && <div className="ev-grid"><DetectionPanel ev={result.ev} /><DefensiveCommandPanel ev={result.ev} /></div>}
      {result.phase === "loading" && <div className="ev-skel" role="status" aria-label="Cargando evidencia"><div /><div /></div>}
      {result.phase === "empty" && (
        <div className="card ev-state-box"><FileText size={22} /><b>Sin evidencia disponible para {code}.</b><small className="mu">El backend no devolvió evidencia para este incidente (404 / lista vacía).</small></div>
      )}
      {result.phase === "error" && (
        <div className="card ev-state-box er" role="alert"><AlertTriangle size={22} /><b>No se pudo cargar la evidencia</b><small className="mu">{result.message} <span className="mono">({result.code})</span></small>
          <button className="ab" onClick={() => pick("contained")}><RotateCcw size={14} />Reintentar</button>{/* BACKEND_GISS: onClick <- volver a pedir la evidencia al backend */}</div>
      )}
    </>
  );
}
