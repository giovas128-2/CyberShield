import { useEffect, useMemo, useState } from "react";
import { Bell, CheckCircle2, Info, Monitor, Shield, UserRound } from "lucide-react";
import "../styles/config.css";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
type Preferences = {
  newEvents: boolean;
  incidentChanges: boolean;
  saveConfirmation: boolean;
  severities: Severity[];
  consoleNotices: boolean;
  density: "compact" | "comfortable";
};

const defaults: Preferences = {
  newEvents: true,
  incidentChanges: true,
  saveConfirmation: true,
  severities: ["CRITICAL", "HIGH", "MEDIUM"],
  consoleNotices: true,
  density: "comfortable",
};

const severityOptions: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

function currentUser(): { name: string; key: string; role: string } {
  try {
    const raw = JSON.parse(localStorage.getItem("cs_user") || "null");
    const name = typeof raw?.name === "string" ? raw.name : "Usuario de CyberShield";
    const key = String(raw?.id ?? raw?.email ?? name);
    const role = typeof raw?.role === "string" ? raw.role : "Usuario autenticado";
    return { name, key, role };
  } catch {
    return { name: "Usuario de CyberShield", key: "user", role: "Usuario autenticado" };
  }
}

function readPrefs(key: string): Preferences {
  try {
    const raw = JSON.parse(localStorage.getItem(key) || "null");
    if (!raw || typeof raw !== "object") return { ...defaults };
    return {
      newEvents: typeof raw.newEvents === "boolean" ? raw.newEvents : defaults.newEvents,
      incidentChanges: typeof raw.incidentChanges === "boolean" ? raw.incidentChanges : defaults.incidentChanges,
      saveConfirmation: typeof raw.saveConfirmation === "boolean" ? raw.saveConfirmation : defaults.saveConfirmation,
      severities: Array.isArray(raw.severities)
        ? severityOptions.filter((s) => raw.severities.includes(s))
        : defaults.severities,
      consoleNotices: typeof raw.consoleNotices === "boolean" ? raw.consoleNotices : defaults.consoleNotices,
      density: raw.density === "compact" ? "compact" : "comfortable",
    };
  } catch {
    return { ...defaults };
  }
}

function SwitchRow({
  title,
  hint,
  checked,
  onChange,
  disabled = false,
}: {
  title: string;
  hint: string;
  checked: boolean;
  onChange?: (next: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className={`cfg-switch-row ${disabled ? "cfg-disabled" : ""}`}>
      <span className="cfg-switch-copy"><strong>{title}</strong><small>{hint}</small></span>
      <input type="checkbox" checked={checked} disabled={disabled}
        onChange={(e) => onChange?.(e.target.checked)} />
      <span className="cfg-switch" aria-hidden="true" />
      <span className="cfg-switch-status">{disabled ? "Pendiente" : checked ? "Activo" : "Inactivo"}</span>
    </label>
  );
}

export default function ConfigPage() {
  const user = useMemo(currentUser, []);
  const storageKey = `cs_preferences_${user.key}`;
  const [saved, setSaved] = useState<Preferences>(() => readPrefs(storageKey));
  const [draft, setDraft] = useState<Preferences>(() => readPrefs(storageKey));
  const [confirmation, setConfirmation] = useState(false);
  const dirty = JSON.stringify(saved) !== JSON.stringify(draft);

  useEffect(() => {
    document.documentElement.dataset.csDensity = saved.density;
  }, [saved.density]);

  const change = <K extends keyof Preferences>(field: K, value: Preferences[K]) => {
    setDraft((prev) => ({ ...prev, [field]: value }));
    setConfirmation(false);
  };

  const toggleSeverity = (level: Severity) => {
    const next = draft.severities.includes(level)
      ? draft.severities.filter((s) => s !== level)
      : severityOptions.filter((s) => draft.severities.includes(s) || s === level);
    change("severities", next);
  };

  const save = () => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(draft));
      setSaved({ ...draft });
      setConfirmation(draft.saveConfirmation);
      window.dispatchEvent(new Event("cybershield:preferences-updated"));
    } catch {
      setConfirmation(false);
      window.alert("No se pudieron guardar las preferencias en este navegador.");
    }
  };

  return (
    <div className="cfg-page">
      <header className="h cfg-header">
        <div>
          <h1>Configuraciones</h1>
          <div className="mu">Preferencias personales de la consola. No modifican controles de seguridad.</div>
        </div>
        <span className={`sv ${dirty ? "wn" : "ok"}`}>
          {dirty ? "Cambios sin guardar" : "Preferencias guardadas"}
        </span>
      </header>

      <div className="cfg-columns">
        <div className="cfg-column">
          <section className="card cfg-card">
            <div className="cfg-title"><Bell size={18} /><h2>Preferencias de notificaciones</h2></div>
            <p className="mu">Personaliza los avisos que deseas ver en la consola.</p>
            <SwitchRow title="Nuevos eventos" hint="Mostrar avisos de nuevos eventos disponibles para tu rol."
              checked={draft.newEvents} onChange={(v) => change("newEvents", v)} />
            <SwitchRow title="Cambios de estado del incidente" hint="Mostrar avisos cuando cambie el estado de un incidente."
              checked={draft.incidentChanges} onChange={(v) => change("incidentChanges", v)} />
            <SwitchRow title="Confirmaciones de preferencias" hint="Mostrar confirmación al guardar configuraciones."
              checked={draft.saveConfirmation} onChange={(v) => change("saveConfirmation", v)} />
          </section>

          <section className="card cfg-card">
            <div className="cfg-title"><Shield size={18} /><h2>Severidades a mostrar</h2></div>
            <p className="mu">Filtro visual personal. No modifica la clasificación ni la detección.</p>
            <div className="cfg-severity-list">
              {severityOptions.map((level) => (
                <label key={level} className="cfg-severity">
                  <input type="checkbox" checked={draft.severities.includes(level)}
                    onChange={() => toggleSeverity(level)} /> {level}
                </label>
              ))}
            </div>
          </section>

          <section className="card cfg-card">
            <div className="cfg-title"><Bell size={18} /><h2>Canales</h2></div>
            <p className="mu">Los canales externos requieren integración y autorización del sistema.</p>
            <SwitchRow title="En consola" hint="Preferencia para avisos visuales dentro de CyberShield."
              checked={draft.consoleNotices} onChange={(v) => change("consoleNotices", v)} />
            <SwitchRow title="Correo electrónico" hint="La entrega de correos no está configurada."
              checked={false} disabled />
            <SwitchRow title="Avisos del navegador" hint="Se requiere integración y autorización del navegador."
              checked={false} disabled />
            <div className="cfg-integration-note">Telegram es un canal operativo gestionado por el backend; no se desactiva desde estas preferencias personales.</div>
          </section>
        </div>

        <div className="cfg-column">
          <section className="card cfg-card">
            <div className="cfg-title"><Monitor size={18} /><h2>Apariencia y visualización</h2></div>
            <p className="mu">Opciones visuales del frontend.</p>
            <label className="cfg-field"><span>Tema</span>
              <select value="dark" disabled aria-label="Tema actual"><option value="dark">CyberShield oscuro</option></select>
              <small>Se conserva el tema oscuro original para mantener consistencia con el resto de la consola.</small>
            </label>
            <label className="cfg-field"><span>Densidad de tablas</span>
              <select value={draft.density} onChange={(e) => change("density", e.target.value as Preferences["density"])}>
                <option value="comfortable">Cómoda</option>
                <option value="compact">Compacta</option>
              </select>
            </label>
            <div className="cfg-field"><span>Zona horaria</span>
              <div className="cfg-readonly">{Intl.DateTimeFormat().resolvedOptions().timeZone || "Zona horaria del navegador"}</div>
              <small>Determinada por tu navegador. Cambiarla en CyberShield requiere un formato horario común para todas las vistas.</small>
            </div>
          </section>

          <aside className="cfg-info"><Info size={20} /><div><strong>Alcance de estas preferencias</strong><p>Son preferencias locales de visualización. No bloquean equipos, no contienen incidentes ni ejecutan respuestas automáticas. No cambian el comportamiento de Wazuh, Suricata ni Telegram.</p></div></aside>

          <section className="card cfg-card">
            <div className="cfg-title"><UserRound size={18} /><h2>Cuenta de ingeniería</h2></div>
            <p><strong>{user.name}</strong></p>
            <p className="mu">Rol: {user.role}. Los permisos reales se administran desde el backend.</p>
          </section>
        </div>
      </div>

      <footer className="card cfg-savebar">
        <div>
          <strong>{dirty ? "Tienes cambios sin guardar" : "No hay cambios pendientes"}</strong>
          <small className="mu">Las preferencias se guardan únicamente en este navegador.</small>
          {confirmation && <span className="cfg-confirm"><CheckCircle2 size={15} /> Preferencias guardadas correctamente.</span>}
        </div>
        <div className="cfg-save-actions">
          <button type="button" className="btn sm gh" disabled={!dirty}
            onClick={() => { setDraft({ ...saved }); setConfirmation(false); }}>Descartar</button>
          <button type="button" className="btn sm" disabled={!dirty} onClick={save}>Guardar preferencias</button>
        </div>
      </footer>
      <p className="mu cfg-footer-note">CyberShield · Consola de ingeniería · Preferencias locales</p>
    </div>
  );
}
