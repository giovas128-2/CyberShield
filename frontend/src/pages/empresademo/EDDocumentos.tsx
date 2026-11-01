import { useMemo, useState } from "react";
import { Info, Upload } from "lucide-react";
import { DEMO_DOCS } from "../../empresademo/data";
import { useIncident } from "../../empresademo/IncidentContext";
import { IncidentBanner, LockableButton } from "../../empresademo/IncidentUI";
import { PageHead } from "../../empresademo/PageHead";

const uniq = (f: (d: (typeof DEMO_DOCS)[number]) => string) => Array.from(new Set(DEMO_DOCS.map(f)));

/* Lámina 04 · Documentos. Con el escenario de modificación anómala, los archivos sensibles pasan a SOLO LECTURA. */
export default function EDDocumentos() {
  const { locked } = useIncident();
  const [q, setQ] = useState(""); const [area, setArea] = useState(""); const [type, setType] = useState(""); const [lvl, setLvl] = useState("");
  const [sel, setSel] = useState(DEMO_DOCS[0].name);
  const rows = useMemo(() => DEMO_DOCS.filter((d) => (!area || d.area === area) && (!type || d.type === type) && (!lvl || d.level === lvl) &&
    (!q.trim() || d.name.toLowerCase().includes(q.trim().toLowerCase()))), [q, area, type, lvl]);
  const readOnly = locked("edit", "documentos");
  return (
    <>
      <PageHead num="04" title="Documentos" sub="Archivos de trabajo y documentos compartidos con su equipo.">
        <div className="ed-fbar"><LockableButton action="bulkUpload" module="documentos">Carga masiva</LockableButton><button className="ed-btn pri"><Upload size={14} />Subir documento</button></div>
      </PageHead>
      <IncidentBanner module="documentos" />
      <div className="ed-grid3">
        {[["Documentos vigentes", "1.284", "Inventario de demostración"], ["Pendientes de revisión", "24", "Distribuidos en cuatro áreas"], ["Áreas de trabajo", "6", "Acceso según confidencialidad"]].map(([l, v, h]) => (
          <div className="ed-card ed-kpi" key={l}><small>{l}</small><b>{v}</b><small>{h}</small></div>))}
      </div>
      <div className="ed-filters">
        <label className="ed-field" style={{ flex: 2 }}>Buscar<input className="ed-in" placeholder="Nombre del documento" value={q} onChange={(e) => setQ(e.target.value)} /></label>
        <label className="ed-field">Área<select className="ed-in" value={area} onChange={(e) => setArea(e.target.value)}><option value="">Todas</option>{uniq((d) => d.area).map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="ed-field">Tipo<select className="ed-in" value={type} onChange={(e) => setType(e.target.value)}><option value="">Todos</option>{uniq((d) => d.type).map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="ed-field">Confidencialidad<select className="ed-in" value={lvl} onChange={(e) => setLvl(e.target.value)}><option value="">Todas</option>{uniq((d) => d.level).map((o) => <option key={o}>{o}</option>)}</select></label>
      </div>
      <section className="ed-card"><h3>Biblioteca de documentos</h3>
        <div className="ed-tw"><table><thead><tr><th>Nombre / tipo</th><th>Área</th><th>Confidencialidad</th><th>Responsable</th><th>Fecha</th><th>Estado / acción</th></tr></thead>
          <tbody>{rows.map((d) => (
            <tr key={d.name} className={`clk ${d.name === sel ? "on" : ""}`} tabIndex={0} aria-selected={d.name === sel} onClick={() => setSel(d.name)}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSel(d.name); } }}>
              <td>{d.name} · {d.type}</td><td>{d.area}</td><td>{d.level}</td><td>{d.owner}</td><td>{d.date}</td>
              <td><span style={{ color: "var(--ed-brand)" }}>{d.state} · Abrir</span>{readOnly && d.level !== "Interno" && <span className="ed-tag er" style={{ marginLeft: 8 }}>Solo lectura</span>}</td></tr>))}</tbody></table></div>
        <div className="ed-tablefoot"><span>Seleccionado: {sel}</span>
          <div className="ed-fbar"><LockableButton action="edit" module="documentos" className="ed-btn pri">Editar</LockableButton><LockableButton action="replace" module="documentos">Reemplazar</LockableButton><LockableButton action="delete" module="documentos">Eliminar</LockableButton></div></div>
      </section>
      <div className="ed-note"><Info size={16} /><div><b>¿Necesita un archivo que no está disponible?</b>Contacte a soporte interno e indique el nombre del documento. No es necesario repetir la operación varias veces.</div></div>
    </>
  );
}
