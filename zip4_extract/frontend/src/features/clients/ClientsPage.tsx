import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchClients, createClient, Client } from "../../api/clients";
import { Plus, X, Building2 } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-good/10 text-good border-good/20",
  inactive: "bg-muted/10 text-muted border-border",
  churned: "bg-danger/10 text-danger border-danger/20",
};

export default function ClientsPage() {
  const [showModal, setShowModal] = useState(false);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["clients"],
    queryFn: () => fetchClients({ page: 1, page_size: 50 }),
  });

  const createMutation = useMutation({
    mutationFn: createClient,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
      setShowModal(false);
    },
  });

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">ACCOUNTS</div>
          <h1 className="font-display text-3xl text-white">Clients</h1>
          <p className="text-sm text-muted mt-1">Leads convert here automatically once qualified.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-brass hover:bg-brassSoft text-ink text-sm font-medium rounded-md px-4 py-2 transition-colors"
        >
          <Plus size={15} /> New client
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading && <p className="text-sm text-muted col-span-full">Loading…</p>}
        {!isLoading && !data?.items?.length && (
          <p className="text-sm text-muted col-span-full">
            No clients yet. Convert a qualified lead, or add one directly.
          </p>
        )}
        {data?.items?.map((c: Client) => (
          <div key={c.id} className="bg-surface border border-border rounded-lg p-5 hover:border-brass/30 transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div className="w-9 h-9 rounded-md bg-brass/10 flex items-center justify-center text-brass">
                <Building2 size={16} />
              </div>
              <span className={`text-xs px-2 py-1 rounded-full border ${STATUS_COLORS[c.status] ?? "border-border text-muted"}`}>
                {c.status}
              </span>
            </div>
            <div className="text-white font-medium mb-0.5">{c.display_name}</div>
            <div className="text-xs text-muted font-mono">{c.client_code}</div>
          </div>
        ))}
      </div>

      {showModal && (
        <NewClientModal
          onClose={() => setShowModal(false)}
          onSubmit={(payload) => createMutation.mutate(payload)}
          submitting={createMutation.isPending}
        />
      )}
    </div>
  );
}

function NewClientModal({ onClose, onSubmit, submitting }: {
  onClose: () => void;
  onSubmit: (payload: Partial<Client>) => void;
  submitting: boolean;
}) {
  const [form, setForm] = useState({ display_name: "", notes: "" });

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-surface border border-border rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-xl text-white">New client</h3>
          <button onClick={onClose} className="text-muted hover:text-white"><X size={18} /></button>
        </div>
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}>
          <div>
            <label className="text-xs text-muted">Name</label>
            <input required value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="text-xs text-muted">Notes</label>
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" rows={3} />
          </div>
          <button type="submit" disabled={submitting}
            className="w-full bg-brass hover:bg-brassSoft text-ink font-medium text-sm rounded-md py-2.5 transition-colors disabled:opacity-50">
            {submitting ? "Creating…" : "Create client"}
          </button>
        </form>
      </div>
    </div>
  );
}
