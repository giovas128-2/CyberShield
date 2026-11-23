import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, CheckCircle2, ClipboardCheck, Layers3,
  Loader2, ShieldCheck, ShieldQuestion,
} from "lucide-react";
import { api, ApiError } from "../api/client";
import type { ProjectAdvice } from "./ProjectRecommendationReport";
import ProjectSecurityPlanDraft from "./ProjectSecurityPlanDraft";
import type { SecurityPlan } from "./ProjectSecurityPlanDraft";

type Related = {
  id: string;
  name: string;
  sensor: string;
  catalog_mode: "integrated" | "simulated" | "pending" | "unknown";
  relationship: "complementary";
  why_related: string;
  limitation: string;
  execution_enabled_in_catalog: boolean | null;
  execution_verified_in_catalog: boolean | null;
  verified_for_project: false;
};
type Match = {
  recommendation_id: string;
  coverage: "unverified_for_project";
  direct_solution_in_catalog: false;
  related_controls: Related[];
  missing_action: string;
};
type Comparison = {
  source: string;
  catalog_controls_total: number;
  items: Match[];
  read_only: true;
  automatic_application: false;
  project_controls_verified: false;
  note: string;
  project_plan: SecurityPlan;
};

const modeLabels: Record<Related["catalog_mode"], string> = {
  integrated: "Integrado en CyberShield",
  simulated: "Simulación de laboratorio",
  pending: "Pendiente en catálogo",
  unknown: "Modo no confirmado",
};

function errorText(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 403) return "La comparación requiere permisos de administrador o ingeniero.";
    if (err.status === 404) return "El backend de pruebas necesita cargar la versión nueva (puerto 8001).";
    return err.message;
  }
  return err instanceof Error ? err.message : "No se pudo leer el catálogo de protecciones.";
}

/**
 * Comparación de orientación, nunca prueba de instalación en el proyecto.
 * Solo transmite identificadores de las recomendaciones; ningún archivo o contexto.
 */
export default function ProjectCatalogComparison({ report }: { report: ProjectAdvice }) {
  const ids = useMemo(
    () => report.recommendations.slice(0, 12).map(item => item.id),
    [report],
  );
  const fingerprint = ids.join("|");
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [loading, setLoading] = useState(ids.length > 0);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!fingerprint) return;
    let active = true;
    setLoading(true);
    setError("");
    setComparison(null);
    api<Comparison>("/intelligence/projects/compare-protections", "POST", {
      recommendation_ids: fingerprint.split("|"),
    }).then(data => {
      if (!data.read_only || data.automatic_application !== false ||
          data.project_controls_verified !== false ||
          !Array.isArray(data.items) ||
          data.project_plan?.mode !== "local_review_draft" ||
          data.project_plan.stored_in_database !== false ||
          data.project_plan.automatic_application !== false) {
        throw new Error("La API devolvió una comparación inválida.");
      }
      if (active) setComparison(data);
    }).catch(err => {
      if (active) setError(errorText(err));
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [fingerprint]);

  if (ids.length === 0) return null;

  const named = new Map(report.recommendations.map(item => [item.id, item.title]));
  const complementary = comparison?.items.filter(i => i.related_controls.length > 0).length ?? 0;

  return <section className="cs-project-comparison" aria-label="Comparar con protecciones registradas">
    <header className="cs-project-comparison-header">
      <Layers3 size={21}/>
      <div>
        <h3>Comparación con las ocho protecciones de CyberShield</h3>
        <p>¿Qué controles del laboratorio podrían complementar estas recomendaciones y qué falta verificar?</p>
      </div>
    </header>
    {loading && <p className="cs-project-comparison-status" role="status">
      <Loader2 size={16} className="spin"/> Consultando el catálogo actual…
    </p>}
    {error && <p className="cs-project-comparison-error" role="alert">
      <AlertTriangle size={16}/>{error}
    </p>}
    {comparison && <>
      <div className="cs-project-comparison-numbers">
        <div><strong>{comparison.catalog_controls_total}</strong><span>Controles históricos en el catálogo</span></div>
        <div><strong>{complementary}</strong><span>Recomendaciones con algún control complementario</span></div>
        <div><strong>0</strong><span>Protecciones verificadas para este proyecto</span></div>
      </div>
      <div className="cs-project-comparison-list">
        {comparison.items.map(item =>
          <article className="cs-project-comparison-item" key={item.recommendation_id}>
            <div className="cs-project-comparison-item-title">
              <ShieldQuestion size={17}/>
              <strong>{named.get(item.recommendation_id) ?? item.recommendation_id}</strong>
            </div>
            {item.related_controls.length === 0
              ? <p className="cs-project-comparison-uncovered">
                  No hay un control equivalente identificado entre c1–c8.
                </p>
              : <div className="cs-project-comparison-related">
                  {item.related_controls.map(control =>
                    <div className="cs-project-comparison-control" key={control.id}>
                      <div className="cs-project-comparison-control-title">
                        <ShieldCheck size={16}/>
                        <strong>{control.id.toUpperCase()} · {control.name}</strong>
                        <span>{modeLabels[control.catalog_mode]}</span>
                      </div>
                      <p>{control.why_related}</p>
                      <small>{control.limitation}</small>
                    </div>
                  )}
                </div>}
            <p className="cs-project-comparison-gap">
              <ClipboardCheck size={15}/>
              <span>Sin cobertura directa verificada en este proyecto. {item.missing_action}</span>
            </p>
          </article>
        )}
      </div>
      <ProjectSecurityPlanDraft key={fingerprint} plan={comparison.project_plan} projectName={report.project.name}/>
      <p className="cs-project-comparison-disclosure">
        <CheckCircle2 size={17}/>
        <span>{comparison.note}</span>
      </p>
    </>}
  </section>;
}
