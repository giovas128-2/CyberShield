import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { DEMO_ROLE_PERMS, DEMO_SESSIONS, ED_USER } from "../../empresademo/data";
import { edClear } from "../../empresademo/fixtures";
import { IncidentBanner, LockableButton } from "../../empresademo/IncidentUI";
import { PageHead } from "../../empresademo/PageHead";

/* Lámina 06 · Perfil y sesiones. Con el escenario de credenciales, se bloquea Cambiar contraseña y el inicio de sesión. */
export default function EDPerfil() {
  const nav = useNavigate();
  return (
    <>
      <PageHead num="06" title="Perfil y sesiones" sub="Mantenga sus datos actualizados y revise los accesos a su cuenta.">
        <button className="ed-btn" onClick={() => { edClear(); nav("/login"); }}><LogOut size={14} />Cerrar sesión</button>
      </PageHead>
      <IncidentBanner module="perfil" />
      <IncidentBanner module="accesos" />
      <div className="ed-cols" style={{ gridTemplateColumns: "minmax(0,1.9fr) minmax(0,1fr)" }}>
        <section className="ed-card"><h3>Mi perfil</h3>
          <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 16 }}>
            <div className="ed-avatar" aria-hidden="true">{ED_USER.initials}</div>
            <div><h2 style={{ margin: 0, fontSize: 22 }}>{ED_USER.name}</h2><div className="ed-mu">{ED_USER.email}</div><span className="ed-tag" style={{ marginTop: 6 }}>{ED_USER.role}</span></div>
          </div>
          <div className="ed-filters">
            <label className="ed-field">Área<select className="ed-in" defaultValue="Operaciones"><option>Operaciones</option></select></label>
            <label className="ed-field">Organización<select className="ed-in" defaultValue="EmpresaDemo"><option>EmpresaDemo</option></select></label>
          </div>
        </section>
        <section className="ed-card"><h3>Permisos del rol</h3>
          <div className="ed-list" style={{ marginBottom: 12 }}>{DEMO_ROLE_PERMS.map(([m, p]) => <div key={m}>{m} · {p}</div>)}</div>
          <LockableButton action="changePassword" module="perfil">Cambiar contraseña</LockableButton>
          <p className="ed-foot-note">Los permisos disponibles dependen del rol asignado a su cuenta.</p>
        </section>
      </div>
      <section className="ed-card"><h3>Sesiones de su cuenta</h3><p className="ed-mu">Si no reconoce una sesión, ciérrela y contacte a soporte interno.</p>
        <div className="ed-tw"><table><thead><tr><th>Dispositivo ficticio</th><th>Ubicación demo</th><th>Último acceso</th><th>Estado</th><th>Acción</th></tr></thead>
          <tbody>{DEMO_SESSIONS.map((s, i) => <tr key={i}><td>{s.device}</td><td>{s.place}</td><td>{s.last}</td><td>{s.state}</td><td><button className="ed-lnk">{s.action}</button></td></tr>)}</tbody></table></div>
        <div className="ed-fbar" style={{ marginTop: 12 }}><button className="ed-btn">Cerrar otras sesiones</button><button className="ed-btn">Ver actividad de acceso</button></div>
        <p className="ed-foot-note" style={{ marginBottom: 0 }}>Los dispositivos, ubicaciones y fechas mostrados son datos ficticios de demostración.</p>
      </section>
    </>
  );
}
