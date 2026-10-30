import { Play, Square } from "lucide-react";
import { useEffect, useState } from "react";
import { EVIDENCE_ATTACKS, EVIDENCE_SCENARIOS, EVIDENCE_SIMULATIONS } from "../../mocks/evidenceMock";

/* D3: ahora también elige el ataque del mock (?ataque=brute_force|ransomware) y el estado escalado. El componente de evidencia es el MISMO para todos.
   SOLO PARA DESARROLLO / DEMO CON MOCK. BACKEND_GISS: borrar este componente y su uso en EvidencePage.tsx cuando llegue el endpoint real
   (con backend real el estado lo dicta el incidente, no un botón). El estado elegido vive en la URL (?estado=...), por eso recargar la página lo conserva. */
const FLOW = ["detected", "responding", "contained"];

export function MockStateSwitcher({ current, attack, onPick, onAttack }: { current: string; attack: string; onPick: (estado: string) => void; onAttack: (ataque: string) => void }) {
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing) return;
    let i = Math.max(0, FLOW.indexOf(current));
    if (current !== FLOW[0]) { i = 0; onPick(FLOW[0]); }
    const t = setInterval(() => {
      i += 1;
      if (i >= FLOW.length) { clearInterval(t); setPlaying(false); return; }
      onPick(FLOW[i]);
    }, 2600);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing]);

  return (
    <div className="ev-demo" role="group" aria-label="Estado del mock (solo desarrollo)">
      <small>MOCK · ATAQUE</small>
      {EVIDENCE_ATTACKS.map((a) => <button key={a.key} aria-pressed={attack === a.key} onClick={() => { setPlaying(false); onAttack(a.key); }}>{a.label}</button>)}
      <span className="sep" />
      <small>ESTADO DEL INCIDENTE</small>
      {EVIDENCE_SCENARIOS.map((s) => <button key={s.key} aria-pressed={current === s.key} onClick={() => { setPlaying(false); onPick(s.key); }}>{s.label}</button>)}
      <button className="play" onClick={() => setPlaying((p) => !p)}>{playing ? <><Square size={12} /> Detener</> : <><Play size={12} /> Reproducir flujo</>}</button>
      <span className="sep" />
      <small>SIMULAR API</small>
      {EVIDENCE_SIMULATIONS.map((s) => <button key={s.key} aria-pressed={current === s.key} onClick={() => { setPlaying(false); onPick(s.key); }}>{s.label}</button>)}
    </div>
  );
}
