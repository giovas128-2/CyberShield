import { useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { Menu } from "lucide-react";
import { AlertModal } from "../components/AlertModal";
import { OriginChip } from "../components/OriginChip";
import { Sidebar, NAV } from "../components/Sidebar";
import { Toast } from "../components/Toast";
import { useCyberShieldData } from "../hooks/useCyberShieldData";
import type { User } from "../types";

export function AppLayout({ user, onLogout }: { user: User; onLogout: () => void }) {
  const loc = useLocation();
  const nav = useNavigate();
  const ctx = useCyberShieldData(user);
  const [menuOpen, setMenuOpen] = useState(false);
  const abiertos = ctx.incidents.filter((i) => i.status !== "resolved").length;
  const current = NAV.flatMap((g) => g.items).find(([p]) => loc.pathname.startsWith(p));

  useEffect(() => { setMenuOpen(false); }, [loc.pathname]);

  return (
    <div className="shell">
      <Sidebar
        openIncidents={abiertos}
        notifications={ctx.notifications.length}
        status={{ stale: ctx.stale, demo: ctx.demo, online: ctx.stats.servidoresOnline, offline: ctx.stats.servidoresOffline, updatedAt: ctx.updatedAt }}
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
      />

      <div className="shell-body">
        <header className="top">
          <button className="menu-btn" onClick={() => setMenuOpen(true)} aria-label="Abrir menú"><Menu size={20} /></button>
          <span className="crumb">CyberShield <span>›</span> <b>{current?.[1] ?? "Detalle"}</b></span>
          <span className="sp" />
          <OriginChip demo={ctx.demo} stale={ctx.stale} at={ctx.updatedAt} />
          <div className="av">{user?.name?.slice(0, 2).toUpperCase()}</div>
          <div className="who" style={{ lineHeight: 1.2 }}>{user?.name}<div className="mu" style={{ fontSize: 11 }}>Administrador</div></div>
          <button className="lnk" style={{ color: "var(--mu)" }} onClick={onLogout}>Salir</button>
        </header>
        <main className="main"><Outlet context={ctx} /></main>
      </div>

      {ctx.alertInc && (
        <AlertModal
          inc={ctx.alertInc}
          onClose={() => ctx.setAlertInc(null)}
          onView={() => {
            ctx.setSelId(ctx.alertInc!.id);
            nav("/incidents");
            ctx.setAlertInc(null);
          }}
        />
      )}
      <Toast toast={ctx.toast} onClose={() => ctx.setToast(null)} />
    </div>
  );
}
