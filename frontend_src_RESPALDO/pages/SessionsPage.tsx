import { DataTable, ModeBadge, PageHeader, Pill, ResourceView } from "../components/ui";
import { useResource } from "../hooks/useResource";
import { getSessions } from "../services/management";
import { timeAgo } from "../utils/format";

const ST = { active: ["Activa", "ok"], revoked: ["Revocada", "er"], expired: ["Expirada", "wn"] } as const;

export default function SessionsPage() {
  const r = useResource((s) => getSessions(s));
  return (
    <>
      <PageHeader title="Sesiones" subtitle="Sesiones de usuario asociadas a dispositivos." />
      <ResourceView r={r} empty="No hay sesiones registradas.">
        <DataTable rows={r.data ?? []} rowKey={(s) => s.id} columns={[
          { label: "Usuario", cell: (s) => s.user }, { label: "Dispositivo", cell: (s) => s.device ?? "—" }, { label: "IP", cell: (s) => <span className="mono">{s.ip ?? "—"}</span> },
          { label: "Inicio", cell: (s) => timeAgo(s.started_at) }, { label: "Estado", cell: (s) => <Pill tone={ST[s.status][1] as any}>{ST[s.status][0]}</Pill> },
          { label: "Origen del dato", cell: (s) => <ModeBadge mode={s.mode} /> },
        ]} />
      </ResourceView>
    </>
  );
}
