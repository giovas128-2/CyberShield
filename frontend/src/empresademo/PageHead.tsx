import type { ReactNode } from "react";

/** Cabecera operacional: no expone estados internos del sistema de seguridad. */
export function PageHead({ title, sub, children }: { num?: string; title: string; sub: string; children?: ReactNode }) {
  return (
    <div className="ed-h">
      <div>
        <h1>{title}</h1>
        <div className="ed-sub">{sub}</div>
      </div>
      {children}
    </div>
  );
}
