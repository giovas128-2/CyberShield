import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bell,
  LayoutDashboard,
  Lock,
  Server,
  Settings,
  ShieldAlert,
} from "lucide-react";
import {
  getDashboard,
  getEvents,
  getIncidents,
  getServers,
  isNet,
  simulateEvent,
  updateIncidentStatus,
} from "../api/client";
import { MOCK_EVENTS, MOCK_INC } from "../data/mock";
import type { Incidente, Stats, User } from "../types";
import { Brand } from "../components/Brand";
import { AlertModal } from "../components/AlertModal";
import { Toast, type ToastData } from "../components/Toast";
import { DashboardView } from "../pages/DashboardView";
import { IncidentsView } from "../pages/IncidentsView";
import { ServersView } from "../pages/ServersView";
import { eventsPerMinute, hhmm } from "../utils/format";

export function Console({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [view, setView] = useState("dashboard");
  const [demo, setDemo] = useState(false);
  const [stats, setStats] = useState<Stats>({
    estado: "Sin amenazas críticas detectadas.",
    servidores: 0,
    eventos: 0,
    incidentes: 0,
    riesgo: 15,
  });
  const [lista, setLista] = useState(MOCK_EVENTS);
  const [incs, setIncs] = useState<Incidente[]>(MOCK_INC);
  const [selId, setSelId] = useState<string | null>(null);
  const [alertInc, setAlertInc] = useState<Incidente | null>(null);
  const [toast, setToast] = useState<ToastData | null>(null);
  const [updatedAt, setUpdatedAt] = useState(new Date());

  const load = useCallback(async () => {
    try {
      const [summary, events, incidents, servers] = await Promise.all([
        getDashboard(),
        getEvents(),
        getIncidents(),
        getServers().catch(() => null),
      ]);

      const activeIncidents = incidents.filter((i) => i.status !== "resolved").length;
      const realServerCount = servers
        ? servers.filter((server) => server.status === "online").length
        : summary.servidores;

      setStats({
        ...summary,
        servidores: realServerCount,
        incidentes: activeIncidents,
      });
      setLista(events);
      setIncs(incidents);
      setDemo(false);
      setUpdatedAt(new Date());
    } catch (err) {
      if (isNet(err)) {
        setDemo(true);
      } else {
        console.error("No se pudo actualizar CyberShield:", err);
      }
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 10000);
    return () => window.clearInterval(timer);
  }, [load]);

  const serie = useMemo(() => eventsPerMinute(lista), [lista]);

  const recentEvents = useMemo(
    () =>
      [...lista].sort((a, b) => {
        const aa = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const bb = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return bb - aa;
      }),
    [lista],
  );

  const changeStatus = async (
    incident: Incidente,
    status: "investigating" | "resolved",
  ): Promise<boolean> => {
    try {
      await updateIncidentStatus(incident.backendId, status);

      setIncs((current) =>
        current.map((item) =>
          item.backendId === incident.backendId
            ? {
                ...item,
                status,
                estado: status === "resolved" ? "Resuelto" : "Investigando",
              }
            : item,
        ),
      );

      setToast({
        kind: "ok",
        text:
          status === "resolved"
            ? "El incidente se ha marcado como Resuelto"
            : "El incidente se ha marcado como En investigación",
      });

      await load();
      return true;
    } catch (err) {
      console.error(`PATCH /incidents/${incident.backendId}/status falló:`, err);
      setToast({
        kind: "err",
        text:
          status === "resolved"
            ? "No se pudo resolver el incidente."
            : "No se pudo iniciar la investigación.",
      });
      return false;
    }
  };

  const simulate = async () => {
    let inc: Incidente;

    try {
      inc = await simulateEvent(user?.name);
      await load();
    } catch (err) {
      if (!isNet(err)) {
        console.error("POST /events/simulate falló:", err);
        setToast({ kind: "err", text: "No se pudo simular el evento." });
        return;
      }

      const nextId = Math.max(0, ...incs.map((i) => i.backendId || 0)) + 1;
      const now = new Date().toISOString();

      inc = {
        id: `INC-${String(nextId).padStart(3, "0")}`,
        backendId: nextId,
        eventType: "multiple_login_attempts",
        titulo: "Múltiples intentos de autenticación",
        resumen: "Número elevado de intentos de inicio de sesión en poco tiempo.",
        severidad: "ALTA",
        estado: "Pendiente",
        status: "open",
        origen: "192.168.1.50",
        servidor: "srv-cyber-01",
        servicio: "Autenticación",
        detectado: new Date().toLocaleString(),
        asignado: user?.name || "—",
        regla: "AUTH-FAIL-MVP",
        reco: "Validar la IP de origen, el usuario y el horario antes de tomar acciones.",
        investigationSteps: [
          "Identificar la IP de origen.",
          "Revisar el usuario afectado.",
          "Comprobar la cantidad de intentos y la ventana de tiempo.",
        ],
        resolutionCriteria:
          "La actividad fue validada como legítima o se aplicó una mitigación autorizada.",
      };

      setIncs((current) => [inc, ...current]);
      setLista((current) => [
        {
          id: Date.now(),
          fecha: hhmm(),
          createdAt: now,
          tipo: "Múltiples intentos de autenticación",
          origen: inc.origen,
          severidad: "ALTA",
          estado: "Detectado",
        },
        ...current,
      ]);
      setStats((current) => ({
        ...current,
        eventos: current.eventos + 1,
        incidentes: current.incidentes + 1,
        riesgo: Math.min(100, current.riesgo + 20),
        estado: "Incidente activo: revisa la actividad reciente.",
      }));
      setDemo(true);
    }

    setAlertInc(inc);
  };

  const abiertos = incs.filter((i) => i.status !== "resolved").length;
  const nav: [string, string, any][] = [
    ["dashboard", "Dashboard", LayoutDashboard],
    ["servers", "Servidores", Server],
    ["events", "Eventos", Activity],
    ["incidents", "Incidentes", ShieldAlert],
    ["security", "Seguridad", Lock],
    ["config", "Configuración", Settings],
  ];

  const data = {
    ...stats,
    demo,
    lista: recentEvents,
    serie,
  };

  return (
    <div className="shell">
      <aside className="side">
        <div style={{ padding: "0 8px 16px" }}><Brand /></div>
        {nav.map(([key, label, Icon]) => (
          <button
            key={key}
            className={`nav ${view === key ? "on" : ""}`}
            onClick={() => setView(key)}
          >
            <Icon size={16} />
            {label}
            {key === "incidents" && abiertos > 0 && <span className="bdg">{abiertos}</span>}
          </button>
        ))}

        <div className="agent">
          <span className="sv ok">● Infraestructura registrada</span>
          <div style={{ marginTop: 6 }}>
            {stats.servidores} servidor{stats.servidores === 1 ? "" : "es"} activo{stats.servidores === 1 ? "" : "s"}
          </div>
          <div className="mono">v0.1.0 / MVP</div>
        </div>
      </aside>

      <div>
        <header className="top">
          <span className="pill">● Sistema activo</span>
          <span className="sp" />
          <span className="mono mu" style={{ fontSize: 11 }}>
            ÚLTIMA ACTUALIZACIÓN {hhmm(updatedAt)}
          </span>
          <Bell size={18} color="#8a9bb0" />
          <div className="av">{(user?.name || "U").slice(0, 2).toUpperCase()}</div>
          <div style={{ lineHeight: 1.2 }}>
            {user?.name}
            <div className="mu" style={{ fontSize: 11 }}>Administrador</div>
          </div>
          <button className="lnk" style={{ color: "var(--mu)" }} onClick={onLogout}>Salir</button>
        </header>

        <main className="main">
          {view === "dashboard" && <DashboardView d={data} simulate={simulate} />}

          {view === "incidents" && (
            <IncidentsView
              list={incs}
              selId={selId}
              setSelId={setSelId}
              onInvestigate={(incident) => changeStatus(incident, "investigating")}
              onResolve={(incident) => changeStatus(incident, "resolved")}
            />
          )}

          {view === "servers" && <ServersView />}

          {!['dashboard', 'incidents', 'servers'].includes(view) && (
            <div className="card">
              <h2>{nav.find((item) => item[0] === view)?.[1]}</h2>
              <div className="mu">Próximamente. Esta sección aún no está disponible en el MVP.</div>
            </div>
          )}
        </main>
      </div>

      {alertInc && (
        <AlertModal
          inc={alertInc}
          onClose={() => setAlertInc(null)}
          onView={() => {
            setSelId(alertInc.id);
            setView("incidents");
            setAlertInc(null);
          }}
        />
      )}

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}
