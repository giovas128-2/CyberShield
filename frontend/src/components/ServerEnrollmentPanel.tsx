import { useState } from "react";
import { Check, ChevronDown, ChevronUp, ClipboardCopy, KeyRound, LockKeyhole, Plus, ServerCog, ShieldAlert, X } from "lucide-react";
import { api, ApiError } from "../api/client";
import type { ServerItem } from "../types";
import "../styles/server-enrollment.css";

type Platform = "linux"|"windows"|"macos"|"other";
type EnrollmentReply = {
  success: boolean;
  server: {id:number;name:string;ip_address:string;status:string};
  agent: {agent_id:string;token:string;platform:string;token_shown_once:boolean};
  message:string;
};
type RegistrationReply = {agent_id:string;server_id:number;token:string;message:string};
type Enrollment = {serverId:number;serverName:string;agentId:string;token:string;platform:Platform};

export default function ServerEnrollmentPanel({selected,onRegistered}:{selected:ServerItem|null;onRegistered:()=>void}) {
  const [expanded,setExpanded]=useState(false);
  const [enrollmentMode,setEnrollmentMode]=useState<"new"|"existing">("new");
  const [name,setName]=useState("");
  const [ip,setIp]=useState("");
  const [platform,setPlatform]=useState<Platform>("linux");
  const [apiUrl,setApiUrl]=useState("");
  const [saving,setSaving]=useState(false);
  const [error,setError]=useState("");
  const [enrollment,setEnrollment]=useState<Enrollment|null>(null);
  const [showToken,setShowToken]=useState(false);
  const [copied,setCopied]=useState(false);

  function begin(mode:"new"|"existing") {
    setError("");setEnrollment(null);setCopied(false);setShowToken(false);
    setEnrollmentMode(mode);setExpanded(true);
  }
  async function submit(event:React.FormEvent<HTMLFormElement>){
    event.preventDefault();if(saving)return;
    if(enrollmentMode==="existing" && (!selected||selected.agentConnection?.state!=="not_enrolled")) {
      setError("Selecciona un servidor que aún no tenga agente individual.");return;
    }
    setSaving(true);setError("");setEnrollment(null);
    try {
      if(enrollmentMode==="new") {
        const result=await api<EnrollmentReply>("/servers/onboard","POST",{
          name:name.trim(),ip_address:ip.trim(),platform,agent_version:"1.0"
        });
        setEnrollment({serverId:result.server.id,serverName:result.server.name,agentId:result.agent.agent_id,token:result.agent.token,platform});
        setName("");setIp("");
      } else if(selected) {
        const result=await api<RegistrationReply>("/api/v1/agents/register","POST",{
          server_id:selected.id,platform,agent_version:"1.0"
        });
        setEnrollment({serverId:selected.id,serverName:selected.name,agentId:result.agent_id,token:result.token,platform});
      }
      onRegistered();
    } catch(err) {
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "No se pudo registrar el agente.");
    } finally {setSaving(false);}
  }
  async function copyToken(){
    if(!enrollment)return;
    try{await navigator.clipboard.writeText(enrollment.token);setCopied(true);}
    catch{setError("No se pudo copiar el token. Muéstralo y cópialo manualmente.");}
  }
  const existingAvailable=Boolean(selected&&(!selected.agentConnection||selected.agentConnection.state==="not_enrolled"));
  const safeUrl=apiUrl.trim();
  const remoteReady=/^https:\/\/[^\s/?#]+(?::\d{1,5})?\/?$/.test(safeUrl);
  const showUrl=remoteReady?safeUrl.replace(/\/$/,""):"https://TU-DOMINIO-DE-CYBERSHIELD";
  const agentScriptUrl="https://github.com/giovas128-2/CyberShield/blob/feature/intelligence-protection-coverage/heartbeat/cybershield-agent-heartbeat.py";

  return <section className="cs-enroll">
    <div className="cs-enroll-top">
      <div className="cs-enroll-title"><span><ServerCog size={22}/></span><div><h2>Integración de servidores reales</h2><p>Alta con agente individual y conexión autenticada. Compatible con Windows y Linux mediante Python.</p></div></div>
      <button type="button" className="cs-enroll-toggle" onClick={()=>setExpanded(v=>!v)} aria-expanded={expanded}>
        {expanded?<><ChevronUp size={17}/> Cerrar alta</>:<><Plus size={17}/> Añadir servidor</>}
      </button>
    </div>

    {expanded&&<>
      <div className="cs-enroll-tabs">
        <button type="button" className={enrollmentMode==="new"?"is-active":""} onClick={()=>begin("new")}>Registrar servidor nuevo</button>
        <button type="button" className={enrollmentMode==="existing"?"is-active":""} onClick={()=>begin("existing")} disabled={!existingAvailable}>Vincular el servidor seleccionado</button>
      </div>
      <form className="cs-enroll-form" onSubmit={submit}>
        {enrollmentMode==="new"?<>
          <label>Nombre del servidor<input required minLength={2} maxLength={100} value={name} onChange={e=>setName(e.target.value)} placeholder="Ej. Servidor de producción 01" disabled={saving}/></label>
          <label>Dirección IP real<input required value={ip} onChange={e=>setIp(e.target.value)} placeholder="Ej. 192.168.10.21 o IPv6" autoComplete="off" disabled={saving}/></label>
        </>:<div className="cs-enroll-existing"><b>Servidor a vincular:</b> {selected?.name} · {selected?.ipAddress}</div>}
        <label>Sistema operativo
          <select value={platform} disabled={saving} onChange={e=>setPlatform(e.target.value as Platform)}>
            <option value="linux">Linux (Ubuntu, Debian, RHEL y otros)</option>
            <option value="windows">Windows Server</option>
            <option value="macos">macOS</option>
            <option value="other">Otro con Python 3</option>
          </select>
        </label>
        <button type="submit" disabled={saving} className="cs-enroll-submit"><ServerCog size={17}/>{saving?"Registrando en PostgreSQL...":enrollmentMode==="new"?"Registrar y crear agente":"Crear credencial individual"}</button>
        {error&&<div role="alert" className="cs-enroll-error"><ShieldAlert size={17}/>{error}</div>}
      </form>
      <div className="cs-enroll-notice"><LockKeyhole size={17}/><span>El registro no pone el servidor en línea ni accede remotamente a su IP. Solo un heartbeat firmado con su token individual confirma la conexión.</span></div>

      {enrollment&&<div className="cs-enroll-setup">
        <div className="cs-enroll-setup-heading"><Check size={20}/><div><h3>{enrollment.serverName} registrado</h3><p>ID de servidor #{enrollment.serverId}. La credencial individual se muestra solo esta vez; guárdala de forma segura.</p></div><button type="button" aria-label="Ocultar credencial" title="Ocultar credencial" onClick={()=>{setEnrollment(null);setShowToken(false);}}><X size={18}/></button></div>
        <div className="cs-enroll-credentials">
          <label>Identificador de agente<input readOnly value={enrollment.agentId}/></label>
          <label>Token individual
            <div className="cs-enroll-secret"><input readOnly value={enrollment.token} type={showToken?"text":"password"} autoComplete="off"/><button type="button" onClick={()=>setShowToken(v=>!v)}>{showToken?"Ocultar":"Mostrar"}</button><button type="button" onClick={copyToken}><ClipboardCopy size={15}/>{copied?"Copiado":"Copiar"}</button></div>
          </label>
        </div>
        <div className="cs-enroll-connection">
          <label>URL HTTPS de CyberShield accesible desde el servidor remoto
            <input type="url" value={apiUrl} onChange={e=>setApiUrl(e.target.value)} placeholder="https://cybershield.tudominio.com" autoComplete="off"/>
          </label>
          {!remoteReady&&<p>Configura primero un dominio/IP accesible mediante HTTPS y un certificado TLS válido. <b>localhost:8000 solo funciona en la máquina donde corre FastAPI.</b></p>}
        </div>
        <div className="cs-enroll-steps">
          <h4>Instala el agente en el servidor remoto</h4>
          <p>Necesitas Python 3 y el paquete <code>httpx</code>. <a href={agentScriptUrl} target="_blank" rel="noreferrer">Ver script oficial del agente en GitHub</a>. Descárgalo al servidor autorizado y ejecútalo allí.</p>
          <div className="cs-enroll-commands">
            <div><b>Linux / macOS (bash)</b><pre>{`python3 -m pip install httpx
export CYBERSHIELD_AGENT_API='${showUrl}'
export CYBERSHIELD_AGENT_ID='${enrollment.agentId}'
read -rsp 'Token individual: ' CYBERSHIELD_AGENT_TOKEN
echo
export CYBERSHIELD_AGENT_TOKEN
python3 cybershield-agent-heartbeat.py --watch`}</pre></div>
            <div><b>Windows Server (PowerShell)</b><pre>{`py -m pip install httpx
$env:CYBERSHIELD_AGENT_API = '${showUrl}'
$env:CYBERSHIELD_AGENT_ID = '${enrollment.agentId}'
$secret = Read-Host 'Token individual' -AsSecureString
$env:CYBERSHIELD_AGENT_TOKEN = [System.Net.NetworkCredential]::new('', $secret).Password
py .\\cybershield-agent-heartbeat.py --watch`}</pre></div>
          </div>
          <p>El agente emitirá una señal cada 30 segundos mientras el proceso siga activo. Para operación permanente configura un servicio administrado por el sistema y protege su secreto mediante los mecanismos del sistema operativo.</p>
        </div>
        <div className="cs-enroll-notice"><ShieldAlert size={17}/><span>El heartbeat demuestra que alguien con el token puede contactar la API; no verifica por sí solo la integridad del host ni recoge logs de ataques. Para telemetría de seguridad integra Wazuh o Suricata por separado. Nunca abras FastAPI directamente a Internet sin un proxy HTTPS y controles de acceso.</span></div>
      </div>}
    </>}
  </section>;
}
