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
];

export default function BottomNav() {
  const pathname = usePathname();
  const { t } = useI18n();
  return (
    <nav className="bottom-nav">
      {ITEMS.map((item) => (
        <Link key={item.href} href={item.href} className={pathname === item.href ? "active" : ""}>
          <span className="icon">{item.icon}</span>
          <span>{t(item.key)}</span>
        </Link>
      ))}
    </nav>
  );
}
