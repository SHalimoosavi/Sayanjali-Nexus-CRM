import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("That email and password don't match our records.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      {/* Left: brand panel */}
      <div className="hidden lg:flex flex-col justify-between p-14 bg-surface relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, #C9A15E 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="relative">
          <div className="text-xs tracking-[0.3em] text-brass/80 font-mono mb-3">SAYANJALI NEXUS</div>
          <h1 className="font-display text-5xl leading-[1.05] text-white">
            One nexus.<br />Every vertical.
          </h1>
        </div>
        <div className="relative space-y-4 text-sm text-muted max-w-sm">
          <p>
            AI, software, hospitality, real estate, agriculture, and more —
            one operating platform holds every pipeline, client, and project
            the company runs.
          </p>
          <div className="flex gap-6 pt-4 border-t border-border font-mono text-xs">
            <div><span className="text-brass">29</span> verticals</div>
            <div><span className="text-brass">01</span> platform</div>
            <div><span className="text-brass">100%</span> local-first</div>
          </div>
        </div>
      </div>

      {/* Right: login form */}
      <div className="flex items-center justify-center p-8 bg-ink">
        <form onSubmit={onSubmit} className="w-full max-w-sm space-y-6">
          <div className="lg:hidden text-xs tracking-[0.3em] text-brass/80 font-mono mb-6">
            SAYANJALI NEXUS
          </div>
          <div>
            <h2 className="font-display text-2xl text-white mb-1">Sign in</h2>
            <p className="text-sm text-muted">Access your CRM workspace.</p>
          </div>

          {error && (
            <div className="text-sm text-danger bg-danger/10 border border-danger/30 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs text-muted font-medium">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface border border-border rounded-md px-3 py-2.5 text-sm text-white placeholder:text-muted/50 focus:border-brass transition-colors"
              placeholder="you@sayanjalinexus.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-muted font-medium">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface border border-border rounded-md px-3 py-2.5 text-sm text-white placeholder:text-muted/50 focus:border-brass transition-colors"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-brass hover:bg-brassSoft text-ink font-medium text-sm rounded-md py-2.5 transition-colors disabled:opacity-50"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-xs text-muted text-center">
            Local-first workspace. Data lives on this machine.
          </p>
        </form>
      </div>
    </div>
  );
}
