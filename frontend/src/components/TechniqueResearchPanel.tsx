import { useEffect, useState } from "react";
import { BookOpen, ClipboardCheck, ExternalLink, FileText, Loader2, TriangleAlert } from "lucide-react";
import { api } from "../api/client";

type Research = {
  attack_id: string;
  name: string;
  source: string;
  source_version: string | null;
  reference_url: string;
  mitigation_count: number;
  mitigations: { id: string; name: string }[];
  summary_es: string;
  verification_steps: string[];
  mode: "documental_sin_ia_generativa";
  needs_human_review: boolean;
  automatic_application: false;
  executable_controls_verified: false;
  note: string;
};

/** Informe gratuito, fundamentado en MITRE importado. No es IA ni certifica seguridad. */
export default function TechniqueResearchPanel({ attackId }: { attackId: string }) {
  const [requested, setRequested] = useState(false);
  const [report, setReport] = useState<Research | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!requested || report) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api<Research>(
      `/intelligence/techniques/${encodeURIComponent(attackId)}/research`,
      "GET", undefined, controller.signal,
    )
      .then(data => {
        if (data.attack_id !== attackId || data.mode !== "documental_sin_ia_generativa"
          || !Array.isArray(data.verification_steps) || !Array.isArray(data.mitigations)
          || data.automatic_application !== false) {
          throw new Error("El informe documental no tiene el formato esperado.");
        }
        if (!controller.signal.aborted) setReport(data);
      })
      .catch(err => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "No fue posible elaborar el informe.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attackId, requested, report]);

  return <section className="cs-threat-report">
    <button type="button" className="cs-threat-report-button"
      onClick={() => setRequested(value => !value)}>
      <FileText size={16}/>
      {requested ? "Ocultar informe" : "Preparar informe documental"}
    </button>
    {requested && <div className="cs-threat-report-content">
      {loading && <p role="status"><Loader2 size={16} className="spin"/> Elaborando informe local…</p>}
      {error && <p role="alert" className="cs-threat-report-error"><TriangleAlert size={16}/>{error}</p>}
      {report && <>
        <div className="cs-threat-report-heading">
          <ClipboardCheck size={18}/><strong>Informe de investigación · {report.attack_id}</strong>
          <span>Sin IA generativa</span>
        </div>
        <p>{report.summary_es}</p>
        <h4>Mitigaciones documentadas ({report.mitigation_count})</h4>
        <div className="cs-threat-report-tags">
          {report.mitigations.map(m => <span key={m.id}>{m.id} · {m.name}</span>)}
          {report.mitigations.length === 0 && <span>Sin mitigaciones vinculadas en esta versión</span>}
        </div>
        <h4>Verificaciones pendientes para el ingeniero</h4>
        <ol>{report.verification_steps.map((step, index) => <li key={index}>{step}</li>)}</ol>
        <a href={report.reference_url} target="_blank" rel="noopener noreferrer">
          <BookOpen size={14}/> Fuente oficial MITRE <ExternalLink size={13}/>
        </a>
        <small>{report.note}</small>
      </>}
    </div>}
  </section>;
}
