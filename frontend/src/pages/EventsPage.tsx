import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getIncidentEvidence,
} from "../api/client";

import type {
  IncidentEvidence,
} from "../types/evidence";

import DetectionPanel from "../components/evidence/DetectionPanel";

import DefensiveCommandPanel from "../components/evidence/DefensiveCommandPanel";


export default function EvidencePage() {
  const { id } = useParams();

  const [
    evidence,
    setEvidence,
  ] = useState<IncidentEvidence | null>(
    null
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  useEffect(() => {
    if (!id) {
      setError(
        "No se recibió un ID de incidente."
      );
      setLoading(false);
      return;
    }

    let active = true;

    async function loadEvidence() {
      try {
        setLoading(true);
        setError(null);

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

    loadEvidence();

    return () => {
      active = false;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="ev-page">
        <Link
          to={`/incidents/${id}`}
          className="lnk"
        >
          ← Volver al incidente
        </Link>

        <div className="ev-card">
          Cargando evidencia...
        </div>
      </div>
    );
  }

  if (error || !evidence) {
    return (
      <div className="ev-page">
        <Link
          to={`/incidents/${id}`}
          className="lnk"
        >
          ← Volver al incidente
        </Link>

        <div className="ev-card">
          <h2>
            No fue posible cargar la evidencia
          </h2>

          <p className="mu">
            {error ??
              "No existe evidencia disponible."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="ev-page">
      <Link
        to={`/incidents/${evidence.incident_id}`}
        className="lnk"
      >
        ← Volver al incidente
      </Link>

      <div className="ev-page-header">
        <div>
          <span className="ev-eyebrow">
            CyberShield · Evidencia
          </span>

          <h1>
            Incidente INC-
            {String(
              evidence.incident_id
            ).padStart(3, "0")}
          </h1>

          <p className="mu">
            Evidencia técnica de detección
            y respuesta defensiva.
          </p>
        </div>

        <div
          className={
            `ev-main-status ev-main-status-${evidence.status.toLowerCase()}`
          }
        >
          {evidence.status}
        </div>
      </div>

      <div className="ev-layout">
        <DetectionPanel
          evidence={evidence}
        />

        <DefensiveCommandPanel
          evidence={evidence}
        />
      </div>

      <section className="ev-card">
        <span className="ev-eyebrow">
          Flujo de respuesta
        </span>

        <div className="ev-timeline">
          {evidence.timeline.map(
            (item, index) => (
              <div
                className="ev-timeline-item"
                key={`${item.stage}-${index}`}
              >
                <div className="ev-dot" />

                <div>
                  <strong>
                    {item.stage}
                  </strong>

                  <span>
                    {item.timestamp
                      ? new Date(
                          item.timestamp
                        ).toLocaleString()
                      : "Sin fecha"}
                  </span>
                </div>
              </div>
            )
          )}
        </div>
      </section>
    </div>
  );
}