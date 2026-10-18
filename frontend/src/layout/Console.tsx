import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, Bell, LayoutDashboard, Lock, Server, Settings, ShieldAlert } from "lucide-react";
import {
  getDashboard,
  getEventStats,
  getEvents,
  getIncidents,
  getNotifications,
  getServers,
  isNet,
  simulateEvent,
  updateIncidentStatus,
} from "../api/client";
import { MOCK_EVENTS, MOCK_INC } from "../data/mock";
import type { EventStats, Incidente, NotificationItem, Stats, User } from "../types";
import { Brand } from "../components/Brand";
import { AlertModal } from "../components/AlertModal";
import { Toast, type ToastData } from "../components/Toast";
import { DashboardView } from "../pages/DashboardView";
import { IncidentsView } from "../pages/IncidentsView";
import { ServersView } from "../pages/ServersView";
import { eventsPerMinute } from "../utils/format";

const emptyStats: Stats = {
  estado: "Monitoreo activo.",
  servidores: 0,
  servidoresOnline: 0,
  servidoresOffline: 0,
  eventos: 0,
  incidentes: 0,
  criticos: 0,
};

export function Console({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [view, setView] = useState("dashboard");
  const [demo, setDemo] = useState(false);
  const [stale, setStale] = useState(false);
  const hasRealData = useRef(false);
  const [stats, setStats] = useState<Stats>(emptyStats);
  const [stats1s, setStats1s] = useState<EventStats | null>(null);
  const [stats60s, setStats60s] = useState<EventStats | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [lista, setLista] = useState(MOCK_EVENTS);
  const [incs, setIncs] = useState<Incidente[]>(MOCK_INC);
  const [selId, setSelId] = useState<string | null>(null);
  const [alertInc, setAlertInc] = useState<Incidente | null>(null);
  const [toast, setToast] = useState<ToastData | null>(null);
  const [updatedAt, setUpdatedAt] = useState(new Date());

  const load = useCallback(async () => {
    try {
    // Primero cargamos eventos.
    // Así, aunque otro endpoint falle,
    // la actividad reciente sí aparece.
      const events = await getEvents();

      setLista(events);
      hasRealData.current = true;
      setDemo(false);
      setStale(false);
      setUpdatedAt(new Date());

    // Después cargamos el resto del dashboard.
      const [
        summary,
        incidents,
        servers,
        s1,
        s60,
        notifs,
      ] = await Promise.all([
        getDashboard(),
        getIncidents(),
        getServers(),
        getEventStats("1s"),
        getEventStats("60s"),
        getNotifications(),
      ]);

      const open = incidents.filter(
        (i) => i.status !== "resolved"
      );

      const online = servers.filter(
        (s) => s.status === "online"
      ).length;

      const offline = servers.filter(
        (s) => s.status === "offline"
      ).length;

      const critical = open.filter(
        (i) => i.severidad === "CRITICAL"
      ).length;

      setStats({
        ...summary,
        servidores: servers.length,
        servidoresOnline: online,
        servidoresOffline: offline,
        eventos: events.length,
        incidentes: open.length,
        criticos: critical,
        estado:
          critical > 0
            ? "Hay incidentes críticos abiertos que requieren revisión."
            : "Monitoreo activo sin incidentes críticos abiertos.",
      });

      setIncs(incidents);
      setStats1s(s1);
      setStats60s(s60);
      setNotifications(notifs);

      hasRealData.current = true;
      setDemo(false);
      setStale(false);
      setUpdatedAt(new Date());

    } catch (err) {
      if (isNet(err)) {
        if (hasRealData.current) {
          setStale(true);
        } else {
          setDemo(true);
        }
      } else {
        console.error(
          "No se pudo actualizar CyberShield:",
          err
        );

        setToast({
          kind: "err",
          text:
            "No se pudo actualizar uno de los endpoints del dashboard.",
        });
      }
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 5000);
    return () => window.clearInterval(timer);
  }, [load]);

  const serie = useMemo(() => eventsPerMinute(lista), [lista]);
  const recentEvents = useMemo(() => [...lista].sort((a, b) => {
    const aa = a.createdAt ? new Date(a.createdAt).getTime() : 0;
    const bb = b.createdAt ? new Date(b.createdAt).getTime() : 0;
    return bb - aa;
  }), [lista]);

  const changeStatus = async (incident: Incidente, status: "investigating" | "resolved"): Promise<boolean> => {
    try {
      await updateIncidentStatus(incident.backendId, status);
      setIncs((current) => current.map((item) => item.backendId === incident.backendId
        ? { ...item, status, estado: status === "resolved" ? "Resuelto" : "Investigando" }
        : item));
      setToast({ kind: "ok", text: status === "resolved" ? "Incidente marcado como Resuelto" : "Incidente marcado como En investigación" });
      await load();
      return true;
    } catch (err) {
      console.error(`PATCH /incidents/${incident.backendId}/status falló:`, err);
      setToast({ kind: "err", text: status === "resolved" ? "No se pudo resolver el incidente." : "No se pudo iniciar la investigación." });
      return false;
    }
  };

  const simulate = async () => {
    try {
      const inc = await simulateEvent(user?.name);
      await load();
      if (inc) setAlertInc(inc);
      setToast({ kind: "ok", text: "Evento HIGH simulado y registrado." });
    } catch (err) {
      console.error("POST /events/simulate falló:", err);
      setToast({ kind: "err", text: "No se pudo simular el evento." });
    }
  };

  const abiertos = incs.filter((i) => i.status !== "resolved").length;
  const nav: [string, string, any][] = [
    ["dashboard", "Dashboard", LayoutDashboard],
    ["servers", "Servidores", Server],
    ["events", "Eventos", Activity],
    ["incidents", "Incidentes", ShieldAlert],
    ["notifications", "Notificaciones", Bell],
    ["security", "Seguridad", Lock],
    ["config", "Configuración", Settings],
  ];

  const data = { ...stats, demo, stale, lista: recentEvents, serie, stats1s, stats60s, notifications };

  return (
    <div className="shell">
      <aside className="side">
        <div style={{ padding: "0 8px 16px" }}><Brand /></div>
        {nav.map(([key, label, Icon]) => (
          <button key={key} className={`nav ${view === key ? "on" : ""}`} onClick={() => setView(key)}>
            <Icon size={16} />{label}
            {key === "incidents" && abiertos > 0 && <span className="bdg">{abiertos}</span>}
            {key === "notifications" && notifications.length > 0 && <span className="bdg">{notifications.length}</span>}
          </button>
        ))}

        <div className="agent">
          <span className={`sv ${stale ? "wn" : demo ? "wn" : "ok"}`}>● {stale ? "Sin conexión" : demo ? "Datos simulados" : "Backend conectado"}</span>
          <div style={{ marginTop: 6 }}>{stats.servidoresOnline} online · {stats.servidoresOffline} offline</div>
          <div>Actualizado: {updatedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</div>
        </div>
      </aside>

      <div>
        <header className="top">
          <span className="pill">CyberShield</span><span className="sp" />
          <div className="av">{user?.name?.slice(0, 2).toUpperCase()}</div>
          <div style={{ lineHeight: 1.2 }}>{user?.name}<div className="mu" style={{ fontSize: 11 }}>Administrador</div></div>
          <button className="lnk" style={{ color: "var(--mu)" }} onClick={onLogout}>Salir</button>
        </header>

        <main className="main">
          {view === "dashboard" && <DashboardView d={data} simulate={simulate} />}
          {view === "incidents" && <IncidentsView list={incs} selId={selId} setSelId={setSelId} onInvestigate={(incident) => changeStatus(incident, "investigating")} onResolve={(incident) => changeStatus(incident, "resolved")} />}
          {view === "servers" && <ServersView />}
          {view === "notifications" && (
            <div className="card">
              <h2>Notificaciones</h2>
              <div className="notification-list">
                {notifications.map((n) => <div className="notification-row" key={n.id}><b>{n.message}</b><span className="mu">{n.status}</span></div>)}
                {!notifications.length && <div className="mu">No hay notificaciones registradas.</div>}
              </div>
            </div>
          )}
          {!['dashboard', 'incidents', 'servers', 'notifications'].includes(view) && (
            <div className="card"><h2>{nav.find((item) => item[0] === view)?.[1]}</h2><div className="mu">Próximamente. Esta sección aún no está disponible en el MVP.</div></div>
          )}
        </main>
      </div>

      {alertInc && <AlertModal inc={alertInc} onClose={() => setAlertInc(null)} onView={() => { setSelId(alertInc.id); setView("incidents"); setAlertInc(null); }} />}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}
