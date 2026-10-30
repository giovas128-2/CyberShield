/* BACKEND_GISS: ED_CLIENTS <- contenido ficticio de la app demo (mocks/mockData.ts §9); no viene de CyberShield. */
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ED_CLIENTS } from "../../empresademo/fixtures";

export default function EDClientes() {
  const [q, setQ] = useState("");
  const [st, setSt] = useState("");
  const [sel, setSel] = useState(ED_CLIENTS[0].id);
  const rows = useMemo(() => ED_CLIENTS.filter((c) => (!st || c.status === st) && (!q.trim() || `${c.name} ${c.code} ${c.sector}`.toLowerCase().includes(q.trim().toLowerCase()))), [q, st]);
  const cur = ED_CLIENTS.find((c) => c.id === sel) ?? ED_CLIENTS[0];
  return (
    <>
      <div className="ed-h"><div><div className="ed-eyebrow">EmpresaDemo / Corporativo</div><h1>Relaciones que crecen.</h1><div className="ed-sub">Directorio de clientes ficticios de tu organización. Nombres comerciales de muestra, sin personas reales.</div></div></div>
      <div className="ed-grid4">
        {[["Clientes en el espacio", "24", "Directorio de demostración"], ["En seguimiento", "08", "Conversaciones de muestra"], ["Proyectos en curso", "12", "Actividad ilustrativa"], ["Altas de este mes", "03", "Octubre 2026 · Ficticio"]].map(([l, v, h]) => (
          <div className="ed-card ed-kpi" key={l}><small>{l}</small><b>{v}</b><small>{h}</small></div>))}
      </div>
      <div className="ed-fbar">
        <input className="ed-in" placeholder="Buscar por organización" aria-label="Buscar por organización" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="ed-in" aria-label="Estado" value={st} onChange={(e) => setSt(e.target.value)}><option value="">Estado: todos</option><option>En curso</option><option>En revisión</option><option>En seguimiento</option></select>
      </div>
      {rows.length ? (
        <div className="ed-tw"><table><thead><tr><th>Organización / código</th><th>Sector</th><th>Responsable ficticio</th><th>Estado</th><th>Última actividad</th></tr></thead>
          <tbody>{rows.map((c) => (
            <tr key={c.id} className={`clk ${c.id === sel ? "on" : ""}`} tabIndex={0} aria-selected={c.id === sel} onClick={() => setSel(c.id)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSel(c.id); } }}>
              <td><b>{c.name}</b> <span className="ed-mu">· {c.code}</span></td><td>{c.sector}</td><td>{c.owner}</td><td><b>{c.status}</b></td><td>{c.last}</td></tr>))}</tbody></table></div>
      ) : (
        <div className="ed-card ed-center"><h2 className="serif">Aún no hay clientes aquí.</h2><div className="ed-mu">Prueba con otra búsqueda o restablece los filtros.</div><button className="ed-btn" onClick={() => { setQ(""); setSt(""); }}>Restablecer filtros</button></div>
      )}
      <small className="ed-foot-note">{rows.length} de 24 clientes ficticios · Muestra del directorio</small>
      <div className="ed-split">
        <div className="ed-card"><div className="ed-h"><h3>{cur.name}</h3><small className="ed-mu">{cur.code} · Seleccionado</small></div><p className="ed-mu">{cur.note}</p>
          <Link className="ed-btn" to="/empresa-demo/documentos">Ver documentos de {cur.name.split(" ").pop()} →</Link></div>
        <div className="ed-card"><h3>Información responsable</h3><p className="ed-mu">Este directorio no incluye correos, teléfonos, direcciones ni información personal. Los responsables son equipos de demostración.</p><span className="ed-tag">Datos totalmente ficticios</span></div>
      </div>
    </>
  );
}
