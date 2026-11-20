/** Avisos personales: solo mientras la consola está abierta.
 * No modifica incidentes, respuestas, Telegram ni persistencia del servidor.
 */
import { useEffect, useRef } from "react";
import type { Evento, Incidente } from "../types";
import type { ToastData } from "./Toast";
import { usePreferences } from "../preferences/cybershieldPreferences";

type Snapshot = { events: Set<string>; incidentStatus: Map<number, string> };

export function NoticeObserver({
  events, incidents, isLive, onToast,
}: {
  events: Evento[];
  incidents: Incidente[];
  isLive: boolean;
  onToast: (toast: ToastData) => void;
}) {
  const prefs = usePreferences();
  const previous = useRef<Snapshot | null>(null);

  useEffect(() => {
    if (!isLive) return;
    const snapshot: Snapshot = {
      events: new Set(events.map((e) => String(e.id))),
      incidentStatus: new Map<number, string>(incidents.map((i) => [i.backendId, i.status] as [number, string])),
    };
    if (!previous.current) {
      previous.current = snapshot;
      return; // no notificar el histórico al abrir la aplicación
    }
    const old = previous.current;
    previous.current = snapshot;
    const allowed = new Set(prefs.severities);
    const added = events.filter((e) => !old.events.has(String(e.id)) && allowed.has(e.severidad));
    const changed = incidents.filter((i) => {
      const prior = old.incidentStatus.get(i.backendId);
      return prior !== undefined && prior !== i.status && allowed.has(i.severidad);
    });

    let title = "";
    let detail = "";
    let target = "";
    if (prefs.incidentChanges && changed.length) {
      title = "CyberShield · Incidente actualizado";
      detail = `${changed.length} incidente(s) cambiaron de estado.`;
      target = "#/incidents";
    } else if (prefs.newEvents && added.length) {
      title = "CyberShield · Nuevos eventos";
      detail = `${added.length} evento(s) nuevos en severidades seleccionadas.`;
      target = "#/events";
    }
    if (!title) return;

    if (prefs.consoleNotices) onToast({kind:"ok", text: `${title}: ${detail}`});
    if (prefs.browserNotices && typeof Notification !== "undefined" &&
        Notification.permission === "granted" && window.isSecureContext) {
      try {
        const notice = new Notification(title, { body: detail, tag: "cybershield-notice", silent: true });
        notice.onclick = () => { window.focus(); window.location.hash = target; notice.close(); };
      } catch (error) {
        console.warn("No se pudo mostrar la notificación del navegador:", error);
      }
    }
  }, [events, incidents, isLive, onToast, prefs]);
  return null;
}
