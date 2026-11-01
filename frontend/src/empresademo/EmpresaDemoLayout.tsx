import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import { Bell, Building2, Files, HelpCircle, LayoutGrid, Menu, SlidersHorizontal, TrendingUp, UserCircle, Users } from "lucide-react";
import "./empresademo.css";
import { edGetDevice } from "./fixtures";
import { ED_FOOT_DATE, ED_USER } from "./data";
import { IncidentProvider } from "./IncidentContext";
import { LockdownOverlay, SimPanel } from "./IncidentUI";

const NAV = [
  ["/empresa-demo/inicio", "Resumen", LayoutGrid], ["/empresa-demo/clientes", "Clientes", Users], ["/empresa-demo/documentos", "Documentos", Files],
  ["/empresa-demo/reportes", "Reportes", TrendingUp], ["/empresa-demo/perfil", "Perfil y sesiones", UserCircle], ["/empresa-demo/administracion", "Administración", SlidersHorizontal],
] as const;
const CRUMB: Record<string, string> = { inicio: "Resumen", clientes: "Clientes", documentos: "Documentos", reportes: "Reportes", perfil: "Perfil y sesiones", administracion: "Administración", "acceso-restringido": "Acceso restringido" };

export const EDBrand = () => <div className="ed-brand"><Building2 size={22} />EmpresaDemo</div>;

/** Shell de la aplicación empresarial ficticia. La comunicación visible es operacional, no técnica. */
export function EmpresaDemoLayout() {
  const dev = edGetDevice();
  const loc = useLocation();
  if (!dev) return <Navigate to="/empresa-demo/login" replace />;
  if (!dev.trusted && !loc.pathname.endsWith("/acceso-restringido")) return <Navigate to="/empresa-demo/acceso-restringido" replace />;
  return <IncidentProvider><Shell restricted={!dev.trusted} /></IncidentProvider>;
}

function Shell({ restricted }: { restricted: boolean }) {
  const loc = useLocation();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [loc.pathname]);
  const seg = loc.pathname.split("/").pop() ?? "";
  const me = ED_USER;

  return (
    <div className="ed">
      <div className="ed-shell">
        <aside className={`ed-side ${open ? "open" : ""}`} aria-label="Navegación de EmpresaDemo">
          <EDBrand />
          <div className="ed-ws"><span>ENTORNO DE DEMOSTRACIÓN</span><b>Portal del empleado</b></div>
          {NAV.map(([to, label, Icon]) => restricted
            ? <span key={to} className="ed-nav" aria-disabled="true" style={{ opacity: .45 }}><Icon size={16} />{label}</span>
            : <NavLink key={to} to={to} className={({ isActive }) => `ed-nav ${isActive ? "on" : ""}`}><Icon size={16} />{label}</NavLink>)}
          <div className="ed-side-foot">
            <div>¿Necesita ayuda?<b>Contacte al equipo de soporte interno.</b></div>
            <div className="ed-help"><HelpCircle size={14} />Guía de uso</div>
            <div className="ed-user"><span className="av" aria-hidden="true">{me.initials}</span><div><b>{me.name}</b>{me.role}</div></div>
          </div>
        </aside>
        {open && <div className="ed-scrim" onClick={() => setOpen(false)} aria-hidden="true" />}
        <div className="ed-body">
          <header className="ed-top">
            <button className="ed-menu" onClick={() => setOpen(true)} aria-label="Abrir menú"><Menu size={20} /></button>
            <span>EmpresaDemo&nbsp; / &nbsp;{CRUMB[seg] ?? "Resumen"}</span><span className="sp" />
            <span className="ed-chip">Datos de muestra</span>
            <span>{ED_FOOT_DATE}</span>
            <Bell size={16} aria-label="Notificaciones" />
          </header>
          <main className="ed-main">
            <Outlet />
            <div className="ed-pagefoot"><span>EmpresaDemo · Portal de operaciones</span><span>Entorno académico · datos ficticios</span></div>
          </main>
        </div>
      </div>
      <LockdownOverlay />
      <SimPanel />
    </div>
  );
}
