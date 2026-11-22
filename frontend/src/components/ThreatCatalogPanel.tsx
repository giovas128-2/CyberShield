import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { AlertTriangle, BookOpen, ChevronLeft, ChevronRight, Database, ExternalLink, Search, ShieldAlert } from "lucide-react";
import { api } from "../api/client";
import MitreMitigations from "./MitreMitigations";
import CisaRemediationPanel from "./CisaRemediationPanel";
import "../styles/threat-catalog.css";

type CatalogKind = "all" | "mitre" | "cisa";
type ThreatRecord = {
  kind: "mitre" | "cisa";
  external_id: string;
  name: string;
  description: string | null;
  source_name: string;
  source_url: string;
  source_version: string | null;
  documented_at: string | null;
  is_subtechnique: boolean;
  reference_url: string | null;
  evidence_status: "official_catalog_imported";
  protection_installed: false;
  cisa_required_action: string | null;
  cisa_action_origin: string | null;
};
type CatalogResponse = {
  kind: CatalogKind;
  page: number;
  size: number;
  total: number;
  items: ThreatRecord[];
  read_only: boolean;
  automatic_application: boolean;
  note: string;
};

const PAGE_SIZE = 10;
const modes: { key: CatalogKind; label: string }[] = [
  { key: "all", label: "Todas las fuentes" },
  { key: "mitre", label: "MITRE ATT&CK" },
  { key: "cisa", label: "CISA KEV" },
];

function friendlyDate(value: string | null) {
  if (!value) return "Sin fecha registrada";
  const time = new Date(value);
  if (Number.isNaN(time.getTime())) return "Sin fecha válida";
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium" }).format(time);
}

export default function ThreatCatalogPanel() {
  const [kind, setKind] = useState<CatalogKind>("all");
  const [draft, setDraft] = useState("");
  const [term, setTerm] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<CatalogResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const params = new URLSearchParams({
      kind, page: String(page), size: String(PAGE_SIZE), search: term,
    });
    api<CatalogResponse>(`/intelligence/threat-catalog?${params.toString()}`, "GET", undefined, controller.signal)
      .then(result => {
        if (!Array.isArray(result.items) || typeof result.total !== "number") {
          throw new Error("La API devolvió un catálogo incompleto.");
        }
        if (!controller.signal.aborted) setData(result);
      })
      .catch(err => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(err instanceof Error ? err.message : "No se pudo consultar el catálogo.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [kind, term, page]);

  function onSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setTerm(draft.trim());
  }

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return <section className="cs-threat" aria-label="Catálogo documental de amenazas">
    <div className="cs-threat-head">
      <div className="cs-threat-icon"><ShieldAlert size={23}/></div>
      <div className="cs-threat-heading">
        <span className="cs-ops-kicker">INTELIGENCIA DEFENSIVA · FUENTES DOCUMENTADAS</span>
        <h2>Catálogo de amenazas verificables</h2>
        <p>Explora técnicas MITRE ATT&CK y vulnerabilidades del catálogo CISA KEV ya importadas en PostgreSQL.</p>
      </div>
      <div className="cs-threat-count"><Database size={16}/>{loading ? "Consultando…" : error ? "Sin conexión" : `${total.toLocaleString("es-MX")} registros`}</div>
    </div>
    <div className="cs-threat-note"><BookOpen size={16}/>
      <span>Una técnica MITRE no equivale a una vulnerabilidad CISA, ni un registro documental significa que exista una protección instalada. Esta vista no aplica reglas ni ejecuta respuestas.</span>
    </div>

    <div className="cs-threat-tools">
      <div className="cs-threat-filters" role="group" aria-label="Filtrar fuente de inteligencia">
        {modes.map(option => <button key={option.key} type="button"
          className={kind === option.key ? "is-active" : ""}
          aria-pressed={kind === option.key}
          onClick={() => { setKind(option.key); setPage(1); }}>
          {option.label}
        </button>)}
      </div>
      <form className="cs-threat-search" onSubmit={onSearch}>
        <label htmlFor="cs-threat-term" className="cs-threat-sr">Buscar técnicas o vulnerabilidades</label>
        <Search size={17}/>
        <input id="cs-threat-term" placeholder="Ej. T1110, CVE-2025 o fuerza bruta"
          value={draft} maxLength={100} onChange={e => setDraft(e.target.value)}/>
        <button type="submit">Buscar</button>
      </form>
    </div>

    {loading && <p role="status" className="cs-threat-status">Consultando catálogo local…</p>}
    {!loading && error && <div className="cs-threat-error" role="alert">
      <AlertTriangle size={18}/>
      <span>No fue posible leer el catálogo. {error} Comprueba que el backend esté ejecutando la rama nueva y que tu sesión siga activa.</span>
    </div>}
    {!loading && data && <>
      {data.items.length === 0 && <p className="cs-threat-status">No se encontraron registros. Revisa los filtros o confirma si ya importaste los catálogos oficiales.</p>}
      <div className="cs-threat-grid">
        {data.items.map(item => <article className="cs-threat-item" key={`${item.kind}:${item.external_id}`}>
          <div className="cs-threat-item-top">
            <span className={`cs-threat-tag ${item.kind === "mitre" ? "is-mitre" : "is-cisa"}`}>
              {item.kind === "mitre" ? (item.is_subtechnique ? "MITRE · Subtécnica" : "MITRE · Técnica") : "CISA · CVE"}
            </span>
            <span className="cs-threat-id">{item.external_id}</span>
          </div>
          <h3>{item.name}</h3>
          <p className="cs-threat-description">{item.description || "Sin descripción disponible en el catálogo importado."}</p>
          <div className="cs-threat-metadata">
            <span>Fuente: {item.source_name}</span>
            <span>Versión: {item.source_version || "No registrada"}</span>
            <span>Fecha documental: {friendlyDate(item.documented_at)}</span>
          </div>
          {item.kind === "mitre" && <MitreMitigations attackId={item.external_id}/>}
          {item.kind === "cisa" && <CisaRemediationPanel
            cveId={item.external_id}
            requiredAction={item.cisa_required_action}
            origin={item.cisa_action_origin}
            referenceUrl={item.reference_url}
          />}
          {item.reference_url && <a href={item.reference_url} target="_blank" rel="noopener noreferrer">
            Consultar referencia oficial <ExternalLink size={14}/>
          </a>}
        </article>)}
      </div>
      {total > 0 && <div className="cs-threat-pagination">
        <span>Mostrando {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} de {total.toLocaleString("es-MX")}</span>
        <div>
          <button type="button" disabled={page <= 1} onClick={() => setPage(p => p - 1)} aria-label="Página anterior"><ChevronLeft size={16}/>Anterior</button>
          <span>Página {page} de {totalPages}</span>
          <button type="button" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Siguiente<ChevronRight size={16}/></button>
        </div>
      </div>}
    </>}
  </section>;
}
