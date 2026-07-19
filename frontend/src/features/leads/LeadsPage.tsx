import { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchLeads, fetchVerticals, createLead, convertLeadToClient,
  bulkUpdateLeads, bulkDeleteLeads, importLeadsCSV, exportLeadsCSV, Lead,
} from "../../api/leads";
import { Plus, X, ArrowRight, Upload, Download, Trash2, Users2 } from "lucide-react";
import LeadDetailDrawer from "./LeadDetailDrawer";

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
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [activeLead, setActiveLead] = useState<Lead | null>(null);
  const [importResult, setImportResult] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  const { data: verticals } = useQuery({ queryKey: ["verticals"], queryFn: fetchVerticals });
  const { data: leadsData, isLoading } = useQuery({
    queryKey: ["leads", verticalFilter],
    queryFn: () => fetchLeads({ page: 1, page_size: 50, vertical_id: verticalFilter || undefined }),
  });

  const createMutation = useMutation({
    mutationFn: ({ payload, force }: { payload: Partial<Lead>; force?: boolean }) =>
      createLead(force ? { ...payload } : payload),
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

  const bulkStageMutation = useMutation({
    mutationFn: (stage: string) => bulkUpdateLeads(Array.from(selected), { stage }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      setSelected(new Set());
    },
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: () => bulkDeleteLeads(Array.from(selected)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      setSelected(new Set());
    },
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => importLeadsCSV(verticalFilter || verticals?.[0]?.id || "", file),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      setImportResult(
        `Imported ${result.created} leads. Skipped ${result.skipped_duplicates} duplicates.` +
        (result.errors.length ? ` ${result.errors.length} row(s) had errors.` : "")
      );
    },
  });

  const toggleSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (!leadsData?.items?.length) return;
    setSelected((prev) =>
      prev.size === leadsData.items.length ? new Set() : new Set(leadsData.items.map((l) => l.id))
    );
  };

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">PIPELINE</div>
          <h1 className="font-display text-3xl text-white">Leads</h1>
        </div>
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) importMutation.mutate(file);
              e.target.value = "";
            }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 text-muted hover:text-white border border-border rounded-md px-3 py-2 text-sm transition-colors"
            title="Import CSV"
          >
            <Upload size={14} /> Import
          </button>
          <button
            onClick={() => exportLeadsCSV(verticalFilter || undefined)}
            className="flex items-center gap-2 text-muted hover:text-white border border-border rounded-md px-3 py-2 text-sm transition-colors"
            title="Export CSV"
          >
            <Download size={14} /> Export
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-brass hover:bg-brassSoft text-ink text-sm font-medium rounded-md px-4 py-2 transition-colors"
          >
            <Plus size={15} /> New lead
          </button>
        </div>
      </div>

      {importResult && (
        <div className="flex items-center justify-between text-sm bg-brass/10 border border-brass/20 text-brass rounded-md px-4 py-2.5 mb-4">
          {importResult}
          <button onClick={() => setImportResult(null)} className="text-brass/70 hover:text-brass"><X size={14} /></button>
        </div>
      )}

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

      {selected.size > 0 && (
        <div className="flex items-center gap-3 bg-surface border border-brass/30 rounded-lg px-4 py-2.5 mb-4">
          <span className="text-xs text-brass flex items-center gap-1.5">
            <Users2 size={13} /> {selected.size} selected
          </span>
          <select
            onChange={(e) => e.target.value && bulkStageMutation.mutate(e.target.value)}
            defaultValue=""
            className="text-xs bg-ink border border-border rounded-md px-2 py-1.5 text-white"
          >
            <option value="" disabled>Move to stage…</option>
            {["New", "Contacted", "Qualified", "Proposal Sent", "Negotiation", "Won", "Lost"].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button
            onClick={() => bulkDeleteMutation.mutate()}
            disabled={bulkDeleteMutation.isPending}
            className="flex items-center gap-1 text-xs text-danger hover:text-danger/80 transition-colors ml-auto"
          >
            <Trash2 size={13} /> Delete selected
          </button>
          <button onClick={() => setSelected(new Set())} className="text-muted hover:text-white">
            <X size={14} />
          </button>
        </div>
      )}

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted">
              <th className="px-4 py-3 w-8">
                <input
                  type="checkbox"
                  checked={!!leadsData?.items?.length && selected.size === leadsData.items.length}
                  onChange={toggleSelectAll}
                  className="accent-brass"
                />
              </th>
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
              <tr><td colSpan={7} className="px-4 py-8 text-center text-muted">Loading…</td></tr>
            )}
            {!isLoading && !leadsData?.items?.length && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-muted">No leads yet. Create one to get started.</td></tr>
            )}
            {leadsData?.items?.map((lead) => (
              <tr key={lead.id} className="border-b border-border last:border-0 hover:bg-white/[0.02]">
                <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selected.has(lead.id)}
                    onChange={() => toggleSelected(lead.id)}
                    className="accent-brass"
                  />
                </td>
                <td className="px-4 py-3 text-white cursor-pointer" onClick={() => setActiveLead(lead)}>
                  {lead.full_name}
                </td>
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
          onSubmit={(payload: Partial<Lead>, force?: boolean) => createMutation.mutate({ payload, force })}
          submitting={createMutation.isPending}
          conflictMatches={
            (createMutation.error as any)?.response?.status === 409
              ? (createMutation.error as any).response.data.detail.matches
              : null
          }
        />
      )}

      {activeLead && <LeadDetailDrawer lead={activeLead} onClose={() => setActiveLead(null)} />}
    </div>
  );
}

function NewLeadModal({ verticals, onClose, onSubmit, submitting, conflictMatches }: {
  verticals: { id: string; name: string }[];
  onClose: () => void;
  onSubmit: (payload: Partial<Lead>, force?: boolean) => void;
  submitting: boolean;
  conflictMatches: { id: string; full_name: string; matched_on: string }[] | null;
}) {
  const [form, setForm] = useState({ full_name: "", company_name: "", phone: "", vertical_id: verticals[0]?.id ?? "" });

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-surface border border-border rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-xl text-white">New lead</h3>
          <button onClick={onClose} className="text-muted hover:text-white"><X size={18} /></button>
        </div>

        {conflictMatches && (
          <div className="bg-warn/10 border border-warn/20 rounded-md px-3 py-2.5 mb-4 text-xs">
            <div className="text-warn font-medium mb-1">Possible duplicate</div>
            <div className="text-white/70">
              Matches an existing lead: {conflictMatches.map((m) => m.full_name).join(", ")}
            </div>
            <button
              onClick={() => onSubmit(form, true)}
              className="text-warn hover:text-warn/80 underline mt-1.5"
            >
              Create anyway
            </button>
          </div>
        )}

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
              {verticals.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
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
