import { useCallback, useEffect, useRef, useState } from "react";
import { Activity, Clock3, HardDrive, Loader2, RefreshCw, Server, ServerCrash, Wifi, WifiOff } from "lucide-react";
import { getServers } from "../api/client";
import type { ServerItem, ServerStatus } from "../types";
import { timeAgo } from "../utils/format";
import "../styles/operations-redesign.css";

const statusText:Record<ServerStatus,string> = {online:"En línea",offline:"Desconectado",registered:"Registrado"};
const statusClass:Record<ServerStatus,string> = {online:"ok",offline:"er",registered:"wn"};

export function ServersView() {
  const [servers,setServers] = useState<ServerItem[]|null>(null);
  const [error,setError] = useState("");
  const [selectedId,setSelectedId] = useState<number|null>(null);
  const [filter,setFilter] = useState<"all"|ServerStatus>("all");
  const inFlight=useRef(false);
  const mounted=useRef(false);

  const load=useCallback(async()=>{
    if(inFlight.current)return;
    inFlight.current=true;
    try{
      const freshServers=await getServers();
      if(!mounted.current)return;
      setServers(freshServers);
      setError("");
    }catch(err){
      console.error("GET /servers falló:",err);
      if(!mounted.current)return;
      setServers(previous=>previous??[]);
      setError("No se pudo actualizar la lista de servidores. Se conservan los últimos datos disponibles.");
    }finally{inFlight.current=false;}
  },[]);
  useEffect(()=>{
    mounted.current=true;
    load();
    const timer=window.setInterval(load,5000);
    return()=>{mounted.current=false;window.clearInterval(timer);};
  },[load]);

  const list=servers??[];
  const filtered=filter==="all"?list:list.filter(s=>s.status===filter);
  const selected=filtered.find(s=>s.id===selectedId)??filtered[0]??null;
  const online=list.filter(s=>s.status==="online").length;
  const offline=list.filter(s=>s.status==="offline").length;
  const registered=list.filter(s=>s.status==="registered").length;

  return <div className="cs-ops">
    <header className="cs-ops-hero">
      <div className="cs-ops-hero-icon"><Server size={27}/></div>
      <div className="cs-ops-hero-copy"><span className="cs-ops-eyebrow">INFRAESTRUCTURA MONITOREADA</span><h1>Servidores</h1><p>Inventario conectado a CyberShield. Revisa el estado declarado, la dirección IP, el agente y la última actividad de cada servidor.</p></div>
      <button type="button" className="cs-ops-refresh" onClick={load}><RefreshCw size={17}/> Actualizar</button>
    </header>
    {servers===null&&<div className="cs-ops-card cs-ops-loading" role="status"><Loader2 size={18} className="spin"/> Cargando servidores…</div>}
    {error&&<div className="cs-ops-alert" role="alert"><ServerCrash size={18}/><div><b>No se pudieron actualizar los servidores</b><p>{error}</p></div></div>}
    {servers&&<>
      <div className="cs-ops-stats">
        <div className="cs-ops-stat"><span><HardDrive size={18}/> Servidores registrados</span><strong>{list.length}</strong><small>Inventario consultado</small></div>
        <div className="cs-ops-stat"><span><Wifi size={18}/> En línea</span><strong>{online}</strong><small>Último estado conocido</small></div>
        <div className="cs-ops-stat"><span><WifiOff size={18}/> Desconectados</span><strong>{offline}</strong><small>Estado reportado por API</small></div>
        <div className="cs-ops-stat"><span><Clock3 size={18}/> Solo registrados</span><strong>{registered}</strong><small>Sin estado en línea confirmado</small></div>
      </div>
      {list.length>0?<section className="cs-ops-card">
        <header className="cs-ops-section-head"><div><span className="cs-ops-kicker">GESTIÓN DE ACTIVOS</span><h2>Inventario y conectividad</h2><p>Selecciona un servidor para revisar su información completa.</p></div><span className="cs-ops-count">{filtered.length} servidores</span></header>
        <div className="cs-ops-tabs" role="group" aria-label="Filtrar servidores">
          {([{id:"all",name:"Todos"},{id:"online",name:"En línea"},{id:"offline",name:"Desconectados"},{id:"registered",name:"Registrados"}] as const).map(f=><button key={f.id} type="button" className={filter===f.id?"is-active":""} aria-pressed={filter===f.id} onClick={()=>{setFilter(f.id);setSelectedId(null);}}>{f.name}</button>)}
        </div>
        <div className="cs-ops-split">
          <div className="cs-ops-record-list">
            {filtered.map(server=><button type="button" key={server.id} className={"cs-ops-record"+(selected?.id===server.id?" is-selected":"")} onClick={()=>setSelectedId(server.id)}>
              <span className="cs-ops-record-symbol"><Server size={20}/></span>
              <span className="cs-ops-record-body"><strong>{server.name}</strong><small className="mono">{server.ipAddress}</small><span className="cs-ops-record-target">{server.agent??"Sin agente"} · {timeAgo(server.lastSeen)}</span></span>
              <span className={`sv ${statusClass[server.status]}`}>● {statusText[server.status]}</span>
            </button>)}
            {!filtered.length&&<div className="cs-ops-empty">No hay servidores con este estado.</div>}
          </div>
          <aside className="cs-ops-detail" aria-label="Detalle del servidor seleccionado">
            {selected?<><span className="cs-ops-eyebrow">FICHA DE INFRAESTRUCTURA</span>
              <div className="cs-ops-detail-top"><span className="cs-ops-detail-icon"><Server size={24}/></span><span className={`sv ${statusClass[selected.status]}`}>● {statusText[selected.status]}</span></div>
              <h3>{selected.name}</h3><p className="cs-ops-subtle">Datos de supervisión recibidos desde el backend.</p>
              <div className="cs-ops-facts">
                <div><small>Identificador</small><b>{selected.id}</b></div>
                <div><small>Dirección IP</small><b className="mono">{selected.ipAddress}</b></div>
                <div><small>Agente</small><b>{selected.agent??"Sin agente registrado"}</b></div>
                <div><small>Estado</small><b>{statusText[selected.status]}</b></div>
                <div><small>Última actividad</small><b>{timeAgo(selected.lastSeen)}</b></div>
                <div><small>Fecha de registro</small><b>{timeAgo(selected.createdAt??null)}</b></div>
              </div><div className="cs-ops-advisory"><Activity size={16}/><span>El estado corresponde a la última información recibida. La ausencia de actividad reciente requiere verificación.</span></div>
            </>:<div className="cs-ops-empty">Selecciona un servidor para consultar sus datos.</div>}
          </aside>
        </div>
      </section>:<section className="cs-ops-card cs-ops-empty-centered"><Server size={40}/><h2>No hay servidores registrados</h2><p>Registra un servidor mediante la API para comenzar a mostrar la infraestructura en CyberShield.</p></section>}
    </>}
  </div>;
}
