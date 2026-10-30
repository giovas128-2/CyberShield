import { DataTable, ModeBadge, PageHeader, Pill, ResourceView } from "../components/ui";
import { useResource } from "../hooks/useResource";
import { getDevices } from "../services/management";
import { timeAgo } from "../utils/format";

const ST = { trusted: ["Confiable", "ok"], unauthorized: ["No autorizado", "er"], unknown: ["Desconocido", "wn"] } as const;

export default function DevicesPage() {
  const r = useResource((s) => getDevices(s));
  return (
    <>
      <PageHeader title="Dispositivos" subtitle="Dispositivos conocidos y su nivel de confianza." />
      <ResourceView r={r} empty="No hay dispositivos registrados.">
        <DataTable rows={r.data ?? []} rowKey={(d) => d.id} columns={[
          { label: "Nombre", cell: (d) => d.name }, { label: "Usuario", cell: (d) => d.user ?? "—" }, { label: "Sistema", cell: (d) => d.os ?? "—" },
          { label: "Estado", cell: (d) => <Pill tone={ST[d.status][1] as any}>{ST[d.status][0]}</Pill> },
          { label: "Última actividad", cell: (d) => timeAgo(d.last_seen) }, { label: "Origen del dato", cell: (d) => <ModeBadge mode={d.mode} /> },
        ]} />
      </ResourceView>
    </>
  );
}
