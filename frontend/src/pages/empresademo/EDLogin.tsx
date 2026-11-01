import { useState } from "react";
import { Building2, Check, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import "../../empresademo/empresademo.css";
import { ED_USER } from "../../empresademo/data";
import { edSetDevice } from "../../empresademo/fixtures";

export default function EDLogin() {
  const nav = useNavigate();
  const [user, setUser] = useState(ED_USER.email);
  const [pass, setPass] = useState("demo-clave-01");
  const enter = () => { edSetDevice("demo-equipo-01"); nav("/empresa-demo/inicio"); };
  return (
    <div className="ed">
      <div className="ed-login">
        <div className="ed-login-l">
          <div className="ed-brand" style={{ padding: 0 }}><Building2 size={24} />EmpresaDemo</div>
          <div style={{ marginTop: 40 }} className="ed-eyebrow">Portal del empleado</div>
          <h1>Su operación.<br />En un solo espacio.</h1>
          <p>Acceda a clientes, documentos, reportes y funciones disponibles según su rol.</p>
          <div className="ed-lcard">
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}><Building2 size={20} /><div><b>Acceso corporativo</b><div style={{ fontSize: 12, color: "#9fb0cc" }}>Cuenta · Información · Permisos</div></div></div>
            <hr />
            <ul>{["Identidad y sesiones", "Recursos de la empresa", "Acciones según su rol"].map((t) => <li key={t}><Check size={14} />{t}</li>)}</ul>
          </div>
          <small style={{ marginTop: "auto", color: "#9fb0cc" }}>Entorno académico de demostración · Datos ficticios.</small>
        </div>
        <div className="ed-login-r">
          <div className="ed-login-top"><span className="ed-eyebrow">EmpresaDemo / Acceso</span><span className="ed-chip">Datos de muestra</span></div>
          <form className="ed-form" onSubmit={(e) => { e.preventDefault(); enter(); }}>
            <div><div style={{ color: "var(--ed-brand)", fontWeight: 600, fontSize: 13 }}>EmpresaDemo</div><h1>Bienvenido de nuevo</h1><div className="ed-sub">Acceso para personal autorizado</div></div>
            <label>Usuario o correo electrónico<input className="ed-in" value={user} onChange={(e) => setUser(e.target.value)} autoComplete="off" /></label>
            <label>Contraseña<input className="ed-in" type="password" value={pass} onChange={(e) => setPass(e.target.value)} autoComplete="off" /></label>
            <div className="ed-row"><label style={{ display: "flex", gap: 8, fontWeight: 400, alignItems: "center" }}><input type="checkbox" />Recordar mi usuario</label><button type="button" className="ed-lnk">Recuperar contraseña</button></div>
            <button className="ed-btn pri" type="submit" style={{ minHeight: 44 }}>Iniciar sesión</button>
            <div className="ed-foot-note" style={{ textAlign: "center" }}><Lock size={12} style={{ verticalAlign: "-2px" }} /> Acceso corporativo</div>
            <button type="button" className="ed-lnk" style={{ justifySelf: "center" }} onClick={() => nav("/login")}>← Cambiar tipo de acceso</button>
          </form>
          <div className="ed-foot-note" style={{ borderTop: "1px solid var(--ed-bd)", paddingTop: 12 }}>Utilice únicamente su cuenta corporativa. Nunca comparta sus credenciales ni códigos de verificación.<br />¿Necesita ayuda? Contacte al equipo de soporte interno.</div>
        </div>
      </div>
    </div>
  );
}
