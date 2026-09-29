"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import TopBar from "@/components/TopBar";
import { api } from "@/lib/api";

function ProgressContent() {
  const params = useSearchParams();
  const label = params.get("label") || "";
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!label) return;
    api.photoProgress(label).then((r) => setEntries(r.entries)).finally(() => setLoading(false));
  }, [label]);

  return (
    <>
      <TopBar title={`${label} — progress`} />
      <main>
        {loading && <div className="card center"><div className="spinner" /></div>}
        {!loading && entries.length === 0 && <div className="card muted">No photos saved for this plant yet.</div>}
        {entries.map((e) => (
          <div className="card" key={e.id}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={api.photoUrl(e.id)} alt={e.created_at} style={{ width: "100%", borderRadius: 10, marginBottom: 8 }} />
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>{e.result.status === "diagnosed" ? (e.result.specific_name || e.result.cause_name) : "Uncertain"}</span>
              <span className="hint">{new Date(e.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </main>
    </>
  );
}

export default function ProgressPage() {
  return (
    <Suspense fallback={<div className="card center"><div className="spinner" /></div>}>
      <ProgressContent />
    </Suspense>
  );
}
