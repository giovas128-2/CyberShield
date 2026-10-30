/* BACKEND_GISS: ED_DEVICES[].trusted <- decisión de confianza del dispositivo (Device Trust) del backend; define si entra a inicio o a acceso restringido. */
import { useState } from "react";
import { Info, Layers } from "lucide-react";
import { useNavigate } from "react-router-dom";
import "../../empresademo/empresademo.css";
import { ED_DEVICES, ED_PROFILE, edSetDevice } from "../../empresademo/fixtures";

export default function EDLogin() {
  const nav = useNavigate();
  const [device, setDevice] = useState("demo-equipo-01");
  const enter = () => { edSetDevice(device); nav(ED_DEVICES[device].trusted ? "/empresa-demo/inicio" : "/empresa-demo/acceso-restringido"); };
  return (
    <div className="ed">
      <div className="ed-login">
        <div className="ed-login-l">
          <div className="ed-brand" style={{ padding: 0 }}><Layers size={22} />EmpresaDemo</div>
          <div style={{ marginTop: 40 }}><span className="ed-tag">Espacio de demostración</span></div>
          <h1>Un buen día empieza con claridad.</h1>
          <p className="ed-sub" style={{ margin: 0 }}>Clientes, documentos y reportes en un espacio pensado para tu equipo.</p>
          <div>
            <label htmlFor="ed-org">Organización de muestra</label>
            <select id="ed-org" className="ed-in" disabled style={{ width: "100%" }}><option>{ED_PROFILE.org}</option></select>
            <label htmlFor="ed-prof">Perfil de demostración</label>
            <input id="ed-prof" className="ed-in" style={{ width: "100%" }} readOnly value={`${ED_PROFILE.alias} · ${ED_PROFILE.user}`} />
            <label htmlFor="ed-dev">Equipo de demostración</label>
            <select id="ed-dev" className="ed-in" style={{ width: "100%" }} value={device} onChange={(e) => setDevice(e.target.value)}>
              <option value="demo-equipo-01">demo-equipo-01 · equipo de confianza</option>
              <option value="demo-equipo-06">demo-equipo-06 · equipo sin autorización</option>
            </select>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button className="ed-btn pri" onClick={enter}>Entrar a la demostración →</button>
            <button className="ed-btn" onClick={() => nav("/login")}>← Cambiar tipo de acceso</button>
          </div>
          <small className="ed-foot-note">Acceso ilustrativo sin contraseña. No introduzcas credenciales ni datos personales reales.</small>
          <div className="ed-note"><Info size={16} style={{ flex: "none", marginTop: 2 }} /><div><b>Tu información está fuera de esta demo</b>Todos los nombres, organizaciones, documentos y cifras son ficticios. No se realizará ninguna autenticación real.</div></div>
          <small className="ed-foot-note" style={{ marginTop: "auto" }}>Origen: DEMO · Empresa ficticia protegida por CyberShield</small>
        </div>
        <div className="ed-login-r">
          <div className="ed-eyebrow">Espacio para lo importante</div>
          <div className="ed-art" aria-hidden="true"><Layers size={72} strokeWidth={1} /></div>
          <h2 className="serif">Todo tu trabajo, en su lugar.</h2>
          <div className="ed-mu">Menos ruido. Más perspectiva.<br />Una forma más amable de llevar el día a día.</div>
          <small className="ed-foot-note">Empresa ficticia · Ilustración genérica · Sin datos reales</small>
        </div>
      </div>
    </div>
  );
}
