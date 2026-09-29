"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";

export default function HistoryPage() {
  const { t } = useI18n();
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.doctorHistory().then((r) => setHistory(r.history)).finally(() => setLoading(false));
  }, []);

  return (
    <>
      <TopBar title={t("history.title")} />
      <main>
        {loading && <div className="card center"><div className="spinner" /></div>}
        {!loading && history.length === 0 && <div className="card muted">{t("history.empty")}</div>}
        {history.map((h) => (
          <div className="card" key={h.id}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{h.crop}</strong>
              <span className="hint">{new Date(h.created_at).toLocaleDateString()}</span>
            </div>
            <p style={{ margin: "6px 0 0" }}>
              {h.result.status === "diagnosed" ? (h.result.specific_name || h.result.cause_name) : "Uncertain — escalated"}
            </p>
            <span className="hint">Feedback: {h.feedback_status}</span>
          </div>
        ))}
      </main>
    </>
  );
}
