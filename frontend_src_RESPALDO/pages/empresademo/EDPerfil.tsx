import { Info } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ED_PROFILE, edClear } from "../../empresademo/fixtures";

const DEFAULTS = { resumen: "Semanal", vista: "Inicio" };
export default function EDPerfil() {
  const nav = useNavigate();
  const [saved, setSaved] = useState(DEFAULTS);
  const [prefs, setPrefs] = useState(DEFAULTS);
  const [done, setDone] = useState(false);
  const dirty = prefs.resumen !== saved.resumen || prefs.vista !== saved.vista;
  return (
    <>
      <div className="ed-h"><div><div className="ed-eyebrow">EmpresaDemo / Corporativo</div><h1>Tu espacio, a tu manera.</h1><div className="ed-sub">Identidad de demostración y preferencias del espacio. No contiene datos personales reales.</div></div></div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,3fr)", gap: 16, alignItems: "start" }} className="ed-perfil-cols">
        <div style={{ display: "grid", gap: 16 }}>
          <div className="ed-card"><h3>Perfil de demostración</h3><div className="ed-avatar" aria-hidden="true">AD</div><h2 className="serif" style={{ margin: "10px 0 2px", fontSize: 24 }}>{ED_PROFILE.alias}</h2>
            <div className="ed-mu">{ED_PROFILE.user}<br />{ED_PROFILE.org}</div><p><span className="ed-tag">Rol · {ED_PROFILE.role}</span></p><small className="ed-mu">Puede consultar clientes, revisar documentos y explorar reportes de muestra.</small></div>
          <div className="ed-note"><Info size={16} style={{ flex: "none", marginTop: 2 }} /><div><b>Sin datos sensibles</b>No se muestran correos reales, contraseñas, claves de acceso ni información personal.</div></div>
        </div>
        <div style={{ display: "grid", gap: 16 }}>
          <div className="ed-card"><div className="ed-h"><h3>Preferencias del espacio</h3><small className="ed-mu">Solo ilustrativas</small></div>
            <div className="ed-tw"><table><thead><tr><th>Preferencia</th><th>Valor de muestra</th></tr></thead><tbody>
              <tr><td>Idioma</td><td>Español</td></tr><tr><td>Zona horaria</td><td>UTC · Horas del entorno DEMO</td></tr>
              <tr><td><label htmlFor="p-res">Resumen del espacio</label></td><td><select id="p-res" className="ed-in" value={prefs.resumen} onChange={(e) => { setDone(false); setPrefs({ ...prefs, resumen: e.target.value }); }}><option>Semanal</option><option>Mensual</option></select></td></tr>
              <tr><td><label htmlFor="p-vis">Vista inicial</label></td><td><select id="p-vis" className="ed-in" value={prefs.vista} onChange={(e) => { setDone(false); setPrefs({ ...prefs, vista: e.target.value }); }}><option>Inicio</option><option>Documentos</option></select></td></tr>
            </tbody></table></div>
            <div className="ed-fbar" style={{ marginTop: 14, alignItems: "center" }}>
              <button className="ed-btn pri" disabled={!dirty} onClick={() => { setSaved(prefs); setDone(true); }}>Guardar preferencias</button>
              <button className="ed-btn" disabled={!dirty} onClick={() => setPrefs(saved)}>Restablecer</button>
              <small className="ed-mu">{done ? "Preferencias de muestra guardadas en esta sesión de demostración." : dirty ? "Tienes cambios sin guardar." : "Sin cambios: no hay nada que guardar."}</small>
            </div></div>
          <div className="ed-card"><div className="ed-h"><h3>Tu acceso actual</h3><small className="ed-mu">{ED_PROFILE.session}</small></div>
            <div className="ed-fbar" style={{ margin: "6px 0 10px" }}><span className="ed-tag">Sesión activa · DEMO</span><span className="ed-tag">Equipo de confianza</span></div>
            <p className="ed-mu">demo-equipo-01 · Inicio hoy a las 09:00 UTC. Esta tarjeta representa un acceso normal. No hay una sesión real asociada a la maqueta.</p>
            <button className="ed-btn" onClick={() => { edClear(); nav("/empresa-demo/login"); }}>Cerrar sesión de muestra</button></div>
        </div>
      </div>
    </>
  );
}
