import { useEffect, useState } from "react";
import {
  AlertTriangle, BrainCircuit, CheckCircle2, ClipboardCheck,
  Loader2, ShieldCheck,
} from "lucide-react";
import { api, ApiError } from "../api/client";
import type { ProjectAdvice } from "./ProjectRecommendationReport";

type Status = {
  enabled: boolean;
  available: boolean;
  model: string | null;
  status: "disabled" | "invalid_model" | "missing_model" | "unreachable" | "ready";
  note: string;
};
type AIResponse = {
  mode: "ollama_local_project";
  model: string;
  summary_es: string;
  automatic_application: false;
  human_review_required: true;
  review_basis: string;
  data_sent: string;
  note: string;
};

export default function ProjectLocalAIInterpretation({ report }: { report: ProjectAdvice }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [checking, setChecking] = useState(true);
  const [statusError, setStatusError] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<AIResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api<Status>("/intelligence/local-ai/status")
      .then(s => {
        if (active) setStatus(s);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setStatusError(err instanceof ApiError && err.status === 403
          ? "Tu cuenta no tiene permisos de ingeniero o administrador para consultar Ollama."
          : err instanceof ApiError && err.status === 404
            ? "Reinicia el backend de pruebas actualizado en el puerto 8001."
            : "No se pudo consultar el estado de Ollama en el backend de pruebas.");
      })
      .finally(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, []);

  async function interpret() {
    if (!status?.available || loading) return;
    setError("");
    setAnswer(null);
    setLoading(true);
    try {
      // Lista explícita de metadatos; jamás enviar los archivos, su código,
      // las rutas, las líneas ni los objetos finding completos.
      const body = {
        project_type: report.project.project_type,
        description: report.project.description.slice(0, 600),
        declared_characteristics: report.project.declared_characteristics,
        languages: report.project.languages_observed.slice(0, 10).map(x => x.name),
        recommendations: report.recommendations.slice(0, 12).map(x => ({
          id: x.id,
          matches: x.matches,
        })),
      };
      const response = await api<AIResponse>(
        "/intelligence/local-ai/projects/interpret",
        "POST", body,
      );
      if (response.mode !== "ollama_local_project" ||
          response.automatic_application !== false ||
          response.human_review_required !== true ||
          !response.summary_es) {
        throw new Error("La IA local devolvió un resultado inesperado.");
      }
      setAnswer(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo consultar Ollama.");
    } finally {
      setLoading(false);
    }
  }

  return <section className="cs-project-ollama" aria-label="Interpretación opcional con Ollama local">
    <div className="cs-project-ollama-heading">
      <BrainCircuit size={22}/>
      <div>
        <h3>Interpretar diagnóstico con IA local</h3>
        <p>Explicación personalizada de los indicios y medidas sugeridas. No instala defensas.</p>
      </div>
      <span>OLLAMA LOCAL</span>
    </div>

    {checking && <p className="cs-project-ollama-status">
      <Loader2 size={15} className="spin"/> Comprobando el modelo local…
    </p>}
    {statusError && <p className="cs-project-ollama-error" role="alert">
      <AlertTriangle size={16}/>{statusError}
    </p>}
    {status && !status.available && <p className="cs-project-ollama-status">
      <AlertTriangle size={16}/>{status.note}
    </p>}
    {status?.available && <>
      <p className="cs-project-ollama-status">
        <CheckCircle2 size={16}/> Modelo disponible: {status.model}.
        Se utilizarán solo el perfil, tecnologías y códigos de hallazgos resumidos.
      </p>
      <button className="cs-project-ollama-button" type="button"
        onClick={interpret} disabled={loading}>
        {loading ? <Loader2 size={17} className="spin"/> : <BrainCircuit size={17}/>}
        {loading ? "Interpretando en tu computadora…" : "Interpretar con IA local"}
      </button>
    </>}

    {error && <p className="cs-project-ollama-error" role="alert">
      <AlertTriangle size={16}/>{error}
    </p>}
    {answer && <div className="cs-project-ollama-result">
      <div className="cs-project-ollama-result-title">
        <ShieldCheck size={18}/>
        <strong>Interpretación con {answer.model}</strong>
      </div>
      <p>{answer.summary_es}</p>
      <div className="cs-project-ollama-disclosure">
        <ClipboardCheck size={16}/>
        <span>{answer.note} {answer.data_sent}</span>
      </div>
    </div>}
    <small>
      El resumen se obtiene del análisis previo; no se envían ZIP, código fuente
      ni rutas de archivos a Ollama. El modelo puede equivocarse: el ingeniero
      debe contrastar cada propuesta con la evidencia antes de actuar.
    </small>
  </section>;
}
