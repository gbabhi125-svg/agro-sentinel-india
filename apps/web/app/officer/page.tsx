"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { api } from "@/lib/api";

export default function OfficerPage() {
  const [summary, setSummary] = useState<any>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.officerSummary(days).then(setSummary).finally(() => setLoading(false));
  }, [days]);

  return (
    <>
      <TopBar title="Officer Dashboard" />
      <main>
        <div className="card stack">
          <p className="muted" style={{ margin: 0 }}>
            Aggregated across all farmers using the app — no per-farmer identity is stored, so
            none is shown here.
          </p>
          <div>
            <label>Window</label>
            <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
        </div>

        {loading && <div className="card center"><div className="spinner" /></div>}

        {!loading && summary && (
          <div className="stack">
            <div className="card">
              <p className="muted" style={{ margin: 0 }}>Total diagnoses</p>
              <h2 style={{ margin: "4px 0" }}>{summary.total_diagnoses}</h2>
              <p className="hint">{summary.uncertain_count} were uncertain / escalated ({summary.total_diagnoses ? Math.round((summary.uncertain_count / summary.total_diagnoses) * 100) : 0}%)</p>
            </div>
            <div className="card">
              <p className="muted" style={{ margin: "0 0 8px" }}>Top causes reported</p>
              {summary.top_causes.length === 0 && <p className="hint">No data yet in this window.</p>}
              {summary.top_causes.map((c: any) => (
                <div key={c.cause} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
                  <span>{c.cause}</span>
                  <span style={{ fontWeight: 600 }}>{c.count}</span>
                </div>
              ))}
            </div>
            <div className="card">
              <p className="muted" style={{ margin: "0 0 8px" }}>By state</p>
              {summary.by_state.length === 0 && <p className="hint">No state data yet in this window.</p>}
              {summary.by_state.map((s: any) => (
                <div key={s.state} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
                  <span>{s.state}</span>
                  <span style={{ fontWeight: 600 }}>{s.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </>
  );
}
