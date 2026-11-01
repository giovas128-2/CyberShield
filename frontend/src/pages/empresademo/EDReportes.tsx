import { useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { DEMO_EXPORTS, DEMO_REPORTS } from "../../empresademo/data";
import { IncidentBanner, LockableButton } from "../../empresademo/IncidentUI";
import { PageHead } from "../../empresademo/PageHead";

/* Lámina 05 · Reportes y exportaciones. Con el escenario de salida inusual se bloquean Exportar / Descargar / Compartir. */
export default function EDReportes() {
  const [area, setArea] = useState(""); const [state, setState] = useState("");
  const [sel, setSel] = useState(DEMO_REPORTS[0].name);
  const areas = Array.from(new Set(DEMO_REPORTS.map((r) => r.area)));
  const rows = useMemo(() => DEMO_REPORTS.filter((r) => (!area || r.area === area) && (!state || r.state === state)), [area, state]);
  return (
    <>
      <PageHead num="05" title="Reportes y exportaciones" sub="Prepare reportes de operaciones y consulte el estado de sus archivos.">
        <LockableButton action="export" module="reportes" className="ed-btn pri"><Plus size={14} />Generar reporte</LockableButton>
      </PageHead>
      <IncidentBanner module="reportes" />
      <div className="ed-filters">
        <label className="ed-field">Periodo<select className="ed-in"><option>Octubre 2026</option></select></label>
        <label className="ed-field">Área<select className="ed-in" value={area} onChange={(e) => setArea(e.target.value)}><option value="">Todas las áreas</option>{areas.map((a) => <option key={a}>{a}</option>)}</select></label>
        <label className="ed-field">Estado<select className="ed-in" value={state} onChange={(e) => setState(e.target.value)}><option value="">Todos</option><option>Listo</option><option>Borrador</option></select></label>
      </div>
      <section className="ed-card"><h3>Reportes disponibles</h3>
        <div className="ed-tw"><table><thead><tr><th>Reporte ficticio</th><th>Fecha</th><th>Área</th><th>Responsable</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.name} className={`clk ${r.name === sel ? "on" : ""}`} onClick={() => setSel(r.name)}>
              <td>{r.name}</td><td>{r.date}</td><td>{r.area}</td><td>{r.owner}</td><td>{r.state}</td>
              <td><button className="ed-lnk" onClick={() => setSel(r.name)}>Ver</button> · {r.state === "Listo"
                ? <LockableButton action="export" module="reportes" className="ed-lnk">Exportar</LockableButton>
                : <button className="ed-lnk">Revisar</button>}</td></tr>))}</tbody></table></div>
        <div className="ed-tablefoot"><span>{sel} · seleccionado</span>
          <div className="ed-fbar"><LockableButton action="export" module="reportes" className="ed-btn pri">Exportar</LockableButton><LockableButton action="download" module="reportes">Descargar</LockableButton><LockableButton action="share" module="reportes">Compartir</LockableButton></div></div>
      </section>
      <section className="ed-card"><h3>Historial de exportaciones</h3>
        <div className="ed-tw"><table><thead><tr><th>Salida legítima</th><th>Solicitante</th><th>Destino autorizado</th><th>Fecha</th><th>Resultado</th></tr></thead>
          <tbody>{DEMO_EXPORTS.map((e) => <tr key={e.file}><td>{e.file}</td><td>{e.who}</td><td>{e.dest}</td><td>{e.when}</td><td style={{ color: "var(--ed-brand)" }}>{e.result}</td></tr>)}</tbody></table></div>
        <p className="ed-foot-note" style={{ marginBottom: 0 }}>Los elementos mostrados corresponden a datos ficticios de demostración.</p>
      </section>
    </>
  );
}
