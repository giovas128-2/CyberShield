import { Info, Lock } from "lucide-react";
import { Link } from "react-router-dom";
import { IncidentBanner } from "../../empresademo/IncidentUI";
import { PageHead } from "../../empresademo/PageHead";

/**
 * La cuenta normal no adquiere privilegios por navegar a esta ruta.
 * La interfaz comunica el límite del rol sin mostrar controles administrativos internos.
 */
export default function EDAdministracion() {
  return (
    <>
      <PageHead title="Administración" sub="Funciones disponibles únicamente para cuentas con permisos administrativos." />
      <IncidentBanner module="administracion" />
      <section className="ed-card ed-center" style={{ maxWidth: 720, padding: 36 }}>
        <div className="ed-avatar" aria-hidden="true"><Lock size={28} /></div>
        <span className="ed-tag">Acceso limitado</span>
        <h2>No tiene funciones administrativas asignadas</h2>
        <p className="ed-mu" style={{ margin: 0, maxWidth: 560 }}>Su cuenta puede continuar utilizando los módulos autorizados. Si necesita realizar una tarea administrativa, contacte al equipo de soporte interno.</p>
        <Link className="ed-btn pri" to="/empresa-demo/inicio">Volver al resumen</Link>
      </section>
      <div className="ed-note"><Info size={16} /><span>Los permisos de administración dependen del rol asignado a su cuenta y no se modifican desde esta pantalla.</span></div>
    </>
  );
}
