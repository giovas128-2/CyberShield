import { useMemo, useState } from "react";
import { Download, Plus } from "lucide-react";
import { DEMO_CLIENTS } from "../../empresademo/data";
import { useIncident } from "../../empresademo/IncidentContext";
import { IncidentBanner, LockableButton } from "../../empresademo/IncidentUI";
import { PageHead } from "../../empresademo/PageHead";

/* Lámina 03 · Clientes + Ficha. Editar / Eliminar / Exportar se bloquean solo con lockdown global. */
export default function EDClientes() {
  const { locked } = useIncident();
  const readOnly = locked("edit", "clientes");
  const [q, setQ] = useState("");
  const [st, setSt] = useState("");
  const [ow, setOw] = useState("");
  const [sel, setSel] = useState(DEMO_CLIENTS[0].id);
  const rows = useMemo(() => DEMO_CLIENTS.filter((c) => (!st || c.status === st) && (!ow || c.owner === ow) &&
    (!q.trim() || `${c.name} ${c.code}`.toLowerCase().includes(q.trim().toLowerCase()))), [q, st, ow]);
  const cur = DEMO_CLIENTS.find((c) => c.id === sel) ?? DEMO_CLIENTS[0];
  const owners = Array.from(new Set(DEMO_CLIENTS.map((c) => c.owner)));
  return (
    <>
      <PageHead num="03" title="Clientes" sub="Gestiona relaciones, documentación y permisos de consulta. Datos exclusivamente ficticios.">
        <button className="ed-btn pri"><Plus size={14} />Nuevo cliente</button>
      </PageHead>
      <IncidentBanner module="clientes" />
      <div className="ed-filters">
        <label className="ed-field" style={{ flex: 3 }}>Buscar cliente<input className="ed-in" placeholder="Buscar por nombre o referencia" value={q} onChange={(e) => setQ(e.target.value)} /></label>
        <label className="ed-field">Estado<select className="ed-in" value={st} onChange={(e) => setSt(e.target.value)}><option value="">Todos los estados</option><option>Activo</option><option>En revisión</option><option>Inactivo</option></select></label>
        <label className="ed-field">Responsable<select className="ed-in" value={ow} onChange={(e) => setOw(e.target.value)}><option value="">Todos</option>{owners.map((o) => <option key={o}>{o}</option>)}</select></label>
        <LockableButton action="export" module="clientes"><Download size={14} />Exportar</LockableButton>
      </div>
      <div className="ed-cols">
        <section className="ed-card"><h3>Directorio · 248 clientes</h3>
          {rows.length ? (
            <div className="ed-tw"><table><thead><tr><th>Cliente ficticio</th><th>Estado</th><th>Responsable</th><th>Última actividad</th><th>Acción</th></tr></thead>
              <tbody>{rows.map((c) => (
                <tr key={c.id} className={`clk ${c.id === sel ? "on" : ""}`} tabIndex={0} aria-selected={c.id === sel} onClick={() => setSel(c.id)}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSel(c.id); } }}>
                  <td><b>{c.name}</b><br /><small className="ed-mu">{c.code}</small></td><td>{c.status}</td><td>{c.owner}</td><td>{c.last}</td>
                  <td><button className="ed-lnk" onClick={() => setSel(c.id)}>Ver detalle →</button></td></tr>))}</tbody></table></div>
          ) : (
            <div className="ed-center"><h2>Aún no hay clientes aquí.</h2><div className="ed-mu">Prueba con otra búsqueda o restablece los filtros.</div><button className="ed-btn" onClick={() => { setQ(""); setSt(""); setOw(""); }}>Restablecer filtros</button></div>
          )}
          <div className="ed-tablefoot"><span>1–{rows.length} de 248 · muestra demo</span><button className="ed-btn" disabled title="Muestra demo: una sola página">Siguiente →</button></div>
        </section>
        <section className="ed-card"><h3>Ficha de cliente</h3>
          <span className={`ed-tag ${readOnly ? "er" : ""}`}>{readOnly ? "Acciones limitadas" : cur.status}</span>
          <h2 style={{ fontSize: 24, margin: "12px 0 4px" }}>{cur.name}</h2>
          <div className="ed-mu" style={{ marginBottom: 12 }}>{cur.code} · {cur.sector}</div>
          <div className="ed-list"><div>Responsable: {cur.ownerFull}</div><div>Contacto: {cur.contact}</div><div>Alta: {cur.alta}</div></div>
          <div className="ed-fbar" style={{ margin: "16px 0" }}>
            <LockableButton action="edit" module="clientes" className="ed-btn pri">Editar</LockableButton>
            <LockableButton action="delete" module="clientes">Eliminar</LockableButton>
          </div>
          <h4 style={{ margin: "0 0 6px" }}>Documentos vinculados</h4>
          <div className="ed-list" style={{ marginBottom: 16 }}>{cur.docs.length ? cur.docs.map((d) => <div key={d.name} style={{ color: "var(--ed-brand)" }}>{d.name} · {d.state}</div>) : <div className="ed-mu">Sin documentos vinculados.</div>}</div>
          <h4 style={{ margin: "0 0 6px" }}>Actividad y permisos</h4>
          <div className="ed-list ed-mu">{cur.activity.map((a) => <div key={a.t + a.text}>{a.t} · {a.text}</div>)}<div>Tu rol: consulta y edición</div><div>Exportación: según permisos de la cuenta</div></div>
        </section>
      </div>
    </>
  );
}
