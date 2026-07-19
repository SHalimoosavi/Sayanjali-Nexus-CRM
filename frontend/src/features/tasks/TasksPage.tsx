import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchTasks, createTask, updateTask, deleteTask, fetchProjects, Task } from "../../api/projects";
import { Plus, X, Check, Trash2, User } from "lucide-react";

const STATUS_TABS = [
  { value: "", label: "All" },
  { value: "todo", label: "To do" },
  { value: "in_progress", label: "In progress" },
  { value: "in_review", label: "In review" },
  { value: "done", label: "Done" },
];

const PRIORITY_COLORS: Record<string, string> = {
  low: "text-muted",
  medium: "text-signal",
  high: "text-warn",
  urgent: "text-danger",
};

export default function TasksPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [projectFilter, setProjectFilter] = useState<string>("");
  const [showModal, setShowModal] = useState(false);
  const qc = useQueryClient();

  const { data: projectsData } = useQuery({
    queryKey: ["projects", "all"],
    queryFn: () => fetchProjects({ page: 1, page_size: 100 }),
  });
  const projectMap = useMemo(() => {
    const m = new Map<string, string>();
    projectsData?.items?.forEach((p) => m.set(p.id, p.name));
    return m;
  }, [projectsData]);

  const { data, isLoading } = useQuery({
    queryKey: ["tasks", "all", statusFilter, projectFilter],
    queryFn: () => fetchTasks({
      status: statusFilter || undefined,
      project_id: projectFilter || undefined,
    }),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateTask(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTask,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      setShowModal(false);
    },
  });

  const tasks = data?.items ?? [];
  const openCount = tasks.filter((t) => t.status !== "done").length;

  return (
    <div className="p-8 max-w-5xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">WORK</div>
          <h1 className="font-display text-3xl text-white">Tasks</h1>
          <p className="text-sm text-muted mt-1">
            {isLoading ? "Loading…" : `${openCount} open across every project, plus anything personal.`}
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-brass hover:bg-brassSoft text-ink text-sm font-medium rounded-md px-4 py-2 transition-colors"
        >
          <Plus size={15} /> New task
        </button>
      </div>

      <div className="flex items-center justify-between gap-4 mb-6 flex-wrap">
        <div className="flex gap-1.5">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                statusFilter === tab.value ? "bg-brass/10 text-brass border-brass/30" : "text-muted border-border hover:border-white/20"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <select
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          className="bg-surface border border-border rounded-md px-3 py-1.5 text-xs text-white"
        >
          <option value="">All projects + personal</option>
          {projectsData?.items?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        {isLoading && <div className="px-4 py-8 text-center text-sm text-muted">Loading…</div>}
        {!isLoading && !tasks.length && (
          <div className="px-4 py-8 text-center text-sm text-muted">
            No tasks here. Create one — leave "Project" empty for a personal task.
          </div>
        )}
        {tasks.map((t: Task) => {
          const done = t.status === "done";
          return (
            <div key={t.id} className="flex items-center gap-3 px-4 py-3 border-b border-border last:border-0 hover:bg-white/[0.02] group">
              <button
                onClick={() => toggleMutation.mutate({ id: t.id, status: done ? "todo" : "done" })}
                className={`w-4.5 h-4.5 rounded border flex items-center justify-center shrink-0 transition-colors ${
                  done ? "bg-good border-good" : "border-border hover:border-brass/50"
                }`}
                style={{ width: 18, height: 18 }}
              >
                {done && <Check size={12} className="text-ink" />}
              </button>

              <div className="flex-1 min-w-0">
                <div className={`text-sm ${done ? "text-muted line-through" : "text-white"}`}>{t.title}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  {t.project_id ? (
                    <span className="text-xs text-muted">{projectMap.get(t.project_id) ?? "Project"}</span>
                  ) : (
                    <span className="text-xs text-brass/70 flex items-center gap-1"><User size={10} /> Personal</span>
                  )}
                  {t.due_date && (
                    <span className="text-xs text-muted">· due {new Date(t.due_date).toLocaleDateString()}</span>
                  )}
                </div>
              </div>

              <span className={`text-xs capitalize shrink-0 ${PRIORITY_COLORS[t.priority] ?? "text-muted"}`}>
                {t.priority}
              </span>

              <button
                onClick={() => deleteMutation.mutate(t.id)}
                className="opacity-0 group-hover:opacity-100 text-muted hover:text-danger transition-all shrink-0"
                title="Delete task"
              >
                <Trash2 size={14} />
              </button>
            </div>
          );
        })}
      </div>

      {showModal && (
        <NewTaskModal
          projects={projectsData?.items ?? []}
          onClose={() => setShowModal(false)}
          onSubmit={(payload: Partial<Task>) => createMutation.mutate(payload)}
          submitting={createMutation.isPending}
        />
      )}
    </div>
  );
}

function NewTaskModal({ projects, onClose, onSubmit, submitting }: {
  projects: { id: string; name: string }[];
  onClose: () => void;
  onSubmit: (payload: Partial<Task>) => void;
  submitting: boolean;
}) {
  const [form, setForm] = useState({ title: "", project_id: "", priority: "medium", due_date: "" });

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-surface border border-border rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-xl text-white">New task</h3>
          <button onClick={onClose} className="text-muted hover:text-white"><X size={18} /></button>
        </div>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit({
              title: form.title,
              project_id: form.project_id || undefined,
              priority: form.priority,
              due_date: form.due_date || undefined,
            });
          }}
        >
          <div>
            <label className="text-xs text-muted">Title</label>
            <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="text-xs text-muted">Project (optional — leave blank for a personal task)</label>
            <select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white">
              <option value="">Personal task</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted">Priority</label>
              <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-muted">Due date</label>
              <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" />
            </div>
          </div>
          <button type="submit" disabled={submitting}
            className="w-full bg-brass hover:bg-brassSoft text-ink font-medium text-sm rounded-md py-2.5 transition-colors disabled:opacity-50">
            {submitting ? "Creating…" : "Create task"}
          </button>
        </form>
      </div>
    </div>
  );
}
