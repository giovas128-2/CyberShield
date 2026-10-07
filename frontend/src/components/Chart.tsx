export function Chart({ data }: { data: number[] }) {
  const max = Math.max(12, ...data), W = 560, H = 160;
  const pts = data.map((v, i) => `${(i / Math.max(1, data.length - 1)) * W},${H - (v / max) * (H - 10)}`).join(" ");
  return <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="170" preserveAspectRatio="none">{[0,1,2,3].map((i)=><line key={i} x1="0" x2={W} y1={(i*H)/3} y2={(i*H)/3} stroke="#1e2b3a" />)}<polygon points={`0,${H} ${pts} ${W},${H}`} fill="#53dbee22" /><polyline points={pts} fill="none" stroke="#53dbee" strokeWidth="2" /></svg>;
}
