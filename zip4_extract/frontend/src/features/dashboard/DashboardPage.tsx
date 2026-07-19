import { useQuery } from "@tanstack/react-query";
import { fetchLeads, fetchVerticals } from "../../api/leads";
import { fetchOpportunities } from "../../api/opportunities";
import { TrendingUp, Users, Briefcase, Clock } from "lucide-react";

function KpiCard({ label, value, icon: Icon, hint }: { label: string; value: string; icon: any; hint?: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-muted">{label}</span>
        <Icon size={16} className="text-brass" />
      </div>
      <div className="font-display text-3xl text-white">{value}</div>
      {hint && <div className="text-xs text-muted mt-1">{hint}</div>}
    </div>
  );
}

const formatINR = (value: number) =>
  new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value);

export default function DashboardPage() {
  const { data: leadsData } = useQuery({
    queryKey: ["leads", "dashboard"],
    queryFn: () => fetchLeads({ page: 1, page_size: 5 }),
  });
  const { data: verticals } = useQuery({ queryKey: ["verticals"], queryFn: fetchVerticals });
  const { data: opportunitiesData } = useQuery({
    queryKey: ["opportunities", "dashboard"],
    queryFn: () => fetchOpportunities({ page: 1, page_size: 1 }),
  });

  return (
    <div className="p-8 max-w-6xl">
      <div className="mb-8">
        <div className="text-xs tracking-[0.2em] text-brass font-mono mb-1">OVERVIEW</div>
        <h1 className="font-display text-3xl text-white">Good to see you.</h1>
        <p className="text-sm text-muted mt-1">Here's what's moving across every vertical today.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Open Leads" value={String(leadsData?.total ?? "—")} icon={Users} hint="Across all verticals" />
        <KpiCard label="Active Verticals" value={String(verticals?.filter(v => v).length ?? "—")} icon={Briefcase} hint="Onboarded business lines" />
        <KpiCard
          label="Pipeline Value"
          value={opportunitiesData ? `₹${formatINR(opportunitiesData.open_value_total)}` : "—"}
          icon={TrendingUp}
          hint={`${opportunitiesData?.total ?? 0} open opportunities`}
        />
        <KpiCard label="Follow-ups Due" value="—" icon={Clock} hint="Reminders module not wired yet" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-surface border border-border rounded-lg p-5">
          <h2 className="font-display text-lg text-white mb-4">Recent leads</h2>
          <div className="space-y-2">
            {leadsData?.items?.length ? (
              leadsData.items.map((lead) => (
                <div key={lead.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <div>
                    <div className="text-sm text-white">{lead.full_name}</div>
                    <div className="text-xs text-muted">{lead.company_name ?? "No company"}</div>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-brass/10 text-brass border border-brass/20">
                    {lead.stage}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No leads yet. Add your first lead to get started.</p>
            )}
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-5">
          <h2 className="font-display text-lg text-white mb-4">Business verticals</h2>
          <div className="space-y-1.5 max-h-72 overflow-y-auto scrollbar-thin">
            {verticals?.slice(0, 10).map((v) => (
              <div key={v.id} className="text-sm text-white/80 px-2 py-1.5 rounded hover:bg-white/5">
                {v.name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
