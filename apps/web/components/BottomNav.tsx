"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/lib/i18n";

const ITEMS = [
  { href: "/", icon: "🏠", key: "nav.home" },
  { href: "/doctor", icon: "🩺", key: "nav.doctor" },
  { href: "/farm", icon: "🌾", key: "nav.farm" },
  { href: "/water", icon: "💧", key: "nav.water" },
  { href: "/market", icon: "📈", key: "nav.market" },
  { href: "/schemes", icon: "🏛️", key: "nav.schemes" },
  { href: "/history", icon: "🕘", key: "nav.history" },
  { href: "/officer", icon: "📊", key: "nav.officer" },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { t } = useI18n();
  return (
    <nav className="topnav">
      <span className="brand">🌾 {t("app_name")}</span>
      {ITEMS.map((item) => (
        <Link key={item.href} href={item.href} className={pathname === item.href ? "active" : ""}>
          <span>{item.icon}</span>
          <span className="label-text">{t(item.key)}</span>
        </Link>
      ))}
      <span className="spacer" />
    </nav>
  );
}
