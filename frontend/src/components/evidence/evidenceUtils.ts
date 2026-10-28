export function formatEvidenceDate(
  value?: string | null
): string {
  if (!value) {
    return "Sin registro";
  }

  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function evidenceStatusLabel(
  status: string
): string {
  switch (status) {
    case "CONTAINED":
      return "Ataque contenido";

    case "FAILED":
      return "Ataque no contenido";

    case "RESPONDING":
      return "Respuesta en proceso";

    case "DETECTED":
      return "Ataque detectado";

    default:
      return status;
  }
}