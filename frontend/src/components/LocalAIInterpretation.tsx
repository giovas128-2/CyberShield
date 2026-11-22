import { useEffect, useState } from "react";
import { AlertTriangle, BrainCircuit, Loader2, ShieldCheck } from "lucide-react";
import { api, ApiError } from "../api/client";

type LocalAIStatus = {
  enabled: boolean;
  available: boolean;
  model: string | null;
  status: "disabled" | "invalid_model" | "missing_model" | "unreachable" | "ready";
  note: string;
};
type LocalAIAnswer = {
  mode: "ollama_local";
  model: string;
  attack_id: string;
  source: string;
  reference_url: string;
  summary_es: string;
  automated_changes: false;
  human_review_required: true;
  data_sent: string;
  note: string;
};

export default function LocalAIInterpretation({ attackId }: { attackId: string }) {
  const [status, setStatus] = useState<LocalAIStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const [answer, setAnswer] = useState<LocalAIAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusError, setStatusError] = useState("");

  useEffect(() => {
    let active = true;
    api<LocalAIStatus>("/intelligence/local-ai/status")
      .then(result => { if (active) setStatus(result); })
      .catch((err: unknown) => {
        if (!active) return;
        setStatus(null);
        const statusCode = err instanceof ApiError ? err.status : null;
        setStatusError(statusCode === 403
          ? "Tu sesión no tiene permiso para usar IA local. Se requiere rol de ingeniero o administrador."
          : statusCode === 404
            ? "El backend no tiene disponible el módulo de IA. Verifica que el puerto 8001 ejecute la rama de pruebas actualizada."
            : statusCode === 401
              ? "Tu sesión expiró. Inicia sesión nuevamente en la instancia de pruebas."
              : "No se pudo consultar el estado de la IA local. Comprueba que el backend de pruebas esté activo.");
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
      const result = await api<LocalAIAnswer>(
        `/intelligence/local-ai/techniques/${encodeURIComponent(attackId)}/interpret`,
        "POST"
      );
      if (result.mode !== "ollama_local" || result.attack_id !== attackId ||
          result.automated_changes !== false || !result.summary_es) {
        throw new Error("La interpretación local devolvió un resultado inválido.");
      }
      setAnswer(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible consultar el modelo local.");
    } finally {
      setLoading(false);
    }
  }

  // El backend mantiene la autorización; esta vista informa el motivo de indisponibilidad.
  return <section className="cs-local-ai" aria-label="Interpretación con IA local">
    <div className="cs-local-ai-head">
      <BrainCircuit size={19}/>
      <strong>IA local (Ollama)</strong>
      <span>Experimental · sin API de pago</span>
    </div>
    {checking && <p className="cs-local-ai-status"><Loader2 size={15} className="spin"/> Consultando estado local…</p>}
    {!checking && statusError && <p className="cs-local-ai-error" role="alert"><AlertTriangle size={15}/>{statusError}</p>}
    {!checking && status && !status.available && <>
      <p className="cs-local-ai-status">
        <AlertTriangle size={15}/>
        {status.note}
      </p>
      <small>El informe documental en español continúa funcionando sin IA.</small>
    </>}
    {status?.available && <>
      <p className="cs-local-ai-status">
        <ShieldCheck size={16}/> Modelo disponible: {status.model}. Solo se enviarán descripciones públicas MITRE a Ollama en esta computadora.
      </p>
      <button type="button" className="cs-local-ai-button" disabled={loading} onClick={interpret}>
        {loading ? <Loader2 size={15} className="spin"/> : <BrainCircuit size={15}/>}
        {loading ? "Analizando localmente…" : "Interpretar con IA local"}
      </button>
    </>}
    {error && <p role="alert" className="cs-local-ai-error">{error}</p>}
    {answer && <div className="cs-local-ai-result" role="status">
      <strong>Interpretación local · {answer.model}</strong>
      <p>{answer.summary_es}</p>
      <small>{answer.note} Requiere revisión humana; no se han instalado protecciones.</small>
    </div>}
  </section>;
}
