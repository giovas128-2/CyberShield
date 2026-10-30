/* BACKEND_GISS: Protection[] <- getProtections() (services/management.ts): id, name, sensor, description, mode, mitre[]. */
import { PageHeader, ModeBadge, ResourceView } from "../components/ui";
import { MitreBadge } from "../components/mitre/MitreTechniqueCard";
import { useResource } from "../hooks/useResource";
import { getProtections } from "../services/management";

export default function ProtectionsPage() {
  const r = useResource((s) => getProtections(s));
  const list = r.data ?? [];
  const integrated = list.filter((p) => p.mode === "integrated").length;
  const simulated = list.filter((p) => p.mode === "simulated").length;
  const pending = list.filter((p) => p.mode === "pending").length;
  const pct = list.length ? Math.round((integrated / list.length) * 100) : 0;

  return (
    <>
      <PageHeader title="Protecciones" subtitle="Estado real de los controles defensivos y su cobertura demostrable." />
      <ResourceView r={r} empty="No hay controles configurados.">
        <div className="card coverage-card">
          <div className="coverage-main">
            <div><span className="eyebrow">Cobertura confirmada</span><b className="coverage-value">{pct}%</b></div>
            <div className="coverage-copy">{integrated} de {list.length} controles están marcados como integración confirmada.</div>
          </div>
          <div className="prog" aria-label={`${pct}% de cobertura integrada`}><i style={{ width: `${pct}%` }} /></div>
          <div className="mode-summary" aria-label="Resumen por modo">
            <span><i className="dot dot-info" />{integrated} integradas</span>
            <span><i className="dot dot-vio" />{simulated} simulaciones</span>
            <span><i className="dot dot-wn" />{pending} pendientes</span>
          </div>
          <small className="safe-copy">El estado describe la integración de CyberShield; no confirma por sí solo que haya ocurrido un ataque.</small>
        </div>

        <div className="pgrid">
          {list.map((p, i) => {
            const primary = p.mitre.find((t) => t.is_primary) ?? p.mitre[0];
            return (
              <article className="card pcard protection-card" key={p.id}>
                <div className="row" style={{ padding: 0 }}><span className="eb mono">CONTROL {String(i + 1).padStart(2, "0")}</span><ModeBadge mode={p.mode} /></div>
                <h3>{p.name}</h3>
                {p.description && <p className="protection-description">{p.description}</p>}
                <div className="pmeta">
                  <div><small className="mu">SENSOR / ORIGEN</small><b>{p.sensor}</b></div>
                  <div>
                    <small className="mu">MITRE ATT&amp;CK ASOCIADO</small>
                    {p.mitre.length ? <span className="acts">{p.mitre.map((t) => <MitreBadge key={t.technique_id} t={t} />)}</span> : <b>Sin clasificación confirmada</b>}
                    {primary && <div className="mitre-inline"><b>{primary.technique_name}</b>{primary.tactic && <span>{primary.tactic}</span>}</div>}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </ResourceView>
    </>
  );
}
