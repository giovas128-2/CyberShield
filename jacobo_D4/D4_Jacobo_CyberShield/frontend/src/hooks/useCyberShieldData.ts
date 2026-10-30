import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
/* BACKEND_GISS: MOCK_MODE=true marca TODA la app como "DATOS SIMULADOS". Con backend real pon MOCK_MODE=false (o bórralo) y deja que `demo` solo se active si el backend no responde. */
const MOCK_MODE = true;
import type { EventStats, Evento, Incidente, NotificationItem, ServerItem, Stats, User } from "../types";
import type { ToastData } from "../components/Toast";
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

export function useCyberShieldData(user: User) {
  const [demo, setDemo] = useState(MOCK_MODE);
  const [stale, setStale] = useState(false);
  const hasRealData = useRef(false); // BACKEND_GISS: true cuando el backend respondió al menos una vez
  const [stats, setStats] = useState<Stats>(emptyStats);
  const [stats1s, setStats1s] = useState<EventStats | null>(null);
  const [stats60s, setStats60s] = useState<EventStats | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [lista, setLista] = useState<Evento[]>([]);
  const [incs, setIncs] = useState<Incidente[]>([]);
  const [servers, setServers] = useState<ServerItem[]>([]);
  const [selId, setSelId] = useState<string | null>(null);
  const [alertInc, setAlertInc] = useState<Incidente | null>(null);
  const [toast, setToast] = useState<ToastData | null>(null);
  const [updatedAt, setUpdatedAt] = useState(new Date());
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const events = await getEvents();
      setLista(events);
      hasRealData.current = true;
      setDemo(MOCK_MODE);
      setStale(false);
      setUpdatedAt(new Date());

      const [summary, incidents, serverList] = await Promise.all([
        getDashboard(),
        getIncidents(),
        getServers(),
      ]);

      const optional = await Promise.allSettled([
        getEventStats("1s"),
        getEventStats("60s"),
        getNotifications(),
      ]);
      const s1 = optional[0].status === "fulfilled" ? optional[0].value : null;
      const s60 = optional[1].status === "fulfilled" ? optional[1].value : null;
      const notifs = optional[2].status === "fulfilled" ? optional[2].value : [];

      const open = incidents.filter((i) => i.status !== "resolved");
      const online = serverList.filter((s) => s.status === "online").length;
      const offline = serverList.filter((s) => s.status === "offline").length;
      const critical = open.filter((i) => i.severidad === "CRITICAL").length;

      setStats({
        ...summary,
        servidores: serverList.length,
        servidoresOnline: online,
        servidoresOffline: offline,
        eventos: events.length,
        incidentes: open.length,
        criticos: critical,
        estado: critical > 0
          ? "Hay incidentes críticos abiertos que requieren revisión."
          : "Monitoreo activo sin incidentes críticos abiertos.",
      });
      setIncs(incidents);
      setServers(serverList);
      setStats1s(s1);
      setStats60s(s60);
      setNotifications(notifs);
      setLoading(false);
      hasRealData.current = true;
      setDemo(MOCK_MODE);
      setStale(false);
      setUpdatedAt(new Date());
    } catch (err) {
      setLoading(false);
      if (isNet(err)) {
        if (hasRealData.current) setStale(true);
        else setDemo(true);
      } else {
        console.error("No se pudo actualizar CyberShield:", err);
        setToast({ kind: "err", text: "No se pudo actualizar uno de los orígenes de datos." });
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

  const changeStatus = useCallback(async (incident: Incidente, status: "investigating" | "resolved"): Promise<boolean> => {
    try {
      await updateIncidentStatus(incident.backendId, status);
      setIncs((current) => current.map((item) => item.backendId === incident.backendId
        ? { ...item, status, estado: status === "resolved" ? "Resuelto" : "Investigando" }
        : item));
      setToast({ kind: "ok", text: status === "resolved" ? "Incidente marcado como Resuelto" : "Incidente marcado como En investigación" });
      await load();
      return true;
    } catch (err) {
      console.error(`No se pudo cambiar el estado del incidente ${incident.backendId}:`, err);
      setToast({ kind: "err", text: status === "resolved" ? "No se pudo resolver el incidente." : "No se pudo iniciar la investigación." });
      return false;
    }
  }, [load]);

  const simulate = useCallback(async () => {
    try {
      const inc = await simulateEvent(user?.name);
      await load();
      if (inc) setAlertInc(inc);
      setToast({ kind: "ok", text: "Evento HIGH simulado y registrado." });
    } catch (err) {
      console.error("No se pudo simular el evento:", err);
      setToast({ kind: "err", text: "No se pudo simular el evento." });
    }
  }, [load, user?.name]);

  const dashboardData = {
    ...stats,
    demo,
    stale,
    lista: recentEvents,
    serie,
    stats1s,
    stats60s,
    notifications,
  };

  return {
    loading,
    demo,
    stale,
    stats,
    stats1s,
    stats60s,
    notifications,
    events: recentEvents,
    incidents: incs,
    servers,
    selId,
    setSelId,
    alertInc,
    setAlertInc,
    toast,
    setToast,
    updatedAt,
    dashboardData,
    load,
    changeStatus,
    simulate,
  };
}

export type CyberShieldCtx = ReturnType<typeof useCyberShieldData>;
