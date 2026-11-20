import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Activity, ArrowLeft, ArrowRight, BookOpen, Database, Search, ShieldCheck, TriangleAlert } from "lucide-react";
import { api } from "../api/client";

type Summary = {
  source: string;
  vulnerabilities: number;
  techniques: number;
  mitigations: number;
  relationships: number;
};
type Mitigation = { mitigation_id: string; name: string; description: string | null };
type Technique = {
  attack_id: string;
  name: string;
  description: string | null;
  is_subtechnique: boolean;
  modified_at: string | null;
  mitigation_count: number;
  mitigations: Mitigation[];
};
type Cve = {
  external_id: string;
  name: string;
  description: string | null;
  reference_url: string | null;
  source_version: string | null;
};
type CvePage = { page: number; size: number; total: number; items: Cve[] };

const PAGE_SIZE = 10;
const KNOWN_TECHNIQUE = /^T\d{4}(?:\.\d{3})?$/i;
const fmt = (value: number | undefined) => typeof value === "number" ? value.toLocaleString("es-MX") : "—";

function explainError(error: unknown) {
  if (
    error instanceof Error &&
    error.message.startsWith("Respuesta inválida")
  ) return error.message;
  if (error && typeof error === "object" && "status" in error) {
    const status = (error as { status?: number }).status;
    if (status === 401) return "Tu sesión no está autorizada. Vuelve a iniciar sesión.";
    if (status === 404) return "La técnica solicitada no existe en el catálogo.";
    if (status === 422) return "Revisa el identificador o texto de búsqueda.";
  }
  return "No fue posible consultar la API. Revisa la conexión y el estado del servidor.";
}

export default function IntelligenceLivePanel() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [query, setQuery] = useState("T1110");
  const [mode, setMode] = useState<"technique" | "cve">("technique");
  const [technique, setTechnique] = useState<Technique | null>(null);
  const [cvePage, setCvePage] = useState<CvePage | null>(null);
  const [term, setTerm] = useState("T1110");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);

  useEffect(() => {
    let alive = true;
    api<Summary>("/intelligence/summary")
      .then(data => {
        if (
          !data ||
          typeof data !== "object" ||
          typeof data.vulnerabilities !== "number"
        ) {
          throw new Error(
            "Respuesta inválida del resumen. Comprueba la conexión de Vite con FastAPI."
          );
        }
        if (alive) setSummary(data);
      })
      .catch(error => { if (alive) setSummaryError(explainError(error)); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    const version = ++requestVersion.current;
    let alive = true;
    setBusy(true);
    setError(null);
    const run = mode === "technique"
      ? api<Technique>(`/intelligence/techniques/${encodeURIComponent(term)}`)
          .then(data => {
            if (
              !data ||
              typeof data !== "object" ||
              typeof data.attack_id !== "string" ||
              !Array.isArray(data.mitigations)
            ) {
              throw new Error(
                "Respuesta inválida de MITRE. La API no devolvió una lista de mitigaciones; revisa el proxy de Vite."
              );
            }
            if (alive && version === requestVersion.current) {
              setTechnique(data);
            }
          })
      : api<CvePage>(`/intelligence/vulnerabilities?search=${encodeURIComponent(term)}&page=${page}&size=${PAGE_SIZE}`)
          .then(data => {
            if (
              !data ||
              typeof data !== "object" ||
              !Array.isArray(data.items)
            ) {
              throw new Error(
                "Respuesta inválida de CISA. La API no devolvió una lista de CVE."
              );
            }
            if (alive && version === requestVersion.current) {
              setCvePage(data);
            }
          });
    run.catch(err => { if (alive && version === requestVersion.current) setError(explainError(err)); })
       .finally(() => { if (alive && version === requestVersion.current) setBusy(false); });
    return () => { alive = false; };
  }, [mode, term, page]);

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = query.trim();
    if (!value) return;
    setError(null);
    setTechnique(null);
    setCvePage(null);
    setPage(1);
    if (KNOWN_TECHNIQUE.test(value)) {
      setMode("technique");
      setTerm(value.toUpperCase());
    } else {
      setMode("cve");
      setTerm(value.slice(0, 100));
    }
  }

  return <>
    <div className="csd-page-heading">
      <div><span className="csd-eyebrow">INTEGRACIÓN REAL · FASE 2</span>
        <h1>Inteligencia de amenazas</h1>
        <p>Consultas en vivo a PostgreSQL mediante FastAPI, con tu sesión JWT actual.</p>
      </div>
      <span className="csd-pill csd-pill-teal"><ShieldCheck size={15}/> Fuente: API autenticada</span>
    </div>
    <div className="csd-stats">
      {([
        ["CVE de CISA KEV", summary?.vulnerabilities, Database],
        ["Técnicas MITRE", summary?.techniques, Activity],
        ["Mitigaciones", summary?.mitigations, ShieldCheck],
        ["Relaciones", summary?.relationships, BookOpen],
      ] as const).map(([label, value, Icon]) =>
        <div className="csd-stat" key={label}>
          <div className="csd-stat-heading"><span>{label}</span><span className="csd-small-icon csd-icon-blue"><Icon size={18}/></span></div>
          <strong>{fmt(value)}</strong><small>Dato obtenido desde CyberShield API</small>
        </div>
      )}
    </div>
    {summaryError && <div className="csd-callout" role="alert"><TriangleAlert size={18}/><span>{summaryError}</span></div>}
    <div className="csd-two-thirds">
      <section className="csd-panel">
        <div className="csd-sectionhead"><span className="csd-iconbox"><Search size={19}/></span><div>
          <h2>Explorador de inteligencia</h2><p>Busca T1110, T1059.001, un CVE o parte del nombre de una vulnerabilidad.</p>
        </div></div>
        <form onSubmit={search} style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:18}}>
          <input aria-label="Técnica o vulnerabilidad" value={query} onChange={e=>setQuery(e.target.value)} maxLength={100}
            placeholder="T1110 o CVE-2026-..." style={{flex:"1 1 240px",minWidth:0,padding:"11px 14px",border:"1px solid #c9d9ed",borderRadius:12,color:"#153052",background:"#fff"}}/>
          <button className="csd-btn csd-btn-primary" type="submit" disabled={busy}><Search size={16}/> Consultar</button>
        </form>
        {busy && <p className="csd-muted" role="status">Consultando datos reales...</p>}
        {error && <div className="csd-callout" role="alert"><TriangleAlert size={18}/><span>{error}</span></div>}
        {!busy && !error && mode === "technique" && technique && <>
          <div className="csd-highlight"><span className="csd-pill csd-pill-blue">{technique.attack_id}</span>
            <h3>{technique.name}</h3><p style={{whiteSpace:"pre-line"}}>{technique.description || "Sin descripción disponible"}</p>
          </div>
          <h3 className="csd-subtitle">Mitigaciones oficiales ({technique.mitigation_count})</h3>
          {technique.mitigations.map(m => <div className="csd-norm" key={m.mitigation_id}>
            <span className="csd-pill csd-pill-teal">{m.mitigation_id}</span>
            <div><b>{m.name}</b><small style={{whiteSpace:"pre-line"}}>{m.description || "Sin descripción en el catálogo"}</small></div>
          </div>)}
          {technique.mitigations.length === 0 && <p className="csd-muted">No hay mitigaciones vinculadas para esta técnica.</p>}
        </>}
        {!busy && !error && mode === "cve" && cvePage && <>
          <p className="csd-muted">{fmt(cvePage.total)} coincidencias · Página {cvePage.page}</p>
          {cvePage.items.map(cve => <div className="csd-norm" key={cve.external_id} style={{alignItems:"flex-start"}}>
            <span className="csd-pill csd-pill-blue">{cve.external_id}</span>
            <div><b>{cve.name}</b><small style={{whiteSpace:"pre-line"}}>{cve.description || "Sin descripción disponible"}</small>
              {cve.reference_url && /^https:\/\//i.test(cve.reference_url) &&
                <a href={cve.reference_url} target="_blank" rel="noopener noreferrer" style={{color:"#1665c1",fontSize:13}}>Consultar referencia</a>}
            </div>
          </div>)}
          {cvePage.items.length === 0 && <p className="csd-muted">No hay coincidencias para esa búsqueda.</p>}
          <div style={{display:"flex",gap:12,justifyContent:"flex-end",marginTop:18}}>
            <button className="csd-btn csd-btn-outline" onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page<=1}><ArrowLeft size={15}/> Anterior</button>
            <button className="csd-btn csd-btn-outline" onClick={()=>setPage(p=>p+1)} disabled={page*PAGE_SIZE>=cvePage.total}>Siguiente <ArrowRight size={15}/></button>
          </div>
        </>}
      </section>
      <div className="csd-stack">
        <section className="csd-panel">
          <div className="csd-sectionhead"><span className="csd-iconbox"><BookOpen size={19}/></span><div><h2>Fuentes verificadas</h2><p>Conocimiento documental</p></div></div>
          <div className="csd-norm"><span className="csd-pill csd-pill-blue">CISA</span><div><b>Known Exploited Vulnerabilities</b><small>Vulnerabilidades explotadas conocidas</small></div></div>
          <div className="csd-norm"><span className="csd-pill csd-pill-blue">MITRE</span><div><b>ATT&CK Enterprise</b><small>Técnicas y mitigaciones relacionadas</small></div></div>
        </section>
        <section className="csd-panel">
          <div className="csd-sectionhead"><span className="csd-iconbox"><ShieldCheck size={19}/></span><div><h2>Interpretación correcta</h2><p>Sin resultados falsos</p></div></div>
          <p className="csd-copy">Las técnicas y CVE son información de referencia. No significan que tu servidor haya sufrido ese ataque.</p>
          <p className="csd-copy">Tampoco implican que una mitigación haya sido aplicada. Eso se comprueba con las evidencias de cada incidente.</p>
        </section>
      </div>
    </div>
  </>;
}
