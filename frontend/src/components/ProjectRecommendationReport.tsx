import { BookOpen, CheckCircle2, ClipboardCheck, FileCode2, Info, Layers3, ShieldCheck } from "lucide-react";
import "../styles/project-recommendations.css";
import ProjectLocalAIInterpretation from "./ProjectLocalAIInterpretation";
import ProjectCatalogComparison from "./ProjectCatalogComparison";

export type ProjectContext = {
  name: string;
  description: string;
  project_type: "unspecified" | "web" | "api" | "mobile" | "desktop" | "automation" | "other";
  internet_exposed: boolean;
  uses_authentication: boolean;
  handles_sensitive_data: boolean;
};

export type ProjectRecommendation = {
  id: string;
  title: string;
  priority: "critical" | "high" | "medium" | "low";
  reason: string;
  suggested_action: string;
  verification_plan: string;
  origin: "code_pattern" | "user_declared";
  evidence_status: "requires_human_verification" | "not_verified_in_code";
  evidence: { file: string; line: number; rule: string }[];
  matches: number;
  reference_url: string | null;
  protection_installed: false;
};

export type ProjectAdvice = {
  project: {
    name: string;
    description: string;
    project_type: string;
    declared_characteristics: string[];
    languages_observed: { name: string; files: number; examples: string[] }[];
    description_origin: "user_declared";
    technology_origin: "file_extensions_only";
  };
  recommendations: ProjectRecommendation[];
  recommendations_total: number;
  source_files_reviewed: number;
  status: "preliminary_contextual_review";
  automatic_application: false;
  protection_installed: false;
  note: string;
};

const projectTypes: Record<string, string> = {
  unspecified: "No indicado",
  web: "Aplicación web",
  api: "API / backend",
  mobile: "Aplicación móvil",
  desktop: "Aplicación de escritorio",
  automation: "Automatización / script",
  other: "Otro proyecto",
};
const characteristics: Record<string, string> = {
  internet_exposed: "Accesible desde internet",
  uses_authentication: "Usuarios e inicio de sesión",
  handles_sensitive_data: "Información sensible",
};
const severities: Record<string, string> = {
  critical: "Crítica", high: "Alta", medium: "Media", low: "Baja",
};

export default function ProjectRecommendationReport({ report }: { report: ProjectAdvice }) {
  const profile = report.project;
  return <section className="cs-audit-card cs-project-report">
    <header className="cs-audit-card-heading">
      <span className="cs-audit-icon"><Layers3 size={22}/></span>
      <div>
        <h2>Diagnóstico contextual del proyecto</h2>
        <p>Hallazgos en archivos y controles sugeridos según lo declarado. Sin instalación automática.</p>
      </div>
      <span className="cs-audit-count">{report.recommendations_total} propuestas</span>
    </header>

    <div className="cs-project-report-profile">
      <div className="cs-project-profile-description">
        <span className="cs-project-kicker">DESCRIPCIÓN INGRESADA POR EL USUARIO</span>
        <h3>{profile.name || "Proyecto sin nombre especificado"}</h3>
        <p>{profile.description || "No se proporcionó una descripción de la aplicación. Puedes completar este campo y volver a analizar."}</p>
        <strong>{projectTypes[profile.project_type] || "Tipo de proyecto no especificado"}</strong>
      </div>
      <div className="cs-project-profile-observed">
        <span className="cs-project-kicker">OBSERVADO EN LOS ARCHIVOS INSPECCIONADOS</span>
        <strong>Tecnologías sugeridas por extensiones</strong>
        <div className="cs-project-chips">
          {profile.languages_observed.map(lang =>
            <span key={lang.name} title={lang.examples.join(", ")}>{lang.name} · {lang.files} archivos</span>
          )}
          {profile.languages_observed.length === 0 && <span>Sin lenguajes identificados</span>}
        </div>
        <small>No se ha verificado el framework ni los servicios instalados.</small>
      </div>
    </div>
    {profile.declared_characteristics.length > 0 && <div className="cs-project-declared">
      <Info size={15}/>
      <div><strong>Características declaradas, no comprobadas:</strong>
        {profile.declared_characteristics.map(item =>
          <span key={item}>{characteristics[item] || item}</span>
        )}
      </div>
    </div>}

    <ProjectLocalAIInterpretation report={report}/>

    <div className="cs-project-report-subtitle">
      <ShieldCheck size={20}/>
      <div><h3>Protecciones que conviene evaluar</h3>
        <p>Cada propuesta incluye su fundamento y cómo verificarla antes de implementarla.</p>
      </div>
    </div>

    {report.recommendations.length === 0 ?
      <div className="cs-project-no-advice">
        <CheckCircle2 size={23}/>
        <div><strong>Sin propuestas específicas con los datos disponibles</strong>
          <p>Esto no demuestra que el proyecto sea seguro. Completa el contexto o amplía el análisis del código.</p>
        </div>
      </div>
      : <div className="cs-project-advice-list">
        {report.recommendations.map((item, i) =>
          <article key={item.id} className="cs-project-advice">
            <div className="cs-project-advice-heading">
              <span className="cs-project-advice-index">{i + 1}</span>
              <div>
                <h4>{item.title}</h4>
                <div className="cs-project-advice-badges">
                  <span className={"is-" + item.priority}>{severities[item.priority] || item.priority}</span>
                  <span className={item.origin === "code_pattern" ? "from-code" : "from-profile"}>
                    {item.origin === "code_pattern" ? "Indicio en código · verificar" : "Solo contexto declarado"}
                  </span>
                </div>
              </div>
            </div>
            <p>{item.reason}</p>
            <div className="cs-project-advice-action"><ShieldCheck size={17}/>
              <div><strong>Protección sugerida</strong><p>{item.suggested_action}</p></div>
            </div>
            <div className="cs-project-advice-verify"><ClipboardCheck size={16}/>
              <div><strong>Cómo comprobarla</strong><p>{item.verification_plan}</p></div>
            </div>
            {item.evidence.length > 0 && <div className="cs-project-evidence">
              <FileCode2 size={15}/>
              <div><strong>Evidencia para revisión</strong>
                {item.evidence.map((e, j) =>
                  <code key={j}>{e.file}:{e.line} · {e.rule}</code>
                )}
              </div>
            </div>}
            {item.reference_url && <a href={item.reference_url} target="_blank" rel="noopener noreferrer">
              <BookOpen size={14}/> Referencia de clasificación CWE
            </a>}
          </article>
        )}
      </div>}
    <ProjectCatalogComparison report={report}/>
    <p className="cs-project-report-note"><Info size={16}/>{report.note}</p>
  </section>;
}
