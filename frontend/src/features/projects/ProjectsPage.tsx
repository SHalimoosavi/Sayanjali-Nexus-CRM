import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchProjects, createProject, fetchTasks, createTask, updateTask, Project } from "../../api/projects";
import { fetchVerticals } from "../../api/leads";
import { fetchClients } from "../../api/clients";
import { Plus, X, ChevronDown, ChevronRight, Check } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  planning: "bg-signal/10 text-signal border-signal/20",
  active: "bg-brass/10 text-brass border-brass/20",
  on_hold: "bg-warn/10 text-warn border-warn/20",
  completed: "bg-good/10 text-good border-good/20",
  cancelled: "bg-danger/10 text-danger border-danger/20",
};

export default function ProjectsPage() {
  const [showModal, setShowModal] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const qc = useQueryClient();

  const { data: verticals } = useQuery({ queryKey: ["verticals"], queryFn: fetchVerticals });
  const { data: clients } = useQuery({ queryKey: ["clients", "all"], queryFn: () => fetchClients({ page: 1, page_size: 100 }) });
  const { data, isLoading } = useQuery({ queryKey: ["projects"], queryFn: () => fetchProjects({ page: 1, page_size: 50 }) });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setShowModal(false);
    },
  });

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">DELIVERY</div>
          <h1 className="font-display text-3xl text-white">Projects</h1>
          <p className="text-sm text-muted mt-1">Progress updates automatically as tasks complete.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-brass hover:bg-brassSoft text-ink text-sm font-medium rounded-md px-4 py-2 transition-colors"
        >
          <Plus size={15} /> New project
        </button>
      </div>

      <div className="space-y-3">
        {isLoading && <p className="text-sm text-muted">Loading…</p>}
        {!isLoading && !data?.items?.length && (
          <p className="text-sm text-muted">No projects yet. Create one, ideally against a client.</p>
        )}
        {data?.items?.map((p: Project) => (
          <div key={p.id} className="bg-surface border border-border rounded-lg overflow-hidden">
            <button
              onClick={() => setExpanded(expanded === p.id ? null : p.id)}
              className="w-full flex items-center gap-3 p-4 text-left hover:bg-white/[0.02] transition-colors"
            >
              {expanded === p.id ? <ChevronDown size={16} className="text-muted shrink-0" /> : <ChevronRight size={16} className="text-muted shrink-0" />}
              <div className="flex-1 min-w-0">
                <div className="text-white font-medium truncate">{p.name}</div>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full border shrink-0 ${STATUS_COLORS[p.status] ?? "border-border text-muted"}`}>
                {p.status.replace("_", " ")}
              </span>
              <div className="w-32 shrink-0">
                <div className="h-1.5 bg-ink rounded-full overflow-hidden">
                  <div className="h-full bg-brass transition-all" style={{ width: `${p.progress_percent}%` }} />
                </div>
                <div className="text-[10px] text-muted mt-1 text-right font-mono">{p.progress_percent}%</div>
              </div>
            </button>
            {expanded === p.id && <ProjectTasks projectId={p.id} />}
          </div>
        ))}
      </div>

      {showModal && (
        <NewProjectModal
          verticals={verticals ?? []}
          clients={clients?.items ?? []}
          onClose={() => setShowModal(false)}
          onSubmit={(payload: Partial<Project>) => createMutation.mutate(payload)}
          submitting={createMutation.isPending}
        />
      )}
    </div>
  );
}

function ProjectTasks({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const [newTitle, setNewTitle] = useState("");

  const { data } = useQuery({
    queryKey: ["tasks", projectId],
    queryFn: () => fetchTasks({ project_id: projectId }),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateTask(id, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks", projectId] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const addMutation = useMutation({
    mutationFn: () => createTask({ project_id: projectId, title: newTitle }),
    onSuccess: () => {
      setNewTitle("");
      qc.invalidateQueries({ queryKey: ["tasks", projectId] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  return (
    <div className="border-t border-border px-4 py-3 bg-ink/40">
      <div className="space-y-1.5 mb-3">
        {data?.items?.map((t) => {
          const done = t.status === "done";
          return (
            <button
              key={t.id}
              onClick={() => toggleMutation.mutate({ id: t.id, status: done ? "todo" : "done" })}
              className="w-full flex items-center gap-2.5 text-left px-2 py-1.5 rounded hover:bg-white/5 transition-colors"
            >
              <span className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors ${
                done ? "bg-good border-good" : "border-border"
              }`}>
                {done && <Check size={11} className="text-ink" />}
              </span>
              <span className={`text-sm ${done ? "text-muted line-through" : "text-white/80"}`}>{t.title}</span>
            </button>
          );
        })}
        {!data?.items?.length && <p className="text-xs text-muted px-2 py-1">No tasks yet.</p>}
      </div>
      <form
        onSubmit={(e) => { e.preventDefault(); if (newTitle.trim()) addMutation.mutate(); }}
        className="flex gap-2"
      >
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="Add a task…"
          className="flex-1 bg-surface border border-border rounded-md px-3 py-1.5 text-sm text-white placeholder:text-muted/50"
        />
        <button type="submit" className="text-xs px-3 py-1.5 rounded-md bg-brass/10 text-brass border border-brass/20 hover:bg-brass/20 transition-colors">
          Add
        </button>
      </form>
    </div>
  );
}

function NewProjectModal({ verticals, clients, onClose, onSubmit, submitting }: any) {
  const [form, setForm] = useState({
    vertical_id: verticals[0]?.id ?? "", client_id: "", name: "", status: "planning",
  });

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-surface border border-border rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-xl text-white">New project</h3>
          <button onClick={onClose} className="text-muted hover:text-white"><X size={18} /></button>
        </div>
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); onSubmit({ ...form, client_id: form.client_id || undefined }); }}>
          <div>
            <label className="text-xs text-muted">Vertical</label>
            <select value={form.vertical_id} onChange={(e) => setForm({ ...form, vertical_id: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white">
              {verticals.map((v: any) => <option key={v.id} value={v.id}>{v.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-muted">Client (optional)</label>
            <select value={form.client_id} onChange={(e) => setForm({ ...form, client_id: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white">
              <option value="">No client</option>
              {clients.map((c: any) => <option key={c.id} value={c.id}>{c.display_name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-muted">Project name</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" />
          </div>
          <button type="submit" disabled={submitting}
            className="w-full bg-brass hover:bg-brassSoft text-ink font-medium text-sm rounded-md py-2.5 transition-colors disabled:opacity-50">
            {submitting ? "Creating…" : "Create project"}
          </button>
        </form>
      </div>
    </div>
  );
}
