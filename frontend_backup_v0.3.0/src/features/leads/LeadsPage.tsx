import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchLeads, fetchVerticals, createLead, convertLeadToClient } from "../../api/leads";
import { Plus, X, ArrowRight } from "lucide-react";

const STAGE_COLORS: Record<string, string> = {
  New: "bg-signal/10 text-signal border-signal/20",
  Contacted: "bg-warn/10 text-warn border-warn/20",
  Qualified: "bg-brass/10 text-brass border-brass/20",
  "Proposal Sent": "bg-brass/10 text-brass border-brass/20",
  Negotiation: "bg-warn/10 text-warn border-warn/20",
  Won: "bg-good/10 text-good border-good/20",
  Lost: "bg-danger/10 text-danger border-danger/20",
};

export default function LeadsPage() {
  const [verticalFilter, setVerticalFilter] = useState<string>("");
  const [showModal, setShowModal] = useState(false);
  const qc = useQueryClient();

  const { data: verticals } = useQuery({ queryKey: ["verticals"], queryFn: fetchVerticals });
  const { data: leadsData, isLoading } = useQuery({
    queryKey: ["leads", verticalFilter],
    queryFn: () => fetchLeads({ page: 1, page_size: 50, vertical_id: verticalFilter || undefined }),
  });

  const createMutation = useMutation({
    mutationFn: createLead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      setShowModal(false);
    },
  });

  const convertMutation = useMutation({
    mutationFn: convertLeadToClient,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">PIPELINE</div>
          <h1 className="font-display text-3xl text-white">Leads</h1>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-brass hover:bg-brassSoft text-ink text-sm font-medium rounded-md px-4 py-2 transition-colors"
        >
          <Plus size={15} /> New lead
        </button>
      </div>

      <div className="flex gap-2 mb-6 flex-wrap">
        <button
          onClick={() => setVerticalFilter("")}
          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
            !verticalFilter ? "bg-brass/10 text-brass border-brass/30" : "text-muted border-border hover:border-white/20"
          }`}
        >
          All verticals
        </button>
        {verticals?.slice(0, 8).map((v) => (
          <button
            key={v.id}
            onClick={() => setVerticalFilter(v.id)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              verticalFilter === v.id ? "bg-brass/10 text-brass border-brass/30" : "text-muted border-border hover:border-white/20"
            }`}
          >
            {v.name}
          </button>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted">
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Company</th>
              <th className="px-4 py-3 font-medium">Phone</th>
              <th className="px-4 py-3 font-medium">Stage</th>
              <th className="px-4 py-3 font-medium">Priority</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">Loading…</td></tr>
            )}
            {!isLoading && !leadsData?.items?.length && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted">No leads yet. Create one to get started.</td></tr>
            )}
            {leadsData?.items?.map((lead) => (
              <tr key={lead.id} className="border-b border-border last:border-0 hover:bg-white/[0.02]">
                <td className="px-4 py-3 text-white">{lead.full_name}</td>
                <td className="px-4 py-3 text-white/70">{lead.company_name ?? "—"}</td>
                <td className="px-4 py-3 text-white/70 font-mono text-xs">{lead.phone ?? "—"}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-1 rounded-full border ${STAGE_COLORS[lead.stage] ?? "border-border text-muted"}`}>
                    {lead.stage}
                  </span>
                </td>
                <td className="px-4 py-3 text-white/70 capitalize">{lead.priority}</td>
                <td className="px-4 py-3 text-right">
                  {!lead.is_converted ? (
                    <button
                      onClick={() => convertMutation.mutate(lead.id)}
                      disabled={convertMutation.isPending}
                      className="text-xs flex items-center gap-1 ml-auto text-brass hover:text-brassSoft transition-colors disabled:opacity-40"
                    >
                      Convert to client <ArrowRight size={12} />
                    </button>
                  ) : (
                    <span className="text-xs text-muted">Converted</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <NewLeadModal
          verticals={verticals ?? []}
          onClose={() => setShowModal(false)}
          onSubmit={(payload: Partial<import("../../api/leads").Lead>) => createMutation.mutate(payload)}
          submitting={createMutation.isPending}
        />
      )}
    </div>
  );
}

function NewLeadModal({ verticals, onClose, onSubmit, submitting }: any) {
  const [form, setForm] = useState({ full_name: "", company_name: "", phone: "", vertical_id: verticals[0]?.id ?? "" });

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-surface border border-border rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-xl text-white">New lead</h3>
          <button onClick={onClose} className="text-muted hover:text-white"><X size={18} /></button>
        </div>
        <form
          className="space-y-4"
          onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}
        >
          <div>
            <label className="text-xs text-muted">Vertical</label>
            <select
              value={form.vertical_id}
              onChange={(e) => setForm({ ...form, vertical_id: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white"
            >
              {verticals.map((v: any) => <option key={v.id} value={v.id}>{v.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-muted">Full name</label>
            <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="text-xs text-muted">Company</label>
            <input value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="text-xs text-muted">Phone</label>
            <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="w-full mt-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white" />
          </div>
          <button type="submit" disabled={submitting}
            className="w-full bg-brass hover:bg-brassSoft text-ink font-medium text-sm rounded-md py-2.5 transition-colors disabled:opacity-50">
            {submitting ? "Creating…" : "Create lead"}
          </button>
        </form>
      </div>
    </div>
  );
}
