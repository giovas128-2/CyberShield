import { useState } from "react";
import { FlaskConical, Loader2, Check } from "lucide-react";
import { ModeBadge, PageHeader, ResourceView } from "../components/ui";
import { MitreBadge } from "../components/mitre/MitreTechniqueCard";
import { useResource } from "../hooks/useResource";
import { getLabScenarios } from "../services/management";
import { LAB_RUN_ENDPOINT } from "../api/endpoints";

export default function LabPage() {
  const r = useResource((s) => getLabScenarios(s));
  const [running, setRunning] = useState<string | null>(null);
  const [done, setDone] = useState<string[]>([]);

  // OLA 1: la ejecución es una simulación LOCAL (LAB_RUN_ENDPOINT = null). Con endpoint real (OLA 3) aquí va el POST.
  const run = async (id: string) => {
    if (running) return;
    setRunning(id);
    if (LAB_RUN_ENDPOINT === null) await new Promise((res) => setTimeout(res, 1500));
    setRunning(null); setDone((d) => [...d, id]);
  };

  return (
    <>
      <div className="labb"><FlaskConical size={18} /><div><b>ENTORNO DE LABORATORIO</b><small>Todos los escenarios usan datos ficticios y acciones reversibles sobre recursos autorizados.</small></div><span className="st t-vio">SIMULACIÓN CONTROLADA</span></div>
      <PageHeader title="Laboratorio de escenarios" subtitle="Ejecuta pruebas benignas y observa el flujo de respuesta." />
      <ResourceView r={r} empty="No hay escenarios disponibles.">
        <div className="pgrid">
          {(r.data ?? []).map((s, i) => (
            <div className="card pcard" key={s.id}>
              <div className="row" style={{ padding: 0 }}><span className="eb mono">ESCENARIO {String(i + 1).padStart(2, "0")}</span><ModeBadge mode={s.mode} /></div>
              <h3 style={{ margin: "10px 0 4px" }}>{s.name}</h3>
              {s.description && <small className="mu">{s.description}</small>}
              <div className="pmeta">
                <div><small className="mu">CONTROL CYBERSHIELD</small><b>{s.control}</b></div>
                <div><small className="mu">ORIGEN DEL EVENTO</small><b>{s.event_source ?? "—"}</b></div>
                <div><small className="mu">MITRE ATT&amp;CK</small>{s.mitre.length ? <span className="acts">{s.mitre.map((t) => <MitreBadge key={t.technique_id} t={t} />)}</span> : <b>—</b>}</div>
              </div>
              <button className="ab" style={{ marginTop: 12, width: "100%", justifyContent: "center" }} disabled={!!running} onClick={() => run(s.id)}>
                {running === s.id ? <><Loader2 size={14} className="spin" />Ejecutando…</> : done.includes(s.id) ? <><Check size={14} />Completado · ejecutar de nuevo</> : "Ejecutar escenario"}
              </button>
            </div>
          ))}
        </div>
      </ResourceView>
    </>
  );
}
