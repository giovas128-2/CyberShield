import { Info, WifiOff } from "lucide-react";

export function SimBanner({ demo, stale }: { demo: boolean; stale: boolean }) {
  if (!demo && !stale) return null;
  return (
    <div className="demo">
      {stale ? <WifiOff size={16} /> : <Info size={16} />}
      {stale
        ? "Sin conexión · Se muestran los últimos datos reales recibidos."
        : "DATOS SIMULADOS · Frontend desacoplado: datos del mock local."}
    </div>
  );
}
