import { useEffect, useId, useState } from "react";
import { AlertTriangle, BookOpen, ChevronDown, ChevronUp, Loader2, ShieldCheck } from "lucide-react";
import { api } from "../api/client";

type Mitigation = {
  mitigation_id: string;
  name: string;
  description: string | null;
};

type TechniqueDetail = {
  attack_id: string;
  name: string;
  mitigation_count: number;
  mitigations: Mitigation[];
};

/**
 * Consulta MITRE al solicitar el detalle. La lista procede de relaciones
 * importadas en PostgreSQL; nunca genera ni instala una protección.
 */
export default function MitreMitigations({ attackId }: { attackId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<TechniqueDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const detailsId = useId();

  useEffect(() => {
    if (!expanded || detail) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api<TechniqueDetail>(
      `/intelligence/techniques/${encodeURIComponent(attackId)}`,
      "GET",
      undefined,
      controller.signal,
    )
      .then(response => {
        if (!Array.isArray(response.mitigations) || response.attack_id !== attackId) {
          throw new Error("La API devolvió un detalle MITRE inválido.");
        }
        if (!controller.signal.aborted) setDetail(response);
      })
      .catch(err => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "No se pudo leer la relación MITRE.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attackId, expanded, detail]);

  return <div className="cs-threat-mitigations">
    <button
      type="button"
      className="cs-threat-mitigations-toggle"
      aria-expanded={expanded}
      aria-controls={detailsId}
      onClick={() => setExpanded(value => !value)}
    >
      <ShieldCheck size={16}/>
      {expanded ? "Ocultar mitigaciones MITRE" : "Ver mitigaciones documentadas"}
      {expanded ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
    </button>
    {expanded && <div id={detailsId} className="cs-threat-mitigations-body">
      {loading && <p role="status" className="cs-threat-mitigations-feedback">
        <Loader2 size={15} className="spin"/> Consultando relaciones oficiales importadas…
      </p>}
      {error && <p role="alert" className="cs-threat-mitigations-error">
        <AlertTriangle size={16}/> {error}
      </p>}
      {detail && <>
        <p className="cs-threat-mitigations-feedback">
          <BookOpen size={15}/>
          {detail.mitigations.length === 0
            ? "No hay mitigaciones relacionadas en la base actual."
            : `${detail.mitigations.length} mitigación(es) relacionadas en MITRE ATT&CK.`}
        </p>
        {detail.mitigations.map(mitigation =>
          <div className="cs-threat-mitigation" key={mitigation.mitigation_id}>
            <div><span>{mitigation.mitigation_id}</span><strong>{mitigation.name}</strong></div>
            {mitigation.description && <p>{mitigation.description}</p>}
          </div>
        )}
        <p className="cs-threat-mitigations-caution">
          Esta relación es documental. No confirma que el servidor esté protegido,
          ni propone ejecutar automáticamente una regla.
        </p>
      </>}
    </div>}
  </div>;
}
