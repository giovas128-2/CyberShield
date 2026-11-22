import { useEffect, useState } from "react";
import { Activity, BookOpen, Database, Layers3, LockKeyhole, ShieldAlert, ShieldCheck } from "lucide-react";
import { api } from "../api/client";
import ThreatCatalogPanel from "../components/ThreatCatalogPanel";
import ProtectionOfficialResearch from "../components/ProtectionOfficialResearch";
import "../styles/operations-redesign.css";
import "../styles/catalog-blue.css";

type IntelligenceSummary = {
  vulnerabilities: number;
  techniques: number;
  mitigations: number;
  relationships: number;
};

function fmtNumber(value: number | undefined): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString("es-MX")
    : "—";
}

/** Pantalla documental independiente. No instala ni activa controles. */
export default function CatalogPage() {
  const [summary, setSummary] = useState<IntelligenceSummary | null>(null);

  useEffect(() => {
    let mounted = true;
    api<IntelligenceSummary>("/intelligence/summary")
      .then(result => {
        if (mounted && typeof result.techniques === "number" &&
            typeof result.vulnerabilities === "number" &&
            typeof result.mitigations === "number" &&
            typeof result.relationships === "number") {
          setSummary(result);
        }
      })
      .catch(() => { if (mounted) setSummary(null); });
    return () => { mounted = false; };
  }, []);

  const total = summary ? summary.techniques + summary.vulnerabilities : undefined;

  return <div className="cs-ops cs-catalog">
    <header className="cs-catalog-hero">
      <div className="cs-catalog-hero-top">
        <span className="cs-catalog-eyebrow"><ShieldCheck size={16}/> CYBERSHIELD INTELLIGENCE</span>
        <span className="cs-catalog-hero-mode"><span/> INVESTIGACIÓN DOCUMENTAL</span>
      </div>
      <div className="cs-catalog-hero-content">
        <div className="cs-catalog-hero-copy">
          <p className="cs-catalog-hero-overline">CENTRO DE INTELIGENCIA DE AMENAZAS</p>
          <h1>Catálogo</h1>
          <p className="cs-catalog-lead">
            Explora amenazas y técnicas documentadas, consulta evidencia
            oficial y analiza su relación con la seguridad de tus servidores.
            Toda la información se consulta desde PostgreSQL.
          </p>
          <div className="cs-catalog-tags">
            <span><BookOpen size={14}/> MITRE ATT&CK</span>
            <span><ShieldCheck size={14}/> CISA KEV</span>
            <span><Database size={14}/> PostgreSQL</span>
          </div>
        </div>
        <div className="cs-catalog-emblem" aria-hidden="true">
          <div className="cs-catalog-orbit cs-catalog-orbit-one"/>
          <div className="cs-catalog-orbit cs-catalog-orbit-two"/>
          <div className="cs-catalog-emblem-core"><ShieldCheck size={57} strokeWidth={1.55}/></div>
          <span className="cs-catalog-orbit-point one"/>
          <span className="cs-catalog-orbit-point two"/>
        </div>
      </div>
    </header>

    <section className="cs-catalog-metrics" aria-label="Resumen del catálogo importado">
      <article className="cs-catalog-metric">
        <span className="cs-catalog-metric-label"><Database size={18}/> Registros documentales</span>
        <strong>{fmtNumber(total)}</strong>
        <small>Total MITRE + CISA actualmente almacenado</small>
      </article>
      <article className="cs-catalog-metric">
        <span className="cs-catalog-metric-label"><Layers3 size={18}/> Técnicas MITRE</span>
        <strong>{fmtNumber(summary?.techniques)}</strong>
        <small>Incluye técnicas y subtécnicas</small>
      </article>
      <article className="cs-catalog-metric">
        <span className="cs-catalog-metric-label"><ShieldAlert size={18}/> Vulnerabilidades CISA</span>
        <strong>{fmtNumber(summary?.vulnerabilities)}</strong>
        <small>Registros del catálogo KEV importado</small>
      </article>
      <article className="cs-catalog-metric">
        <span className="cs-catalog-metric-label"><Activity size={18}/> Mitigaciones MITRE</span>
        <strong>{fmtNumber(summary?.mitigations)}</strong>
        <small>Mitigaciones documentales; no instaladas</small>
      </article>
    </section>

    <div className="cs-catalog-notice">
      <LockKeyhole size={18}/>
      <span>Modo consulta: estas fichas no indican ataques detectados en tu infraestructura ni protecciones instaladas. No se ejecutan respuestas automáticas desde el catálogo.</span>
    </div>

    <ThreatCatalogPanel />
    <ProtectionOfficialResearch />
  </div>;
}
