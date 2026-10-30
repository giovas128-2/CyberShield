import type {
  IncidentEvidence,
} from "../../types/evidence";

import {
  formatEvidenceDate,
} from "./evidenceUtils";


interface Props {
  evidence: IncidentEvidence;
}


export default function DefensiveCommandPanel({
  evidence,
}: Props) {
  const response = evidence.response;

  if (!response) {
    return (
      <section className="ev-card">
        <span className="ev-eyebrow">
          Respuesta defensiva
        </span>

        <h2>Sin acción registrada</h2>

        <p className="ev-muted">
          CyberShield todavía no tiene una
          acción defensiva asociada a este
          incidente.
        </p>
      </section>
    );
  }

  return (
    <section className="ev-card">
      <span className="ev-eyebrow">
        Respuesta defensiva
      </span>

      <h2>
        {response.action_type}
      </h2>

      <div className="ev-command">
        <div>
          <span>Objetivo</span>
          <strong>
            {response.target ?? "N/D"}
          </strong>
        </div>

        <div>
          <span>Estado</span>
          <strong>
            {response.status}
          </strong>
        </div>

        <div>
          <span>Reversible</span>
          <strong>
            {response.reversible
              ? "Sí"
              : "No"}
          </strong>
        </div>

        <div>
          <span>Duración</span>
          <strong>
            {response.duration_seconds
              ? `${response.duration_seconds} s`
              : "N/D"}
          </strong>
        </div>
      </div>

      {response.reason && (
        <div className="ev-terminal">
          <div className="ev-terminal-title">
            Acción propuesta
          </div>

          <pre>
            {response.reason}
          </pre>
        </div>
      )}

      {response.result && (
        <div className="ev-terminal">
          <div className="ev-terminal-title">
            Resultado
          </div>

          <pre>
            {response.result}
          </pre>
        </div>
      )}

      {response.failure_reason && (
        <div className="ev-failure">
          <strong>
            No se pudo contener el ataque.
          </strong>

          <p>
            {response.failure_reason}
          </p>

          <span>
            Se requiere intervención del
            ingeniero de seguridad.
          </span>
        </div>
      )}

      <div className="ev-times">
        <span>
          Creada:{" "}
          {formatEvidenceDate(
            response.created_at
          )}
        </span>

        {response.executed_at && (
          <span>
            Ejecutada:{" "}
            {formatEvidenceDate(
              response.executed_at
            )}
          </span>
        )}

        {response.rolled_back_at && (
          <span>
            Rollback:{" "}
            {formatEvidenceDate(
              response.rolled_back_at
            )}
          </span>
        )}
      </div>
    </section>
  );
}