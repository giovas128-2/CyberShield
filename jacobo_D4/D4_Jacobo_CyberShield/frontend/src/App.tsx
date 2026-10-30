import { useState } from "react";
import { HashRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { Login } from "./pages/Login";
import PortalChoicePage from "./pages/PortalChoicePage";
import { Register } from "./pages/Register";
import { AppLayout } from "./layout/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import { ServersView } from "./pages/ServersView";
import EventsPage from "./pages/EventsPage";
import IncidentsPage from "./pages/IncidentsPage";
import IncidentDetailPage from "./pages/IncidentDetailPage";
import EvidencePage from "./pages/EvidencePage";
import NotificationsPage from "./pages/NotificationsPage";
import DevicesPage from "./pages/DevicesPage";
import SessionsPage from "./pages/SessionsPage";
import ActionsPage from "./pages/ActionsPage";
import ProtectionsPage from "./pages/ProtectionsPage";
import LabPage from "./pages/LabPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import { EmpresaDemoLayout } from "./empresademo/EmpresaDemoLayout";
import EDLogin from "./pages/empresademo/EDLogin";
import EDInicio from "./pages/empresademo/EDInicio";
import EDClientes from "./pages/empresademo/EDClientes";
import EDDocumentos from "./pages/empresademo/EDDocumentos";
import EDReportes from "./pages/empresademo/EDReportes";
import EDPerfil from "./pages/empresademo/EDPerfil";
import EDRestringido from "./pages/empresademo/EDRestringido";
import type { User } from "./types";

const readUser = (): User | null => {
  try { return JSON.parse(localStorage.getItem("cs_user") || "null"); } catch { return null; }
};

function RegisterRoute() {
  const nav = useNavigate();
  return <Register goLogin={() => nav("/login/cybershield")} onDone={() => nav("/login/cybershield", { state: { notice: "Cuenta creada. Inicia sesión para continuar." } })} />;
}

function LoginRoute({ onUser }: { onUser: (u: User) => void }) {
  const nav = useNavigate();
  const { state } = useLocation();
  return <Login notice={(state as any)?.notice} goRegister={() => nav("/register")} goPortals={() => nav("/login")} onLogin={(u) => { onUser(u); nav("/dashboard"); }} />;
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
          <Route path="/login" element={<PortalChoicePage />} />
          <Route path="/login/cybershield" element={<LoginRoute onUser={saveUser} />} />
          <Route path="/register" element={<RegisterRoute />} />

          <Route path="/empresa-demo/login" element={<EDLogin />} />
          <Route element={<EmpresaDemoLayout />}>
            <Route path="/empresa-demo/inicio" element={<EDInicio />} />
            <Route path="/empresa-demo/clientes" element={<EDClientes />} />
            <Route path="/empresa-demo/documentos" element={<EDDocumentos />} />
            <Route path="/empresa-demo/reportes" element={<EDReportes />} />
            <Route path="/empresa-demo/perfil" element={<EDPerfil />} />
            <Route path="/empresa-demo/acceso-restringido" element={<EDRestringido />} />
          </Route>
          <Route element={guard(<AppLayout user={user!} onLogout={logout} />)}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/servers" element={<ServersView />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route path="/incidents/:id" element={<IncidentDetailPage />} />
            <Route path="/incidents/:id/evidence" element={<EvidencePage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route path="/actions" element={<ActionsPage />} />
            <Route path="/protections" element={<ProtectionsPage />} />
            <Route path="/lab" element={<LabPage />} />
            <Route path="/security" element={<PlaceholderPage title="Seguridad" />} />
            <Route path="/config" element={<PlaceholderPage title="Configuración" />} />
          </Route>
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </HashRouter>
    </div>
  );
}
