"use client";

import Link from "next/link";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";

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
  return (
    <>
      <TopBar title={t("app_name")} />
      <main>
        <p className="muted" style={{ marginTop: 0, marginBottom: 14 }}>{t("home.title")}</p>
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
