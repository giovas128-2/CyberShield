
import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bell,
  CheckCircle2,
  Clock3,
  Crosshair,
  FileSearch,
  Monitor,
  Radio,
  Server,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  TrendingUp,
  WifiOff,
  Zap,
} from "lucide-react";

import type {
  Evento,
  Incidente,
  Scope,
  Severidad,
  ServerItem,
} from "../types";

import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import { SeverityBadge } from "../components/SeverityBadge";
import { SimBanner } from "../components/SimBanner";
import "../styles/dashboard-soc.css";

const ATTACK_LEVELS: Severidad[] = ["HIGH", "CRITICAL"];

const scopeClass: Record<Scope, string> = {
  BLOCKED: "ok",
  REACHED: "wn",
  IMPACT: "er",
};

const bySeverity = (severity: Severidad) =>
  severity === "CRITICAL"
    ? 3
    : severity === "HIGH"
      ? 2
      : severity === "WARNING"
        ? 1
        : 0;

const isHigh = (severity: Severidad) =>
  ATTACK_LEVELS.includes(severity);

const pretty = (value: string) =>
  value.replaceAll("_", " ");

const sourceLabel = (value?: string | null) =>
  value && value !== "—" && value !== "null"
    ? value
    : "No identificado";

const number = (value: number) =>
  new Intl.NumberFormat("es-MX").format(value);

function validTime(raw?: string | null): number | null {
  if (!raw) return null;

  const timestamp = Date.parse(raw);

  return Number.isFinite(timestamp) ? timestamp : null;
}

function last24Hours(events: Evento[]) {
  const until = Date.now();
  const start = until - 24 * 60 * 60 * 1000;

  const bins = Array.from({ length: 24 }, () => 0);

  const valid = events.filter((event) => {
    const timestamp = validTime(event.createdAt);

    if (
      timestamp === null ||
      timestamp < start ||
      timestamp > until
    ) {
      return false;
    }

    const slot = Math.min(
      23,
      Math.floor((timestamp - start) / 3600000),
    );

    bins[slot] += 1;

    return true;
  });

  const labels = Array.from({ length: 24 }, (_, index) => {
    const date = new Date(start + (index + 1) * 3600000);

    return date.toLocaleTimeString("es-MX", {
      hour: "2-digit",
      minute: "2-digit",
    });
  });

  return { events: valid, bins, labels };
}

function ActivityChart({
  data,
  labels,
}: {
  data: number[];
  labels: string[];
}) {
  const width = 900;
  const height = 190;
  const padTop = 14;
  const padBottom = 29;
  const chartH = height - padTop - padBottom;

  const ceiling = Math.max(1, ...data);

  const points = data.map((value, index) => {
    const x =
      (index / Math.max(1, data.length - 1)) * width;

    const y =
      padTop + chartH - (value / ceiling) * chartH;

    return [x, y] as const;
  });

  const line = points
    .map(
      ([x, y], index) =>
        `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`,
    )
    .join(" ");

  const area = `${line} L${width},${height - padBottom} L0,${
    height - padBottom
  } Z`;

  const ticks = [0, 6, 12, 18, 23];

  return (
    <div className="soc-chart-wrap">
      <svg
        className="soc-chart"
        role="img"
        aria-label="Histórico de eventos registrados en las últimas 24 horas"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient
            id="soc-activity-grad"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop
              offset="0%"
              stopColor="#53dbee"
              stopOpacity=".31"
            />
            <stop
              offset="100%"
              stopColor="#53dbee"
              stopOpacity=".02"
            />
          </linearGradient>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
          const y = padTop + tick * chartH;

          return (
            <line
              key={tick}
              x1={0}
              x2={width}
              y1={y}
              y2={y}
              stroke="var(--bd)"
              strokeDasharray="5 6"
              strokeWidth="1"
            />
          );
        })}

        <path d={area} fill="url(#soc-activity-grad)" />

        <path
          d={line}
          fill="none"
          stroke="var(--ac)"
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />

        {ticks.map((index) => (
          <text
            key={index}
            x={(index / 23) * width}
            y={height - 5}
            textAnchor={
              index === 0
                ? "start"
                : index === 23
                  ? "end"
                  : "middle"
            }
            fill="var(--mu)"
            fontSize="14"
          >
            {labels[index]}
          </text>
        ))}
      </svg>
    </div>
  );
}

function StatusPill({
  label,
  tone = "cyan",
}: {
  label: string;
  tone?: "red" | "amber" | "green" | "cyan";
}) {
  return (
    <span className={`soc-pill soc-${tone}`}>
      {label}
    </span>
  );
}

function Kpi({
  icon: Icon,
  label,
  value,
  detail,
  tone = "cyan",
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  detail: string;
  tone?: "red" | "amber" | "green" | "cyan";
}) {
  return (
    <div className={`soc-kpi soc-kpi-${tone}`}>
      <div className="soc-kpi-head">
        <Icon size={22} />
        <span>{label}</span>
      </div>

      <div className="soc-kpi-num">{value}</div>

      <div className="soc-kpi-foot">{detail}</div>
    </div>
  );
}

function CardHead({
  icon: Icon,
  title,
  extra,
  onExtra,
}: {
  icon: typeof Activity;
  title: string;
  extra?: string;
  onExtra?: () => void;
}) {
  return (
    <div className="soc-card-head">
      <h2>
        <Icon size={19} />
        {title}
      </h2>

      {extra &&
        (onExtra ? (
          <button
            className="soc-textlink"
            type="button"
            onClick={onExtra}
          >
            {extra}
            <ArrowRight size={14} />
          </button>
        ) : (
          <span className="soc-muted soc-card-meta">
            {extra}
          </span>
        ))}
    </div>
  );
}

function incidentStatus(incident: Incidente) {
  if (incident.status === "resolved") {
    return {
      text: "RESUELTO",
      tone: "green" as const,
    };
  }

  if (incident.status === "investigating") {
    return {
      text: "EN INVESTIGACIÓN",
      tone: "amber" as const,
    };
  }

  if (incident.status === "escalated") {
    return {
      text: "ESCALADO",
      tone: "red" as const,
    };
  }

  return {
    text: "PENDIENTE",
    tone: "red" as const,
  };
}

function Hero({
  incident,
  isActive,
  onOpen,
  onEvidence,
  demo,
}: {
  incident?: Incidente;
  isActive: boolean;
  onOpen: (id: number) => void;
  onEvidence: (id: number) => void;
  demo: boolean;
}) {
  if (!incident) {
    return (
      <section className="soc-hero soc-hero-safe">
        <div className="soc-hero-mark">
          <ShieldCheck size={31} />
        </div>

        <div className="soc-hero-main">
          <div className="soc-hero-title">
            Sin incidentes de severidad alta registrados
          </div>

          <p>
            No hay incidentes HIGH o CRITICAL en los
            datos disponibles. Consulta Eventos para
            revisar toda la actividad.
          </p>

          <div className="soc-hero-sub">
            {demo
              ? "Modo de demostración: los datos no representan un entorno real."
              : "El monitoreo continúa activo."}
          </div>
        </div>
      </section>
    );
  }

  const status = incidentStatus(incident);

  const contained =
    incident.status === "resolved" &&
    ["executed", "rolled_back"].includes(
      incident.responseAction?.status ?? "",
    );

  const label = isActive
    ? "ALERTA DE SEGURIDAD ACTIVA"
    : contained
      ? "ÚLTIMO INCIDENTE CONTENIDO"
      : "ÚLTIMO INCIDENTE RESUELTO";

  return (
    <section
      className={`soc-hero ${
        isActive ? "soc-hero-alert" : "soc-hero-contained"
      }`}
    >
      <div className="soc-hero-mark">
        {isActive ? (
          <AlertTriangle size={36} />
        ) : (
          <ShieldCheck size={36} />
        )}
      </div>

      <div className="soc-hero-main">
        <div className="soc-hero-title">{label}</div>

        <p>
          {isActive
            ? "Incidente detectado que requiere revisión del equipo de seguridad."
            : "Este incidente ya está cerrado. Se muestra como referencia del último caso relevante."}
        </p>

        <div className="soc-hero-facts">
          <div>
            <small>Tipo de alerta</small>
            <b>
              <Crosshair size={17} />
              {pretty(incident.eventType ?? incident.titulo)}
            </b>
          </div>

          <div>
            <small>Origen / IP registrada</small>
            <b>
              <Monitor size={16} />
              {sourceLabel(incident.origen)}
            </b>
          </div>

          <div>
            <small>Servidor afectado</small>
            <b>
              <Server size={16} />
              {incident.servidor || "No especificado"}
            </b>
          </div>

          <div>
            <small>Severidad</small>
            <SeverityBadge value={incident.severidad} />
          </div>

          <div>
            <small>Estado</small>
            <StatusPill
              label={status.text}
              tone={status.tone}
            />
          </div>

          <div>
            <small>Incidente</small>
            <b className="soc-mono">
              #{incident.backendId}
            </b>
          </div>
        </div>
      </div>

      <div className="soc-hero-buttons">
        <button
          type="button"
          className="soc-action-primary"
          onClick={() => onOpen(incident.backendId)}
        >
          Ver incidente
          <ArrowRight size={17} />
        </button>

        <button
          type="button"
          className="soc-action-secondary"
          onClick={() => onEvidence(incident.backendId)}
        >
          <FileSearch size={17} />
          Ver evidencia
        </button>
      </div>
    </section>
  );
}

function TopTypes({ events }: { events: Evento[] }) {
  const totals = new Map<string, number>();

  events
    .filter((event) => isHigh(event.severidad))
    .forEach((event) => {
      totals.set(
        event.tipo,
        (totals.get(event.tipo) ?? 0) + 1,
      );
    });

  const top = [...totals.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const total = [...totals.values()].reduce(
    (a, b) => a + b,
    0,
  );

  return (
    <section className="soc-panel">
      <CardHead
        icon={Crosshair}
        title="Principales tipos de alerta"
        extra="Alta severidad · 24 h"
      />

      <div className="soc-bars">
        {top.map(([name, count]) => (
          <div key={name} className="soc-bar-row">
            <span title={name}>{pretty(name)}</span>

            <div className="soc-track">
              <i
                style={{
                  width: `${
                    total ? (count / total) * 100 : 0
                  }%`,
                }}
              />
            </div>

            <strong>{number(count)}</strong>
          </div>
        ))}

        {!top.length && (
          <div className="soc-empty">
            Sin eventos HIGH o CRITICAL en las últimas
            24 horas.
          </div>
        )}
      </div>
    </section>
  );
}

function IncidentList({
  incidents,
  onOpen,
}: {
  incidents: Incidente[];
  onOpen: (id: number) => void;
}) {
  return (
    <section className="soc-panel">
      <CardHead
        icon={Zap}
        title="Incidentes relevantes"
        extra="Ver todos"
        onExtra={() => onOpen(-1)}
      />

      <div className="soc-list">
        {incidents.slice(0, 4).map((incident) => {
          const status = incidentStatus(incident);

          return (
            <button
              className="soc-incident"
              type="button"
              key={incident.id}
              onClick={() => onOpen(incident.backendId)}
            >
              <SeverityBadge value={incident.severidad} />

              <span className="soc-incident-main">
                <strong>
                  {pretty(
                    incident.eventType ?? incident.titulo,
                  )}
                </strong>

                <small>
                  Incidente #{incident.backendId} ·{" "}
                  {sourceLabel(incident.origen)} ·{" "}
                  {incident.servidor}
                </small>
              </span>

              <StatusPill
                label={status.text}
                tone={status.tone}
              />
            </button>
          );
        })}

        {!incidents.length && (
          <div className="soc-empty">
            No hay incidentes de severidad alta registrados.
          </div>
        )}
      </div>
    </section>
  );
}

function AffectedAssets({
  incidents,
  servers,
  onOpen,
}: {
  incidents: Incidente[];
  servers: ServerItem[];
  onOpen: () => void;
}) {
  const active = incidents.filter(
    (incident) =>
      incident.status !== "resolved" &&
      isHigh(incident.severidad),
  );

  const riskyNames = new Set(
    active.map((incident) => incident.servidor),
  );

  return (
    <section className="soc-panel">
      <CardHead
        icon={Server}
        title="Activos monitoreados"
        extra="Ver servidores"
        onExtra={onOpen}
      />

      <div className="soc-assets">
        {servers.slice(0, 5).map((server) => {
          const risky =
            riskyNames.has(server.name) ||
            riskyNames.has(`Servidor #${server.id}`);

          const tone =
            server.status === "offline"
              ? "red"
              : risky
                ? "amber"
                : server.status === "online"
                  ? "green"
                  : "cyan";

          const label =
            server.status === "offline"
              ? "OFFLINE"
              : risky
                ? "CON ALERTAS"
                : server.status === "online"
                  ? "ONLINE"
                  : "REGISTRADO";

          return (
            <div className="soc-asset" key={server.id}>
              <Server size={16} />

              <span title={server.name}>
                <b>
                  {server.name ||
                    `Servidor #${server.id}`}
                </b>

                <small>{server.ipAddress}</small>
              </span>

              <StatusPill tone={tone} label={label} />
            </div>
          );
        })}

        {!servers.length && (
          <div className="soc-empty">
            No hay servidores registrados.
          </div>
        )}
      </div>

      <p className="soc-footnote">
        El estado online/offline proviene del registro
        de servidores; no equivale a una evaluación
        de riesgo.
      </p>
    </section>
  );
}

function TopOrigins({
  events,
  onOpen,
}: {
  events: Evento[];
  onOpen: () => void;
}) {
  const totals = new Map<string, number>();

  events
    .filter((event) => isHigh(event.severidad))
    .forEach((event) => {
      const key = sourceLabel(event.origen);

      totals.set(key, (totals.get(key) ?? 0) + 1);
    });

  const rows = [...totals.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <section className="soc-panel">
      <CardHead
        icon={Monitor}
        title="Principales orígenes"
        extra="Ver eventos"
        onExtra={onOpen}
      />

      <div className="soc-sources">
        {rows.map(([source, count]) => (
          <div className="soc-source" key={source}>
            <span title={source}>
              <Monitor size={15} />
              {source}
            </span>

            <b>{number(count)}</b>
          </div>
        ))}

        {!rows.length && (
          <div className="soc-empty">
            Sin IP de origen asociadas a alertas altas
            en 24 h.
          </div>
        )}
      </div>

      <p className="soc-footnote">
        Origen = IP reportada, no identidad confirmada
        del atacante.
      </p>
    </section>
  );
}

export function DashboardView({
  ctx,
}: {
  ctx: CyberShieldCtx;
}) {
  const nav = useNavigate();

  const events = ctx.events;
  const incidents = ctx.incidents;
  const servers = ctx.servers;
  const modeDemo = ctx.demo;

  const openIncidents = incidents.filter(
    (incident) => incident.status !== "resolved",
  );

  const highOpen = openIncidents.filter(
    (incident) => isHigh(incident.severidad),
  );

  const criticalOpen = openIncidents.filter(
    (incident) => incident.severidad === "CRITICAL",
  );

  const relevant = incidents.filter(
    (incident) => isHigh(incident.severidad),
  );

  const sorted = [...relevant].sort(
    (a, b) =>
      bySeverity(b.severidad) -
      bySeverity(a.severidad),
  );

  const focus =
    sorted.find(
      (incident) => incident.status !== "resolved",
    ) ??
    relevant.find(
      (incident) => incident.status === "resolved",
    );

  const openFocus = Boolean(
    focus && focus.status !== "resolved",
  );

  const contained = incidents.filter(
    (incident) =>
      incident.status === "resolved" &&
      ["executed", "rolled_back"].includes(
        incident.responseAction?.status ?? "",
      ),
  ).length;

  const { events: recent24h, bins, labels } = useMemo(
    () => last24Hours(events),
    [events],
  );

  const recentHighEvents = recent24h.filter(
    (event) => isHigh(event.severidad),
  );

  const scoped = {
    BLOCKED: 0,
    REACHED: 0,
    IMPACT: 0,
  };

  recent24h.forEach((event) => {
    if (event.scope) {
      scoped[event.scope]++;
    }
  });

  const knownScoped =
    scoped.BLOCKED +
    scoped.REACHED +
    scoped.IMPACT;

  const displayedIncidents = [
    ...highOpen,
    ...relevant.filter(
      (incident) => incident.status === "resolved",
    ),
  ];

  const goIncident = (id: number) => {
    nav(
      id < 0
        ? "/incidents"
        : `/incidents/${id}`,
    );
  };

  return (
    <div className="soc-dashboard">

      {/* ENCABEZADO SIN BOTÓN DE SIMULACIÓN */}
      <div className="soc-heading">
        <div>
          <h1>Dashboard</h1>
          <p>
            Vista operativa de amenazas, incidentes
            y respuestas defensivas.
          </p>
        </div>
      </div>

      {/* ESTADO DE CONEXIÓN */}
      <SimBanner
        demo={modeDemo}
        stale={ctx.stale}
      />

      {ctx.stale && (
        <div className="soc-stale">
          <WifiOff size={17} />
          Los datos pueden estar desactualizados:
          se perdió la conexión con el backend.
        </div>
      )}

      {/* ALERTA PRINCIPAL */}
      <Hero
        incident={focus}
        isActive={openFocus}
        onOpen={goIncident}
        onEvidence={(id) =>
          nav(`/incidents/${id}/evidence`)
        }
        demo={modeDemo}
      />

      {/* INDICADORES PRINCIPALES */}
      <section
        className="soc-kpis"
        aria-label="Resumen de seguridad"
      >
        <Kpi
          icon={Crosshair}
          label="Alertas altas abiertas"
          value={highOpen.length}
          detail="HIGH y CRITICAL sin resolver"
          tone={highOpen.length ? "red" : "green"}
        />

        <Kpi
          icon={ShieldAlert}
          label="Incidentes abiertos"
          value={openIncidents.length}
          detail="Todos los niveles de severidad"
        />

        <Kpi
          icon={AlertTriangle}
          label="Críticos abiertos"
          value={criticalOpen.length}
          detail="Requieren priorización"
          tone={criticalOpen.length ? "red" : "green"}
        />

        <Kpi
          icon={ShieldCheck}
          label="Incidentes contenidos"
          value={contained}
          detail="Resueltos con respuesta registrada"
          tone="green"
        />

        <Kpi
          icon={ShieldX}
          label="Servidores offline"
          value={
            servers.filter(
              (server) => server.status === "offline",
            ).length
          }
          detail={`De ${servers.length} servidores registrados`}
          tone="amber"
        />
      </section>

      {/* ANALÍTICA Y GRÁFICAS */}
      <div className="soc-analytics">
        <section className="soc-panel soc-activity">
          <CardHead
            icon={Activity}
            title="Actividad de eventos"
            extra="Últimas 24 h · registros cargados"
          />

          <div className="soc-activity-stats">
            <div className="soc-total">
              <strong>{number(recent24h.length)}</strong>
              <span>eventos registrados</span>
            </div>

            <div className="soc-scope-summary">
              {(
                ["BLOCKED", "REACHED", "IMPACT"] as Scope[]
              ).map((scope) => (
                <div
                  key={scope}
                  className={`soc-scope soc-scope-${scope.toLowerCase()}`}
                >
                  <b>{scope}</b>

                  <span>
                    {number(scoped[scope])}{" "}
                    {knownScoped
                      ? `(${Math.round(
                          (scoped[scope] / knownScoped) *
                            100,
                        )}%)`
                      : ""}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <ActivityChart
            data={bins}
            labels={labels}
          />

          <p className="soc-footnote">
            Eventos recibidos del backend con fecha
            válida. BLOCKED / REACHED / IMPACT
            describen alcance, no confirman por sí
            solos un ataque.
          </p>
        </section>

        <TopTypes events={recent24h} />
      </div>

      {/* INFORMACIÓN OPERATIVA */}
      <div className="soc-operations">
        <IncidentList
          incidents={displayedIncidents}
          onOpen={goIncident}
        />

        <AffectedAssets
          incidents={incidents}
          servers={servers}
          onOpen={() => nav("/servers")}
        />

        <TopOrigins
          events={recent24h}
          onOpen={() => nav("/events")}
        />
      </div>

      {/* TABLA DE EVENTOS */}
      <section className="soc-panel soc-eventpanel">
        <CardHead
          icon={Clock3}
          title="Eventos recientes"
          extra="Ver todos los eventos"
          onExtra={() => nav("/events")}
        />

        <div className="soc-tablewrap">
          <table className="soc-eventtable">
            <thead>
              <tr>
                <th>Hora</th>
                <th>Tipo</th>
                <th>Origen / IP</th>
                <th>Servidor</th>
                <th>Severidad</th>
                <th>Scope</th>
                <th>Estado</th>
              </tr>
            </thead>

            <tbody>
              {events.slice(0, 7).map((event) => (
                <tr key={event.id}>
                  <td className="soc-mono">
                    {event.fecha}
                  </td>

                  <td>{pretty(event.tipo)}</td>

                  <td className="soc-mono">
                    {sourceLabel(event.origen)}
                  </td>

                  <td>
                    {event.serverName ??
                      (event.serverId !== null
                        ? `#${event.serverId}`
                        : "—")}
                  </td>

                  <td>
                    <SeverityBadge
                      value={event.severidad}
                    />
                  </td>

                  <td>
                    {event.scope ? (
                      <span
                        className={`sv ${
                          scopeClass[event.scope]
                        }`}
                      >
                        {event.scope}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>

                  <td className="soc-muted">
                    ● {event.estado}
                  </td>
                </tr>
              ))}

              {!events.length && (
                <tr>
                  <td
                    colSpan={7}
                    className="soc-empty"
                  >
                    Sin eventos disponibles.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* INFORMACIÓN INFERIOR */}
      <div className="soc-bottomline">
        <span>
          <Radio size={14} />
          Actualización automática cada 5 segundos
        </span>

        <span>
          <Bell size={14} />
          {ctx.notifications.length} notificaciones
          visibles
        </span>

        <span>
          <TrendingUp size={14} />
          {number(recentHighEvents.length)} eventos
          de alta severidad en registros de 24 h
        </span>

        <span>
          <CheckCircle2 size={14} />
          Datos{" "}
          {modeDemo
            ? "simulados"
            : ctx.stale
              ? "desactualizados"
              : "del backend"}
        </span>
      </div>
    </div>
  );
}
