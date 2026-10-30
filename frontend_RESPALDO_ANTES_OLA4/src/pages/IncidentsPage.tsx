import { useOutletContext } from "react-router-dom";
import { IncidentsView } from "./IncidentsView";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";

export default function IncidentsPage() {
  const ctx = useOutletContext<CyberShieldCtx>();
  return (
    <IncidentsView
      list={ctx.incidents}
      selId={ctx.selId}
      setSelId={ctx.setSelId}
      onInvestigate={(incident) => ctx.changeStatus(incident, "investigating")}
      onResolve={(incident) => ctx.changeStatus(incident, "resolved")}
    />
  );
}
