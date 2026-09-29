"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";

export default function MarketPage() {
  const { t } = useI18n();
  const [crop, setCrop] = useState("rice");
  const [price, setPrice] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function lookup() {
    setLoading(true);
    setPrice(null);
    setForecast(null);
    const [p, f] = await Promise.all([
      api.marketPrice(crop).catch((e) => ({ available: false, reason: e.message })),
      api.marketForecast(crop).catch((e) => ({ available: false, reason: e.message })),
    ]);
    setPrice(p);
    setForecast(f);
    setLoading(false);
  }

  return (
    <>
      <TopBar title={t("market.title")} />
      <main>
        <div className="card stack">
          <div>
            <label>{t("farm.crop")}</label>
            <input value={crop} onChange={(e) => setCrop(e.target.value)} placeholder="e.g. rice, wheat, onion" />
          </div>
          <button onClick={lookup} disabled={loading} type="button">
            {loading ? t("common.loading") : t("market.current_price")}
          </button>
        </div>

        {price && (
          <div className="card">
            <p className="muted" style={{ margin: 0 }}>{t("market.current_price")}</p>
            {price.available ? (
              <>
                <h2 style={{ margin: "4px 0" }}>₹{price.price} / quintal</h2>
                <p className="hint">{price.sample_market}, {price.sample_state} — {price.date} — {price.source}</p>
              </>
            ) : (
              <p>{t("market.unavailable")} <span className="hint">({price.reason})</span></p>
            )}
          </div>
        )}

        {forecast && forecast.available && (
          <div className="card">
            <p className="muted" style={{ margin: 0 }}>{t("market.forecast")}</p>
            {forecast.forecast.map((f: any) => (
              <div key={f.days_ahead} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
                <span>+{f.days_ahead}d</span>
                <span>₹{f.low}–₹{f.high} (≈₹{f.point_estimate})</span>
              </div>
            ))}
            <p className="hint" style={{ marginTop: 8 }}>{forecast.disclaimer}</p>
          </div>
        )}
        {forecast && !forecast.available && (
          <div className="card muted">{forecast.reason}</div>
        )}
      </main>
    </>
  );
}
