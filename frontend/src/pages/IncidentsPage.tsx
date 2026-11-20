import { useOutletContext } from "react-router-dom";
import { IncidentsView } from "./IncidentsView";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";
import { useVisibleSeverities } from "../hooks/useVisibleSeverities";

export default function IncidentsPage() {
  const ctx = useOutletContext<CyberShieldCtx>();
  const visibleLevels = useVisibleSeverities();
  return (
    <IncidentsView
      list={ctx.incidents}
      visibleLevels={visibleLevels}
      selId={ctx.selId}
      setSelId={ctx.setSelId}
      onInvestigate={(incident) => ctx.changeStatus(incident, "investigating")}
      onResolve={(incident) => ctx.changeStatus(incident, "resolved")}
    />
  );
}
