import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import IntelligenceLivePanel from "../components/IntelligenceLivePanel";
import { Link } from "react-router-dom";
import {
  Activity, AlertTriangle, ArrowLeft, ArrowRight, Bell,
  BookOpen, BrainCircuit, CheckCircle2, ChevronDown, ChevronRight,
  CircleAlert, Clock3, Code2, Copy, Database,
  FileArchive, FileCode2, FileText, Filter, Github, HardDrive, Info,
  LayoutDashboard, ListChecks, LockKeyhole, Menu, Play, Search, Server,
  Settings, ShieldAlert, ShieldCheck, Sparkles, Terminal, UploadCloud, X
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import "../styles/cybershield-design-preview.css";

type View = "dashboard" | "incidents" | "incident-detail" | "intelligence" | "catalog" | "analysis" | "servers" | "notifications" | "settings";
type SourceMode = "github" | "zip" | "code";
type TerminalMode = "response" | "audit" | "configuration";

type NavItem = { id: View; label: string; icon: LucideIcon };
const NAV: { title: string; items: NavItem[] }[] = [
  { title: "OPERACIONES", items: [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "incidents", label: "Incidentes", icon: ShieldAlert },
    { id: "intelligence", label: "Inteligencia", icon: BookOpen },
    { id: "catalog", label: "Ataques registrados", icon: Activity },
    { id: "servers", label: "Servidores", icon: Server },
    { id: "analysis", label: "Análisis con IA", icon: BrainCircuit },
    { id: "notifications", label: "Notificaciones", icon: Bell },
  ]},
  { title: "SISTEMA", items: [
    { id: "settings", label: "Configuración", icon: Settings },
  ]},
];

const VIEW_TITLES: Record<View, string> = {
  dashboard: "Centro de operaciones",
  incidents: "Incidentes de seguridad",
  "incident-detail": "Centro de incidente",
  intelligence: "Inteligencia de amenazas",
  catalog: "Ataques registrados",
  analysis: "Análisis de aplicaciones con IA",
  servers: "Servidores e infraestructura",
  notifications: "Notificaciones",
  settings: "Configuración",
};

const ATTACKS = [
  { code: "T1110", title: "Brute Force", source: "MITRE ATT&CK", severity: "Alta", className: "high", area: "Identidad y acceso", category: "Técnica" },
  { code: "T1021", title: "Remote Services", source: "MITRE ATT&CK", severity: "Alta", className: "high", area: "Movimiento lateral", category: "Técnica" },
  { code: "T1078", title: "Valid Accounts", source: "MITRE ATT&CK", severity: "Media", className: "medium", area: "Autenticación", category: "Técnica" },
  { code: "CISA KEV", title: "Vulnerabilidades explotadas", source: "CISA KEV", severity: "Consultar CVE", className: "info", area: "Software afectado", category: "Fuente" },
  { code: "CWE-89", title: "Inyección SQL", source: "CWE / OWASP", severity: "Alta", className: "high", area: "Aplicaciones web", category: "Debilidad" },
  { code: "CWE-798", title: "Credenciales embebidas", source: "CWE / OWASP", severity: "Alta", className: "high", area: "Código / secretos", category: "Debilidad" },
];
const INCIDENTS = [
  { id: "INC-DEMO-001", title: "Múltiples intentos de acceso SSH", technique: "T1110", host: "srv-lab-01", severity: "Alta", badge: "high", status: "Respuesta registrada" },
  { id: "INC-DEMO-002", title: "Actividad de exfiltración sospechosa", technique: "T1041", host: "srv-lab-02", severity: "Crítica", badge: "critical", status: "Revisión necesaria" },
  { id: "INC-DEMO-003", title: "Movimiento lateral por SSH", technique: "T1021", host: "srv-lab-03", severity: "Alta", badge: "high", status: "En investigación" },
  { id: "INC-DEMO-004", title: "Cambio sospechoso en archivo", technique: "T1486", host: "srv-lab-01", severity: "Media", badge: "medium", status: "Por verificar" },
];

function Pill({ children, tone = "blue" }: { children: ReactNode; tone?: string }) {
  return <span className={`csd-pill csd-pill-${tone}`}>{children}</span>;
}
function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`csd-panel ${className}`}>{children}</section>;
}
function SectionHead({ title, desc, icon: Icon }: { title: string; desc?: string; icon: LucideIcon }) {
  return <div className="csd-sectionhead"><span className="csd-iconbox"><Icon size={19} /></span><div><h2>{title}</h2>{desc && <p>{desc}</p>}</div></div>;
}
function Stat({ icon: Icon, label, value, hint, tone = "blue" }: { icon: LucideIcon; label: string; value: string; hint: string; tone?: string }) {
  return <div className="csd-stat"><div className="csd-stat-heading"><span>{label}</span><span className={`csd-small-icon csd-icon-${tone}`}><Icon size={18}/></span></div><strong>{value}</strong><small>{hint}</small></div>;
}
function Callout({ children, icon: Icon = Info }: { children: ReactNode; icon?: LucideIcon }) {
  return <div className="csd-callout"><Icon size={17}/><div>{children}</div></div>;
}

export default function CyberShieldDesignPreview() {
  const [view, setView] = useState<View>("dashboard");
  const [mobileMenu, setMobileMenu] = useState(false);
  const [period, setPeriod] = useState("24 horas");
  const [incidentFilter, setIncidentFilter] = useState("Todos");
  const [selectedIncident, setSelectedIncident] = useState(INCIDENTS[0]);
  const [termMode, setTermMode] = useState<TerminalMode>("response");
  const [catalogQuery, setCatalogQuery] = useState("");
  const [catalogFilter, setCatalogFilter] = useState("Todas");
  const [selectedAttack, setSelectedAttack] = useState(ATTACKS[0]);
  const [sourceMode, setSourceMode] = useState<SourceMode>("github");
  const [repoUrl, setRepoUrl] = useState("");
  const [codeSnippet, setCodeSnippet] = useState("// Pega aquí un fragmento para revisar\nfunction buscarUsuario(id) {\n  return db.query('SELECT * FROM users WHERE id=' + id);\n}");
  const [zipName, setZipName] = useState("");
  const [analysisDemo, setAnalysisDemo] = useState(false);
  const [findingFilter, setFindingFilter] = useState("Todas");
  const [showEngineerDetails, setShowEngineerDetails] = useState(false);
  const [notificationRead, setNotificationRead] = useState<string[]>([]);
  const [selectedServer, setSelectedServer] = useState("srv-lab-01");
  const [compact, setCompact] = useState(false);
  const [copied, setCopied] = useState(false);
  const [searchIncident, setSearchIncident] = useState("");

  function navigate(next: View) { setView(next); setMobileMenu(false); window.scrollTo({ top: 0, behavior: "smooth" }); }
  const filteredAttacks = useMemo(() => ATTACKS.filter(a =>
    (catalogFilter === "Todas" || a.source === catalogFilter) &&
    `${a.code} ${a.title} ${a.source} ${a.area}`.toLowerCase().includes(catalogQuery.toLowerCase())
  ), [catalogQuery, catalogFilter]);
  const filteredIncidents = INCIDENTS.filter(i =>
    (incidentFilter === "Todos" || i.severity === incidentFilter) &&
    `${i.title} ${i.host} ${i.id}`.toLowerCase().includes(searchIncident.toLowerCase())
  );
  const terminalTexts: Record<TerminalMode, string> = {
    response: `# Ejemplo de registro de una respuesta de Wazuh\n$ sudo tail -n 20 /var/ossec/logs/active-responses.log\n# La salida real se mostrará cuando exista evidencia asociada.\n\n# Comprobar estado del servicio de Wazuh\n$ systemctl is-active wazuh-manager\n# Resultado ilustrativo: active`,
    audit: `# Consultar acciones ejecutadas por Wazuh\n$ sudo tail -n 50 /var/ossec/logs/active-responses.log\n\n# Consultar alertas relacionadas\n$ sudo tail -n 50 /var/ossec/logs/alerts/alerts.json\n\n# No se han consultado logs reales desde este prototipo.`,
    configuration: `# Configuración de laboratorio registrada (referencia)\n<active-response>\n  <command>firewall-drop</command>\n  <location>local</location>\n  <rules_id>5763</rules_id>\n  <timeout>180</timeout>\n</active-response>\n\n# Configuración ≠ evidencia de ejecución o contención.`,
  };
  async function copyTerminal() {
    try {
      await navigator.clipboard.writeText(terminalTexts[termMode]);
      setCopied(true);
    } catch { setCopied(false); }
  }
  function markRead(id: string) {
    setNotificationRead(old => old.includes(id) ? old : [...old, id]);
  }
  const header = (eyebrow: string, title: string, subtitle: string, action?: ReactNode) =>
    <div className="csd-page-heading"><div><span className="csd-eyebrow">{eyebrow}</span><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>;

  const renderDashboard = () => <>
    {header("VISIÓN GENERAL", "Centro de operaciones", "Una vista clara de los riesgos, eventos y equipos que requieren tu atención.", <div className="csd-select-wrap"><Clock3 size={16}/><select value={period} onChange={e => setPeriod(e.target.value)} aria-label="Periodo"><option>24 horas</option><option>7 días</option><option>30 días</option></select><ChevronDown size={15}/></div>)}
    <div className="csd-stats">
      <Stat icon={ShieldAlert} label="Incidentes abiertos" value={period === "24 horas" ? "04" : "12"} hint="Ejemplo de actividad del laboratorio" tone="red"/>
      <Stat icon={Activity} label="Eventos procesados" value={period === "24 horas" ? "128" : "1,284"} hint="Eventos de ejemplo"/>
      <Stat icon={Server} label="Servidores supervisados" value="03" hint="2 activos · 1 en revisión" tone="teal"/>
      <Stat icon={BrainCircuit} label="Fuentes documentales" value="02" hint="CISA KEV · MITRE ATT&CK"/>
    </div>
    <div className="csd-two-thirds">
      <Panel><SectionHead title="Actividad de seguridad" desc={`Distribución ilustrativa de eventos · ${period}`} icon={Activity}/><div className="csd-chart">{[42,65,36,76,52,85,59,72,49,90,67,44,80,63,93,56,82,61].map((v, idx) => <div key={idx} className="csd-chart-bar" style={{height:`${v}%`}} title={`Periodo ${idx+1}: ejemplo visual`}/>)}</div><div className="csd-chart-scale"><span>Inicio del periodo</span><span>Fin del periodo</span></div></Panel>
      <Panel><SectionHead title="Prioridades" desc="Acciones recomendadas para revisión" icon={ListChecks}/><div className="csd-priority"><Pill tone="red">Alta</Pill><div><b>Revisar intentos SSH</b><small>Consultar evidencia y estado real de contención</small></div><ChevronRight size={17}/></div><div className="csd-priority"><Pill tone="amber">Media</Pill><div><b>Comprobar agentes</b><small>Validar comunicación y último heartbeat</small></div><ChevronRight size={17}/></div><div className="csd-priority"><Pill tone="blue">Info</Pill><div><b>Inteligencia disponible</b><small>CISA y MITRE listos para consultar</small></div><ChevronRight size={17}/></div></Panel>
    </div>
    <Panel><div className="csd-between"><SectionHead title="Actividad reciente" desc="Casos de ejemplo para probar el diseño" icon={Clock3}/><button className="csd-btn csd-btn-ghost" onClick={()=>navigate("incidents")}>Ver incidentes <ArrowRight size={16}/></button></div><div className="csd-table-wrap"><table className="csd-table"><thead><tr><th>Incidente</th><th>Servidor</th><th>Técnica</th><th>Prioridad</th><th>Estado</th><th></th></tr></thead><tbody>{INCIDENTS.slice(0,3).map(inc=><tr key={inc.id}><td><b>{inc.title}</b><small>{inc.id}</small></td><td>{inc.host}</td><td><Pill>{inc.technique}</Pill></td><td><Pill tone={inc.badge}>{inc.severity}</Pill></td><td>{inc.status}</td><td><button className="csd-linkbtn" onClick={()=>{setSelectedIncident(inc);navigate("incident-detail");}}>Abrir <ArrowRight size={15}/></button></td></tr>)}</tbody></table></div></Panel>
  </>;

  const renderIncidents = () => <>
    {header("INVESTIGACIÓN", "Incidentes de seguridad", "Investiga lo que ocurrió, revisa la evidencia y comprende las respuestas realizadas.", <button className="csd-btn csd-btn-outline" onClick={()=>navigate("incident-detail")}><FileText size={16}/> Ver centro de incidente</button>)}
    <div className="csd-stats"><Stat icon={ShieldAlert} label="Casos de ejemplo" value="04" hint="Vista de diseño sin consulta real"/><Stat icon={CircleAlert} label="Críticos" value="01" hint="Requieren investigación" tone="red"/><Stat icon={CheckCircle2} label="Contención comprobada" value="—" hint="Se mostrará con evidencia real" tone="teal"/><Stat icon={Clock3} label="Última sincronización" value="—" hint="Se conectará en Fase 2"/></div>
    <Panel><div className="csd-between csd-section-margin"><SectionHead title="Registro de incidentes" desc="Selecciona un incidente para ver su investigación" icon={ShieldAlert}/><div className="csd-toolbar"><label className="csd-search"><Search size={17}/><input value={searchIncident} onChange={e=>setSearchIncident(e.target.value)} placeholder="Buscar incidente o servidor"/></label><select className="csd-select" value={incidentFilter} onChange={e=>setIncidentFilter(e.target.value)} aria-label="Filtrar prioridad"><option>Todos</option><option>Crítica</option><option>Alta</option><option>Media</option></select></div></div><div className="csd-table-wrap"><table className="csd-table"><thead><tr><th>ID / Ataque</th><th>Activo afectado</th><th>MITRE</th><th>Severidad</th><th>Seguimiento</th><th></th></tr></thead><tbody>{filteredIncidents.map(inc=><tr key={inc.id}><td><b>{inc.title}</b><small>{inc.id}</small></td><td>{inc.host}</td><td><Pill>{inc.technique}</Pill></td><td><Pill tone={inc.badge}>{inc.severity}</Pill></td><td>{inc.status}</td><td><button className="csd-linkbtn" onClick={()=>{setSelectedIncident(inc);navigate("incident-detail");}}>Investigar <ArrowRight size={16}/></button></td></tr>)}</tbody></table></div>{filteredIncidents.length===0&&<p className="csd-muted">No hay coincidencias en los datos de demostración.</p>}</Panel>
  </>;

  const renderIncidentDetail = () => <>
    <button className="csd-back" onClick={()=>navigate("incidents")}><ArrowLeft size={16}/> Volver a incidentes</button>
    {header("CENTRO DE INCIDENTE", `${selectedIncident.id} · ${selectedIncident.title}`, "Proceso completo: detección, decisión, respuesta, verificación y referencias consultadas.", <Pill tone="amber">Contención no verificada</Pill>)}
    <div className="csd-stats"><Stat icon={ShieldAlert} label="Severidad" value={selectedIncident.severity} hint="Clasificación ilustrativa" tone="red"/><Stat icon={Server} label="Servidor afectado" value={selectedIncident.host} hint="Identificador de demostración"/><Stat icon={Activity} label="Técnica relacionada" value={selectedIncident.technique} hint="Asociación ilustrativa"/><Stat icon={Clock3} label="Verificación real" value="Pendiente" hint="Fase 3: enlazar evidencias" tone="amber"/></div>
    <div className="csd-two-thirds">
      <div className="csd-stack"><Panel><SectionHead title="Línea de tiempo" desc="Qué sucedió y qué faltaría verificar" icon={Clock3}/><div className="csd-timeline">{[
        ["Detección", "Wazuh identifica una secuencia de eventos sospechosos", "Referencia"],
        ["Clasificación", `Se relaciona el patrón con ${selectedIncident.technique}`, "Referencia"],
        ["Respuesta", "Se registra la acción defensiva solicitada o ejecutada", "Requiere evidencia"],
        ["Verificación", "Se confirma el bloqueo y la ausencia de nuevos intentos", "Pendiente"],
        ["Cierre", "Un ingeniero valida el resultado y conserva las evidencias", "Pendiente"]
      ].map(([name,desc,status],i)=><div className="csd-timeline-item" key={name}><span className={`csd-timeline-dot ${i>2?"csd-timeline-future":""}`}>{i+1}</span><div><b>{name}</b><p>{desc}</p></div><span className="csd-timeline-status">{status}</span></div>)}</div></Panel>
      <Panel><div className="csd-between"><SectionHead title="Demostración en terminal" desc="Referencia técnica: no son comandos ejecutados por esta vista" icon={Terminal}/><button className="csd-btn csd-btn-outline csd-btn-sm" onClick={()=>void copyTerminal()}><Copy size={15}/>{copied?"Copiado":"Copiar"}</button></div><div className="csd-tabbar csd-tight"><button className={termMode==="response"?"is-active":""} onClick={()=>{setTermMode("response");setCopied(false);}}>Respuesta</button><button className={termMode==="audit"?"is-active":""} onClick={()=>{setTermMode("audit");setCopied(false);}}>Logs y auditoría</button><button className={termMode==="configuration"?"is-active":""} onClick={()=>{setTermMode("configuration");setCopied(false);}}>Configuración Wazuh</button></div><div className="csd-terminal"><div className="csd-terminal-top"><span className="csd-dots"><i/><i/><i/></span><span>cybershield@laboratorio:~</span><Pill tone="slate">Solo lectura</Pill></div><pre>{terminalTexts[termMode]}</pre></div><Callout>En la Fase 3 mostraremos el comando, su salida, fecha y evidencia solo cuando realmente estén registrados. Esta terminal no ejecuta nada.</Callout></Panel></div>
      <div className="csd-stack"><Panel><SectionHead title="Normas y marcos relacionados" desc="Distinguir fuentes de referencia de controles aplicados" icon={BookOpen}/><div className="csd-norm"><Pill>MITRE</Pill><div><b>{selectedIncident.technique} · Técnica asociada</b><small>Conocimiento documental de MITRE ATT&CK</small></div></div><div className="csd-norm"><Pill>NIST</Pill><div><b>Respuesta a incidentes</b><small>Referencia para documentar y verificar el proceso</small></div></div><div className="csd-norm"><Pill>ISO</Pill><div><b>ISO/IEC 27001</b><small>Marco de gestión; control aplicado aún sin verificar</small></div></div><div className="csd-norm"><Pill>CISA</Pill><div><b>Vulnerabilidades conocidas</b><small>Consultar coincidencias de software afectado</small></div></div></Panel>
      <Panel><SectionHead title="Evidencia de respuesta" desc="Qué necesitamos para demostrar la contención" icon={Database}/>{["Evento original y regla Wazuh", "Acción defensiva asociada al incidente", "Salida del ejecutor y código de resultado", "Prueba de bloqueo y comprobación posterior"].map((x,i)=><div className="csd-checkrow" key={x}><span className="csd-checkempty">{i+1}</span><span>{x}</span><Pill tone="amber">Por vincular</Pill></div>)}</Panel>
      <Panel><SectionHead title="Explicación de IA" desc="Versión para cualquier persona o para el ingeniero" icon={Sparkles}/><div className="csd-tabbar csd-tight"><button className={!showEngineerDetails?"is-active":""} onClick={()=>setShowEngineerDetails(false)}>Explicación sencilla</button><button className={showEngineerDetails?"is-active":""} onClick={()=>setShowEngineerDetails(true)}>Explicación técnica</button></div><p className="csd-copy">{showEngineerDetails ? "Ejemplo: revisar reglas de correlación, logs de autenticación, trazabilidad de active-response, aplicación real del firewall y observación posterior." : "La plataforma detectó una actividad que podría indicar un ataque. Para asegurar que se detuvo, debemos revisar las pruebas de la protección aplicada."}</p><Callout>Texto explicativo de muestra, no generado por IA ni basado en un informe verificado de este caso.</Callout></Panel></div>
    </div>
  </>;

  const renderIntelligence = () => <IntelligenceLivePanel />;

  const renderCatalog = () => <>
    {header("CENTRO DE AMENAZAS", "Ataques registrados", "Diferencia el catálogo de amenazas conocidas de los incidentes realmente detectados.", <button className="csd-btn csd-btn-outline" onClick={()=>navigate("incidents")}><Activity size={16}/> Ver incidentes</button>)}
    <div className="csd-stats"><Stat icon={ShieldAlert} label="CVE CISA" value="1,786" hint="Registros documentales"/><Stat icon={BookOpen} label="Técnicas MITRE" value="706" hint="Catálogo de referencia"/><Stat icon={ShieldCheck} label="Mitigaciones MITRE" value="44" hint="No son ejecuciones" tone="teal"/><Stat icon={Activity} label="Incidentes del sistema" value="—" hint="Se conectarán en Fase 2" tone="amber"/></div>
    <Panel><div className="csd-between csd-section-margin"><SectionHead title="Explorador de amenazas" desc="La tabla contiene ejemplos de registros y referencias" icon={Filter}/><div className="csd-toolbar"><label className="csd-search"><Search size={17}/><input value={catalogQuery} onChange={e=>setCatalogQuery(e.target.value)} placeholder="Buscar nombre o técnica"/></label><select aria-label="Filtrar fuente" className="csd-select" value={catalogFilter} onChange={e=>setCatalogFilter(e.target.value)}><option>Todas</option><option>MITRE ATT&CK</option><option>CISA KEV</option><option>CWE / OWASP</option></select></div></div><div className="csd-two-thirds csd-catalog-layout"><div className="csd-table-wrap"><table className="csd-table"><thead><tr><th>Amenaza</th><th>Fuente</th><th>Tipo</th><th>Prioridad</th><th></th></tr></thead><tbody>{filteredAttacks.map(a=><tr key={a.code} className={selectedAttack.code===a.code?"csd-tr-selected":""}><td><b>{a.title}</b><small>{a.code}</small></td><td>{a.source}</td><td>{a.category}</td><td><Pill tone={a.className}>{a.severity}</Pill></td><td><button className="csd-linkbtn" onClick={()=>setSelectedAttack(a)}>Detalles <ChevronRight size={15}/></button></td></tr>)}</tbody></table>{filteredAttacks.length===0&&<p className="csd-muted">No hay coincidencias.</p>}</div><aside className="csd-detailbox"><Pill>{selectedAttack.code}</Pill><h3>{selectedAttack.title}</h3><p className="csd-muted">{selectedAttack.source} · {selectedAttack.area}</p><div className="csd-detail-divider"/><b>Qué representa</b><p>Elemento ilustrativo del catálogo. La severidad y la disponibilidad de defensa deben verificarse para cada activo.</p><b>Estado de automatización</b><p><Pill tone="amber">No determinado</Pill></p><button className="csd-btn csd-btn-outline" onClick={()=>navigate("intelligence")}>Ver inteligencia <ArrowRight size={15}/></button></aside></div></Panel>
  </>;

  const findings = [
    { title: "Posible inyección SQL", file: "src/controllers/usuarios.js", level: "Crítica", tone: "critical", note: "La construcción de consultas con texto concatenado podría permitir manipulación de datos.", fix: "Usar consultas parametrizadas y validar la entrada." },
    { title: "Secreto incluido en código", file: "config/settings.py", level: "Alta", tone: "high", note: "Una clave guardada en el repositorio podría quedar expuesta a terceros.", fix: "Retirar el secreto, rotarlo y usar un almacén seguro." },
    { title: "Dependencia desactualizada", file: "package.json", level: "Media", tone: "medium", note: "Algunas versiones de dependencias pueden contener vulnerabilidades conocidas.", fix: "Revisar el inventario y actualizar a versiones corregidas." },
  ];
  const filteredFindings = findings.filter(f=>findingFilter==="Todas" || f.level===findingFilter);
  const renderAnalysis = () => <>
    {header("LABORATORIO DE ANÁLISIS", "Análisis de aplicaciones con IA", "El usuario podrá revisar código, repositorios o ZIP y recibir explicaciones comprensibles.", <Pill tone="amber">Motor de análisis pendiente · Fase 4</Pill>)}
    <Panel><SectionHead title="¿Qué quieres inspeccionar?" desc="Elige el origen. En esta fase no se envían archivos ni se analiza el código." icon={Code2}/><div className="csd-source-tabs"><button className={sourceMode==="github"?"is-active":""} onClick={()=>{setSourceMode("github");setAnalysisDemo(false);}}><Github size={20}/><b>Repositorio GitHub</b><small>URL de repositorio autorizado</small></button><button className={sourceMode==="zip"?"is-active":""} onClick={()=>{setSourceMode("zip");setAnalysisDemo(false);}}><FileArchive size={20}/><b>Archivo ZIP</b><small>Paquete de código fuente</small></button><button className={sourceMode==="code"?"is-active":""} onClick={()=>{setSourceMode("code");setAnalysisDemo(false);}}><Code2 size={20}/><b>Fragmento de código</b><small>Pega un ejemplo pequeño</small></button></div><div className="csd-source-input">{sourceMode==="github"&&<label className="csd-field"><span>URL de repositorio (ejemplo)</span><input type="url" value={repoUrl} placeholder="https://github.com/organizacion/proyecto" onChange={e=>{setRepoUrl(e.target.value);setAnalysisDemo(false);}}/></label>}{sourceMode==="zip"&&<label className="csd-filedrop"><UploadCloud size={23}/><b>{zipName || "Seleccionar archivo .zip"}</b><span>El archivo permanece en tu equipo; no se carga ni procesa.</span><input type="file" accept=".zip,application/zip" onChange={e=>{setZipName(e.target.files?.[0]?.name||"");setAnalysisDemo(false);}}/></label>}{sourceMode==="code"&&<label className="csd-field"><span>Fragmento de código (no se envía)</span><textarea spellCheck={false} value={codeSnippet} onChange={e=>{setCodeSnippet(e.target.value);setAnalysisDemo(false);}} rows={6}/></label>}<div className="csd-source-footer"><span><LockKeyhole size={16}/> Sin cargas a servidores en el prototipo</span><button className="csd-btn csd-btn-primary" onClick={()=>{setAnalysisDemo(true);setFindingFilter("Todas");}}><Play size={16}/> Mostrar resultados de ejemplo</button></div></div></Panel>
    <div className="csd-analysis-results"><div className="csd-between"><SectionHead title="Hallazgos y recomendaciones" desc="Diseño de cómo se verá una inspección, no un análisis ejecutado" icon={BrainCircuit}/><Pill tone={analysisDemo?"blue":"slate"}>{analysisDemo?"Ejemplo visual activado":"Sin resultados reales"}</Pill></div>{!analysisDemo ? <div className="csd-empty"><span className="csd-empty-icon"><BrainCircuit size={33}/></span><h3>Aquí aparecerá el informe del análisis</h3><p>Selecciona «Mostrar resultados de ejemplo» para explorar la interfaz. No se analizará ningún repositorio, ZIP o código todavía.</p></div> : <><div className="csd-stats"><Stat icon={AlertTriangle} label="Hallazgos de ejemplo" value="03" hint="No son vulnerabilidades verificadas" tone="red"/><Stat icon={ShieldAlert} label="Riesgo ilustrativo" value="Alto" hint="La gravedad real exige análisis" tone="red"/><Stat icon={FileCode2} label="Archivos destacados" value="03" hint="Rutas ficticias"/><Stat icon={ListChecks} label="Recomendaciones" value="03" hint="Pautas correctivas ilustrativas" tone="teal"/></div><div className="csd-two-thirds"><Panel><div className="csd-between csd-section-margin"><SectionHead title="Posibles debilidades" desc="Selecciona una prioridad" icon={ShieldAlert}/><div className="csd-tabbar csd-tight">{["Todas","Crítica","Alta","Media"].map(f=><button key={f} className={findingFilter===f?"is-active":""} onClick={()=>setFindingFilter(f)}>{f}</button>)}</div></div>{filteredFindings.map(f=><div className="csd-finding" key={f.title}><Pill tone={f.tone}>{f.level}</Pill><div><b>{f.title}</b><small>{f.file}</small><p>{f.note}</p><p className="csd-fix"><CheckCircle2 size={15}/> {f.fix}</p></div></div>)}{filteredFindings.length===0&&<p className="csd-muted">No hay hallazgos en esta categoría.</p>}</Panel><div className="csd-stack"><Panel><SectionHead title="Así explicaría la IA" desc="Con una explicación sencilla y otra técnica" icon={Sparkles}/><p className="csd-copy"><b>En palabras simples:</b> algunos errores de programación podrían poner en riesgo datos privados.</p><p className="csd-copy"><b>Para ingeniería:</b> validar el flujo de datos, comprobar la versión de dependencias y asociar cada hallazgo a una evidencia reproducible.</p><Callout>No se ha ejecutado un modelo de IA: este texto es un ejemplo editorial.</Callout></Panel><Panel><SectionHead title="Acciones recomendadas" desc="Lista para priorizar correcciones" icon={ListChecks}/>{["Parametrizar consultas", "Retirar y rotar credenciales", "Actualizar dependencias", "Revisar los hallazgos con una persona"].map(x=><label className="csd-checkrow" key={x}><input type="checkbox"/><span>{x}</span></label>)}</Panel></div></div><Panel><SectionHead title="Ejemplo de terminal de análisis" desc="La salida ilustra el formato que tendrá un escáner real" icon={Terminal}/><div className="csd-terminal"><div className="csd-terminal-top"><span className="csd-dots"><i/><i/><i/></span><span>CyberShield · modo demostración</span></div><pre>{`$ cybershield scan --source DEMO\n[SIMULACIÓN] No se ejecutó ningún análisis.\n[SIMULACIÓN] Hallazgos ficticios: 3\n[SIMULACIÓN] Se mostrarán referencias, evidencia y soluciones.`}</pre></div></Panel></>}</div>
  </>;

  const renderServers = () => <>
    {header("INFRAESTRUCTURA", "Servidores e infraestructura", "Identifica rápidamente qué equipos requieren revisión y qué información está disponible.", <Pill tone="slate">Datos operativos de ejemplo</Pill>)}
    <div className="csd-stats"><Stat icon={Server} label="Equipos de ejemplo" value="03" hint="Activos ficticios"/><Stat icon={CheckCircle2} label="En línea" value="02" hint="Estados simulados" tone="teal"/><Stat icon={AlertTriangle} label="Requieren atención" value="01" hint="No es una alerta real" tone="amber"/><Stat icon={Clock3} label="Último heartbeat" value="—" hint="Se conectará al backend"/></div>
    <div className="csd-two-thirds"><Panel><SectionHead title="Inventario" desc="Elige un equipo para abrir sus detalles" icon={Server}/>{["srv-lab-01","srv-lab-02","srv-lab-03"].map((host,i)=><button className={`csd-serverrow ${selectedServer===host?"is-selected":""}`} onClick={()=>setSelectedServer(host)} key={host}><span className="csd-iconbox"><HardDrive size={19}/></span><span><b>{host}</b><small>Linux · Laboratorio</small></span><Pill tone={i===2?"amber":"teal"}>{i===2?"Revisión":"En línea"}</Pill><ChevronRight size={16}/></button>)}</Panel><Panel><SectionHead title="Detalle del servidor" desc="Panel preparado para métricas reales" icon={HardDrive}/><div className="csd-highlight"><Pill>Activo seleccionado</Pill><h3>{selectedServer}</h3><p>Monitoreo de logs, cambios, agentes y señales de riesgo.</p></div>{["Conectividad del agente", "Eventos recientes", "Respuestas defensivas", "Última verificación"].map(x=><div className="csd-norm" key={x}><div><b>{x}</b><small>Pendiente de conexión con el backend</small></div><Pill tone="slate">No disponible</Pill></div>)}</Panel></div>
  </>;

  const notifications = [
    { id:"N-DEMO-01", title:"Posible fuerza bruta", desc:"Revisar actividad SSH y evidencia de respuesta", tone:"red", time:"Ejemplo · reciente" },
    { id:"N-DEMO-02", title:"Estado del agente", desc:"Comprobar el último heartbeat de un servidor", tone:"amber", time:"Ejemplo · ayer" },
    { id:"N-DEMO-03", title:"Nueva información de amenazas", desc:"MITRE y CISA están disponibles para consulta", tone:"blue", time:"Ejemplo · esta semana" }
  ];
  const renderNotifications = () => <>
    {header("MENSAJES Y ALERTAS", "Notificaciones", "Atiende lo importante, reconoce lo que ya revisaste y conserva la trazabilidad.")}
    <div className="csd-stats"><Stat icon={Bell} label="Mensajes de ejemplo" value="03" hint="Aún no conectados al backend"/><Stat icon={CircleAlert} label="Sin leer" value={String(3-notificationRead.length).padStart(2,"0")} hint="Estado local del prototipo" tone="amber"/><Stat icon={ShieldCheck} label="Canal Telegram" value="—" hint="Se verificará la integración" tone="teal"/><Stat icon={Clock3} label="Historial" value="—" hint="Datos reales en Fase 2"/></div><Panel><SectionHead title="Bandeja de mensajes" desc="Haz clic para marcar como leído" icon={Bell}/>{notifications.map(n=><button className={`csd-notice ${notificationRead.includes(n.id)?"is-read":""}`} key={n.id} onClick={()=>markRead(n.id)}><span className={`csd-notice-icon csd-icon-${n.tone}`}><Bell size={19}/></span><span><b>{n.title}</b><small>{n.desc}</small></span><span className="csd-notice-time">{notificationRead.includes(n.id)?"Leído":n.time}</span></button>)}<Callout>En Fase 2 esta bandeja mostrará notificaciones reales. Marcar como leído aquí solo cambia el prototipo.</Callout></Panel>
  </>;

  const renderSettings = () => <>
    {header("PREFERENCIAS DE INTERFAZ", "Configuración", "Un diseño accesible para analistas, ingenieros y personas que necesitan entender el riesgo.")}
    <div className="csd-two-thirds"><Panel><SectionHead title="Identidad visual" desc="Blanco como base y cinco tonalidades de azul" icon={Settings}/><div className="csd-palette">{[["#EFF6FF","Azul 050"],["#CFE4FF","Azul 100"],["#8ABFFF","Azul 300"],["#347DE1","Azul 500"],["#0D4A95","Azul 700"],["#0AAFA2","Turquesa"]].map(([color,name])=><div key={color}><span style={{background:color}}/><b>{name}</b><small>{color}</small></div>)}</div><Callout>Las alertas críticas emplean rojo o ámbar solo para identificar gravedad; el fondo general permanece blanco.</Callout></Panel><Panel><SectionHead title="Preferencias" desc="Configuración visual local del prototipo" icon={ListChecks}/><label className="csd-toggle"><span><b>Diseño compacto</b><small>Reduce el espacio vertical de las tarjetas</small></span><input type="checkbox" checked={compact} onChange={e=>setCompact(e.target.checked)}/></label><label className="csd-toggle"><span><b>Explicaciones para ingeniería</b><small>Muestra inicialmente el enfoque técnico en incidentes</small></span><input type="checkbox" checked={showEngineerDetails} onChange={e=>setShowEngineerDetails(e.target.checked)}/></label><Callout>Estas preferencias no se guardan en tu perfil. La persistencia se incorpora más adelante.</Callout></Panel></div>
  </>;

  function content() {
    switch(view) {
      case "dashboard": return renderDashboard();
      case "incidents": return renderIncidents();
      case "incident-detail": return renderIncidentDetail();
      case "intelligence": return renderIntelligence();
      case "catalog": return renderCatalog();
      case "analysis": return renderAnalysis();
      case "servers": return renderServers();
      case "notifications": return renderNotifications();
      case "settings": return renderSettings();
    }
  }
  return <div className={`csd-shell ${compact?"csd-compact":""}`}>
    {mobileMenu && <button className="csd-mobile-overlay" onClick={()=>setMobileMenu(false)} aria-label="Cerrar navegación"/>}
    <aside className={`csd-sidebar ${mobileMenu?"csd-sidebar-open":""}`}>
      <div className="csd-brand"><span className="csd-brand-mark"><ShieldCheck size={23}/></span><div><strong>CyberShield</strong><small>SECURITY CENTER</small></div><button className="csd-mobile-close" onClick={()=>setMobileMenu(false)} aria-label="Cerrar menú"><X size={19}/></button></div>
      <div className="csd-sidebar-scroll">{NAV.map(group=><div className="csd-nav-group" key={group.title}><span className="csd-nav-label">{group.title}</span>{group.items.map(({id,label,icon:Icon})=><button key={id} className={`csd-nav-item ${view===id||(id==="incidents"&&view==="incident-detail")?"is-active":""}`} onClick={()=>navigate(id)}><Icon size={19}/><span>{label}</span>{id==="incidents"&&<em>4</em>}</button>)}</div>)}</div>
      <div className="csd-side-footer"><span className="csd-demo-dot"/><b>FASE 1 · PROTOTIPO</b><p>Inteligencia conectada a la API. El resto del prototipo usa datos de ejemplo; no ejecuta defensas.</p></div>
    </aside>
    <div className="csd-workspace"><header className="csd-topbar"><button className="csd-menu-btn" onClick={()=>setMobileMenu(true)} aria-label="Abrir menú"><Menu size={21}/></button><div className="csd-breadcrumb">Consola <ChevronRight size={15}/> <b>{VIEW_TITLES[view]}</b></div><div className="csd-topbar-actions"><Pill>Modo claro</Pill><Link to="/dashboard" className="csd-return-link"><ArrowLeft size={15}/> Volver al sistema</Link><span className="csd-avatar">CS</span></div></header><main className="csd-main"><div className="csd-banner"><div><Sparkles size={16}/><b>Prototipo visual — Fase 1</b><span>Inteligencia consulta datos reales · resto de vistas demostrativas</span></div><span className="csd-banner-stamp">Diseño interactivo</span></div>{content()}<div className="csd-page-footer"><span><ShieldCheck size={16}/> CyberShield · Prototipo de interfaz</span><span>Datos de ejemplo claramente identificados · Ningún cambio en Wazuh</span></div></main></div>
  </div>;
}
