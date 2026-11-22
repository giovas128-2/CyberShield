import { BookOpen, Database, ShieldAlert } from "lucide-react";
import ThreatCatalogPanel from "../components/ThreatCatalogPanel";
import ProtectionOfficialResearch from "../components/ProtectionOfficialResearch";
import "../styles/operations-redesign.css";

/** Vista documental. No instala ni habilita controles defensivos. */
export default function CatalogPage() {
  return <div className="cs-ops">
    <header className="cs-ops-hero">
      <div className="cs-ops-hero-icon"><Database size={27}/></div>
      <div className="cs-ops-hero-copy">
        <span className="cs-ops-eyebrow">INTELIGENCIA DE CIBERSEGURIDAD</span>
        <h1>Catálogo</h1>
        <p>Consulta técnicas de MITRE ATT&CK, vulnerabilidades de CISA KEV y referencias oficiales de NIST y CIS. Los registros provienen de la base de datos y se muestran con sus fuentes documentales.</p>
      </div>
      <div className="cs-ops-hero-chip"><BookOpen size={16}/> Información documentada</div>
    </header>
    <div className="cs-ops-advisory">
      <ShieldAlert size={16}/>
      <span>Este catálogo reúne información para investigación. Sus registros no equivalen a ataques detectados ni a protecciones instaladas.</span>
    </div>
    <ThreatCatalogPanel />
    <ProtectionOfficialResearch />
  </div>;
}
