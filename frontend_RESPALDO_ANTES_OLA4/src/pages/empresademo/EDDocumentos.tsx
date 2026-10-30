import { useMemo, useState } from "react";
import { ED_DOCS } from "../../empresademo/fixtures";

export default function EDDocumentos() {
  const [q, setQ] = useState("");
  const [cl, setCl] = useState("");
  const [sel, setSel] = useState(ED_DOCS[0].id);
  const clients = Array.from(new Set(ED_DOCS.map((d) => d.client)));
  const rows = useMemo(() => ED_DOCS.filter((d) => (!cl || d.client === cl) && (!q.trim() || `${d.title} ${d.code}`.toLowerCase().includes(q.trim().toLowerCase()))), [q, cl]);
  // Se conserva la selección al filtrar mientras siga visible; si no, se usa la primera fila visible.
  const cur = rows.find((d) => d.id === sel) ?? rows[0];
  const count = (s: string) => ED_DOCS.filter((d) => d.state === s).length;
  return (
    <>
      <div className="ed-h"><div><div className="ed-eyebrow">EmpresaDemo / Corporativo</div><h1>Documentos, sin perder el hilo.</h1><div className="ed-sub">El material de tu equipo, organizado por cliente y proyecto. Todos los archivos son de muestra.</div></div></div>
      <div className="ed-grid3">
        <div className="ed-card ed-kpi"><small>Todos los documentos</small><b>18</b></div>
        <div className="ed-card ed-kpi"><small>Por revisar</small><b>{String(count("Por revisar")).padStart(2, "0")}</b></div>
        <div className="ed-card ed-kpi"><small>Compartidos con el equipo</small><b>09</b></div>
      </div>
      <div className="ed-fbar">
        <input className="ed-in" placeholder="Buscar documento" aria-label="Buscar documento" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="ed-in" aria-label="Cliente" value={cl} onChange={(e) => setCl(e.target.value)}><option value="">Cliente: todos</option>{clients.map((c) => <option key={c}>{c}</option>)}</select>
      </div>
      {cur ? (
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1.25fr) minmax(0,1fr)", gap: 16, alignItems: "start" }} className="ed-docs-cols">
          <div>
            <div className="ed-tw"><table><thead><tr><th>Nombre / referencia</th><th>Cliente</th><th>Estado</th><th>Versión</th></tr></thead>
              <tbody>{rows.map((d) => (
                <tr key={d.id} className={`clk ${d.id === cur.id ? "on" : ""}`} tabIndex={0} aria-selected={d.id === cur.id} onClick={() => setSel(d.id)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSel(d.id); } }}>
                  <td>{d.title}<div className="ed-mu" style={{ fontSize: 12 }}>{d.code} · {d.kind}</div></td><td>{d.client}</td><td><b>{d.state}</b></td><td>{d.version} · {d.when}</td></tr>))}</tbody></table></div>
            <small className="ed-foot-note">{rows.length} de 18 documentos de muestra</small>
          </div>
          <div style={{ display: "grid", gap: 16 }}>
            <div className="ed-card"><div className="ed-h"><h3>Vista previa</h3><small className="ed-mu">{cur.code}</small></div>
              <div className="ed-prev"><div className="ed-eyebrow">{cur.client} / Muestra</div><h2 className="serif" style={{ margin: "4px 0", fontSize: 24 }}>{cur.title}</h2>
                {cur.outline.map((o, i) => <div key={o} className="ed-mu">{String(i + 1).padStart(2, "0")} · {o}</div>)}<div><span className="ed-tag">Contenido ficticio</span></div></div>
              <p className="ed-mu" style={{ fontSize: 13 }}>Versión {cur.version.replace("v", "")} · {cur.owner}. Actualizado: {cur.when}.</p></div>
            <div className="ed-card"><h3>Actividad reciente</h3>
              <div className="ed-list"><div><small>10:08</small><div><b>Versión 3 guardada</b><br /><small>Cambio de alcance de muestra.</small></div></div><div><small>09:55</small><div><b>Revisión solicitada</b><br /><small>Equipo Demo A · Pendiente.</small></div></div></div></div>
          </div>
        </div>
      ) : (
        <div className="ed-card ed-center"><h2 className="serif">Aún no hay documentos aquí.</h2><div className="ed-mu">Prueba otra colección o restablece los filtros.</div><button className="ed-btn" onClick={() => { setQ(""); setCl(""); }}>Restablecer filtros</button></div>
      )}
    </>
  );
}
