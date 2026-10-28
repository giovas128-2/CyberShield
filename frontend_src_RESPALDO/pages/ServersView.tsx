import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw, Server } from "lucide-react";
import { getServers } from "../api/client";
import type { ServerItem, ServerStatus } from "../types";
import { timeAgo } from "../utils/format";

const statusText: Record<ServerStatus, string> = {
  online: "Online",
  offline: "Offline",
  registered: "Registrado",
};

const statusClass: Record<ServerStatus, string> = {
  online: "ok",
  offline: "er",
  registered: "wn",
};

export function ServersView() {
  const [servers, setServers] = useState<ServerItem[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    setServers(null);

    try {
      setServers(await getServers());
    } catch (err) {
      console.error("GET /servers falló:", err);
      setServers([]);
      setError("No se pudo cargar la lista de servidores. Verifica que el backend esté activo.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <div className="h">
        <div>
          <h1>Servidores</h1>
          <div className="mu">Infraestructura registrada y supervisada por CyberShield.</div>
        </div>
        <button className="btn sm gh" onClick={load}>
          <RefreshCw size={15} /> Actualizar
        </button>
      </div>

      {servers === null && (
        <div className="card server-loading">
          <Loader2 size={17} className="spin" /> Cargando servidores…
        </div>
      )}

      {error && <div className="errbox"><b>Error</b>{error}</div>}

      {servers && !error && servers.length > 0 && (
        <div className="tw">
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>IP</th>
                <th>Estado</th>
                <th>Agente</th>
                <th>Última actividad</th>
              </tr>
            </thead>
            <tbody>
              {servers.map((server) => (
                <tr key={server.id}>
                  <td><b>{server.name}</b></td>
                  <td className="mono">{server.ipAddress}</td>
                  <td>
                    <span className={`sv ${statusClass[server.status]}`}>
                      ● {statusText[server.status]}
                    </span>
                  </td>
                  <td>{server.agent ?? "Sin agente"}</td>
                  <td className="mu">{timeAgo(server.lastSeen)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {servers && !error && servers.length === 0 && (
        <div className="card server-empty">
          <Server size={52} strokeWidth={1.4} />
          <h2>No hay servidores registrados</h2>
          <p className="mu">
            Registra un servidor mediante la API para comenzar a mostrar infraestructura en CyberShield.
          </p>
        </div>
      )}
    </>
  );
}
