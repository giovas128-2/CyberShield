import { useEffect, useState } from "react";
import { BrainCircuit, ClipboardCheck, RefreshCw } from "lucide-react";
import { api, ApiError } from "../api/client";

type Analysis = {
  incident_id: number;
  engine: string;
  ai_generated: boolean;
  classification: {
    severity: string; priority: string; simulated: boolean;
    mitre_technique_id: string | null; mitre_tactic: string | null;
    scope: string | null;
  };
  summary: string;
  evidence: {label:string;value:string;source:string}[];
  recommendation: string;
  investigation_steps: string[];
  response_assessment: string;
  frameworks: {name:string;basis:string;technique_id?:string|null}[];
  disclaimer: string;
};
export default function IncidentAnalysisPanel({incidentId}:{incidentId:number}) {
  const [result,setResult] = useState<Analysis|null>(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState("");
  const [revision,setRevision] = useState(0);
  useEffect(()=>{
    if (!Number.isInteger(incidentId) || incidentId < 1) {
      setResult(null);setLoading(false);setError("ID de incidente inválido");return;
    }
    const controller = new AbortController();
    setLoading(true);setError("");setResult(null);
    api<Analysis>(`/incidents/${incidentId}/analysis`,"GET",undefined,controller.signal)
      .then(data=>{if (!controller.signal.aborted) setResult(data);})
      .catch(err=>{
        if (!controller.signal.aborted)
          setError(err instanceof ApiError ? err.message : "No se pudo consultar el análisis.");
      })
      .finally(()=>{if (!controller.signal.aborted) setLoading(false);});
    return ()=>controller.abort();
  },[incidentId,revision]);
  return <section className="card" style={{padding:18,marginTop:16}}>
    <div className="row" style={{padding:0,alignItems:"center",justifyContent:"space-between"}}>
      <h3 style={{margin:0}}><BrainCircuit size={19}/> Análisis inteligente del incidente</h3>
      <button className="btn sm gh" type="button" disabled={loading} onClick={()=>setRevision(n=>n+1)}><RefreshCw size={14}/> Actualizar</button>
    </div>
    {loading && <p role="status" className="mu">Analizando registros del incidente...</p>}
    {error && <p role="alert" className="mu">{error}</p>}
    {result && <>
      <p className="mu" style={{marginTop:12}}>Motor: {result.ai_generated ? "IA generativa" : "Análisis automatizado por reglas (sin IA generativa)"} · Prioridad sugerida: <b>{result.classification.priority}</b> · {result.classification.simulated ? "Simulación de laboratorio" : "Origen según registro"}</p>
      <p>{result.summary}</p>
      <div style={{display:"grid",gap:8,marginTop:12}}>
        <strong><ClipboardCheck size={16}/> Evidencia disponible</strong>
        {result.evidence.map((entry,index)=><div key={index} className="mu" style={{display:"flex",justifyContent:"space-between",gap:12,flexWrap:"wrap"}}>
          <span>{entry.label}: <b>{entry.value}</b></span><small>{entry.source}</small>
        </div>)}
      </div>
      <div className="reco recommendation-panel" style={{marginTop:14}}><b>Interpretación de la respuesta</b><p>{result.response_assessment}</p></div>
      <div className="reco recommendation-panel" style={{marginTop:12}}><b>Recomendación para el analista</b><p>{result.recommendation}</p></div>
      <p className="mu" style={{marginTop:12}}>Marcos de referencia: {result.frameworks.map(f=>`${f.name} (${f.basis})`).join(" · ")}</p>
      <small className="mu">{result.disclaimer}</small>
    </>}
  </section>;
}
