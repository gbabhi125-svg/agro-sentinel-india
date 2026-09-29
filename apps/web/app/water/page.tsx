"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";

export default function WaterPage() {
  const { t } = useI18n();
  const [states, setStates] = useState<string[]>([]);
  const [crops, setCrops] = useState<string[]>([]);
  const [state, setState] = useState("Punjab");
  const [crop, setCrop] = useState("Wheat");
  const [daysSinceSowing, setDaysSinceSowing] = useState(20);
  const [areaHa, setAreaHa] = useState(1);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.states().then((r) => setStates(r.states)).catch(() => {});
    api.crops().then((r) => setCrops(r.crops)).catch(() => {});
  }, []);

  async function getPlan() {
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await api.irrigationPlan({ crop, state, days_since_sowing: daysSinceSowing, area_ha: areaHa, forecast_days: 7 });
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <TopBar title={t("water.title")} />
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
            <label>{t("water.days_since_sowing")}</label>
            <input type="number" value={daysSinceSowing} onChange={(e) => setDaysSinceSowing(Number(e.target.value))} />
          </div>
          <div>
            <label>{t("water.area")}</label>
            <input type="number" value={areaHa} onChange={(e) => setAreaHa(Number(e.target.value))} />
          </div>
          <button onClick={getPlan} disabled={loading} type="button">
            {loading ? t("common.loading") : t("water.plan")}
          </button>
        </div>

        {error && (
          <div className="card" style={{ color: "var(--danger)" }}>
            {error}
            <p className="hint">Live weather is required for this — it needs internet access to Open-Meteo.</p>
          </div>
        )}

        {result && (
          <div className="stack">
            <div className="card">
              <p className="muted" style={{ margin: 0 }}>{t("water.total_need")}</p>
              <h2 style={{ margin: "4px 0" }}>{result.total_irrigation_mm} mm</h2>
              <p className="hint">≈ {result.total_volume_m3.toLocaleString()} m³ for {areaHa}ha — {result.method}</p>
            </div>
            <div className="card">
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
                    <th>Date</th><th>ET0</th><th>Kc</th><th>Need</th><th>Rain used</th><th>Irrigate</th>
                  </tr>
                </thead>
                <tbody>
                  {result.daily_plan.map((d: any) => (
                    <tr key={d.date} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td>{d.date.slice(5)}</td>
                      <td>{d.et0_mm}</td>
                      <td>{d.kc}</td>
                      <td>{d.crop_water_need_mm}</td>
                      <td>{d.effective_rainfall_mm}</td>
                      <td style={{ fontWeight: 600 }}>{d.irrigation_needed_mm}mm</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
