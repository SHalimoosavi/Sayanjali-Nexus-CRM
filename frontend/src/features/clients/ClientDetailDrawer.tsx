import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchClientNotes, addClientNote, fetchClientTimeline } from "../../api/clients";
import type { Client } from "../../api/clients";
import { X, Clock, StickyNote, ArrowRightLeft } from "lucide-react";

const ACTIVITY_ICONS: Record<string, string> = {
  created: "✦",
  status_change: "→",
  contact_added: "＋",
  converted_from_lead: "★",
};

export default function ClientDetailDrawer({ clientRecord, onClose }: { clientRecord: Client; onClose: () => void }) {
  const [tab, setTab] = useState<"timeline" | "notes">("timeline");
  const [noteText, setNoteText] = useState("");
  const qc = useQueryClient();

  const { data: notes } = useQuery({
    queryKey: ["client-notes", clientRecord.id],
    queryFn: () => fetchClientNotes(clientRecord.id),
  });
  const { data: timeline } = useQuery({
    queryKey: ["client-timeline", clientRecord.id],
    queryFn: () => fetchClientTimeline(clientRecord.id),
  });

  const addNoteMutation = useMutation({
    mutationFn: (note: string) => addClientNote(clientRecord.id, note),
    onSuccess: () => {
      setNoteText("");
      qc.invalidateQueries({ queryKey: ["client-notes", clientRecord.id] });
    },
  });

  return (
    <div className="fixed inset-0 bg-black/60 flex justify-end z-50">
      <div className="w-full max-w-md h-full bg-surface border-l border-border flex flex-col">
        <div className="flex items-start justify-between p-6 border-b border-border">
          <div>
            <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">CLIENT</div>
            <h2 className="font-display text-xl text-white">{clientRecord.display_name}</h2>
            {clientRecord.client_code && <div className="text-sm text-muted font-mono">{clientRecord.client_code}</div>}
          </div>
          <button onClick={onClose} className="text-muted hover:text-white"><X size={18} /></button>
        </div>

        <div className="flex border-b border-border px-6">
          <button
            onClick={() => setTab("timeline")}
            className={`flex items-center gap-1.5 text-xs px-3 py-3 border-b-2 transition-colors ${
              tab === "timeline" ? "border-brass text-brass" : "border-transparent text-muted hover:text-white"
            }`}
          >
            <Clock size={13} /> Timeline
          </button>
          <button
            onClick={() => setTab("notes")}
            className={`flex items-center gap-1.5 text-xs px-3 py-3 border-b-2 transition-colors ${
              tab === "notes" ? "border-brass text-brass" : "border-transparent text-muted hover:text-white"
            }`}
          >
            <StickyNote size={13} /> Notes {notes?.length ? `(${notes.length})` : ""}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
          {tab === "timeline" && (
            <div className="space-y-4">
              {!timeline?.length && <p className="text-sm text-muted">No activity yet.</p>}
              {timeline?.map((t) => (
                <div key={t.id} className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-brass/10 text-brass border border-brass/20 flex items-center justify-center text-xs shrink-0">
                    {ACTIVITY_ICONS[t.activity_type] ?? <ArrowRightLeft size={11} />}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm text-white/90">{t.description}</div>
                    <div className="text-xs text-muted mt-0.5">{new Date(t.created_at).toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "notes" && (
            <div className="space-y-4">
              <form
                onSubmit={(e) => { e.preventDefault(); if (noteText.trim()) addNoteMutation.mutate(noteText); }}
                className="flex gap-2"
              >
                <input
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Add a note…"
                  className="flex-1 bg-ink border border-border rounded-md px-3 py-2 text-sm text-white placeholder:text-muted/50"
                />
                <button type="submit" disabled={addNoteMutation.isPending}
                  className="text-xs px-3 py-2 rounded-md bg-brass/10 text-brass border border-brass/20 hover:bg-brass/20 transition-colors disabled:opacity-50">
                  Add
                </button>
              </form>
              {!notes?.length && <p className="text-sm text-muted">No notes yet.</p>}
              {notes?.map((n) => (
                <div key={n.id} className="border-b border-border pb-3 last:border-0">
                  <div className="text-sm text-white/90">{n.note}</div>
                  <div className="text-xs text-muted mt-1">{new Date(n.created_at).toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
