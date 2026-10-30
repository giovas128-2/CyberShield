import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { BarChart3, FileText, Home, Layers, Menu, UserCircle, Users } from "lucide-react";
import "./empresademo.css";
import { ED_ORIGIN, ED_PROFILE, edClear, edGetDevice } from "./fixtures";

const NAV = [
  ["/empresa-demo/inicio", "Inicio", Home], ["/empresa-demo/clientes", "Clientes", Users], ["/empresa-demo/documentos", "Documentos", FileText],
  ["/empresa-demo/reportes", "Reportes", BarChart3], ["/empresa-demo/perfil", "Mi perfil", UserCircle],
] as const;

export const EDBrand = () => <div className="ed-brand"><Layers size={22} />EmpresaDemo</div>;

/* Shell de EmpresaDemo. Es la app ficticia protegida; no comparte layout ni estilos con la consola CyberShield. */
export function EmpresaDemoLayout() {
  const dev = edGetDevice();
  const loc = useLocation();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [loc.pathname]);

  if (!dev) return <Navigate to="/empresa-demo/login" replace />;
  // Un equipo no confiable solo puede ver la pantalla de acceso restringido (nunca documentos, clientes ni reportes).
  if (!dev.trusted && !loc.pathname.endsWith("/acceso-restringido")) return <Navigate to="/empresa-demo/acceso-restringido" replace />;
  const restricted = !dev.trusted;

  return (
    <div className="ed">
      <div className="ed-shell">
        <aside className={`ed-side ${open ? "open" : ""}`} aria-label="Navegación de EmpresaDemo">
          <EDBrand />
          <div className="ed-ws">ESPACIO DEMO<b>{ED_PROFILE.org}</b></div>
          {NAV.map(([to, label, Icon]) => restricted
            ? <span key={to} className="ed-nav" aria-disabled="true" style={{ opacity: .45 }}><Icon size={16} />{label}</span>
            : <NavLink key={to} to={to} className={({ isActive }) => `ed-nav ${isActive ? "on" : ""}`}><Icon size={16} />{label}</NavLink>)}
          <div className="ed-foot">
            <span className="ed-tag">DEMO · datos ficticios</span>
            <div style={{ marginTop: 8 }}>Un espacio sin datos personales reales.</div>
            <div>AD · {ED_PROFILE.alias}</div>
            <button className="ed-btn" style={{ marginTop: 10, minHeight: 36 }} onClick={() => { edClear(); nav("/login"); }}>Salir de la demo</button>
          </div>
        </aside>
        {open && <div className="ed-scrim" onClick={() => setOpen(false)} aria-hidden="true" />}
        <div className="ed-body">
          <header className="ed-top">
            <button className="ed-menu" onClick={() => setOpen(true)} aria-label="Abrir menú"><Menu size={20} /></button>
            <span>Mi organización / Espacio de trabajo</span><span className="sp" />
            <span className="ed-origin">{ED_ORIGIN}</span>
          </header>
          <main className="ed-main"><Outlet /></main>
        </div>
      </div>
    </div>
  );
}
