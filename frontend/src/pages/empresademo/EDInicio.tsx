import { FolderOpen, TrendingUp, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { DEMO_ACTIVITY, DEMO_KPIS, ED_USER } from "../../empresademo/data";
import { useIncident } from "../../empresademo/IncidentContext";
import { EmployeeSummaryBanner } from "../../empresademo/IncidentUI";
import { PageHead } from "../../empresademo/PageHead";

function Availability({ label, status, tone = "" }: { label: string; status: string; tone?: string }) {
  return <div className="ed-availability"><span>{label}</span><span className={`ed-chip ${tone}`}>{status}</span></div>;
}

/** Resumen inspirado en la propuesta visual de Alex: operación + disponibilidad, sin detalle técnico. */
export default function EDInicio() {
  const { state, locked } = useIncident();
  const clientsLimited = locked("edit", "clientes") || locked("export", "clientes") || locked("delete", "clientes");
  const docsLimited = locked("edit", "documentos") || locked("replace", "documentos") || locked("delete", "documentos") || locked("bulkUpload", "documentos");
  const reportsLimited = locked("export", "reportes") || locked("download", "reportes") || locked("share", "reportes");
  const accessLimited = locked("login", "accesos") || locked("changePassword", "perfil");

  return (
    <>
      <PageHead title="Resumen de operaciones" sub={`Buen día, ${ED_USER.name.split(" ")[0]}. Este es el estado de su espacio de trabajo.`}>
        <Link className="ed-btn" to="/empresa-demo/documentos"><FolderOpen size={14} />Ver documentos</Link>
      </PageHead>
      <EmployeeSummaryBanner />
      <div className="ed-grid4">
        {DEMO_KPIS.map((k) => <div className="ed-card ed-kpi" key={k.label}><small>{k.label}</small><b>{k.value}</b><small>{k.hint}</small></div>)}
      </div>
      <div className="ed-cols">
        <section className="ed-card"><h3>Actividad reciente</h3>
          <div className="ed-tw"><table><thead><tr><th>Actividad</th><th>Responsable</th><th>Momento</th></tr></thead>
            <tbody>{DEMO_ACTIVITY.map((a) => <tr key={a.what}><td>{a.what}</td><td>{a.who}</td><td>{a.when}</td></tr>)}</tbody></table></div>
        </section>
        <section className="ed-card"><h3>Disponibilidad de funciones</h3><p className="ed-mu">Estado operativo para su cuenta.</p>
          <div className="ed-availability-list">
            <Availability label="Consulta de clientes" status={clientsLimited ? "Acciones limitadas" : "Disponible"} tone={clientsLimited ? "warn" : "ok"} />
            <Availability label="Lectura de documentos" status="Disponible" tone="ok" />
            <Availability label="Gestión de documentos" status={docsLimited ? "Restringida" : "Disponible"} tone={docsLimited ? "warn" : "ok"} />
            <Availability label="Exportar reportes" status={reportsLimited ? "Restringida" : "Disponible"} tone={reportsLimited ? "warn" : "ok"} />
            <Availability label="Cuenta y sesiones" status={accessLimited ? "Verificación requerida" : "Disponible"} tone={accessLimited ? "warn" : "ok"} />
            <Availability label="Administración" status="Acceso limitado" />
          </div>
          <p className="ed-foot-note">Si una acción no está disponible, inténtelo nuevamente más tarde o contacte a soporte interno.</p>
        </section>
      </div>
      <section className="ed-card"><h3>Accesos rápidos</h3>
        <div className="ed-fbar">
          <Link className="ed-btn" to="/empresa-demo/clientes"><Users size={14} />Consultar clientes</Link>
          <Link className="ed-btn" to="/empresa-demo/documentos"><FolderOpen size={14} />Abrir documentos</Link>
          <Link className="ed-btn" to="/empresa-demo/reportes"><TrendingUp size={14} />Consultar reportes</Link>
        </div>
      </section>
    </>
  );
}
