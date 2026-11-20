import { useState } from "react";
import type { ChangeEvent } from "react";
import { AlertTriangle, BrainCircuit, FileCode, Github, Search, ShieldCheck } from "lucide-react";
import { api, ApiError } from "../api/client";

type Finding = {
  id: string; file: string; line: number; rule: string;
  severity: string; title: string; cwe: string; recommendation: string;
  evidence: string; verification: string;
};
type Scan = {
  files_scanned: number; findings_total: number; findings: Finding[];
  analysis: {mode: string; summary: string};
  note: string; execution: string;
};
const allowed = /\.(py|js|jsx|ts|tsx|php|java|go|rb|yml|yaml|json|sql)$|\.env\.example$/i;
function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : "No se pudo completar el análisis. Comprueba la API y la conexión.";
}
export default function CodeSecurityReviewPage() {
  const [mode, setMode] = useState<"files" | "github">("files");
  const [files, setFiles] = useState<{path:string;content:string}[]>([]);
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [branch, setBranch] = useState("");
  const [ai, setAi] = useState(false);
  const [result, setResult] = useState<Scan|null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function selectFiles(event: ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(event.target.files ?? []);
    setResult(null); setError("");
    if (!picked.length) return;
    if (picked.length > 20 || picked.some(file=>!allowed.test(file.name) || file.size>60000)) {
      setError("Selecciona máximo 20 archivos de código permitidos, de hasta 60 KB cada uno.");
      return;
    }
    if (picked.reduce((sum,f)=>sum+f.size,0)>180000) {
      setError("El contenido total no puede superar los 180 KB.");
      return;
    }
    try {
      const read = await Promise.all(picked.map(async file=>({path:file.name,content:await file.text()})));
      if (read.reduce((sum,f)=>sum+new TextEncoder().encode(f.content).length,0)>180000) throw new Error("demasiado grande");
      setFiles(read);
    } catch { setError("No se pudieron leer los archivos."); }
  }
  function parseGithub() {
    const value = owner.trim();
    const match = value.match(/^(?:https?:\/\/github\.com\/)?([\w.-]+)\/([\w.-]+?)(?:\.git)?\/?$/i);
    if (match) return {owner:match[1],repo:match[2]};
    return {owner:value,repo:repo.trim()};
  }
  async function run() {
    setBusy(true); setError(""); setResult(null);
    try {
      if (mode==="files" && !files.length) throw new Error("Selecciona primero los archivos.");
      const parsed = parseGithub();
      if (mode==="github" && (!parsed.owner || !parsed.repo)) throw new Error("Indica propietario y repositorio público.");
      const path=mode==="files" ? "/intelligence/code-review/files" : "/intelligence/code-review/github";
      const body=mode==="files" ? {files,use_ai:ai} : {...parsed,branch:branch.trim(),use_ai:ai};
      const data = await api<Scan>(path,"POST",body);
      if (!Array.isArray(data?.findings)) throw new Error("El servidor devolvió una respuesta no válida.");
      setResult(data);
    } catch(err) {
      setError(err instanceof Error && !(err instanceof ApiError) ? err.message : errorMessage(err));
    } finally {setBusy(false);}
  }
  return <div>
    <header className="h"><div><h1>Auditoría de código</h1><div className="mu">Revisión pasiva de archivos y repositorios GitHub públicos. No ejecuta el código ni modifica incidentes.</div></div><span className="sv ok">SOLO LECTURA</span></header>
    <section className="card" style={{padding:20,marginBottom:16}}>
      <div style={{display:"flex",gap:10,marginBottom:18,flexWrap:"wrap"}}>
        <button className="btn sm gh" type="button" onClick={()=>{setMode("files");setResult(null);}} aria-pressed={mode==="files"}><FileCode size={17}/> Subir archivos</button>
        <button className="btn sm gh" type="button" onClick={()=>{setMode("github");setResult(null);}} aria-pressed={mode==="github"}><Github size={17}/> Repositorio GitHub</button>
      </div>
      {mode==="files" ? <div>
        <label htmlFor="audit-files"><strong>Archivos de código fuente</strong></label>
        <p className="mu">Hasta 20 archivos, máximo 60 KB por archivo y 180 KB en total. No subas contraseñas, claves ni información confidencial.</p>
        <input id="audit-files" type="file" multiple onChange={selectFiles} accept=".py,.js,.jsx,.ts,.tsx,.php,.java,.go,.rb,.yml,.yaml,.json,.sql" />
        <p className="mu">{files.length ? files.map(f=>f.path).join(", ") : "No hay archivos seleccionados"}</p>
      </div> : <div style={{display:"grid",gap:12,maxWidth:560}}>
        <label>Propietario o URL de GitHub<input aria-label="Propietario o URL" value={owner} onChange={e=>setOwner(e.target.value)} placeholder="usuario o https://github.com/usuario/repositorio" style={{display:"block",width:"100%",padding:10,boxSizing:"border-box"}}/></label>
        <label>Repositorio (si escribiste solo propietario)<input aria-label="Repositorio" value={repo} onChange={e=>setRepo(e.target.value)} placeholder="nombre-del-repositorio" style={{display:"block",width:"100%",padding:10,boxSizing:"border-box"}}/></label>
        <label>Rama (opcional)<input aria-label="Rama" value={branch} onChange={e=>setBranch(e.target.value)} placeholder="Por defecto, rama principal" style={{display:"block",width:"100%",padding:10,boxSizing:"border-box"}}/></label>
        <p className="mu">Solo repositorios públicos. Se analiza un máximo de 20 archivos permitidos; no se clona ni ejecuta nada.</p>
      </div>}
      <label style={{display:"flex",alignItems:"center",gap:8,margin:"16px 0"}}>
        <input type="checkbox" checked={ai} onChange={e=>setAi(e.target.checked)}/>
        <span><BrainCircuit size={16}/> Solicitar explicación con IA, si está configurada</span>
      </label>
      <p className="mu">Cuando se habilita la IA, se envían al proveedor únicamente los metadatos y resúmenes de los hallazgos, no el código fuente.</p>
      <button className="btn" type="button" onClick={run} disabled={busy}><Search size={17}/>{busy ? "Analizando..." : "Analizar seguridad"}</button>
      {error && <p role="alert" style={{marginTop:12}}><AlertTriangle size={15}/> {error}</p>}
    </section>
    {result && <>
      <section className="card" style={{padding:20,marginBottom:16}}>
        <h2><ShieldCheck size={19}/> Resultado del análisis</h2>
        <p><strong>{result.files_scanned}</strong> archivos revisados · <strong>{result.findings_total}</strong> coincidencias preliminares</p>
        <p className="mu">Motor: {result.analysis.mode === "llm_explanation" ? "Reglas + explicación con IA" : "Reglas estáticas (sin IA generativa)"}</p>
        <p>{result.analysis.summary}</p>
        <p className="mu">{result.note}</p>
      </section>
      <section className="card" style={{padding:20}}>
        <h2>Hallazgos y recomendaciones</h2>
        {result.findings.length===0 && <p className="mu">No hay coincidencias con las reglas disponibles. Esto no garantiza que el código esté libre de vulnerabilidades.</p>}
        {result.findings.map(item=><article key={item.id} style={{padding:"12px 0",borderBottom:"1px solid #d1dce9"}}>
          <div style={{display:"flex",gap:8,justifyContent:"space-between",flexWrap:"wrap"}}><strong>{item.title}</strong><span className="mu">{item.severity.toUpperCase()} · {item.cwe}</span></div>
          <p className="mu">{item.file}:{item.line} · {item.rule}</p>
          <p>{item.recommendation}</p>
          <small className="mu">{item.evidence}</small>
        </article>)}
      </section>
    </>}
  </div>;
}
