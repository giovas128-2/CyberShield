import { useId, useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, ExternalLink, ShieldAlert } from "lucide-react";

type Props = {
  cveId: string;
  requiredAction: string | null;
  origin: string | null;
  referenceUrl: string | null;
};

/** Representación de requiredAction importado desde el catálogo CISA KEV.
 *  No es una defensa instalada y no envía solicitudes de IA.
 */
export default function CisaRemediationPanel({
  cveId, requiredAction, origin, referenceUrl,
}: Props) {
  const [open, setOpen] = useState(false);
  const detailsId = useId();

  return <section className="cs-cisa-remediation" aria-label={`Remediación de ${cveId}`}>
    <button type="button" className="cs-cisa-action-toggle"
      aria-expanded={open} aria-controls={detailsId}
      onClick={() => setOpen(value => !value)}>
      <ShieldAlert size={17}/>
      {open ? "Ocultar acción CISA" : "Ver acción recomendada por CISA"}
      {open ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
    </button>
    {open && <div id={detailsId} className="cs-cisa-action-body">
      <strong>Acción oficial documentada para {cveId}</strong>
      {requiredAction
        ? <p className="cs-cisa-action-text">{requiredAction}</p>
        : <p>La copia importada no contiene una acción separable. Consulta el registro original antes de decidir una remediación.</p>}
      {origin && <small><BookOpen size={14}/> Procedencia: {origin}</small>}
      <p className="cs-cisa-action-warning">
        Esta acción es documental y podría exigir comprobar producto, versión,
        alcance y recomendaciones del fabricante. No confirma que el dispositivo
        sea vulnerable ni que la protección esté instalada.
      </p>
      {referenceUrl && <a href={referenceUrl} target="_blank" rel="noopener noreferrer">
        Consultar catálogo oficial CISA KEV <ExternalLink size={14}/>
      </a>}
    </div>}
  </section>;
}
