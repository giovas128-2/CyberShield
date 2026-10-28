import { ArrowRight, Building2, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { AuthShell } from "../components/AuthShell";

export default function PortalChoicePage() {
  const nav = useNavigate();

  return (
    <AuthShell>
      <section className="portal-choice" aria-labelledby="portal-title">
        <div className="eyebrow">Selecciona tu espacio</div>
        <h2 id="portal-title">¿Dónde quieres iniciar sesión?</h2>
        <p className="mu portal-choice-intro">
          CyberShield es la consola de seguridad. EmpresaDemo representa la aplicación empresarial ficticia protegida durante la demostración.
        </p>

        <div className="portal-choice-grid">
          <button className="portal-card" type="button" onClick={() => nav("/login/cybershield")}>
            <span className="portal-card-icon"><ShieldCheck size={24} /></span>
            <span className="portal-card-copy">
              <b>CyberShield</b>
              <small>Consola de monitoreo, incidentes, MITRE y respuesta.</small>
              <span className="portal-card-action">Iniciar sesión en CyberShield <ArrowRight size={15} /></span>
            </span>
          </button>

          <button className="portal-card portal-card-company" type="button" onClick={() => nav("/empresa-demo/login")}>
            <span className="portal-card-icon"><Building2 size={24} /></span>
            <span className="portal-card-copy">
              <b>EmpresaDemo</b>
              <small>Aplicación empresarial ficticia con clientes, documentos y reportes.</small>
              <span className="portal-card-action">Entrar a EmpresaDemo <ArrowRight size={15} /></span>
            </span>
          </button>
        </div>

        <div className="note portal-choice-note">
          EmpresaDemo utiliza únicamente datos ficticios y acceso de demostración. No solicita credenciales reales.
        </div>
      </section>
    </AuthShell>
  );
}
