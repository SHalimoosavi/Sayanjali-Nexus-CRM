import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./features/auth/AuthContext";
import LoginPage from "./features/auth/LoginPage";
import AppLayout from "./components/layout/AppLayout";
import DashboardPage from "./features/dashboard/DashboardPage";
import LeadsPage from "./features/leads/LeadsPage";
import ClientsPage from "./features/clients/ClientsPage";
import ProjectsPage from "./features/projects/ProjectsPage";

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="p-8">
      <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">MODULE</div>
      <h1 className="font-display text-3xl text-white mb-2">{title}</h1>
      <p className="text-sm text-muted">This module follows the same pattern as Leads &mdash; scaffold it next.</p>
    </div>
  );
}

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen flex items-center justify-center text-muted">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="leads" element={<LeadsPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="tasks" element={<PlaceholderPage title="Tasks" />} />
        <Route path="communications" element={<PlaceholderPage title="Communication Center" />} />
        <Route path="calendar" element={<PlaceholderPage title="Calendar" />} />
        <Route path="documents" element={<PlaceholderPage title="Documents" />} />
        <Route path="settings" element={<PlaceholderPage title="Settings" />} />
      </Route>
    </Routes>
  );
}
