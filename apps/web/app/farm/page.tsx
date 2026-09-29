"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";

const SEASONS = ["Kharif", "Rabi", "Summer", "Whole Year", "Autumn", "Winter"];

export default function FarmPage() {
  const { t } = useI18n();
  const [states, setStates] = useState<string[]>([]);
  const [crops, setCrops] = useState<string[]>([]);
  const [state, setState] = useState("Maharashtra");
  const [crop, setCrop] = useState("Rice");
  const [season, setSeason] = useState("Kharif");
  const [rainfall, setRainfall] = useState(1000);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.states().then((r) => setStates(r.states)).catch(() => {});
    api.crops().then((r) => setCrops(r.crops)).catch(() => {});
  }, []);

  async function predict() {
    setError(null);
    setLoading(true);
    try {
      const res = await api.farmPredict({
        state, crop, season, year: new Date().getFullYear(), rainfall_mm: rainfall,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const riskBadge = (level: string) => `badge badge-${level.toLowerCase()}`;

  return (
    <>
      <TopBar title={t("farm.title")} />
      <main>
        <div className="card stack">
          <div>
            <label>{t("farm.state")}</label>
            <select value={state} onChange={(e) => setState(e.target.value)}>
              {states.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label>{t("farm.crop")}</label>
            <select value={crop} onChange={(e) => setCrop(e.target.value)}>
              {crops.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label>{t("farm.season")}</label>
            <select value={season} onChange={(e) => setSeason(e.target.value)}>
              {SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label>{t("farm.rainfall")}</label>
            <input type="number" value={rainfall} onChange={(e) => setRainfall(Number(e.target.value))} />
          </div>
          <button onClick={predict} disabled={loading} type="button">
            {loading ? t("common.loading") : t("farm.predict")}
          </button>
        </div>

        {error && <div className="card" style={{ color: "var(--danger)" }}>{error}</div>}

        {result && (
          <div className="stack">
            <div className="card">
              <p className="muted" style={{ margin: 0 }}>{t("farm.yield")}</p>
              <h2 style={{ margin: "4px 0" }}>{result.yield.predicted_yield} {result.yield.unit}</h2>
              {result.yield.model_mae_for_this_crop != null && (
                <p className="hint">± {result.yield.model_mae_for_this_crop} {result.yield.unit} typical error for {crop} ({result.yield.model_mae_note})</p>
              )}
            </div>
            <div className="card">
              <p className="muted" style={{ margin: 0 }}>{t("farm.failure_risk")}</p>
              <span className={riskBadge(result.failure.risk_level)}>{result.failure.risk_level} ({(result.failure.failure_probability * 100).toFixed(0)}%)</span>
              <p className="hint">{result.failure.model_honesty_note}</p>
            </div>
            <div className="card">
              <p className="muted" style={{ margin: 0 }}>{t("farm.drought_risk")}</p>
              <span className={riskBadge(result.drought.risk_level)}>{result.drought.category}</span>
              <p className="hint">{result.drought.departure_from_lpa_pct}% vs this state&apos;s long-period average ({result.drought.state_lpa_mm}mm) — {result.drought.method}</p>
            </div>
            {!result.season.suppressed ? (
              <div className="card">
                <p className="muted" style={{ margin: 0 }}>{t("farm.best_season")}</p>
                <h3 style={{ margin: "4px 0" }}>{result.season.best_season} ({(result.season.confidence * 100).toFixed(0)}%)</h3>
              </div>
            ) : (
              <div className="card muted">{result.season.reason}</div>
            )}
          </div>
        )}
      </main>
    </>
  );
}
