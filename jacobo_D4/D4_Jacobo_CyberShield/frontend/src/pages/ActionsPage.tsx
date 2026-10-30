/* BACKEND_GISS: ActionItem[] <- getActions() (services/management.ts): id, type, target, status, incident_id, created_at, reversible, mode. */
import { Link } from "react-router-dom";
import { DataTable, ModeBadge, PageHeader, Pill, ResourceView } from "../components/ui";
import { useResource } from "../hooks/useResource";
import { getActions } from "../services/management";
import { incidentCode } from "../api/client";
import { timeAgo } from "../utils/format";

const ST = { pending: ["Pendiente", "info"], executed: ["Ejecutada", "ok"], reverted: ["Revertida", "wn"], failed: ["Falló", "er"] } as const;

export default function ActionsPage() {
  const r = useResource((s) => getActions(s));
  return (
    <>
      <PageHeader title="Acciones" subtitle="Acciones de respuesta seguras y reversibles." />
      <ResourceView r={r} empty="No hay acciones de respuesta registradas.">
        <DataTable rows={r.data ?? []} rowKey={(a) => a.id} columns={[
          { label: "Acción", cell: (a) => a.type }, { label: "Objetivo", cell: (a) => <span className="mono">{a.target ?? "—"}</span> },
          { label: "Incidente", cell: (a) => (a.incident_id != null ? <Link className="lnk" to={`/incidents/${a.incident_id}`}>{incidentCode(a.incident_id)}</Link> : "—") },
          { label: "Estado", cell: (a) => <Pill tone={ST[a.status][1] as any}>{ST[a.status][0]}</Pill> },
          { label: "Reversible", cell: (a) => (a.reversible ? "Sí" : "No") }, { label: "Creada", cell: (a) => timeAgo(a.created_at) },
          { label: "Origen del dato", cell: (a) => <ModeBadge mode={a.mode} /> },
        ]} />
      </ResourceView>
    </>
  );
}
