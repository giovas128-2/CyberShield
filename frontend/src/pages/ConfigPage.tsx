import { useEffect, useState } from "react";
import { Bell, CheckCircle2, Info, Monitor, RotateCcw, Shield, UserRound } from "lucide-react";
import {
  currentUserDisplay, DEFAULT_PREFERENCES, getPreferences, savePreferences,
  usePreferences, SEVERITIES,
} from "../preferences/cybershieldPreferences";
import type { Preferences, TimeZoneChoice } from "../preferences/cybershieldPreferences";
import type { Severidad } from "../types";
import "../styles/config.css";

function SwitchRow({ title, hint, checked, onChange, disabled = false }: {
  title: string; hint: string; checked: boolean;
  onChange?: (next: boolean) => void; disabled?: boolean;
}) {
  return (
    <label className={`cfg-switch-row ${disabled ? "cfg-disabled" : ""}`}>
      <span className="cfg-switch-copy"><strong>{title}</strong><small>{hint}</small></span>
      <input type="checkbox" checked={checked} disabled={disabled}
        onChange={(e) => onChange?.(e.target.checked)} />
      <span className="cfg-switch" aria-hidden="true" />
      <span className="cfg-switch-status">{disabled ? "No disponible" : checked ? "Activo" : "Inactivo"}</span>
    </label>
  );
}

const labels: Record<Severidad, string> = {
  CRITICAL: "CRITICAL", HIGH: "HIGH", WARNING: "MEDIA (WARNING)", NORMAL: "BAJA (NORMAL)",
};

const ZONES: { value: TimeZoneChoice; name: string }[] = [
  { value: "browser", name: "Automática (navegador)" },
  { value: "America/Mexico_City", name: "Ciudad de México" },
  { value: "America/Monterrey", name: "Monterrey" },
  { value: "America/Tijuana", name: "Tijuana" },
  { value: "UTC", name: "UTC" },
];

function canUseNotifications() {
  return typeof Notification !== "undefined" && window.isSecureContext;
}

export default function ConfigPage() {
  const saved = usePreferences();
  const [draft, setDraft] = useState<Preferences>(() => getPreferences());
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [permission, setPermission] = useState(() => typeof Notification === "undefined" ? "no disponible" : Notification.permission);
  const user = currentUserDisplay();
  useEffect(() => { setDraft(saved); }, [saved]);

  const dirty = JSON.stringify(saved) !== JSON.stringify(draft);
  const change = <K extends keyof Preferences>(field: K, value: Preferences[K]) => {
    setDraft((old) => ({...old, [field]: value}));
    setFeedback(""); setError("");
  };
  const toggleSeverity = (level: Severidad) => {
    const values = draft.severities.includes(level)
      ? draft.severities.filter((item) => item !== level)
      : SEVERITIES.filter((item) => draft.severities.includes(item) || item === level);
    change("severities", values);
  };

  const save = async () => {
    const next = { ...draft };
    try {
      if (next.browserNotices) {
        if (!canUseNotifications()) {
          next.browserNotices = false;
          setError("Avisos del navegador: se requiere HTTPS o localhost y un navegador compatible.");
        } else if (Notification.permission !== "granted") {
          // Permiso pedido SOLO al pulsar Guardar (gesto explícito del usuario).
          const result = await Notification.requestPermission();
          setPermission(result);
          if (result !== "granted") {
            next.browserNotices = false;
            setError("El navegador no autorizó las notificaciones. El resto de preferencias sí se guardó.");
          }
        }
      }
      savePreferences(next);
      setDraft(next);
      if (next.saveConfirmation) setFeedback("Preferencias guardadas correctamente.");
    } catch {
      setError("No se pudieron guardar las preferencias. Revisa el almacenamiento de este navegador.");
    }
  };

  const testNotice = () => {
    if (!canUseNotifications() || Notification.permission !== "granted") {
      setError("Autoriza primero los avisos del navegador y guarda la configuración.");
      return;
    }
    try {
      new Notification("CyberShield · Aviso de prueba", {
        body: "Los avisos de este navegador funcionan mientras CyberShield esté abierto.",
        tag: "cybershield-notice-test", silent: true,
      });
      setFeedback("Aviso de prueba enviado al navegador.");
      setError("");
    } catch {
      setError("El navegador no permitió mostrar el aviso de prueba.");
    }
  };

  const draftZone = draft.timeZone === "browser"
    ? (Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC") : draft.timeZone;
  const preview = new Intl.DateTimeFormat("es-MX", {
    timeZone: draftZone, day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(new Date());

  return (
    <div className="cfg-page">
      <header className="h cfg-header">
        <div><h1>Configuraciones</h1><div className="mu">Personaliza tu consola sin modificar las defensas ni las alertas operativas.</div></div>
        <span className={`sv ${dirty ? "wn" : "ok"}`}>{dirty ? "Cambios sin guardar" : "Preferencias guardadas"}</span>
      </header>

      <div className="cfg-columns">
        <div className="cfg-column">
          <section className="card cfg-card">
            <div className="cfg-title"><Bell size={18}/><h2>Preferencias de notificaciones</h2></div>
            <p className="mu">Se activan cuando llegan datos NUEVOS; no vuelven a avisar de registros antiguos.</p>
            <SwitchRow title="Nuevos eventos" hint="Avisar cuando el backend registre eventos nuevos de las severidades seleccionadas."
              checked={draft.newEvents} onChange={(v) => change("newEvents", v)}/>
            <SwitchRow title="Cambios de estado del incidente" hint="Avisar cuando un incidente existente pase a investigación, resuelto u otro estado."
              checked={draft.incidentChanges} onChange={(v) => change("incidentChanges", v)}/>
            <SwitchRow title="Confirmaciones de preferencias" hint="Mostrar un mensaje cuando la configuración se guarde."
              checked={draft.saveConfirmation} onChange={(v) => change("saveConfirmation", v)}/>
          </section>

          <section className="card cfg-card">
            <div className="cfg-title"><Shield size={18}/><h2>Severidades a mostrar</h2></div>
            <p className="mu">Aplica a las listas de Eventos, Incidentes, Notificaciones y eventos recientes del Dashboard.</p>
            <div className="cfg-severity-list">
              {SEVERITIES.map((level) => (
                <label key={level} className="cfg-severity">
                  <input type="checkbox" checked={draft.severities.includes(level)}
                    onChange={() => toggleSeverity(level)}/> {labels[level]}
                </label>
              ))}
            </div>
            {!draft.severities.length && <p className="cfg-warn">No seleccionaste ninguna severidad: las listas aparecerán vacías. Los contadores globales continuarán mostrando las amenazas reales.</p>}
          </section>

          <section className="card cfg-card">
            <div className="cfg-title"><Bell size={18}/><h2>Canales</h2></div>
            <p className="mu">Los avisos personales no desactivan Telegram, Wazuh ni las respuestas automáticas.</p>
            <SwitchRow title="En consola" hint="Mostrar mensajes emergentes dentro de CyberShield cuando lleguen novedades."
              checked={draft.consoleNotices} onChange={(v) => change("consoleNotices", v)}/>
            <SwitchRow title="Avisos del navegador" hint="Mostrar notificaciones del sistema mientras la pestaña esté abierta. Requiere permiso y HTTPS o localhost."
              checked={draft.browserNotices} onChange={(v) => change("browserNotices", v)} disabled={!canUseNotifications()}/>
            <div className="cfg-inline-tools">
              <span className="mu">Permiso: {permission}</span>
              <button className="btn sm gh" type="button" onClick={testNotice} disabled={!canUseNotifications() || permission !== "granted"}>Probar aviso</button>
            </div>
            <SwitchRow title="Correo electrónico" hint="No existe todavía un transporte SMTP habilitado ni sus credenciales configuradas en el backend."
              checked={false} disabled/>
            <div className="cfg-integration-note">Para enviar correos reales debe configurarse y probarse un servicio SMTP del backend. No se simula que un correo se entregó. Telegram continúa administrado por el backend.</div>
          </section>
        </div>

        <div className="cfg-column">
          <section className="card cfg-card">
            <div className="cfg-title"><Monitor size={18}/><h2>Apariencia y visualización</h2></div>
            <p className="mu">Los cambios se aplican al guardar y se recuperan al volver a entrar.</p>
            <label className="cfg-field"><span>Tema</span>
              <select value={draft.theme} onChange={(e) => change("theme", e.target.value as Preferences["theme"])}>
                <option value="dark">CyberShield oscuro</option><option value="light">CyberShield claro</option>
              </select>
            </label>
            <label className="cfg-field"><span>Densidad de tablas</span>
              <select value={draft.density} onChange={(e) => change("density", e.target.value as Preferences["density"])}>
                <option value="comfortable">Cómoda</option><option value="compact">Compacta</option>
              </select>
              <small>Cambia el espacio de las tablas de eventos, servidores, notificaciones, dashboard y otras listas.</small>
            </label>
            <label className="cfg-field"><span>Zona horaria</span>
              <select value={draft.timeZone} onChange={(e) => change("timeZone", e.target.value as TimeZoneChoice)}>
                {ZONES.map((zone) => <option value={zone.value} key={zone.value}>{zone.name}</option>)}
              </select>
              <small>Vista previa: {preview} · {draftZone}</small>
            </label>
            <div className="cfg-inline-tools">
              <button className="btn sm gh" type="button" onClick={() => setDraft({...DEFAULT_PREFERENCES})}><RotateCcw size={14}/> Restablecer valores</button>
            </div>
          </section>

          <aside className="cfg-info"><Info size={20}/><div><strong>Alcance de las preferencias</strong><p>Solo cambian visualización y avisos de esta sesión del navegador. El backend conserva todos los eventos y continúa procesando incidentes, Telegram y acciones defensivas. Los totales globales no se ocultan por filtros.</p></div></aside>

          <section className="card cfg-card">
            <div className="cfg-title"><UserRound size={18}/><h2>Cuenta de ingeniería</h2></div>
            <p><strong>{user.name}</strong></p>
            <p className="mu">Rol: {user.role}. Los permisos reales deben ser comprobados por la API.</p>
          </section>
        </div>
      </div>

      <footer className="card cfg-savebar">
        <div>
          <strong>{dirty ? "Tienes cambios sin guardar" : "No hay cambios pendientes"}</strong>
          <small className="mu">Preferencias guardadas por usuario en este navegador.</small>
          {feedback && <span className="cfg-confirm"><CheckCircle2 size={15}/> {feedback}</span>}
          {error && <span className="cfg-warn" role="alert">{error}</span>}
        </div>
        <div className="cfg-save-actions">
          <button type="button" className="btn sm gh" disabled={!dirty} onClick={() => {setDraft(saved);setError("");setFeedback("");}}>Descartar</button>
          <button type="button" className="btn sm" disabled={!dirty} onClick={() => {void save();}}>Guardar preferencias</button>
        </div>
      </footer>
      <p className="mu cfg-footer-note">CyberShield · Preferencias personales · Sin modificar el sistema de seguridad</p>
    </div>
  );
}
