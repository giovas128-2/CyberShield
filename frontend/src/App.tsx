import { useState } from "react";
import { HashRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { AppLayout } from "./layout/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import { ServersView } from "./pages/ServersView";
import EventsPage from "./pages/EventsPage";
import IncidentsPage from "./pages/IncidentsPage";
import IncidentDetailPage from "./pages/IncidentDetailPage";
import NotificationsPage from "./pages/NotificationsPage";
import DevicesPage from "./pages/DevicesPage";
import SessionsPage from "./pages/SessionsPage";
import ActionsPage from "./pages/ActionsPage";
import ProtectionsPage from "./pages/ProtectionsPage";
import LabPage from "./pages/LabPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import type { User } from "./types";

const readUser = (): User | null => {
  try { return JSON.parse(localStorage.getItem("cs_user") || "null"); } catch { return null; }
};

function RegisterRoute() {
  const nav = useNavigate();
  return <Register goLogin={() => nav("/login")} onDone={() => nav("/login", { state: { notice: "Cuenta creada. Inicia sesión para continuar." } })} />;
}

function LoginRoute({ onUser }: { onUser: (u: User) => void }) {
  const nav = useNavigate();
  const { state } = useLocation();
  return <Login notice={(state as any)?.notice} goRegister={() => nav("/register")} onLogin={(u) => { onUser(u); nav("/dashboard"); }} />;
}

export default function App() {
  const [user, setUser] = useState<User | null>(readUser());
  const saveUser = (u: User) => { localStorage.setItem("cs_user", JSON.stringify(u)); setUser(u); };
  const logout = () => { localStorage.removeItem("cs_token"); localStorage.removeItem("cs_user"); setUser(null); };
  const guard = (el: JSX.Element) => user ? el : <Navigate to="/login" replace />;

  return (
    <div className="cs">
      <HashRouter>
        <Routes>
          <Route path="/register" element={<RegisterRoute />} />
          <Route path="/login" element={<LoginRoute onUser={saveUser} />} />
          <Route element={guard(<AppLayout user={user!} onLogout={logout} />)}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/servers" element={<ServersView />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route path="/incidents/:id" element={<IncidentDetailPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route path="/actions" element={<ActionsPage />} />
            <Route path="/protections" element={<ProtectionsPage />} />
            <Route path="/lab" element={<LabPage />} />
            <Route path="/security" element={<PlaceholderPage title="Seguridad" />} />
            <Route path="/config" element={<PlaceholderPage title="Configuración" />} />
          </Route>
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/register"} replace />} />
        </Routes>
      </HashRouter>
    </div>
  );
}
