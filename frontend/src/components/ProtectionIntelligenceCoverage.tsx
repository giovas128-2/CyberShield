import { useEffect, useState } from "react";
import { BookOpen, Database, ShieldCheck, TriangleAlert } from "lucide-react";
import { api } from "../api/client";
import "../styles/cybershield-design-preview.css";

type Mitigation = { mitigation_id: string; name: string; description: string | null };
type CoverageControl = {
  id: string; name: string; sensor: string; mode: string;
  mitre_techniques: string[]; mitre_mitigations: Mitigation[];
  mitigation_count: number; execution_status: "not_evaluated";
};
type Coverage = {
  source: string; controls_total: number; controls_integrated: number;
  controls_simulated: number; controls: CoverageControl[]; note: string;
};

export default function ProtectionIntelligenceCoverage() {
  const [data, setData] = useState<Coverage | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    api<Coverage>("/intelligence/protection-coverage")
      .then((result) => {
        if (!result || !Array.isArray(result.controls)) {
          throw new Error("Respuesta de cobertura inválida");
        }
        if (active) setData(result);
      })
      .catch(() => {
        if (active) setError("No se pudo consultar la cobertura MITRE. Comprueba tu sesión y la API.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return <section className="csd-shell" style={{display:"block", minHeight:0, padding:0, background:"transparent"}}>
    <div className="csd-page-heading" style={{marginTop:22}}>
      <div><span className="csd-eyebrow">INTELIGENCIA REAL · SOLO LECTURA</span>
        <h2 style={{fontSize:24, margin:"6px 0"}}>Cobertura defensiva y recomendaciones MITRE</h2>
        <p>Las ocho protecciones existentes siguen funcionando como antes. Aquí se muestran sus mitigaciones documentales asociadas.</p>
      </div>
    </div>
    {loading && <div className="csd-panel" role="status">Consultando relaciones MITRE en PostgreSQL…</div>}
    {error && <div className="csd-callout" role="alert"><TriangleAlert size={17}/>{error}</div>}
    {data && <>
      <div className="csd-stats">
        <div className="csd-stat"><div className="csd-stat-heading"><span>Controles del sistema</span><Database size={18}/></div><strong>{data.controls_total}</strong><small>Catálogo existente</small></div>
        <div className="csd-stat"><div className="csd-stat-heading"><span>Integrados</span><ShieldCheck size={18}/></div><strong>{data.controls_integrated}</strong><small>Clasificación actual del backend</small></div>
        <div className="csd-stat"><div className="csd-stat-heading"><span>Simulados</span><BookOpen size={18}/></div><strong>{data.controls_simulated}</strong><small>No confirman defensa real</small></div>
        <div className="csd-stat"><div className="csd-stat-heading"><span>Nuevas defensas ejecutables</span><ShieldCheck size={18}/></div><strong>0</strong><small>Esta fase no crea ejecutores</small></div>
      </div>
      <div className="csd-two-thirds" style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(min(100%,360px),1fr))"}}>
        {data.controls.map((control) => <article key={control.id} className="csd-panel">
          <div className="csd-between">
            <span className="csd-pill csd-pill-blue">{control.id.toUpperCase()}</span>
            <span className={`csd-pill ${control.mode === "integrated" ? "csd-pill-teal" : "csd-pill-amber"}`}>{control.mode === "integrated" ? "Integrada" : "Simulada"}</span>
          </div>
          <h3 style={{margin:"12px 0 4px", color:"#123360"}}>{control.name}</h3>
          <p className="csd-copy">Sensor: {control.sensor} · MITRE: {control.mitre_techniques.join(", ") || "Sin clasificar"}</p>
          <h4 style={{margin:"16px 0 7px"}}>Mitigaciones MITRE asociadas ({control.mitigation_count})</h4>
          {control.mitre_mitigations.length === 0
            ? <p className="csd-muted">No se registran mitigaciones asociadas en la base actual.</p>
            : control.mitre_mitigations.map((m) => <div className="csd-norm" key={m.mitigation_id}>
                <span className="csd-pill csd-pill-slate">{m.mitigation_id}</span>
                <div><b>{m.name}</b><small>Recomendación documental, no ejecutada</small></div>
              </div>)}
        </article>)}
      </div>
      <div className="csd-callout"><TriangleAlert size={17}/><div><b>Sin activaciones automáticas nuevas.</b> {data.note}</div></div>
    </>}
  </section>;
}
