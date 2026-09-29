"use client";

import { useI18n, LANG_LABELS, Lang } from "@/lib/i18n";
import { useTheme } from "@/lib/theme";

export default function TopBar({ title }: { title: string }) {
  const { lang, setLang } = useI18n();
  const { theme, setTheme } = useTheme();

  return (
    <header className="topbar">
      <h1>{title}</h1>
      <div className="btn-row" style={{ width: "auto", gap: 6 }}>
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value as Lang)}
          style={{ width: "auto", padding: "6px 8px", marginBottom: 0, fontSize: "0.8rem" }}
          aria-label="Language"
        >
          {Object.entries(LANG_LABELS).map(([code, label]) => (
            <option key={code} value={code}>{label}</option>
          ))}
        </select>
        <button
          className="iconbtn"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle dark mode"
          type="button"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
      </div>
    </header>
  );
}
