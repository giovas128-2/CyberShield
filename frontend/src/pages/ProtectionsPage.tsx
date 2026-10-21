import { PageHeader, ModeBadge, ResourceView } from "../components/ui";
import { MitreBadge } from "../components/mitre/MitreTechniqueCard";
import { useResource } from "../hooks/useResource";
import { getProtections } from "../services/management";

export default function ProtectionsPage() {
  const r = useResource((s) => getProtections(s));
  const list = r.data ?? [];
  const integrated = list.filter((p) => p.mode === "integrated").length;
  const pct = list.length ? Math.round((integrated / list.length) * 100) : 0;
  return (
    <>
      <PageHeader title="Protecciones" subtitle="Controles configurados para detectar y responder a amenazas." />
      <ResourceView r={r} empty="No hay controles configurados.">
        <div className="card">
          <div className="row" style={{ padding: 0 }}><b style={{ fontSize: 22 }}>{pct}% <small className="mu">cobertura integrada</small></b><span className="mu">{integrated} de {list.length} controles reciben telemetría integrada</span></div>
          <div className="prog"><i style={{ width: `${pct}%`, background: "var(--ac)" }} /></div>
        </div>
        <div className="pgrid">
          {list.map((p, i) => (
            <div className="card pcard" key={p.id}>
              <div className="row" style={{ padding: 0 }}><span className="eb mono">{String(i + 1).padStart(2, "0")}</span><ModeBadge mode={p.mode} /></div>
              <h3 style={{ margin: "10px 0 4px" }}>{p.name}</h3>
              {p.description && <small className="mu">{p.description}</small>}
              <div className="pmeta"><div><small className="mu">SENSOR</small><b>{p.sensor}</b></div>
                <div><small className="mu">MITRE ATT&amp;CK</small>{p.mitre.length ? <span className="acts">{p.mitre.map((t) => <MitreBadge key={t.technique_id} t={t} />)}</span> : <b>—</b>}</div></div>
            </div>
          ))}
        </div>
      </ResourceView>
    </>
  );
}
