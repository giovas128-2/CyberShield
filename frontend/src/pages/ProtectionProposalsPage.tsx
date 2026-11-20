import { useEffect, useState } from "react";
import { BookOpen, ChevronLeft, ChevronRight, ClipboardList, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";
import { api, ApiError } from "../api/client";

type ProposalStatus = "review_required" | "under_review" | "rejected";
type Proposal = {
  id: number;
  technique_id: string;
  technique_name: string;
  title: string;
  candidate_sensor: string;
  required_evidence: string;
  validation_plan: string;
  priority: number;
  status: ProposalStatus;
  generation_mode: string;
  telemetry_verified: boolean;
  detection_verified: boolean;
  execution_allowed: boolean;
  executed: boolean;
  review_notes: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
};
type ProposalPage = {
  page: number;
  size: number;
  total: number;
  items: Proposal[];
  read_only: boolean;
};

const SIZE = 10;
const statusText: Record<ProposalStatus, string> = {
  review_required: "Pendiente de revisión",
  under_review: "En revisión",
  rejected: "Rechazada",
};

function message(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return "Tu cuenta no tiene el rol de ingeniero o administrador.";
    if (error.status === 401) return "Tu sesión expiró. Inicia sesión de nuevo.";
    if (error.status === 404) return "La propuesta no existe o dejó de estar disponible.";
    return error.message || "La API rechazó la consulta.";
  }
  return "No fue posible cargar las propuestas. Comprueba la conexión con FastAPI.";
}

export default function ProtectionProposalsPage() {
  const [status, setStatus] = useState<"all" | ProposalStatus>("all");
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState<ProposalPage | null>(null);
  const [selected, setSelected] = useState<Proposal | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setSelected(null);
    const filter = status === "all" ? "" : `&status=${encodeURIComponent(status)}`;
    api<ProposalPage>(`/intelligence/protection-proposals?page=${page}&size=${SIZE}${filter}`)
      .then((data) => {
        if (!Array.isArray(data?.items) || !data.read_only || typeof data.total !== "number") {
          throw new Error("Respuesta de propuestas inválida");
        }
        if (active) setResult(data);
      })
      .catch((err) => {
        if (active) { setResult(null); setError(message(err)); }
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [status, page, revision]);

  async function showDetail(id: number) {
    setLoadingDetail(true);
    setDetailError("");
    setSelected(null);
    try {
      const data = await api<Proposal>(`/intelligence/protection-proposals/${id}`);
      if (typeof data?.technique_id !== "string") throw new Error("Detalle inválido");
      setSelected(data);
    } catch (err) {
      setDetailError(message(err));
    } finally {
      setLoadingDetail(false);
    }
  }

  return (
    <div>
      <header className="h">
        <div>
          <h1>Propuestas de protección</h1>
          <div className="mu">Borradores derivados de MITRE ATT&amp;CK. Consulta exclusiva para ingeniería; no son defensas activas.</div>
        </div>
        <span className="sv wn">REVISIÓN HUMANA REQUERIDA</span>
      </header>

      <div className="card" style={{padding:18, marginBottom:16}}>
        <div style={{display:"flex",flexWrap:"wrap",alignItems:"center",gap:12,justifyContent:"space-between"}}>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <ClipboardList size={20}/>
            <div><strong>Bandeja de propuestas</strong><div className="mu">{result?.total ?? "—"} registros para el filtro actual</div></div>
          </div>
          <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
            <label className="mu" htmlFor="proposal-filter">Estado</label>
            <select id="proposal-filter" value={status} onChange={(e)=>{
              setStatus(e.target.value as "all" | ProposalStatus);
              setPage(1);
            }} style={{padding:"7px 10px",borderRadius:8}}>
              <option value="all">Todos</option>
              <option value="review_required">Pendientes</option>
              <option value="under_review">En revisión</option>
              <option value="rejected">Rechazadas</option>
            </select>
            <button type="button" className="btn sm gh" onClick={()=>setRevision(r=>r+1)} disabled={loading}>
              <RefreshCw size={15}/> Actualizar
            </button>
          </div>
        </div>

        {loading && <p className="mu" role="status">Consultando propuestas...</p>}
        {error && <p role="alert" style={{color:"var(--danger, #bd342f)"}}><TriangleAlert size={16}/> {error}</p>}
        {!loading && !error && result?.items.length === 0 && <p className="mu">No hay propuestas para este estado.</p>}

        {!loading && !error && result && <div style={{display:"grid",gap:10,marginTop:16}}>
          {result.items.map(item => (
            <article key={item.id} className="card" style={{padding:14}}>
              <div style={{display:"flex",justifyContent:"space-between",gap:8,flexWrap:"wrap"}}>
                <strong>{item.technique_id} · {item.title}</strong>
                <span className="mu">{statusText[item.status] ?? item.status} · Prioridad {item.priority}</span>
              </div>
              <p className="mu" style={{margin:"8px 0"}}>{item.technique_name} · Sensor candidato: {item.candidate_sensor}</p>
              <button type="button" className="btn sm gh" onClick={()=>showDetail(item.id)}>Ver evidencia y validación</button>
            </article>
          ))}
        </div>}
        {!loading && result && result.total > SIZE && <div style={{display:"flex",alignItems:"center",gap:10,justifyContent:"flex-end",marginTop:14}}>
          <button type="button" className="btn sm gh" disabled={page===1} onClick={()=>setPage(p=>Math.max(1,p-1))}><ChevronLeft size={16}/>Anterior</button>
          <span className="mu">Página {page}</span>
          <button type="button" className="btn sm gh" disabled={page*SIZE>=result.total} onClick={()=>setPage(p=>p+1)}>Siguiente<ChevronRight size={16}/></button>
        </div>}
      </div>

      {loadingDetail && <p className="mu" role="status">Cargando detalle...</p>}
      {detailError && <p role="alert" className="mu">{detailError}</p>}
      {selected && <section className="card" style={{padding:20}}>
        <div style={{display:"flex",gap:8,alignItems:"center",marginBottom:12}}>
          <BookOpen size={20}/>
          <h2 style={{margin:0}}>Detalle · {selected.technique_id}</h2>
        </div>
        <p><strong>{selected.title}</strong></p>
        <p><strong>Sensor candidato:</strong> {selected.candidate_sensor}</p>
        <p><strong>Evidencia requerida:</strong> {selected.required_evidence}</p>
        <p><strong>Plan de validación:</strong> {selected.validation_plan}</p>
        <p><strong>Estado:</strong> {statusText[selected.status] ?? selected.status}</p>
        <p><strong>Notas de revisión:</strong> {selected.review_notes || "Todavía no hay notas."}</p>
        <p className="mu">Origen: {selected.generation_mode}. Telemetría verificada: {selected.telemetry_verified ? "Sí" : "No"}. Detección verificada: {selected.detection_verified ? "Sí" : "No"}.</p>
        <p className="mu"><ShieldCheck size={15}/> Ejecución autónoma: {selected.execution_allowed || selected.executed ? "REVISAR INMEDIATAMENTE" : "Deshabilitada"}.</p>
        <p className="mu">Vista de solo lectura. La aprobación y activación requieren un procedimiento independiente.</p>
      </section>}
    </div>
  );
}
