import { useState } from "react";
import { FlaskConical, Loader2, Check, ShieldCheck } from "lucide-react";
import { ModeBadge, PageHeader, ResourceView } from "../components/ui";
import { MitreBadge } from "../components/mitre/MitreTechniqueCard";
import { useResource } from "../hooks/useResource";
import { getLabScenarios } from "../services/management";
import { LAB_RUN_ENDPOINT } from "../api/endpoints";
import { api } from "../api/client";


export default function LabPage() {
  const r = useResource((s) => getLabScenarios(s));
  const [running, setRunning] = useState<string | null>(null);
  const [done, setDone] = useState<string[]>([]);

  // Sin endpoint confirmado, la ejecución permanece local y se etiqueta explícitamente como simulación.
  const run = async (id: string) => {
  if (running) return;

  setRunning(id);

  try {
    if (LAB_RUN_ENDPOINT === null) {
      await new Promise((res) => setTimeout(res, 1500));
    } else if (
      id === "sc1" || 
      id === "sc2" || 
      id === "sc3" || 
      id === "sc4" || 
      id === "sc5" ||
      id === "sc6" ||
      id === "sc7" ||
      id === "sc8"
    ) {
      await api(`${LAB_RUN_ENDPOINT}/${id}/run`, "POST");
    } else {
      await new Promise((res) => setTimeout(res, 800));
    }

    setDone((d) => d.includes(id) ? d : [...d, id]);
  } finally {
    setRunning(null);
  }
};

  return (
    <>
      <div className="labb" role="note"><FlaskConical size={18} /><div><b>ENTORNO DE LABORATORIO</b><small>Solo usa datos ficticios, recursos autorizados y acciones reversibles. Una simulación no representa un ataque real.</small></div><span className="st t-vio">SIMULACIÓN CONTROLADA</span></div>
      <PageHeader title="Laboratorio de escenarios" subtitle="Valida de forma segura la cadena señal → detección → incidente → respuesta." />
      <div className="demo-flow" aria-label="Flujo visual de la demostración">
        <span>1 · Señal</span><b>→</b><span>2 · Clasificación</span><b>→</b><span>3 · Incidente</span><b>→</b><span>4 · Acción</span><b>→</b><span>5 · Evidencia</span>
      </div>
      <ResourceView r={r} empty="No hay escenarios disponibles.">
        <div className="pgrid">
          {(r.data ?? []).map((s, i) => (
            <article className="card pcard lab-card" key={s.id}>
              <div className="row" style={{ padding: 0 }}><span className="eb mono">ESCENARIO {String(i + 1).padStart(2, "0")}</span><ModeBadge mode={s.mode} /></div>
              <h3>{s.name}</h3>
              {s.description && <p className="protection-description">{s.description}</p>}
              <div className="pmeta">
                <div><small className="mu">CONTROL CYBERSHIELD</small><b>{s.control}</b></div>
                <div><small className="mu">ORIGEN DEL EVENTO</small><b>{s.event_source ?? "—"}</b></div>
                <div><small className="mu">MITRE ATT&amp;CK RELACIONADO</small>{s.mitre.length ? <span className="acts">{s.mitre.map((t) => <MitreBadge key={t.technique_id} t={t} />)}</span> : <b>Sin clasificación confirmada</b>}</div>
              </div>
              {done.includes(s.id) && <div className="lab-result"><ShieldCheck size={16} /><span><b>Escenario ejecutado correctamente</b><small>{LAB_RUN_ENDPOINT === null ? " No se generó un incidente real porque el endpoint de ejecución aún no está confirmado." : " Revisa el incidente y la evidencia generada."}</small></span></div>}
              <button className="ab lab-run" disabled={!!running} onClick={() => run(s.id)} aria-label={`Ejecutar escenario ${s.name}`}>
                {running === s.id ? <><Loader2 size={14} className="spin" />Ejecutando…</> : done.includes(s.id) ? <><Check size={14} />Ejecutar de nuevo</> : "Ejecutar escenario"}
              </button>
            </article>
          ))}
        </div>
      </ResourceView>
    </>
  );
}
