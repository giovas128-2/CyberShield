import { useOutletContext } from "react-router-dom";
import { DashboardView } from "./DashboardView";
import type { CyberShieldCtx } from "../hooks/useCyberShieldData";

export default function DashboardPage() {
  const ctx = useOutletContext<CyberShieldCtx>();
  return <DashboardView d={ctx.dashboardData} simulate={ctx.simulate} />;
}
