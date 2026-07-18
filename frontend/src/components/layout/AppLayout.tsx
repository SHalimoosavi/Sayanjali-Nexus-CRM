import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard, Users, Briefcase, ListChecks, Building2,
  MessageSquare, Calendar, FileText, Settings, LogOut, Search,
} from "lucide-react";
import { useAuth } from "../../features/auth/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/leads", label: "Leads", icon: Users },
  { to: "/clients", label: "Clients", icon: Building2 },
  { to: "/projects", label: "Projects", icon: Briefcase },
  { to: "/tasks", label: "Tasks", icon: ListChecks },
  { to: "/communications", label: "Communications", icon: MessageSquare },
  { to: "/calendar", label: "Calendar", icon: Calendar },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-ink">
      <aside className="w-60 shrink-0 border-r border-border bg-surface flex flex-col">
        <div className="px-5 py-5 border-b border-border">
          <div className="text-xs tracking-[0.25em] text-brass font-mono">SAYANJALI</div>
          <div className="font-display text-lg text-white -mt-0.5">Nexus CRM</div>
        </div>

        <button className="mx-4 mt-4 flex items-center gap-2 text-xs text-muted border border-border rounded-md px-3 py-2 hover:border-brass/50 transition-colors">
          <Search size={14} />
          <span>Search…</span>
          <span className="ml-auto font-mono text-[10px] opacity-60">⌘K</span>
        </button>

        <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto scrollbar-thin">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-brass/10 text-brass border border-brass/20"
                    : "text-white/70 hover:bg-white/5 border border-transparent"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-brass/20 text-brass flex items-center justify-center text-xs font-medium">
              {user?.full_name?.slice(0, 2).toUpperCase() ?? "??"}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-white truncate">{user?.full_name}</div>
              <div className="text-[11px] text-muted truncate">{user?.email}</div>
            </div>
            <button onClick={logout} className="text-muted hover:text-danger transition-colors" title="Sign out">
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto scrollbar-thin">
        <Outlet />
      </main>
    </div>
  );
}
