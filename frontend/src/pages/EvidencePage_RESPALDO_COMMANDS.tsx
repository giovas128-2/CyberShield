import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  ShieldCheck,
  Terminal,
  Clock3,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Server,
  Activity,
  Database,
  Download,
} from "lucide-react";

import {
  getIncidentEvidence,
} from "../api/client";

import type {
  IncidentEvidence,
} from "../types/evidence";


function dateText(
  value: string | null | undefined
) {
  if (!value) return "Sin registro";

  return new Date(value).toLocaleString(
    "es-MX"
  );
}


function incidentCode(id: number) {
  return `INC-${String(id).padStart(3, "0")}`;
}
function stageLabel(stage: string) {
  switch (stage) {
    case "DETECTED":
      return "Ataque recibido";

    case "RESPONDING":
      return "Acción ejecutada";

    case "CONTAINED":
      return "Ataque bloqueado";

    case "FAILED":
      return "No contenido";

    case "ROLLED_BACK":
      return "Bloqueo retirado";

    default:
      return stage;
  }
}

export default function EvidencePage() {
  const { id } = useParams();

  const [evidence, setEvidence] =
    useState<IncidentEvidence | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);


  useEffect(() => {
    if (!id) {
      setError(
        "No se recibió un ID de incidente."
      );
      setLoading(false);
      return;
    }

    let active = true;

    async function load() {
      try {
        setLoading(true);

        const data =
          await getIncidentEvidence(id);

        if (active) {
          setEvidence(data);
        }

      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "No fue posible cargar la evidencia."
          );
        }

      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [id]);


  if (loading) {
    return (
      <div className="evidence-real-page">
        <div className="evidence-main-card">
          Cargando evidencia...
        </div>
      </div>
    );
  }


  if (error || !evidence) {
    return (
      <div className="evidence-real-page">

        <Link
          to="/incidents"
          className="lnk"
        >
          ← Volver a incidentes
        </Link>

        <div className="evidence-main-card">
          <h2>
            No fue posible cargar la evidencia
          </h2>

          <p>
            {error ??
              "No existe evidencia."}
          </p>
        </div>
      </div>
    );
  }


  const response = evidence.response;

  const contained =
    evidence.status === "CONTAINED";

  const failed =
    evidence.status === "FAILED";
  const downloadEvidence = () => {
  const blob = new Blob(
    [
      JSON.stringify(
        evidence,
        null,
        2
      ),
    ],
    {
      type: "application/json",
    }
  );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    `CyberShield_${incidentCode(
      evidence.incident_id
    )}_evidencia.json`;

  document.body.appendChild(link);

  link.click();

  document.body.removeChild(link);

  URL.revokeObjectURL(url);
};
const timelineItems = [
  ...evidence.timeline,

  ...(response?.rolled_back_at
    ? [
        {
          stage: "ROLLED_BACK",
          timestamp:
            response.rolled_back_at,
          completed: true,
        },
      ]
    : []),
];

  return (
    <div className="evidence-real-page">

      {/* HEADER */}

      <div className="evidence-top-row">
        <div>
          <div className="evidence-breadcrumb">
            CyberShield
            <span>›</span>
            Incidentes
            <span>›</span>
            {incidentCode(
              evidence.incident_id
            )}
            <span>›</span>
            Evidencia de protección
          </div>

          <h1>
            Evidencia de protección /
            Respuesta real
          </h1>

          <p className="evidence-subtitle">
            Monitoreo del ataque y acciones
            defensivas registradas por
            CyberShield.
          </p>
        </div>

        <Link
          to="/incidents"
          className="evidence-back-button"
        >
          ← Volver a incidentes
        </Link>
      </div>


      <div className="evidence-two-panels">

        {/* =====================================================
            PANTALLA 1
            ===================================================== */}

        <div className="evidence-screen">

          <div className="evidence-screen-header">
            <div className="evidence-screen-icon">
              <ShieldCheck size={24} />
            </div>

            <div>
              <h2>
                Pantalla 1 · Detección y
                contención
              </h2>

              <p>
                Flujo de detección del ataque
                y evidencia de la respuesta.
              </p>
            </div>

            <span
              className={
                contained
                  ? "evidence-live evidence-green"
                  : failed
                  ? "evidence-live evidence-red"
                  : "evidence-live"
              }
            >
              ●{" "}
              {contained
                ? "Ataque contenido"
                : failed
                ? "No contenido"
                : "Evidencia en tiempo real"}
            </span>
          </div>


          {/* DATOS DEL INCIDENTE */}

          <div className="evidence-summary-grid">

            <div>
              <small>
                ID DE INCIDENTE
              </small>

              <strong className="evidence-cyan">
                {incidentCode(
                  evidence.incident_id
                )}
              </strong>
            </div>

            <div>
              <small>ESTADO</small>

              <strong
                className={
                  contained
                    ? "evidence-green-text"
                    : failed
                    ? "evidence-red-text"
                    : ""
                }
              >
                {evidence.status}
              </strong>
            </div>

            <div>
              <small>
                SERVIDOR AFECTADO
              </small>

              <strong>
  {evidence.server_id
    ? `Servidor #${evidence.server_id}`
    : "N/D"}
</strong>
            </div>

            <div>
              <small>
                MITRE ATT&CK
              </small>

              <strong>
                {evidence.mitre
                  ? `${evidence.mitre.technique_id} · ${evidence.mitre.technique_name}`
                  : "N/D"}
              </strong>

              <span>
                {evidence.mitre?.tactic}
              </span>
            </div>

            <div>
              <small>SEVERIDAD</small>

              <strong className="evidence-red-text">
                {evidence.severity.toUpperCase()}
              </strong>
            </div>

            <div>
              <small>IP DE ORIGEN</small>

              <strong>
                {evidence.source_ip ??
                  "N/D"}
              </strong>
            </div>

            <div>
              <small>REGLA APLICADA</small>

              <strong>
                WAZUH-
                {evidence.detection.rule_id ??
                  "N/D"}
              </strong>
            </div>

            <div>
              <small>DETECTADO</small>

              <strong>
                {dateText(
                  evidence.detection
                    .timestamp
                )}
              </strong>
            </div>
          </div>


          {/* CONSOLA */}

          <div className="evidence-console-card">

            <div className="evidence-console-head">

  <div className="evidence-section-title">
    <Terminal size={20} />

    <div>
      <strong>
        Consola de Evidencia
      </strong>

      <span>
        Registro de eventos y acciones
        ejecutadas por CyberShield.
      </span>
    </div>
  </div>

  <button
    type="button"
    className="evidence-download"
    onClick={downloadEvidence}
  >
    <Download size={15} />

    Descargar evidencia
  </button>

</div>

            <div className="evidence-console">

              <div>
                <span>[INFO]</span>{" "}
                Fuente:
                {" "}
                {evidence.source}
              </div>

              <div>
                <span>[INFO]</span>{" "}
                Regla Wazuh:
                {" "}
                {evidence.detection.rule_id}
              </div>

              <div>
                <span>[INFO]</span>{" "}
                IP origen:
                {" "}
                {evidence.source_ip}
              </div>

              <div>
                <span>[INFO]</span>{" "}
                Intentos:
                {" "}
                {evidence.detection.attempts}
              </div>

              <div>
                <span>[INFO]</span>{" "}
                Usuario:
                {" "}
                {evidence.detection.user}
              </div>

              {evidence.mitre && (
                <div>
                  <span>[INFO]</span>{" "}
                  Clasificación:
                  {" "}
                  {evidence.mitre.technique_id}
                  {" - "}
                  {evidence.mitre.technique_name}
                </div>
              )}

              {response && (
                <>
                  <div>
                    <span>[INFO]</span>{" "}
                    Acción:
                    {" "}
                    {response.action_type}
                    {" → "}
                    {response.target}
                  </div>

                  <div>
                    <span>[INFO]</span>{" "}
                    Estado:
                    {" "}
                    {response.status}
                  </div>

                  {response.result && (
                    <div>
                      <span>[RESULT]</span>{" "}
                      {response.result}
                    </div>
                  )}
                </>
              )}

              {contained && (
                <div className="evidence-console-success">
                  [OK] Ataque contenido.
                </div>
              )}

              {failed && (
                <div className="evidence-console-failed">
                  [ERROR] No fue posible
                  contener el ataque.
                </div>
              )}

            </div>
          </div>


          {/* TIMELINE */}

          <div className="evidence-timeline-card">

            <div className="evidence-section-title">
              <Clock3 size={20} />

              <div>
                <strong>
                  Línea de tiempo del incidente
                </strong>

                <span>
                  Proceso de detección y
                  contención.
                </span>
              </div>
            </div>

            <div className="evidence-horizontal-timeline">

              {timelineItems.map(
                (item, index) => (
                  <div
                    className="evidence-timeline-step"
                    key={`${item.stage}-${index}`}
                  >
                    <div
                      className={
                        `evidence-step-circle ${
                          item.stage === "FAILED"
                            ? "evidence-step-red"
                            : item.stage === "CONTAINED"
                            ? "evidence-step-green"
                            : ""
                        }`
                      }
                    >
                      {index + 1}
                    </div>

                   <strong>
  {stageLabel(item.stage)}
</strong>

                    <span>
                      {dateText(
                        item.timestamp
                      )}
                    </span>
                  </div>
                )
              )}

            </div>
          </div>


          {/* RESULTADO */}

          <div
            className={
              contained
                ? "evidence-result evidence-result-success"
                : failed
                ? "evidence-result evidence-result-failure"
                : "evidence-result"
            }
          >

            <h3>
              {contained
                ? "Resultado de la contención"
                : failed
                ? "Resultado de la respuesta"
                : "Estado de la respuesta"}
            </h3>

            <div className="evidence-result-grid">

              <div>
                {contained
                  ? <CheckCircle2 />
                  : <AlertTriangle />}

                <span>
                  <strong>
                    {contained
                      ? "Ataque contenido"
                      : failed
                      ? "Ataque no contenido"
                      : "Respuesta en proceso"}
                  </strong>

                  <small>
                    Estado confirmado por
                    CyberShield.
                  </small>
                </span>
              </div>

              <div>
                <Lock />

                <span>
                  <strong>
                    IP objetivo
                  </strong>

                  <small>
                    {response?.target ??
                      "N/D"}
                  </small>
                </span>
              </div>

              <div>
                <Activity />

                <span>
                  <strong>
                    Acción defensiva
                  </strong>

                  <small>
                    {response?.action_type ??
                      "Sin acción"}
                  </small>
                </span>
              </div>

              <div>
                <ShieldCheck />

                <span>
                  <strong>
                    Estado final
                  </strong>

                  <small>
                    {response?.status ??
                      evidence.status}
                  </small>
                </span>
              </div>

            </div>
          </div>
        </div>


        {/* =====================================================
            PANTALLA 2
            ===================================================== */}

        <div className="evidence-screen">

          <div className="evidence-screen-header">
            <div className="evidence-screen-icon">
              <Terminal size={24} />
            </div>

            <div>
              <h2>
                Pantalla 2 · Respuesta defensiva
                asociado al incidente
              </h2>

              <p>
  CyberShield muestra únicamente el
  comando o acción defensiva vinculada
  al ataque detectado.
</p>
            </div>

            {response && (
              <span
                className={
                  failed
                    ? "evidence-live evidence-red"
                    : "evidence-live evidence-green"
                }
              >
                ●{" "}
                {failed
                  ? "Respuesta fallida"
                  : "Respuesta registrada"}
              </span>
            )}
          </div>


          <div className="evidence-attack-type">
            <Lock size={18} />

            Tipo de incidente actual:
            {" "}

            <strong>
              {evidence.mitre
                ?.technique_name ??
                evidence.event_type}
            </strong>
          </div>


          {response ? (
            <>

              <div className="evidence-command-header">
                <Lock size={18} />

                <strong>
                  Respuesta defensiva:
                  {" "}
                  {response.action_type}
                </strong>

                <span>
                  MITRE:
                  {" "}
                  {evidence.mitre
                    ?.technique_id ??
                    "N/D"}
                </span>
              </div>


              <div className="evidence-command-console">

                <div>
                  <span>
                    [ACTION]
                  </span>{" "}
                  {response.action_type}
                </div>

                <div>
                  <span>
                    [TARGET]
                  </span>{" "}
                  {response.target ??
                    "N/D"}
                </div>

                <div>
                  <span>
                    [STATUS]
                  </span>{" "}
                  {response.status}
                </div>

                <div>
                  <span>
                    [REVERSIBLE]
                  </span>{" "}
                  {response.reversible
                    ? "YES"
                    : "NO"}
                </div>

                {response.duration_seconds && (
                  <div>
                    <span>
                      [TIMEOUT]
                    </span>{" "}
                    {response.duration_seconds}s
                  </div>
                )}

                {response.result && (
                  <>
                    <br />

                    <div>
                      <span>
                        [RESULT]
                      </span>{" "}
                      {response.result}
                    </div>
                  </>
                )}

                {failed && (
                  <>
                    <br />

                    <div className="evidence-console-failed">
                      [FAILED] Se requiere
                      intervención del ingeniero
                      de seguridad.
                    </div>
                  </>
                )}

              </div>


              <div className="evidence-reason-card">
                <div className="evidence-info-icon">
                  i
                </div>

                <div>
                  <h3>
                    Motivo de esta respuesta
                  </h3>

                  <p>
                    {response.reason}
                  </p>
                </div>
              </div>

            </>
          ) : (
            <div className="evidence-main-card">
              No existe respuesta defensiva
              registrada.
            </div>
          )}


          {/* HERRAMIENTAS */}

          <div className="evidence-tools-card">

            <div className="evidence-section-title">
              <Server size={20} />

              <div>
                <strong>
                  Herramientas utilizadas
                </strong>

                <span>
                  Tecnologías que participan
                  en la detección y respuesta.
                </span>
              </div>
            </div>

            <div className="evidence-tools-grid">

              <div>
                <ShieldCheck />
                <strong>Wazuh</strong>
                <span>
                  Detección host
                </span>
              </div>

              <div>
                <Activity />
                <strong>Suricata</strong>
                <span>
                  Análisis de red
                </span>
              </div>

              <div>
                <ShieldCheck />
                <strong>
                  CyberShield
                </strong>
                <span>
                  Coordinación
                </span>
              </div>

              <div>
                <Database />
                <strong>
                  PostgreSQL
                </strong>
                <span>
                  Evidencia
                </span>
              </div>

              <div>
                <Lock />
                <strong>
                  Active Response
                </strong>
                <span>
                  Mitigación
                </span>
              </div>

            </div>
          </div>

        </div>
      </div>
    </div>
  );
}