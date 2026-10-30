import { useCallback, useEffect, useRef, useState } from "react";
import type { Loaded, Source } from "../services/management";

/* Carga un recurso con estados loading / error / datos. Polling opcional y CANCELABLE:
   al desmontar (o cambiar pollMs) se aborta la petición en curso y se detiene el intervalo; nunca se solapan dos peticiones. */
export function useResource<T>(fetcher: (signal: AbortSignal) => Promise<Loaded<T>>, pollMs = 0) {
  const [state, setState] = useState<{ data: T | null; source: Source | null; reason?: string; loading: boolean; error: string | null }>({ data: null, source: null, loading: true, error: null });
  const fRef = useRef(fetcher); fRef.current = fetcher;
  const inFlight = useRef(false);
  const ctrl = useRef<AbortController | null>(null);

  const run = useCallback(async (signal: AbortSignal, silent: boolean) => {
    if (inFlight.current) return;
    inFlight.current = true;
    if (!silent) setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const r = await fRef.current(signal);
      if (!signal.aborted) setState({ data: r.data, source: r.source, reason: r.reason, loading: false, error: null });
    } catch (e) {
      if (!signal.aborted) setState((s) => ({ ...s, loading: false, error: e instanceof Error ? e.message : "Error desconocido" }));
    } finally { inFlight.current = false; }
  }, []);

  useEffect(() => {
    const c = new AbortController(); ctrl.current = c;
    run(c.signal, false);
    const t = pollMs ? setInterval(() => run(c.signal, true), pollMs) : undefined;
    return () => { c.abort(); inFlight.current = false; if (t) clearInterval(t); };
  }, [run, pollMs]);

  const reload = useCallback(() => { if (ctrl.current) run(ctrl.current.signal, false); }, [run]);
  return { ...state, reload };
}
