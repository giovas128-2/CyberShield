import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  Bell,
  FlaskConical,
  LayoutDashboard,
  Lock,
  Server,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Smartphone,
  User as UserIcon,
  Wrench,
} from "lucide-react";
import { Brand } from "../components/Brand";
import { AlertModal } from "../components/AlertModal";
import { Toast } from "../components/Toast";
import { useCyberShieldData } from "../hooks/useCyberShieldData";
import type { User } from "../types";
import type { LucideIcon } from "lucide-react";

const NAV: { sec: string; items: [string, string, LucideIcon][] }[] = [
  { sec: "OPERACIONES", items: [
    ["/dashboard", "Dashboard", LayoutDashboard],
    ["/servers", "Servidores", Server],
    ["/events", "Eventos", Activity],
    ["/incidents", "Incidentes", ShieldAlert],
    ["/notifications", "Notificaciones", Bell],
  ] },
  { sec: "GESTIÓN", items: [
    ["/devices", "Dispositivos", Smartphone],
    ["/sessions", "Sesiones", UserIcon],
    ["/actions", "Acciones", Wrench],
    ["/protections", "Protecciones", ShieldCheck],
    ["/lab", "Laboratorio", FlaskConical],
  ] },
  { sec: "SISTEMA", items: [
    ["/security", "Seguridad", Lock],
    ["/config", "Configuración", Settings],
  ] },
];

export function AppLayout({ user, onLogout }: { user: User; onLogout: () => void }) {
  const loc = useLocation();
  const nav = useNavigate();
  const ctx = useCyberShieldData(user);
  const abiertos = ctx.incidents.filter((i) => i.status !== "resolved").length;
  const current = NAV.flatMap((g) => g.items).find(([p]) => loc.pathname.startsWith(p));

  return (
    <div className="shell">
      <aside className="side">
        <div style={{ padding: "0 8px 12px" }}><Brand /></div>
        {NAV.map((group) => (
          <div key={group.sec}>
            <div className="sec">{group.sec}</div>
            {group.items.map(([path, label, Icon]) => (
              <NavLink key={path} to={path} className={({ isActive }) => `nav ${isActive ? "on" : ""}`}>
                <Icon size={16} />{label}
                {path === "/incidents" && abiertos > 0 && <span className="bdg">{abiertos}</span>}
                {path === "/notifications" && ctx.notifications.length > 0 && <span className="bdg">{ctx.notifications.length}</span>}
              </NavLink>
            ))}
          </div>
        ))}
        <div className="agent">
          <span className={`sv ${ctx.stale || ctx.demo ? "wn" : "ok"}`}>
            ● {ctx.stale ? "Sin conexión" : ctx.demo ? "Datos simulados" : "Backend conectado"}
          </span>
          <div style={{ marginTop: 6 }}>{ctx.stats.servidoresOnline} online · {ctx.stats.servidoresOffline} offline</div>
          <div>Actualizado: {ctx.updatedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</div>
        </div>
      </aside>

      <div>
        <header className="top">
          <span className="crumb">CyberShield <span>›</span> <b>{current?.[1] ?? "Detalle"}</b></span>
          <span className="sp" />
          <div className="av">{user?.name?.slice(0, 2).toUpperCase()}</div>
          <div style={{ lineHeight: 1.2 }}>{user?.name}<div className="mu" style={{ fontSize: 11 }}>Administrador</div></div>
          <button className="lnk" style={{ color: "var(--mu)" }} onClick={onLogout}>Salir</button>
        </header>
        <main className="main"><Outlet context={ctx} /></main>
      </div>

      {ctx.alertInc && (
        <AlertModal
          inc={ctx.alertInc}
          onClose={() => ctx.setAlertInc(null)}
          onView={() => {
            ctx.setSelId(ctx.alertInc!.id);
            nav("/incidents");
            ctx.setAlertInc(null);
          }}
        />
      )}
      <Toast toast={ctx.toast} onClose={() => ctx.setToast(null)} />
    </div>
  );
}
