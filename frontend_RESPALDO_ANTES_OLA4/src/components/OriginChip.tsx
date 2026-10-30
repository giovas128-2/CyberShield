/* Indica el ORIGEN de lo que se ve en pantalla: backend real, datos simulados o sin conexión (últimos datos reales). */
export function OriginChip({ demo, stale, at }: { demo: boolean; stale: boolean; at: Date }) {
  const utc = at.toISOString().slice(0, 16).replace("T", " ") + " UTC";
  if (stale) return <span className="origin er" title="El backend no responde; se muestran los últimos datos reales recibidos">SIN CONEXIÓN · ÚLTIMOS DATOS REALES · {utc}</span>;
  if (demo) return <span className="origin wn" title="El backend nunca respondió en esta sesión">ORIGEN: DEMO · DATOS SIMULADOS</span>;
  return <span className="origin ok">ORIGEN: BACKEND REAL · {utc}</span>;
}
