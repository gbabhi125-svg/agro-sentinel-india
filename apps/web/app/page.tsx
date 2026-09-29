"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

const TILES = [
  { href: "/doctor", emoji: "🩺", labelKey: "nav.doctor", subKey: "home.doctor.sub" },
  { href: "/farm", emoji: "🌾", labelKey: "nav.farm", subKey: "home.farm.sub" },
  { href: "/water", emoji: "💧", labelKey: "nav.water", subKey: "home.water.sub" },
  { href: "/market", emoji: "📈", labelKey: "nav.market", subKey: "home.market.sub" },
  { href: "/schemes", emoji: "🏛️", labelKey: "nav.schemes", subKey: "home.schemes.sub" },
  { href: "/history", emoji: "🕘", labelKey: "nav.history", subKey: "home.history.sub" },
  { href: "/officer", emoji: "📊", labelKey: "nav.officer", subKey: "home.officer.sub" },
];

export default function Home() {
  const { t } = useI18n();
  const { user, logout } = useAuth();
  const [stats, setStats] = useState<{
    records: number; crops: number; states: number; yieldR2: number; failureRecall: number;
  } | null>(null);

  useEffect(() => {
    Promise.all([api.modelCard(), api.crops(), api.states()])
      .then(([card, crops, states]) => {
        const v = card.validation;
        setStats({
          records: v.n_train + v.n_test,
          crops: crops.crops.length,
          states: states.states.length,
          yieldR2: v.yield_test_r2,
          failureRecall: v.failure_test_recall,
        });
      })
      .catch(() => {});
  }, []);

  return (
    <>
      <TopBar title={t("app_name")} />
      <main>
        <div className="hero">
          <div style={{ fontSize: "1.8rem" }}>🌾</div>
          <h1>{t("app_name")}</h1>
          <p>{t("home.title")}</p>
          <div className="hero-badges">
            <span className="hero-badge">📡 {t("home.market.sub")}</span>
            <span className="hero-badge">🌤 Live Weather</span>
            <span className="hero-badge">💧 Irrigation AI</span>
            <span className="hero-badge">🐛 Pest Risk</span>
            <span className="hero-badge">🏛️ Govt Schemes</span>
          </div>
        </div>

        {stats && (
          <div className="stat-grid">
            <div className="stat-tile"><span className="value">{stats.records.toLocaleString()}</span><span className="label">Records</span></div>
            <div className="stat-tile"><span className="value">{stats.crops}</span><span className="label">Crops</span></div>
            <div className="stat-tile"><span className="value">{stats.states}</span><span className="label">States</span></div>
            <div className="stat-tile"><span className="value">{(stats.yieldR2 * 100).toFixed(1)}%</span><span className="label">Yield R² (out-of-time)</span></div>
            <div className="stat-tile"><span className="value">{(stats.failureRecall * 100).toFixed(0)}%</span><span className="label">Failure recall</span></div>
            <div className="stat-tile"><span className="value">Rule</span><span className="label">Drought method</span></div>
          </div>
        )}

        {user && (
          <div className="user-bar">
            <span>👋 {user.name}</span>
            <button className="btn-secondary" style={{ width: "auto", padding: "6px 12px" }} onClick={logout} type="button">
              {t("auth.logout")}
            </button>
          </div>
        )}

        <div className="grid-2">
          {TILES.map((tile) => (
            <Link key={tile.href} href={tile.href} className="nav-tile">
              <span className="emoji">{tile.emoji}</span>
              <span className="label">{t(tile.labelKey)}</span>
              <span className="sub">{t(tile.subKey)}</span>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
