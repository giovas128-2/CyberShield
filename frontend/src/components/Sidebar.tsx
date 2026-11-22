import { NavLink } from "react-router-dom";
import { Palette, BookOpen, ClipboardList, Activity, Bell, FlaskConical, LayoutDashboard, Server, Settings, ShieldAlert, ShieldCheck, Smartphone, User as UserIcon, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Brand } from "./Brand";
import { formatClock } from "../preferences/cybershieldPreferences";

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
    ["/catalog", "Catálogo", BookOpen],
    ["/protections", "Protecciones", ShieldCheck],
    ["/protection-proposals", "Propuestas", ClipboardList],
    ["/code-review", "Análisis de proyectos", ClipboardList],
    ["/lab", "Laboratorio", FlaskConical],
  ] },
  { sec: "SISTEMA", items: [
    ["/design-preview", "Prototipo UI", Palette],
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
          <div>Actualizado: {formatClock(status.updatedAt, true)}</div>
        </div>
      </aside>
      {open && <div className="scrim" onClick={onClose} aria-hidden="true" />}
    </>
  );
}
