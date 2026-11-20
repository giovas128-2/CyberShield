import { useEffect, useState } from "react";
import { AlertTriangle, BookOpen, CheckCircle2, Clock3, ExternalLink,
  FileSearch, Globe2, Loader2, RefreshCw, ShieldCheck } from "lucide-react";
import { api } from "../api/client";
import "../styles/protection-official-research.css";

type SourceKey = "mitre" | "nist" | "cis" | "cisa";
type OfficialSource = {
  key: SourceKey; name: string; url: string;
  baseline_version: string | null; observed_version: string | null;
  last_checked_at: string | null; last_success_at: string | null;
  last_changed_at: string | null; status: "verified" | "unavailable" | "not_checked";
  needs_review: boolean; record_count: number | null;
};
type ControlReference = {
  id: string; name: string; mode: string; mapping_status: string;
  mitre: {id: string; url: string}[]; nist: string[]; cis: string[];
};
type Research = {
  configured: boolean; sources: OfficialSource[];
  controls: ControlReference[]; automatic_application: boolean;
  note: string; failed_sources?: string[];
};

function formatted(date: string | null): string {
  if (!date) return "Sin comprobación";
  const value = new Date(date);
  return Number.isNaN(value.getTime()) ? "Sin fecha válida"
    : new Intl.DateTimeFormat("es-MX", {dateStyle: "medium", timeStyle: "short"}).format(value);
}

function stateLabel(source: OfficialSource): string {
  if (source.status === "unavailable") return "No disponible";
  if (source.status !== "verified") return "Pendiente de consulta";
  return source.needs_review ? "Cambio por revisar" : "Versión observada";
}

export default function ProtectionOfficialResearch() {
  const [data, setData] = useState<Research | null>(null);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api<Research>("/intelligence/official-frameworks")
      .then(report => {
        if (!Array.isArray(report.sources) || !Array.isArray(report.controls)) {
          throw new Error("Respuesta oficial incompleta");
        }
        if (mounted) setData(report);
      })
      .catch(() => {if (mounted) setError("No fue posible leer las referencias oficiales desde el backend.");})
      .finally(() => {if (mounted) setLoading(false);});
    return () => { mounted = false; };
  }, []);

  async function checkNow() {
    if (checking || !data?.configured) return;
    setChecking(true);
    setError("");
    try {
      const result = await api<Research>("/intelligence/official-frameworks/check", "POST");
      if (!Array.isArray(result.sources) || !Array.isArray(result.controls)) {
        throw new Error("Respuesta oficial incompleta");
      }
      setData(result);
      if (result.failed_sources?.length) {
        setError("Algunas fuentes oficiales no respondieron. Sus datos anteriores permanecen identificados como históricos.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron revisar las fuentes oficiales.");
    } finally {
      setChecking(false);
    }
  }

  const reviewed = data?.sources.filter(s => s.needs_review).length ?? 0;
  const lastSuccessful = data?.sources.filter(s => s.last_success_at).length ?? 0;
  const byKey = Object.fromEntries((data?.sources ?? []).map(source => [source.key, source])) as Partial<Record<SourceKey, OfficialSource>>;

  return <section className="cs-official" aria-label="Investigación de marcos y fuentes oficiales">
    <header className="cs-official-head">
      <span className="cs-official-icon"><Globe2 size={23}/></span>
      <div className="cs-official-heading">
        <span className="cs-ops-kicker">INTELIGENCIA DOCUMENTAL · FUENTES OFICIALES</span>
        <h2>Vigilancia de normas, marcos y amenazas</h2>
        <p>Comprueba versiones reales de MITRE, NIST y CIS, y cambios en el catálogo CISA KEV. Las ocho protecciones se muestran con referencias de investigación.</p>
      </div>
      <button className="cs-official-refresh" type="button" disabled={checking || loading || !data?.configured} onClick={checkNow}>
        {checking ? <Loader2 size={15} className="spin"/> : <RefreshCw size={15}/>}
        {checking ? "Consultando..." : "Consultar fuentes oficiales"}
      </button>
    </header>

    <div className="cs-official-disclaimer">
      <ShieldCheck size={17}/>
      <span>Las consultas salen del backend hacia cuatro sitios públicos oficiales. No se envían incidentes, datos de servidores ni credenciales a terceros o a una IA externa. Esta función no instala reglas ni certifica cumplimiento.</span>
    </div>
    {loading && <p className="cs-official-feedback"><Loader2 size={17} className="spin"/> Cargando historial documental…</p>}
    {error && <p className="cs-official-feedback is-error" role="alert"><AlertTriangle size={17}/>{error}</p>}
    {data && <>
      {!data.configured && <p className="cs-official-feedback is-warning"><AlertTriangle size={17}/> Falta aplicar la migración 013 a PostgreSQL. Las referencias son visibles, pero la investigación automática aún no se puede ejecutar.</p>}
      <div className="cs-official-counters">
        <div><strong>8</strong><span>Controles originales relacionados</span></div>
        <div><strong>{lastSuccessful}/4</strong><span>Fuentes con consulta histórica correcta</span></div>
        <div><strong>{reviewed}</strong><span>Fuentes con cambios pendientes de estudiar</span></div>
      </div>

      <div className="cs-official-source-grid">
        {data.sources.map(source => <article className="cs-official-source" key={source.key}>
          <div className="cs-official-source-top">
            <span className="cs-official-source-symbol"><BookOpen size={18}/></span>
            <span className={"cs-official-state " + (source.status === "unavailable" ? "is-unavailable" : source.needs_review ? "is-review" : "is-neutral")}>
              {source.status === "verified" && !source.needs_review ? <CheckCircle2 size={13}/> : <Clock3 size={13}/>}
              {stateLabel(source)}
            </span>
          </div>
          <h3>{source.name}</h3>
          <p className="cs-official-source-version">{source.observed_version ? "Versión observada: " + source.observed_version : "Versión aún no comprobada"}</p>
          {source.record_count != null && <p className="cs-official-source-count">{source.record_count.toLocaleString("es-MX")} registros en el catálogo CISA KEV</p>}
          <small>Última comprobación: {formatted(source.last_checked_at)}</small>
          {source.status === "unavailable" && <small>La última consulta falló; no se afirma que esté actualizado.</small>}
          {source.needs_review && <small>Referencia inicial: {source.baseline_version ?? "Sin versión"} · El cambio no se ha aplicado.</small>}
          <a href={source.url} target="_blank" rel="noopener noreferrer">Consultar publicación oficial <ExternalLink size={14}/></a>
        </article>)}
      </div>

      <div className="cs-official-section-title">
        <div><span className="cs-ops-kicker">RELACIÓN POR CONTROL</span><h3>Referencias para las ocho protecciones</h3><p>Correspondencias orientativas; la pertinencia de cada norma debe verificarse antes de configurar una defensa.</p></div>
      </div>
      <div className="cs-official-control-grid">
        {data.controls.map((control) => <article key={control.id} className="cs-official-control">
          <div className="cs-official-control-head">
            <span className="cs-official-control-id">{control.id.toUpperCase()}</span>
            <span>{control.mode === "integrated" ? "Integrada" : control.mode === "simulated" ? "Simulada" : "Pendiente"}</span>
          </div>
          <h4>{control.name}</h4>
          <div className="cs-official-ref-group">
            <strong>MITRE ATT&CK</strong>
            {control.mitre.length ? <div className="cs-official-techniques">{control.mitre.map(t =>
              <a key={t.id} href={t.url} rel="noopener noreferrer" target="_blank">{t.id} <ExternalLink size={12}/></a>
            )}</div> : <small>Sin clasificación validada</small>}
          </div>
          <div className="cs-official-ref-group"><strong>NIST CSF</strong>
            {control.nist.length ? control.nist.map(n => <small key={n}>{n}</small>) : <small>Por evaluar</small>}
          </div>
          <div className="cs-official-ref-group"><strong>CIS Controls</strong>
            {control.cis.length ? control.cis.map(c => <small key={c}>{c}</small>) : <small>Por evaluar</small>}
          </div>
          {(["mitre","nist","cis"] as const).some(key => byKey[key]?.needs_review) &&
            <p className="cs-official-review-note"><AlertTriangle size={14}/> Una fuente cambió de versión: revisar si afecta a este control.</p>}
        </article>)}
      </div>
      <p className="cs-official-foot"><FileSearch size={15}/> CISA KEV se consulta como catálogo general de vulnerabilidades explotadas conocidas: una CVE no se atribuye a ninguna de las ocho protecciones sin comprobar el producto afectado y su relevancia. Los cambios de referencia no se implementan automáticamente.</p>
    </>}
  </section>;
