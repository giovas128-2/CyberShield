import { NavLink } from "react-router-dom";
import { Activity, Bell, FlaskConical, LayoutDashboard, Lock, Server, Settings, ShieldAlert, ShieldCheck, Smartphone, User as UserIcon, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Brand } from "./Brand";

/* Navegación única de la consola. Se reutiliza para el sidebar y para el breadcrumb del topbar. */
export const NAV: { sec: string; items: [string, string, LucideIcon][] }[] = [
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

export interface SidebarStatus {
  stale: boolean; demo: boolean; online: number; offline: number; updatedAt: Date;
}

interface Props {
  openIncidents: number;
  notifications: number;
  status: SidebarStatus;
  open: boolean;            // solo aplica en pantallas angostas (drawer)
  onClose: () => void;
}

export function Sidebar({ openIncidents, notifications, status, open, onClose }: Props) {
  const label = status.stale ? "Sin conexión" : status.demo ? "DATOS SIMULADOS" : "Backend conectado";
  return (
    <>
      <aside className={`side ${open ? "open" : ""}`} aria-label="Navegación principal">
        <div className="side-brand"><Brand /></div>
        <nav>
          {NAV.map((group) => (
            <div key={group.sec}>
              <div className="sec">{group.sec}</div>
              {group.items.map(([path, text, Icon]) => (
                <NavLink key={path} to={path} className={({ isActive }) => `nav ${isActive ? "on" : ""}`} onClick={onClose}>
                  <Icon size={16} />{text}
                  {path === "/incidents" && openIncidents > 0 && <span className="bdg">{openIncidents}</span>}
                  {path === "/notifications" && notifications > 0 && <span className="bdg">{notifications}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="agent">
          <span className={`sv ${status.stale || status.demo ? "wn" : "ok"}`}>● {label}</span>
          <div style={{ marginTop: 6 }}>{status.online} online · {status.offline} offline</div>
          <div>Actualizado: {status.updatedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</div>
        </div>
      </aside>
      {open && <div className="scrim" onClick={onClose} aria-hidden="true" />}
    </>
  );
}
