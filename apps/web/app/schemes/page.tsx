"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";

export default function SchemesPage() {
  const { t } = useI18n();
  const [crop, setCrop] = useState("");
  const [landHa, setLandHa] = useState(1);
  const [droughtRisk, setDroughtRisk] = useState("Low");
  const [schemes, setSchemes] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [claimGuide, setClaimGuide] = useState<any>(null);
  const [showClaimGuide, setShowClaimGuide] = useState(false);

  async function find() {
    setLoading(true);
    try {
      const res = await api.schemesMatch({ crop: crop || undefined, drought_risk: droughtRisk, land_ha: landHa });
      setSchemes(res.schemes);
    } finally {
      setLoading(false);
    }
  }

  async function toggleClaimGuide() {
    if (!claimGuide) {
      const g = await api.pmfbyClaimGuide();
      setClaimGuide(g);
    }
    setShowClaimGuide((v) => !v);
  }

  return (
    <>
      <TopBar title={t("schemes.title")} />
      <main>
        <div className="card stack">
          <div>
            <label>{t("farm.crop")} (optional)</label>
            <input value={crop} onChange={(e) => setCrop(e.target.value)} placeholder="e.g. Rice" />
          </div>
          <div>
            <label>Land size (hectares)</label>
            <input type="number" value={landHa} onChange={(e) => setLandHa(Number(e.target.value))} />
          </div>
          <div>
            <label>{t("farm.drought_risk")}</label>
            <select value={droughtRisk} onChange={(e) => setDroughtRisk(e.target.value)}>
              <option>Low</option><option>Medium</option><option>High</option>
            </select>
          </div>
          <button onClick={find} disabled={loading} type="button">
            {loading ? t("common.loading") : t("schemes.find")}
          </button>
        </div>

        {schemes?.map((s) => (
          <div className="card" key={s.id}>
            <h3 style={{ margin: "0 0 4px" }}>{s.full_name}</h3>
            <p style={{ margin: "0 0 6px" }}>{s.benefit}</p>
            <p className="hint" style={{ margin: "0 0 8px" }}>Eligibility: {s.eligibility}</p>
            <a href={s.link} target="_blank" rel="noopener noreferrer" className="hint">
              {s.source} (verified {s.last_verified})
            </a>
          </div>
        ))}

        <div className="card">
          <button className="btn-secondary" onClick={toggleClaimGuide} type="button">
            {showClaimGuide ? "Hide" : "🛡️ My crop failed — how do I file a PMFBY claim?"}
          </button>
          {showClaimGuide && claimGuide && (
            <div style={{ marginTop: 12 }}>
              <p className="hint">{claimGuide.urgency}</p>
              {claimGuide.steps.map((s: any) => (
                <div key={s.step} style={{ marginBottom: 10 }}>
                  <strong>{s.step}. {s.title}</strong>
                  <p style={{ margin: "2px 0 0" }}>{s.detail}</p>
                </div>
              ))}
              <p className="hint">Source: {claimGuide.source} (verified {claimGuide.last_verified}). This is guidance, not an automated filing — PMFBY has no public API to file a claim through.</p>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
