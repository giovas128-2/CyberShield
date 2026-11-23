import { useEffect, useState } from "react";
import {
  AlertTriangle, CheckCircle2, ClipboardCheck, Clock3,
  FolderOpen, Loader2, RefreshCw, ShieldCheck,
} from "lucide-react";
import { ApiError, api, http } from "../api/client";
import "../styles/project-plan-review.css";

type Status = "review_required" | "under_review" | "planned" | "rejected";
type PlanListItem = {
  id: number; project_name: string; created_by: number;
  created_at: string; tasks_total: number;
  pending: number; reviewing: number; planned: number; rejected: number;
};
type PlanList = {
  page: number; size: number; total: number;
  items: PlanListItem[]; execution_allowed: false;
};
type PlanTask = {
  task_id: string; title: string; priority: string;
  action_type: string; origin: string; owner_role: string;
  rationale: string; next_step: string; verification: string;
  related_catalog_controls: string[];
  implementation_approved: false; execution_allowed: false;
  review: {
    id: number; status: Status; reviewed_by: number | null;
    review_notes: string | null; reviewed_at: string | null;
  };
};
type History = {
  id: number; task_id: number; actor_id: number;
  from_status: Status; to_status: Status; notes: string; created_at: string;
};
type PlanDetail = {
  id: number; project_name: string; created_by: number; created_at: string;
  tasks: PlanTask[]; history: History[];
  execution_allowed: false; implementation_approved: false; note: string;
};
const statusNames: Record<Status, string> = {
  review_required: "Pendiente",
  under_review: "En revisión",
  planned: "Aceptada para planificación",
  rejected: "Rechazada",
};
function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 503) return "La bandeja aún no está habilitada. Falta validar y aplicar la migración 014 en la base de pruebas.";
    if (err.status === 403) return "Tu cuenta necesita permisos de ingeniero o administrador.";
    if (err.status === 409) return "El estado de la tarea cambió. Actualiza su información antes de continuar.";
    return err.message;
  }
  return err instanceof Error ? err.message : "No se pudo acceder al backend.";
}

export default function ProjectPlanReviewPage() {
  const [plans, setPlans] = useState<PlanList | null>(null);
  const [selected, setSelected] = useState<PlanDetail | null>(null);
  const [page, setPage] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");
  const [editing, setEditing] = useState<number | null>(null);
  const [nextStatus, setNextStatus] = useState<"under_review"|"planned"|"rejected">("under_review");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api<PlanList>(`/intelligence/project-plans?page=${page}&size=10`)
      .then(result => {
        if (active && result.execution_allowed === false && Array.isArray(result.items)) setPlans(result);
        else if (active) throw new Error("Respuesta de la bandeja inválida.");
      })
      .catch(err => { if (active) {setError(errorMessage(err));setPlans(null);} })
      .finally(() => { if (active) setLoading(false); });
    return () => {active = false;};
  }, [page, refreshKey]);

  async function openPlan(id: number) {
    setDetailLoading(true); setDetailError(""); setFeedback(""); setSelected(null);
    setEditing(null);
    try {
      const detail = await api<PlanDetail>(`/intelligence/project-plans/${id}`);
      if (detail.execution_allowed !== false ||
          detail.implementation_approved !== false ||
          !Array.isArray(detail.tasks)) throw new Error("Detalle de plan inválido.");
      setSelected(detail);
    } catch (err) {setDetailError(errorMessage(err));}
    finally {setDetailLoading(false);}
  }
  function beginReview(task: PlanTask) {
    setEditing(task.review.id);
    setNextStatus(task.review.status === "under_review" ? "planned" : "under_review");
    setNotes(task.review.review_notes || "");
    setFeedback("");
    setDetailError("");
  }
  async function saveReview() {
    if (!selected || editing === null || saving) return;
    if (notes.trim().length < 10 || notes.trim().length > 2000) {
      setDetailError("Escribe observaciones de 10 a 2000 caracteres.");
      return;
    }
    setSaving(true); setDetailError("");
    try {
      const response = await http.patch(
        `/intelligence/project-plans/${selected.id}/tasks/${editing}/review`,
        {status: nextStatus, notes: notes.trim()},
      );
      if (response.data?.execution_allowed !== false ||
          response.data?.implementation_approved !== false) {
        throw new Error("La revisión devolvió un estado inesperado.");
      }
      await openPlan(selected.id);
      setRefreshKey(key => key + 1);
      setFeedback("Revisión guardada y registrada en el historial. No se instaló ninguna defensa.");
    } catch (err) {setDetailError(errorMessage(err));}
    finally {setSaving(false);}
  }

  return <div className="cs-review-page">
    <header className="cs-review-hero">
      <ClipboardCheck size={26}/>
      <div><span>REVISIÓN HUMANA · PROYECTOS</span>
        <h1>Bandeja de planes de seguridad</h1>
        <p>Revisa y documenta decisiones sobre correcciones y controles. Ninguna decisión instala defensas.</p>
      </div>
    </header>

    <section className="cs-review-panel">
      <header className="cs-review-panel-header">
        <div><h2>Planes registrados</h2><p>Separados de las propuestas MITRE y del catálogo ejecutable.</p></div>
        <button type="button" onClick={() => setRefreshKey(k => k + 1)} disabled={loading}>
          <RefreshCw size={16}/> Actualizar
        </button>
      </header>
      {loading && <p><Loader2 size={16} className="spin"/> Consultando planes…</p>}
      {error && <p role="alert" className="cs-review-error"><AlertTriangle size={17}/>{error}</p>}
      {!loading && !error && plans?.items.length === 0 &&
        <p className="cs-review-empty">Todavía no hay planes enviados. Crea uno desde «Análisis de proyectos».</p>}
      {plans?.items.map(plan =>
        <article key={plan.id} className="cs-review-list-item">
          <div><strong>#{plan.id} · {plan.project_name}</strong>
            <small>{plan.tasks_total} tareas · {plan.pending} pendientes · {plan.reviewing} en revisión · {plan.planned} para planificación · {plan.rejected} rechazadas</small>
          </div>
          <button type="button" onClick={() => openPlan(plan.id)}><FolderOpen size={16}/> Abrir</button>
        </article>
      )}
      {plans && plans.total > 10 && <div className="cs-review-paging">
        <button type="button" disabled={page===1} onClick={() => setPage(p=>p-1)}>Anterior</button>
        <span>Página {page}</span>
        <button type="button" disabled={page*10>=plans.total} onClick={() => setPage(p=>p+1)}>Siguiente</button>
      </div>}
    </section>

    {detailLoading && <p className="cs-review-msg"><Loader2 size={16} className="spin"/> Abriendo plan…</p>}
    {detailError && <p role="alert" className="cs-review-error"><AlertTriangle size={17}/>{detailError}</p>}
    {feedback && <p role="status" className="cs-review-success"><CheckCircle2 size={17}/>{feedback}</p>}
    {selected && <section className="cs-review-panel">
      <header className="cs-review-panel-header">
        <div><h2>Plan #{selected.id} · {selected.project_name}</h2>
          <p>{selected.tasks.length} tareas · revisión documental · ejecución deshabilitada</p>
        </div>
        <ShieldCheck size={23}/>
      </header>
      <div className="cs-review-tasks">
        {selected.tasks.map(task => <article key={task.task_id} className="cs-review-task">
          <div className="cs-review-task-top">
            <div><strong>{task.title}</strong><small>{task.action_type.replaceAll("_", " ")} · {task.owner_role === "developer" ? "Desarrollador" : "Ingeniería de seguridad"}</small></div>
            <span className={"cs-review-status is-" + task.review.status}>{statusNames[task.review.status]}</span>
          </div>
          <p>{task.rationale}</p>
          <p><b>Acción:</b> {task.next_step}</p>
          <p><b>Cómo verificar:</b> {task.verification}</p>
          {task.related_catalog_controls.length > 0 &&
            <small>Controles complementarios: {task.related_catalog_controls.join(", ").toUpperCase()}. No significa cobertura real del proyecto.</small>}
          {task.review.review_notes && <p className="cs-review-previous"><b>Última revisión:</b> {task.review.review_notes}</p>}
          {(task.review.status === "review_required" || task.review.status === "under_review") &&
            <button className="cs-review-task-open" onClick={() => beginReview(task)}>
              <ClipboardCheck size={16}/> Revisar esta tarea
            </button>}
          {editing === task.review.id && <div className="cs-review-form">
            <label>Decisión del ingeniero
              <select value={nextStatus} onChange={e => setNextStatus(e.target.value as typeof nextStatus)}>
                {task.review.status === "review_required"
                  ? <><option value="under_review">Marcar en revisión</option><option value="rejected">Rechazar</option></>
                  : <><option value="planned">Aceptar para planificación (no instalar)</option><option value="rejected">Rechazar</option></>}
              </select>
            </label>
            <label>Observaciones técnicas (mínimo 10 caracteres)
              <textarea rows={3} maxLength={2000} value={notes}
                onChange={e=>setNotes(e.target.value)}
                placeholder="Qué evidencia se revisó, qué se debe verificar y por qué se tomó la decisión. No incluyas secretos."/>
            </label>
            <button type="button" disabled={saving} onClick={saveReview}>
              <CheckCircle2 size={15}/> {saving ? "Guardando…" : "Registrar decisión"}
            </button>
          </div>}
        </article>)}
      </div>
      <div className="cs-review-history">
        <h3><Clock3 size={17}/> Historial de decisiones</h3>
        {selected.history.length === 0
          ? <p>Este plan aún no tiene decisiones registradas.</p>
          : selected.history.map(entry => <p key={entry.id}>
              Tarea #{entry.task_id} · {statusNames[entry.from_status]} → {statusNames[entry.to_status]}
              · Revisor #{entry.actor_id} · {entry.notes}
            </p>)}
      </div>
      <p className="cs-review-note">{selected.note}</p>
    </section>}
  </div>;
}
