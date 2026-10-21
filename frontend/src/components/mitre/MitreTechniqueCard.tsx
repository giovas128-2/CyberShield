import { ExternalLink } from "lucide-react";
import type { MitreTechnique } from "../../types";

/* Chip compacto: T1110 (con tooltip de nombre y táctica). */
export function MitreBadge({ t }: { t: MitreTechnique }) {
  const tip = `${t.technique_name}${t.tactic ? ` · ${t.tactic}` : ""}`;
  return t.url
    ? <a className="mb" href={t.url} target="_blank" rel="noreferrer" title={tip}>{t.technique_id}</a>
    : <span className="mb" title={tip}>{t.technique_id}</span>;
}

/* Tarjeta MITRE. Soporta 0, 1 o N técnicas sin romper la vista. La lista viene del backend (no hay catálogo en React). */
export function MitreTechniqueCard({ techniques, showNote = true }: { techniques: MitreTechnique[]; showNote?: boolean }) {
  if (!techniques.length) {
    return <div className="mc"><span className="mlogo">M</span><div><div className="eb">MITRE ATT&amp;CK</div><span className="mu">Sin técnicas asociadas.</span></div></div>;
  }
  const sorted = [...techniques].sort((a, b) => Number(b.is_primary) - Number(a.is_primary));
  return (
    <div className="mcs">
      {sorted.map((t, i) => (
        <div className="mc" key={`${t.technique_id}-${i}`}>
          <span className="mlogo">M</span>
          <div style={{ flex: 1 }}>
            <div className="eb">MITRE ATT&amp;CK · {t.is_primary ? "Técnica primaria" : "Técnica relacionada"}</div>
            <b>{t.technique_id} · {t.technique_name}</b>
            {t.tactic && <small className="mu">Táctica: {t.tactic}</small>}
            {t.rationale && <small className="mu">{t.rationale}</small>}
          </div>
          {t.url && <a href={t.url} target="_blank" rel="noreferrer" aria-label={`Abrir ${t.technique_id} en MITRE`} className="lnk"><ExternalLink size={16} /></a>}
        </div>
      ))}
      {showNote && <small className="mu">El mapeo se basa en la señal disponible; una técnica no confirma por sí sola un ataque.</small>}
    </div>
  );
}
