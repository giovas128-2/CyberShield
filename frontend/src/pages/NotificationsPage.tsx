import { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { Activity, AlertTriangle, Bell, BellRing, CheckCircle2, Clock3, Inbox, Search, ShieldCheck } from "lucide-react";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import { useVisibleSeverities } from "../hooks/useVisibleSeverities";
import { SeverityBadge } from "../components/SeverityBadge";
import { timeAgo } from "../utils/format";
import "../styles/operations-redesign.css";

export default function NotificationsPage() {
  const ctx=useOutletContext<CyberShieldCtx>();
  const visible=useVisibleSeverities();
  const [statusFilter,setStatusFilter]=useState("all");
  const [search,setSearch]=useState("");
  const [selectedId,setSelectedId]=useState<number|null>(null);
  const allowed=ctx.notifications.filter(n=>visible.has(n.severity));
  const hiddenCount=ctx.notifications.length-allowed.length;
  const filtered=allowed.filter(n=>(statusFilter==="all"||n.status===statusFilter) &&
    (!search.trim()||[n.message,n.channel,n.recipient,String(n.incident_id)].some(v=>String(v??"").toLowerCase().includes(search.trim().toLowerCase()))));
  const selected=filtered.find(n=>n.id===selectedId)??filtered[0]??null;
  const pending=allowed.filter(n=>n.status==="pending").length;
  const failed=allowed.filter(n=>n.status==="failed").length;
  const other=allowed.length-pending-failed;
  const statuses=Array.from(new Set(allowed.map(n=>n.status)));

  return <div className="cs-ops">
    <header className="cs-ops-hero">
      <div className="cs-ops-hero-icon"><BellRing size={27}/></div>
      <div className="cs-ops-hero-copy"><span className="cs-ops-eyebrow">CENTRO DE ALERTAS</span><h1>Notificaciones</h1><p>Mensajes del backend asociados a incidentes. Consulta su severidad, canal y estado registrado, sin alterar las alertas ni Telegram.</p></div>
      <span className="cs-ops-hero-chip"><ShieldCheck size={16}/> Historial de avisos</span>
    </header>
    {ctx.demo&&<div className="cs-ops-alert"><AlertTriangle size={17}/><span>Datos de demostración: el backend no proporcionó una carga completa.</span></div>}
    {ctx.stale&&<div className="cs-ops-alert"><Clock3 size={17}/><span>Datos conservados de una carga anterior: comprueba la conexión con el backend.</span></div>}
    {hiddenCount>0&&<div className="cs-ops-advisory" role="status"><ShieldCheck size={17}/><span>Filtro personal: {hiddenCount} notificaciones ocultas. El backend y Telegram no se modifican.</span></div>}
    <div className="cs-ops-stats">
      <div className="cs-ops-stat"><span><Bell size={18}/> Avisos visibles</span><strong>{allowed.length}</strong><small>{hiddenCount} ocultos por preferencias</small></div>
      <div className="cs-ops-stat"><span><Clock3 size={18}/> Pendientes</span><strong>{pending}</strong><small>Estado registrado</small></div>
      <div className="cs-ops-stat"><span><AlertTriangle size={18}/> Fallidos</span><strong>{failed}</strong><small>Requieren revisión</small></div>
      <div className="cs-ops-stat"><span><CheckCircle2 size={18}/> Otros estados</span><strong>{other}</strong><small>No implica entrega confirmada</small></div>
    </div>
    <section className="cs-ops-card">
      <header className="cs-ops-section-head"><div><span className="cs-ops-kicker">REGISTRO DE NOTIFICACIONES</span><h2>Bandeja de alertas</h2><p>Filtra por estado o busca un mensaje, canal o incidente.</p></div><span className="cs-ops-count">{filtered.length} avisos</span></header>
      <div className="cs-ops-notification-tools">
        <label className="cs-ops-search"><Search size={18}/><input value={search} onChange={e=>{setSearch(e.target.value);setSelectedId(null);}} placeholder="Buscar por incidente, mensaje o canal" aria-label="Buscar notificaciones"/></label>
        <select value={statusFilter} onChange={e=>{setStatusFilter(e.target.value);setSelectedId(null);}} aria-label="Filtrar notificaciones por estado"><option value="all">Todos los estados</option>{statuses.map(s=><option key={s} value={s}>{s}</option>)}</select>
      </div>
      <div className="cs-ops-split">
        <div className="cs-ops-record-list">
          {filtered.map(n=>{
            const inc=ctx.incidents.find(i=>i.backendId===Number(n.incident_id));
            const count=inc?.correlatedEventsCount??1;
            return <button type="button" key={n.id} className={"cs-ops-record"+(selected?.id===n.id?" is-selected":"")} onClick={()=>setSelectedId(n.id)}>
              <span className="cs-ops-record-symbol"><Bell size={19}/></span>
              <span className="cs-ops-record-body"><strong>{n.message}</strong><small>INC-{n.incident_id} · {count} {count===1?"evento asociado":"eventos correlacionados"}</small><span className="cs-ops-record-target">{n.channel} · {timeAgo(n.created_at)}</span></span>
              <span className={`sv ${n.status==="pending"?"wn":n.status==="failed"?"er":"ok"}`}>{n.status}</span>
            </button>;
          })}
          {!filtered.length&&<div className="cs-ops-empty"><Inbox size={24}/> No hay notificaciones que coincidan con los filtros.</div>}
        </div>
        <aside className="cs-ops-detail" aria-label="Detalle de la notificación seleccionada">
          {selected?<><span className="cs-ops-eyebrow">DETALLE DEL AVISO</span><div className="cs-ops-detail-top"><span className="cs-ops-detail-icon"><Bell size={24}/></span><SeverityBadge value={selected.severity}/></div>
            <h3>Notificación #{selected.id}</h3><p className="cs-ops-subtle">{selected.message}</p>
            <div className="cs-ops-facts">
              <div><small>Incidente asociado</small><Link to={`/incidents/${selected.incident_id}`} className="cs-ops-inline-link">INC-{selected.incident_id}</Link></div>
              <div><small>Estado del registro</small><b>{selected.status}</b></div>
              <div><small>Canal</small><b>{selected.channel}</b></div>
              <div><small>Destinatario</small><b>{selected.recipient||"No registrado"}</b></div>
              <div><small>Creada</small><b>{timeAgo(selected.created_at)}</b></div>
              <div><small>Enviada</small><b>{selected.sent_at?timeAgo(selected.sent_at):"Sin fecha registrada"}</b></div>
            </div>
            <div className="cs-ops-advisory"><Activity size={16}/><span>El estado mostrado proviene del backend. No se comprueba la entrega en el dispositivo del destinatario.</span></div>
          </>:<div className="cs-ops-empty">Selecciona una notificación para consultar sus datos.</div>}
        </aside>
      </div>
    </section>
  </div>;
}
