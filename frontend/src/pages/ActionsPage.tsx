import { useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowUpRight, CheckCircle2, Clock3, RotateCcw, ShieldAlert, ShieldCheck, Terminal, Wrench } from "lucide-react";
import { ModeBadge, Pill, ResourceView } from "../components/ui";
import { useResource } from "../hooks/useResource";
import { getActions } from "../services/management";
import { incidentCode } from "../api/client";
import { timeAgo } from "../utils/format";
import type { ActionItem } from "../types";
import "../styles/operations-redesign.css";

const ST = {
  pending: ["Pendiente", "info"],
  executed: ["Ejecutada", "ok"],
  reverted: ["Revertida", "wn"],
  failed: ["Falló", "er"],
} as const;
type StatusFilter = "all" | ActionItem["status"];
const filters: {id:StatusFilter; name:string}[] = [
  {id:"all",name:"Todas"},{id:"executed",name:"Ejecutadas"},{id:"pending",name:"Pendientes"},
  {id:"reverted",name:"Revertidas"},{id:"failed",name:"Fallidas"}
];

export default function ActionsPage() {
  const r = useResource(s => getActions(s));
  const list = r.data ?? [];
  const [filter,setFilter] = useState<StatusFilter>("all");
  const [selectedId,setSelectedId] = useState<string|null>(null);
  const filtered = filter === "all" ? list : list.filter(a => a.status === filter);
  const selected = filtered.find(a => a.id === selectedId) ?? filtered[0] ?? null;
  const count = (status: ActionItem["status"]) => list.filter(a => a.status === status).length;

  return <div className="cs-ops">
    <header className="cs-ops-hero">
      <div className="cs-ops-hero-icon"><Wrench size={26}/></div>
      <div className="cs-ops-hero-copy"><span className="cs-ops-eyebrow">CENTRO DE RESPUESTA</span><h1>Acciones defensivas</h1>
        <p>Seguimiento de las acciones vinculadas a incidentes: estado registrado, objetivo, reversibilidad y origen de los datos.</p>
      </div>
      <div className="cs-ops-hero-chip"><ShieldCheck size={16}/> Consulta de registros</div>
    </header>
    <ResourceView r={r} empty="No hay acciones de respuesta registradas.">
      <div className="cs-ops-stats">
        <div className="cs-ops-stat"><span><Activity size={18}/> Acciones registradas</span><strong>{list.length}</strong><small>Origen identificado en cada acción</small></div>
        <div className="cs-ops-stat"><span><CheckCircle2 size={18}/> Ejecutadas</span><strong>{count("executed")}</strong><small>Estado de base de datos</small></div>
        <div className="cs-ops-stat"><span><RotateCcw size={18}/> Revertidas</span><strong>{count("reverted")}</strong><small>Estado de rollback registrado</small></div>
        <div className="cs-ops-stat"><span><ShieldAlert size={18}/> Fallidas</span><strong>{count("failed")}</strong><small>Requieren revisión</small></div>
      </div>
      <div className="cs-ops-card">
        <header className="cs-ops-section-head"><div><span className="cs-ops-kicker">HISTORIAL DE RESPUESTAS</span><h2>Registro de acciones</h2><p>Selecciona una acción para ver todos sus datos originales.</p></div><span className="cs-ops-count">{filtered.length} registros</span></header>
        <div className="cs-ops-tabs" role="group" aria-label="Filtrar acciones por estado">
          {filters.map(f=><button key={f.id} type="button" className={filter===f.id?"is-active":""} aria-pressed={filter===f.id} onClick={()=>{setFilter(f.id);setSelectedId(null);}}>{f.name}</button>)}
        </div>
        <div className="cs-ops-split">
          <div className="cs-ops-record-list">
            {filtered.length===0&&<div className="cs-ops-empty">No hay acciones registradas con este estado.</div>}
            {filtered.map(a=><button key={a.id} type="button" onClick={()=>setSelectedId(a.id)} className={"cs-ops-record"+(selected?.id===a.id?" is-selected":"")}>
              <span className="cs-ops-record-symbol"><Terminal size={19}/></span>
              <span className="cs-ops-record-body"><strong>{a.type}</strong><small>{a.incident_id != null ? incidentCode(a.incident_id):"Sin incidente asociado"} · {timeAgo(a.created_at)}</small><span className="cs-ops-record-target">Objetivo: {a.target || "No especificado"}</span></span>
              <Pill tone={ST[a.status][1]}>{ST[a.status][0]}</Pill>
            </button>)}
          </div>
          <aside className="cs-ops-detail" aria-label="Detalle de acción seleccionada">
            {selected ? <>
              <span className="cs-ops-eyebrow">FICHA DE RESPUESTA</span>
              <div className="cs-ops-detail-top"><span className="cs-ops-detail-icon"><Terminal size={23}/></span><Pill tone={ST[selected.status][1]}>{ST[selected.status][0]}</Pill></div>
              <h3>{selected.type}</h3>
              <p className="cs-ops-subtle">Información registrada para la acción {selected.id}.</p>
              <div className="cs-ops-facts">
                <div><small>Identificador</small><b>{selected.id}</b></div>
                <div><small>Objetivo</small><b className="mono">{selected.target ?? "No registrado"}</b></div>
                <div><small>Incidente</small>{selected.incident_id != null ? <Link to={`/incidents/${selected.incident_id}`} className="cs-ops-inline-link">{incidentCode(selected.incident_id)} <ArrowUpRight size={14}/></Link> : <b>Sin asociación</b>}</div>
                <div><small>Reversible</small><b>{selected.reversible?"Sí":"No"}</b></div>
                <div><small>Fecha de creación</small><b>{timeAgo(selected.created_at)}</b></div>
                <div><small>Origen del dato</small><ModeBadge mode={selected.mode}/></div>
              </div>
              <div className="cs-ops-advisory"><Clock3 size={16}/><span>El estado registrado no prueba por sí solo que la contención haya sido efectiva. Consulta la evidencia del incidente.</span></div>
            </> : <div className="cs-ops-empty">Selecciona una acción para inspeccionar su información.</div>}
          </aside>
        </div>
      </div>
    </ResourceView>
  </div>;
}
