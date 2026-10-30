import type {
  IncidentEvidence,
} from "../../types/evidence";

import {
  evidenceStatusLabel,
  formatEvidenceDate,
} from "./evidenceUtils";


interface Props {
  evidence: IncidentEvidence;
}


export default function DetectionPanel({
  evidence,
}: Props) {
  return (
    <section className="ev-card">
      <div className="ev-card-header">
        <div>
          <span className="ev-eyebrow">
            Evidencia de detección
          </span>

          <h2>
            {evidenceStatusLabel(
              evidence.status
            )}
          </h2>
        </div>

        <span
          className={
            `ev-status ev-status-${evidence.status.toLowerCase()}`
          }
        >
          {evidence.status}
        </span>
      </div>

      <div className="ev-grid">
        <div className="ev-field">
          <span>Incidente</span>
          <strong>
            INC-{evidence.incident_id}
          </strong>
        </div>

        <div className="ev-field">
          <span>Severidad</span>
          <strong>
            {evidence.severity.toUpperCase()}
          </strong>
        </div>

        <div className="ev-field">
          <span>Origen</span>
          <strong>
            {evidence.source}
          </strong>
        </div>

        <div className="ev-field">
          <span>IP origen</span>
          <strong>
            {evidence.source_ip ?? "N/D"}
          </strong>
        </div>

        <div className="ev-field">
          <span>Regla Wazuh</span>
          <strong>
            {evidence.detection.rule_id ?? "N/D"}
          </strong>
        </div>

        <div className="ev-field">
          <span>Intentos</span>
          <strong>
            {evidence.detection.attempts ?? "N/D"}
          </strong>
        </div>

        <div className="ev-field">
          <span>Usuario</span>
          <strong>
            {evidence.detection.user ?? "N/D"}
          </strong>
        </div>

        <div className="ev-field">
          <span>Fecha detección</span>
          <strong>
            {formatEvidenceDate(
              evidence.detection.timestamp
            )}
          </strong>
        </div>
      </div>

      {evidence.mitre && (
        <div className="ev-mitre">
          <span>MITRE ATT&CK</span>

          <strong>
            {evidence.mitre.technique_id}
            {" · "}
            {evidence.mitre.technique_name}
          </strong>

          <small>
            {evidence.mitre.tactic}
          </small>
        </div>
      )}

      <div className="ev-description">
        {evidence.description}
      </div>
    </section>
  );
}