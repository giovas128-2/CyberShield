import { useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import {
  AlertCircle, AlertTriangle, ArrowRight, BrainCircuit, CheckCircle2,
  CircleHelp, Code2, FileCheck2, FileCode2, FileSearch, FolderOpen,
  Github, Info, Layers3, Loader2, LockKeyhole, Search, Shield,
  ShieldAlert, ShieldCheck, Sparkles, UploadCloud,
} from "lucide-react";
import { api, ApiError } from "../api/client";
import "../styles/code-security-review.css";

type Finding = {
  id: string; file: string; line: number; rule: string;
  severity: string; title: string; cwe: string; recommendation: string;
  evidence: string; verification: string;
};
type Scan = {
  files_scanned: number; findings_total: number; findings: Finding[];
  analysis: { mode: string; summary: string };
  note: string; execution: string;
};
type SourceFile = {path: string; content: string};

const permittedExtensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".java", ".go", ".rb", ".yml", ".yaml", ".json", ".sql", ".env.example"];
const rules = [
  { id: "CWE-95", name: "Ejecución dinámica" },
  { id: "CWE-78", name: "Comandos del sistema" },
  { id: "CWE-89", name: "Posible inyección SQL" },
  { id: "CWE-295", name: "Verificación TLS" },
  { id: "CWE-489", name: "Modo de depuración" },
  { id: "CWE-798", name: "Posibles secretos embebidos" },
];

function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "No se pudo completar el análisis. Comprueba la API y la conexión.";
}
function severityTone(severity: string): string {
  const value = severity.toLowerCase();
  if (value === "critical") return "critical";
  if (value === "high") return "high";
  if (value === "medium") return "medium";
  return "low";
}
function severityLabel(severity: string): string {
  const labels: Record<string,string> = {critical:"Crítica",high:"Alta",medium:"Media",low:"Baja",info:"Informativa"};
  return labels[severity.toLowerCase()] || severity.toUpperCase();
}

export default function CodeSecurityReviewPage() {
  const [mode, setMode] = useState<"files" | "github">("files");
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [branch, setBranch] = useState("");
  const [ai, setAi] = useState(false);
  const [result, setResult] = useState<Scan | null>(null);
  const [busy, setBusy] = useState(false);
  const [reading, setReading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  async function readFiles(picked: File[]) {
    setResult(null);
    setError("");
    setFiles([]);
    if (!picked.length) return;
    if (
      picked.length > 20 ||
      picked.some(file => file.size > 60000 ||
        !permittedExtensions.some(extension => file.name.toLowerCase().endsWith(extension)))
    ) {
      setError("Selecciona como máximo 20 archivos de código permitidos, de hasta 60 KB cada uno.");
      return;
    }
    if (picked.reduce((total, file) => total + file.size, 0) > 180000) {
      setError("El contenido total no puede superar los 180 KB.");
      return;
    }
    setReading(true);
    try {
      const selected = await Promise.all(picked.map(async file => ({path: file.name, content: await file.text()})));
      if (selected.reduce((total, file) => total + new TextEncoder().encode(file.content).length, 0) > 180000) {
        throw new Error("Los archivos exceden los 180 KB permitidos.");
      }
      setFiles(selected);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron leer los archivos.");
    } finally {
      setReading(false);
    }
  }
  async function selectFiles(event: ChangeEvent<HTMLInputElement>) {
    await readFiles(Array.from(event.target.files || []));
    event.target.value = "";
  }
  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    void readFiles(Array.from(event.dataTransfer.files || []));
  }
  function parseGithub() {
    const value = owner.trim();
    const match = value.match(/^(?:https?:\/\/github\.com\/)?([\w.-]+)\/([\w.-]+?)(?:\.git)?\/?$/i);
    if (match) return {owner: match[1], repo: match[2]};
    return {owner: value, repo: repo.trim()};
  }
  async function run() {
    if (busy || reading) return;
    setBusy(true); setError(""); setResult(null);
    try {
      if (mode === "files" && !files.length) throw new Error("Primero selecciona al menos un archivo de código.");
      const parsed = parseGithub();
      if (mode === "github" && (!parsed.owner || !parsed.repo)) {
        throw new Error("Indica el propietario y el repositorio público de GitHub.");
      }
      const path = mode === "files" ? "/intelligence/code-review/files" : "/intelligence/code-review/github";
      const body = mode === "files" ? {files, use_ai: ai} : {...parsed, branch: branch.trim(), use_ai: ai};
      const data = await api<Scan>(path, "POST", body);
      if (!Array.isArray(data?.findings)) throw new Error("El servidor devolvió una respuesta de análisis no válida.");
      setResult(data);
    } catch (err) {
      setError(err instanceof Error && !(err instanceof ApiError) ? err.message : errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const critical = result?.findings.filter(f => f.severity.toLowerCase() === "critical").length || 0;
  const high = result?.findings.filter(f => f.severity.toLowerCase() === "high").length || 0;
  const hasSource = mode === "files" ? files.length > 0 : Boolean(parseGithub().owner && parseGithub().repo);

  return (
    <div className="cs-audit">
      <section className="cs-audit-hero">
        <div className="cs-audit-hero-main">
          <span className="cs-audit-eyebrow"><Shield size={14}/> CYBERSHIELD / APPLICATION SECURITY</span>
          <h1>Auditoría de código</h1>
          <p>Detecta posibles debilidades en archivos de código y repositorios GitHub públicos. Revisa cada hallazgo con su clasificación CWE y una recomendación concreta.</p>
          <div className="cs-audit-hero-tags">
            <span><CheckCircle2 size={15}/> Análisis estático</span>
            <span><LockKeyhole size={15}/> Sin ejecutar código</span>
            <span><ShieldCheck size={15}/> Sin modificar incidentes</span>
          </div>
        </div>
        <div className="cs-audit-hero-mark" aria-hidden="true"><ShieldCheck size={68} strokeWidth={1.4}/><div>CODE SECURITY</div></div>
      </section>

      <div className="cs-audit-layout">
        <div className="cs-audit-main">
          <section className="cs-audit-card">
            <header className="cs-audit-card-heading">
              <span className="cs-audit-icon"><FileSearch size={22}/></span>
              <div><h2>Nueva revisión de seguridad</h2><p>Selecciona el origen del código que deseas inspeccionar.</p></div>
              <span className="cs-audit-step">PASO 01</span>
            </header>

            <div className="cs-audit-source-options" role="group" aria-label="Origen del código">
              <button type="button" className={"cs-audit-source" + (mode === "files" ? " is-selected" : "")}
                aria-pressed={mode === "files"} disabled={busy || reading}
                onClick={() => {setMode("files");setResult(null);setError("");}}>
                <span className="cs-audit-source-icon"><FolderOpen size={24}/></span>
                <strong>Archivos locales</strong>
                <small>Sube archivos de tu equipo</small>
                <span className="cs-audit-source-check"><CheckCircle2 size={17}/></span>
              </button>
              <button type="button" className={"cs-audit-source" + (mode === "github" ? " is-selected" : "")}
                aria-pressed={mode === "github"} disabled={busy || reading}
                onClick={() => {setMode("github");setResult(null);setError("");}}>
                <span className="cs-audit-source-icon"><Github size={24}/></span>
                <strong>Repositorio GitHub</strong>
                <small>Consulta un repositorio público</small>
                <span className="cs-audit-source-check"><CheckCircle2 size={17}/></span>
              </button>
            </div>

            {mode === "files" ? (
              <div className="cs-audit-source-form">
                <label htmlFor="cs-audit-file-input" className={"cs-audit-dropzone" + (dragging ? " is-dragging" : "")}
                  onDragOver={event => {event.preventDefault();setDragging(true);}}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}>
                  <span className="cs-audit-upload-icon"><UploadCloud size={27}/></span>
                  <strong>Arrastra tus archivos aquí</strong>
                  <span>o <b>haz clic para seleccionarlos</b> desde tu equipo</span>
                  <small>Formatos de código permitidos · 20 archivos máximo · 60 KB por archivo · 180 KB en total</small>
                  <input id="cs-audit-file-input" className="cs-audit-file-input" type="file" multiple
                    disabled={busy || reading} onChange={selectFiles}
                    accept=".py,.js,.jsx,.ts,.tsx,.php,.java,.go,.rb,.yml,.yaml,.json,.sql,.env.example"
                    aria-label="Seleccionar archivos de código para analizar"/>
                </label>
                {reading && <p className="cs-audit-inline-status"><Loader2 size={15} className="spin"/> Leyendo archivos...</p>}
                {!!files.length && <div className="cs-audit-selected">
                  <div className="cs-audit-between"><strong><FileCheck2 size={17}/> Archivos preparados</strong><span>{files.length} / 20</span></div>
                  <div className="cs-audit-file-list">{files.map((f, i) =>
                    <span key={i} className="cs-audit-file-chip"><FileCode2 size={15}/>{f.path}</span>
                  )}</div>
                </div>}
              </div>
            ) : (
              <div className="cs-audit-source-form cs-audit-github-form">
                <div className="cs-audit-field">
                  <label htmlFor="cs-audit-owner">Propietario o URL de GitHub</label>
                  <input id="cs-audit-owner" value={owner} disabled={busy} autoComplete="off"
                    onChange={event => setOwner(event.target.value)}
                    placeholder="usuario o https://github.com/usuario/repositorio"/>
                </div>
                <div className="cs-audit-field-grid">
                  <div className="cs-audit-field">
                    <label htmlFor="cs-audit-repo">Repositorio</label>
                    <input id="cs-audit-repo" value={repo} disabled={busy}
                      onChange={event => setRepo(event.target.value)}
                      placeholder="nombre-repositorio"/>
                  </div>
                  <div className="cs-audit-field">
                    <label htmlFor="cs-audit-branch">Rama <span>(opcional)</span></label>
                    <input id="cs-audit-branch" value={branch} disabled={busy}
                      onChange={event => setBranch(event.target.value)}
                      placeholder="Rama predeterminada"/>
                  </div>
                </div>
                <p className="cs-audit-hint"><Info size={15}/> Si escribes la URL completa, no necesitas llenar el campo repositorio. Solo se admiten repositorios públicos.</p>
              </div>
            )}

            <div className="cs-audit-ai-option">
              <div className="cs-audit-ai-icon"><BrainCircuit size={21}/></div>
              <div className="cs-audit-ai-copy"><strong>Explicación adicional con IA</strong>
                <span>Opcional. Si hay un modelo configurado, enviará únicamente metadatos y resúmenes de los hallazgos, nunca el código fuente.</span>
              </div>
              <label className="cs-audit-switch">
                <input type="checkbox" checked={ai} disabled={busy} onChange={event => setAi(event.target.checked)}
                  aria-label="Solicitar explicación adicional con IA"/>
                <span aria-hidden="true"/>
              </label>
            </div>

            {error && <div className="cs-audit-error" role="alert"><AlertCircle size={19}/><span>{error}</span></div>}
            <button className="cs-audit-run" type="button" onClick={run} disabled={busy || reading} aria-busy={busy}>
              {busy ? <><Loader2 size={18} className="spin"/> Analizando archivos y buscando patrones...</> :
                <><Search size={19}/> Analizar seguridad <ArrowRight size={18}/></>}
            </button>
            <p className="cs-audit-form-foot"><LockKeyhole size={14}/> Solo se realiza análisis pasivo. No se ejecutan archivos ni se generan ataques.</p>
          </section>

          {!result && <section className="cs-audit-empty cs-audit-card" aria-live="polite">
            <span className="cs-audit-empty-symbol"><FileSearch size={32}/></span>
            <div><h3>Tu informe aparecerá aquí</h3><p>{hasSource ? "El origen está listo. Pulsa «Analizar seguridad» para obtener un informe." : "Elige archivos o un repositorio público para comenzar. Los hallazgos incluirán archivo, línea, CWE y recomendación."}</p></div>
          </section>}

          {result && <div className="cs-audit-results" aria-live="polite">
            <section className="cs-audit-card cs-audit-results-summary">
              <div className="cs-audit-results-head"><span className="cs-audit-icon"><ShieldCheck size={22}/></span>
                <div><span className="cs-audit-kicker">REVISIÓN FINALIZADA</span><h2>Resultado del análisis</h2></div>
                <span className="cs-audit-status">Análisis completado</span>
              </div>
              <div className="cs-audit-kpis">
                <div><span>Archivos revisados</span><strong>{result.files_scanned}</strong><FileCode2 size={19}/></div>
                <div><span>Coincidencias</span><strong>{result.findings_total}</strong><Search size={19}/></div>
                <div><span>Críticas</span><strong>{critical}</strong><ShieldAlert size={19}/></div>
                <div><span>Altas</span><strong>{high}</strong><AlertTriangle size={19}/></div>
              </div>
              <div className="cs-audit-engine"><Sparkles size={18}/><div>
                <strong>Motor: {result.analysis.mode === "llm_explanation" ? "Reglas estáticas + explicación con IA" : "Análisis estático mediante reglas"}</strong>
                <p>{result.analysis.summary}</p>
              </div></div>
              <p className="cs-audit-muted">{result.note}</p>
            </section>

            <section className="cs-audit-card">
              <header className="cs-audit-card-heading"><span className="cs-audit-icon"><Layers3 size={22}/></span>
                <div><h2>Hallazgos y recomendaciones</h2><p>Coincidencias de patrones que requieren revisión del contexto.</p></div>
                <span className="cs-audit-count">{result.findings.length} hallazgos</span>
              </header>
              {result.findings.length === 0 ? <div className="cs-audit-clear">
                <CheckCircle2 size={30}/><div><strong>No se detectaron coincidencias con las reglas actuales</strong><p>Esto no garantiza que el código esté libre de vulnerabilidades. Revisa también dependencias, configuración y lógica de negocio.</p></div>
              </div> : <div className="cs-audit-findings">
                {result.findings.map((item, index) => <article className="cs-audit-finding" key={item.id}>
                  <div className="cs-audit-finding-head">
                    <div className="cs-audit-finding-number">{String(index + 1).padStart(2,"0")}</div>
                    <div><h3>{item.title}</h3><p><FileCode2 size={15}/>{item.file}:{item.line} <span>·</span> {item.rule}</p></div>
                    <div className="cs-audit-finding-badges">
                      <span className={"cs-audit-severity cs-audit-severity-" + severityTone(item.severity)}>{severityLabel(item.severity)}</span>
                      <span className="cs-audit-cwe">{item.cwe}</span>
                    </div>
                  </div>
                  <div className="cs-audit-finding-details">
                    <div className="cs-audit-recommendation"><CheckCircle2 size={19}/><div><strong>Recomendación</strong><p>{item.recommendation}</p></div></div>
                    {item.evidence && <div className="cs-audit-finding-note"><Info size={15}/><span>{item.evidence}</span></div>}
                    {item.verification && <div className="cs-audit-finding-note"><CircleHelp size={15}/><span>{item.verification}</span></div>}
                  </div>
                </article>)}
              </div>}
            </section>
          </div>}
        </div>

        <aside className="cs-audit-aside">
          <section className="cs-audit-card cs-audit-rules">
            <header className="cs-audit-card-heading"><span className="cs-audit-icon"><Code2 size={20}/></span>
              <div><h2>¿Qué revisa CyberShield?</h2><p>Reglas de detección disponibles.</p></div>
            </header>
            <div className="cs-audit-rules-list">{rules.map(rule => <div key={rule.id}>
              <span className="cs-audit-rule-dot"/><div><strong>{rule.name}</strong><small>{rule.id}</small></div>
            </div>)}</div>
            <p className="cs-audit-rules-foot"><Info size={16}/> Un hallazgo es preliminar y no demuestra explotación ni compromiso.</p>
          </section>
          <section className="cs-audit-aside-help">
            <span className="cs-audit-help-icon"><LockKeyhole size={19}/></span>
            <h3>Revisión responsable</h3>
            <p>No subas contraseñas, claves privadas, tokens ni información confidencial. En GitHub, utiliza únicamente repositorios públicos que tengas autorización para revisar.</p>
            <div><CheckCircle2 size={16}/> Hasta 20 archivos</div>
            <div><CheckCircle2 size={16}/> Sin ejecución de código</div>
            <div><CheckCircle2 size={16}/> Recomendaciones por CWE</div>
          </section>
        </aside>
      </div>
    </div>
  );
}
