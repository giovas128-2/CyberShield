import { useState } from "react";
import { Activity, BookOpen, CheckCircle2, ChevronRight, CircleHelp, LockKeyhole, Radar, ShieldCheck } from "lucide-react";
import { ModeBadge, ResourceView } from "../components/ui";
import ProtectionIntelligenceCoverage from "../components/ProtectionIntelligenceCoverage";
import ProtectionOfficialResearch from "../components/ProtectionOfficialResearch";
import { MitreBadge } from "../components/mitre/MitreTechniqueCard";
import { useResource } from "../hooks/useResource";
import { getProtections } from "../services/management";
import type { Protection, SourceMode } from "../types";
import "../styles/operations-redesign.css";

type ModeFilter = "all" | SourceMode;
const filters:{id:ModeFilter;name:string}[]=[
  {id:"all",name:"Todos los controles"},{id:"integrated",name:"Integrados"},
  {id:"simulated",name:"Simulados"},{id:"pending",name:"Pendientes"},
];

export default function ProtectionsPage() {
  const r = useResource(s => getProtections(s));
  const list = r.data ?? [];
  const [filter,setFilter] = useState<ModeFilter>("all");
  const [selectedId,setSelectedId] = useState<string|null>(null);
  const integrated = list.filter(p => p.mode === "integrated").length;
  const simulated = list.filter(p => p.mode === "simulated").length;
  const pending = list.filter(p => p.mode === "pending").length;
  const pct = list.length ? Math.round(integrated / list.length * 100) : 0;
  const filtered = filter === "all" ? list : list.filter(p => p.mode === filter);
  const selected:Protection|null = filtered.find(p=>p.id===selectedId) ?? filtered[0] ?? null;

  return <div className="cs-ops">
    <header className="cs-ops-hero">
      <div className="cs-ops-hero-icon"><ShieldCheck size={27}/></div>
      <div className="cs-ops-hero-copy"><span className="cs-ops-eyebrow">SEGURIDAD Y COBERTURA</span><h1>Protecciones defensivas</h1><p>Consulta el catálogo existente, sus sensores, sus técnicas MITRE y el nivel de integración registrado.</p></div>
      <div className="cs-ops-hero-chip"><LockKeyhole size={16}/> Catálogo de controles</div>
    </header>
    <ResourceView r={r} empty="No hay controles configurados.">
      <div className="cs-ops-stats">
        <div className="cs-ops-stat"><span><Radar size={18}/> Controles registrados</span><strong>{list.length}</strong><small>Catálogo cargado por CyberShield</small></div>
        <div className="cs-ops-stat"><span><CheckCircle2 size={18}/> Integrados</span><strong>{integrated}</strong><small>Marcados como integración confirmada</small></div>
        <div className="cs-ops-stat"><span><Activity size={18}/> Simulados</span><strong>{simulated}</strong><small>Escenarios de laboratorio</small></div>
        <div className="cs-ops-stat"><span><CircleHelp size={18}/> Pendientes</span><strong>{pending}</strong><small>Requieren validación</small></div>
      </div>
      <section className="cs-ops-card cs-ops-coverage">
        <div className="cs-ops-coverage-title"><div><span className="cs-ops-kicker">VISIBILIDAD DE CONTROLES</span><h2>Cobertura de integración declarada</h2><p>{integrated} de {list.length} controles están marcados como integrados en el catálogo actual.</p></div><div className="cs-ops-coverage-value">{pct}<small>%</small></div></div>
        <div className="cs-ops-progress" aria-label={`${pct}% del catálogo está integrado`} role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}><div style={{width:`${pct}%`}}/></div>
        <div className="cs-ops-legend"><span><i className="cs-ops-dot is-green"/> {integrated} integrados</span><span><i className="cs-ops-dot is-blue"/> {simulated} simulaciones</span><span><i className="cs-ops-dot is-amber"/> {pending} pendientes</span></div>
        <div className="cs-ops-advisory"><CircleHelp size={16}/><span>Esta cobertura describe estados de integración. No garantiza que se haya detectado, bloqueado o mitigado un ataque real.</span></div>
      </section>
      <section className="cs-ops-card">
        <header className="cs-ops-section-head"><div><span className="cs-ops-kicker">CATÁLOGO DEFENSIVO</span><h2>Controles de CyberShield</h2><p>Selecciona una tarjeta para consultar el sensor y las técnicas asociadas.</p></div><span className="cs-ops-count">{filtered.length} controles</span></header>
        <div className="cs-ops-tabs" role="group" aria-label="Filtrar protecciones">{filters.map(f=><button key={f.id} type="button" className={filter===f.id?"is-active":""} aria-pressed={filter===f.id} onClick={()=>{setFilter(f.id);setSelectedId(null);}}>{f.name}</button>)}</div>
        <div className="cs-ops-protection-grid">
          {filtered.map((p,i)=><button key={p.id} type="button" className={"cs-ops-protection"+(selected?.id===p.id?" is-selected":"")} onClick={()=>setSelectedId(p.id)}>
            <span className="cs-ops-protection-top"><span className="cs-ops-protection-icon"><ShieldCheck size={20}/></span><ModeBadge mode={p.mode}/></span>
            <small className="cs-ops-kicker">CONTROL · {p.id || String(i+1).padStart(2,"0")}</small>
            <strong>{p.name}</strong>
            <span className="cs-ops-protection-desc">{p.description || "Control registrado en el catálogo defensivo."}</span>
            <span className="cs-ops-protection-meta"><span>Sensor: {p.sensor}</span><ChevronRight size={18}/></span>
          </button>)}
          {!filtered.length&&<p className="cs-ops-empty">Sin protecciones con este estado.</p>}
        </div>
        {selected&&<section className="cs-ops-control-detail" aria-label="Detalle del control seleccionado">
          <div className="cs-ops-detail-top"><div><span className="cs-ops-kicker">FICHA DEL CONTROL SELECCIONADO</span><h3>{selected.name}</h3></div><ModeBadge mode={selected.mode}/></div>
          <p>{selected.description || "El catálogo no incluye una descripción adicional."}</p>
          <div className="cs-ops-facts">
            <div><small>Identificador</small><b>{selected.id}</b></div>
            <div><small>Sensor / origen</small><b>{selected.sensor}</b></div>
            <div><small>Modo</small><b>{selected.mode === "integrated" ? "Integrado" : selected.mode === "simulated" ? "Simulación controlada" : "Pendiente"}</b></div>
            <div><small>Técnicas MITRE asociadas</small><b>{selected.mitre.length}</b></div>
          </div>
          <div className="cs-ops-mitre"><strong><BookOpen size={17}/> MITRE ATT&CK vinculado</strong>
            {selected.mitre.length ? <div className="cs-ops-mitre-list">{selected.mitre.map(t=><div key={t.technique_id}><MitreBadge t={t}/><span><b>{t.technique_name}</b>{t.tactic&&<small>{t.tactic}</small>}{t.rationale&&<small>{t.rationale}</small>}</span></div>)}</div> : <p>No se ha confirmado una clasificación MITRE para este control.</p>}
          </div>
        </section>}
      </section>
    </ResourceView>
    <section className="cs-ops-intel"><ProtectionOfficialResearch /></section>
    <section className="cs-ops-intel"><ProtectionIntelligenceCoverage /></section>
  </div>;
}
