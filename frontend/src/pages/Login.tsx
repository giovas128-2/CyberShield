import { useState } from "react";
import {
  ArrowRight,
  Check,
  Loader2,
  ShieldCheck,
} from "lucide-react";

import { login } from "../api/client";
import { emailOk } from "../utils/format";
import { PasswordInput } from "../components/PasswordInput";
import { AuthShell } from "../components/AuthShell";
import type { User } from "../types";


export function Login({
  onLogin,
  goRegister,
  notice,
}: {
  onLogin: (u: User) => void;
  goRegister: () => void;
  notice?: string;
}) {
  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();

    if (loading) {
      return;
    }

    setError("");

    if (!emailOk(form.email) || !form.password) {
      setError(
        "Ingresa un correo electrónico y una contraseña válidos."
      );
      return;
    }

    setLoading(true);

    try {
      const data = await login({
        email: form.email,
        password: form.password,
      });

      localStorage.setItem(
        "cs_token",
        data.token
      );

      onLogin(data.user);

    } catch (err: any) {
      setError(
        err?.message ||
          "No fue posible iniciar sesión."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell>
      <form
        className="form"
        onSubmit={submit}
        noValidate
      >
        <div className="eyebrow">
          Bienvenido a CyberShield
        </div>

        <h2>Iniciar sesión</h2>

        <p className="mu">
          Accede a la consola de monitoreo y
          respuesta de seguridad.
        </p>

        {notice && (
          <div
            className="note"
            style={{
              color: "var(--ok)",
            }}
          >
            <Check size={16} />
            {notice}
          </div>
        )}

        <label>
          Correo electrónico
        </label>

        <div className="inp">
          <input
            type="email"
            placeholder="admin.demo@example.com"
            value={form.email}
            autoComplete="username"
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
          />
        </div>

        <label>
          Contraseña
        </label>

        <PasswordInput
          value={form.password}
          placeholder="Introduce tu contraseña"
          onChange={(e) =>
            setForm({
              ...form,
              password: e.target.value,
            })
          }
        />

        <div className="hint">
          El acceso administrativo está sujeto
          a políticas de origen autorizado.
        </div>

        {error && (
          <div className="errbox">
            <b>Acceso no autorizado</b>
            {error}
          </div>
        )}

        <button
          className="btn"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2
                size={16}
                className="spin"
              />
              Verificando acceso...
            </>
          ) : (
            <>
              <ArrowRight size={16} />
              Iniciar sesión
            </>
          )}
        </button>

        <div className="foot mu">
          ¿Aún no tienes una cuenta?{" "}
          <button
            type="button"
            className="lnk"
            onClick={goRegister}
          >
            Crear cuenta
          </button>
        </div>

        <div className="note">
          <ShieldCheck size={16} />
          Los intentos de acceso pueden ser
          registrados y correlacionados por
          CyberShield.
        </div>
      </form>
    </AuthShell>
  );
}