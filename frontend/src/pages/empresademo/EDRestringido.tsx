import { Laptop } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { edClear, edGetDevice } from "../../empresademo/fixtures";

export default function EDRestringido() {
  const nav = useNavigate();
  const dev = edGetDevice();
  const [asked, setAsked] = useState(false);
  return (
    <>
      <div className="ed-h"><div><div className="ed-eyebrow">EmpresaDemo / Corporativo</div><h1>Vamos a revisar tu dispositivo.</h1><div className="ed-sub">Este dispositivo requiere una verificación adicional antes de continuar.</div></div></div>
      <div className="ed-card ed-center" style={{ padding: 40, maxWidth: "none" }}>
        <div className="ed-avatar" style={{ background: "#efe6d3", color: "var(--ed-mu)" }}><Laptop size={30} strokeWidth={1.3} /></div>
        <span className="ed-tag">Verificación requerida</span>
        <h2 className="serif">Este equipo aún no está autorizado.</h2>
        <p className="ed-mu" style={{ maxWidth: 520, margin: 0 }}>Para continuar con tus clientes, documentos y reportes, utiliza un dispositivo de confianza o solicita una revisión al equipo responsable de tu organización.</p>
        <div style={{ background: "#faf8f3", borderRadius: 12, padding: "12px 20px", display: "flex", gap: 40, textAlign: "left" }}>
          <div><small className="ed-mu">DISPOSITIVO DE MUESTRA</small><div><b>{dev ? `${dev.name} · ${dev.id}` : "demo-equipo-06 · DV-006"}</b></div></div>
          <div><small className="ed-mu">ESTADO</small><div className="ed-err">Verificación pendiente</div></div>
        </div>
        <div className="ed-fbar" style={{ justifyContent: "center" }}>
          <button className="ed-btn pri" disabled={asked} onClick={() => setAsked(true)}>{asked ? "Solicitud registrada" : "Solicitar revisión"}</button>
          <button className="ed-btn" onClick={() => { edClear(); nav("/empresa-demo/login"); }}>Volver al acceso</button>
        </div>
        <small className="ed-foot-note">{asked ? "Solicitud registrada en esta demostración. El acceso permanece restringido hasta completar la verificación." : "La solicitud no autoriza el equipo automáticamente."}</small>
      </div>
      <div className="ed-split">
        <div className="ed-card"><h3>¿Qué puede hacer?</h3><p className="ed-mu" style={{ margin: 0 }}>Utilice un dispositivo corporativo reconocido o solicite una revisión. No es necesario intentar iniciar sesión repetidamente.</p></div>
        <div className="ed-card"><h3>Protección de la información</h3><p className="ed-mu" style={{ margin: 0 }}>Mientras la verificación está pendiente no se muestran documentos, datos de clientes ni reportes. Contacte a soporte interno si necesita ayuda.</p></div>
      </div>
    </>
  );
}
