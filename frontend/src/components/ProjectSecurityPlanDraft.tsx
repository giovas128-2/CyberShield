import { useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import {
  CheckCircle2, ClipboardList, Download, FileCode2, Info,
  LockKeyhole, ShieldCheck, Wrench,
} from "lucide-react";

export type SecurityPlanTask = {
  task_id: string;
  title: string;
  priority: "critical" | "high" | "medium" | "low";
  origin: "code_pattern" | "user_declared";
  action_type: "code_correction" | "control_evaluation" | "environment_review";
  owner_role: "developer" | "security_engineer";
  rationale: string;
  next_step: string;
  verification: string;
  reference_url: string | null;
  related_catalog_controls: string[];
  status: "draft_for_human_review";
  project_deployment_verified: false;
  implementation_approved: false;
  execution_allowed: false;
};

export type SecurityPlan = {
  mode: "local_review_draft";
  tasks: SecurityPlanTask[];
  tasks_total: number;
  code_corrections: number;
  control_evaluations: number;
  environment_reviews: number;
  stored_in_database: false;
  read_only: true;
  automatic_application: false;
  human_review_required: true;
  project_protections_verified: 0;
  note: string;
};

const actionNames: Record<SecurityPlanTask["action_type"], string> = {
  code_correction: "Requiere corrección de código",
  control_evaluation: "Evaluar protección complementaria",
  environment_review: "Revisar configuración del entorno",
};
const roleNames: Record<SecurityPlanTask["owner_role"], string> = {
  developer: "Desarrollador",
  security_engineer: "Ingeniero de seguridad",
};
const priorityNames: Record<SecurityPlanTask["priority"], string> = {
  critical: "Crítica", high: "Alta", medium: "Media", low: "Baja",
};

/** El archivo exportado es un borrador, no un documento aprobado ni un cambio de controles. */
export default function ProjectSecurityPlanDraft({ plan, projectName }: { plan: SecurityPlan; projectName: string }) {
  const [selected, setSelected] = useState<string[]>(() => plan.tasks.map(t => t.task_id));
  const [downloaded, setDownloaded] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [savedPlanId, setSavedPlanId] = useState<number | null>(null);
  const [saveError, setSaveError] = useState("");

  const selectedTasks = plan.tasks.filter(task => selected.includes(task.task_id));

  function toggle(id: string, checked: boolean) {
    setSelected(old => checked ? [...old, id] : old.filter(value => value !== id));
    setDownloaded(false);
  }

  async function sendForReview() {
    if (!selectedTasks.length || submitting) return;
    setSubmitting(true);
    setSavedPlanId(null);
    setSaveError("");
    try {
      const data = await api<{ id: number; stored_in_database: true; execution_allowed: false }>(
        "/intelligence/project-plans", "POST", {
          project_name: (projectName.trim() || "Proyecto sin nombre").slice(0, 100),
          recommendation_ids: selectedTasks.map(task => task.task_id),
        }
      );
      if (!Number.isInteger(data.id) || !data.stored_in_database ||
          data.execution_allowed !== false) {
        throw new Error("El servidor no confirmó el registro seguro del plan.");
      }
      setSavedPlanId(data.id);
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setSaveError("La bandeja todavía no está habilitada en PostgreSQL de pruebas. El borrador se puede descargar sin guardar.");
      } else if (err instanceof ApiError && err.status === 403) {
        setSaveError("Se requiere una cuenta con rol de ingeniero o administrador.");
      } else {
        setSaveError(err instanceof Error ? err.message : "No se pudo registrar el plan.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function downloadDraft() {
    if (!selectedTasks.length) return;
    // Contiene solo los títulos y planes generados desde reglas permitidas,
    // sin descripción libre, ZIP, código, rutas ni credenciales del proyecto.
    const documentData = {
      document_type: "cybershield_project_security_review_draft",
      version: 1,
      generated_at_utc: new Date().toISOString(),
      status: "draft_not_submitted",
      stored_in_database: false,
      approved: false,
      automatic_application: false,
      project_deployment_verified: false,
      tasks: selectedTasks,
      note: plan.note,
    };
    const blob = new Blob([JSON.stringify(documentData, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "cybershield-plan-seguridad-borrador.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setDownloaded(true);
  }

  return <section className="cs-project-plan" aria-label="Plan de seguridad del proyecto">
    <header className="cs-project-plan-heading">
      <ClipboardList size={22}/>
      <div>
        <h3>Plan de protección personalizado</h3>
        <p>Organiza las medidas recomendadas para que un ingeniero decida qué validar.</p>
      </div>
      <span>BORRADOR</span>
    </header>
    <div className="cs-project-plan-metrics">
      <div><strong>{plan.code_corrections}</strong><span>Correcciones de código</span></div>
      <div><strong>{plan.control_evaluations}</strong><span>Controles por evaluar</span></div>
      <div><strong>{plan.environment_reviews}</strong><span>Revisiones de entorno</span></div>
    </div>
    <p className="cs-project-plan-lede">
      Marca las tareas que deseas incluir en el borrador para ingeniería.
      No se registran propuestas ni se instalan protecciones.
    </p>
    <div className="cs-project-plan-tasks">
      {plan.tasks.map(task =>
        <article className="cs-project-plan-task" key={task.task_id}>
          <label className="cs-project-plan-task-head">
            <input type="checkbox" checked={selected.includes(task.task_id)}
              onChange={event => toggle(task.task_id, event.target.checked)}/>
            <span className="cs-project-plan-task-label">
              <strong>{task.title}</strong>
              <span className="cs-project-plan-tags">
                <span>{priorityNames[task.priority]}</span>
                <span>{actionNames[task.action_type]}</span>
                <span>{roleNames[task.owner_role]}</span>
              </span>
            </span>
          </label>
          <div className="cs-project-plan-task-detail">
            <p>{task.rationale}</p>
            <div><Wrench size={15}/><span><b>Acción:</b> {task.next_step}</span></div>
            <div><CheckCircle2 size={15}/><span><b>Validación:</b> {task.verification}</span></div>
            {task.related_catalog_controls.length > 0 && <div>
              <ShieldCheck size={15}/>
              <span><b>Controles relacionados:</b> {task.related_catalog_controls.map(x=>x.toUpperCase()).join(", ")}. No verifican cobertura del proyecto.</span>
            </div>}
            {task.origin === "code_pattern" && <div>
              <FileCode2 size={15}/>
              <span>Indicio por regla estática, pendiente de inspección manual.</span>
            </div>}
            {task.reference_url && <a href={task.reference_url}
              target="_blank" rel="noopener noreferrer">Consultar referencia CWE</a>}
          </div>
        </article>
      )}
    </div>
    <div className="cs-project-plan-actions">
      <div className="cs-project-plan-selection">
        <label>
          <input type="checkbox" checked={selected.length === plan.tasks.length}
            onChange={e => {
              setSelected(e.target.checked ? plan.tasks.map(t => t.task_id) : []);
              setDownloaded(false);
            }}/>
          Seleccionar todas
        </label>
        <span>{selectedTasks.length} de {plan.tasks.length} tareas seleccionadas</span>
      </div>
      <button type="button" className="cs-project-plan-export"
        disabled={selectedTasks.length === 0 || submitting} onClick={sendForReview}>
        <ClipboardList size={17}/> {submitting ? "Guardando en la bandeja…" : "Enviar a revisión"}
      </button>
      <button type="button" className="cs-project-plan-export"
        disabled={selectedTasks.length === 0} onClick={downloadDraft}>
        <Download size={17}/> Descargar borrador para revisión
      </button>
    </div>
    {savedPlanId !== null && <p role="status" className="cs-project-plan-feedback">
      <CheckCircle2 size={16}/> Plan #{savedPlanId} guardado sin activar defensas.
      <Link to="/project-plans">Abrir bandeja de planes</Link>
    </p>}
    {saveError && <p className="cs-project-plan-save-error" role="alert">{saveError}</p>}
    {downloaded && <p role="status" className="cs-project-plan-feedback">
      <CheckCircle2 size={16}/> Borrador preparado para revisión humana. No se registró ninguna aprobación.
    </p>}
    <p className="cs-project-plan-warning">
      <LockKeyhole size={16}/>
      <span>{plan.note} El archivo descargado no incluye código, rutas ni descripción libre. El navegador no conserva las selecciones si recargas la página.</span>
    </p>
    <p className="cs-project-plan-extra">
      <Info size={15}/>
      La bandeja de planes del proyecto es independiente de las propuestas MITRE. Las decisiones solo afectan la revisión documental, nunca las protecciones instaladas.
    </p>
  </section>;
}
