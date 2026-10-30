/* BACKEND_GISS: ED_ACTIVITY / ED_DOCS / ED_PROFILE / ED_DATE_LABEL <- contenido ficticio de la app demo (mocks/mockData.ts §9). ED_PROFILE.session <- id de sesión de CyberShield. */
import { FileText } from "lucide-react";
import { Link } from "react-router-dom";
import { ED_ACTIVITY, ED_DATE_LABEL, ED_DOCS, ED_PROFILE } from "../../empresademo/fixtures";

export default function EDInicio() {
  return (
    <>
      <div className="ed-h"><div><div className="ed-eyebrow">EmpresaDemo / Corporativo</div><h1>Hola, {ED_PROFILE.alias}.</h1><div className="ed-sub">Un vistazo a tu jornada. {ED_DATE_LABEL}.</div></div>
        <Link className="ed-btn" to="/empresa-demo/documentos">Abrir documentos</Link></div>
      <section className="ed-hero">
        <div><span className="ed-tag">Dispositivo de confianza · DEMO</span><h2 className="serif">Todo listo para seguir avanzando.</h2>
          <div className="ed-sub">Tu acceso de muestra está habilitado desde demo-equipo-01. Encuentra lo reciente y retoma lo importante.</div></div>
        <div style={{ display: "grid", gap: 12, justifyItems: "end" }}><FileText size={36} strokeWidth={1.2} color="var(--ed-mu)" /><Link className="ed-btn pri" to="/empresa-demo/reportes">Ver actividad del equipo →</Link></div>
      </section>
      <div className="ed-grid4">
        {[["Clientes de muestra", "24", "6 destacados en el directorio"], ["Documentos del espacio", "18", "3 actualizados hoy"], ["Reportes disponibles", "06", "Periodo · Octubre 2026"], ["Tareas del equipo", "04", "2 documentos por revisar"]].map(([l, v, h]) => (
          <div className="ed-card ed-kpi" key={l}><small>{l}</small><b>{v}</b><small>{h}</small></div>))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1.6fr)", gap: 16 }} className="ed-inicio-cols">
        <div className="ed-card"><div className="ed-h"><h3>Tus documentos recientes</h3><Link to="/empresa-demo/documentos" className="ed-mu">Ver todos →</Link></div>
          <div className="ed-tw" style={{ marginTop: 8 }}><table><thead><tr><th>Documento</th><th>Cliente</th><th>Actualizado</th></tr></thead>
            <tbody>{ED_DOCS.slice(0, 3).map((d) => <tr key={d.id}><td>{d.title} · {d.code}</td><td>{d.client}</td><td>{d.when}</td></tr>)}</tbody></table></div>
          <small className="ed-foot-note">Archivos de muestra. No contienen información de clientes reales.</small></div>
        <div className="ed-card"><h3>Actividad del espacio</h3>
          <div className="ed-list">{ED_ACTIVITY.map((a) => <div key={a.t}><small>{a.t}</small><div><b>{a.title}</b><br /><small>{a.meta}</small></div></div>)}</div></div>
      </div>
      <div className="ed-card"><h3>Una organización de muestra, una experiencia completa</h3>
        <div className="ed-fbar"><Link className="ed-btn" to="/empresa-demo/clientes">Explorar clientes →</Link><Link className="ed-btn" to="/empresa-demo/reportes">Consultar reportes →</Link><Link className="ed-btn" to="/empresa-demo/perfil">Mi perfil →</Link></div></div>
      <small className="ed-foot-note">EmpresaDemo · Experiencia corporativa ficticia · Demostración · Sin integración real</small>
    </>
  );
}
