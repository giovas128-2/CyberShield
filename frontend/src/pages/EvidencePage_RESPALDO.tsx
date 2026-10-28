import {
  useParams,
} from "react-router-dom";


export default function EvidencePage() {
  const { id } = useParams();

  return (
    <div className="ev-page">
      <div className="ev-page-header">
        <div>
          <span className="ev-eyebrow">
            CyberShield
          </span>

          <h1>
            Evidencia del incidente
          </h1>

          <p>
            Incidente {id}
          </p>
        </div>
      </div>

      <div className="ev-card">
        <p>
          Conexión con backend pendiente.
        </p>
      </div>
    </div>
  );
}