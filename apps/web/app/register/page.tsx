"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { useTheme } from "@/lib/theme";

export default function RegisterPage() {
  const { t } = useI18n();
  const { theme, setTheme } = useTheme();
  const { register } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError(t("auth.error_generic"));
      return;
    }
    setLoading(true);
    try {
      await register(name, username, password);
      router.replace("/");
    } catch (err: any) {
      setError(err.message || t("auth.error_generic"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <div style={{ position: "absolute", top: 16, right: 16 }}>
        <button
          className="iconbtn"
          type="button"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle dark mode"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
      </div>
      <div className="center" style={{ marginBottom: 24 }}>
        <div style={{ fontSize: "2.4rem" }}>🌾</div>
        <h1 style={{ margin: "8px 0 0" }}>{t("app_name")}</h1>
      </div>
      <form className="card stack" onSubmit={submit}>
        <h2 style={{ margin: 0 }}>{t("auth.register_title")}</h2>
        {error && <p style={{ color: "var(--danger)", margin: 0 }}>{error}</p>}
        <div>
          <label>{t("auth.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
        </div>
        <div>
          <label>{t("auth.username")}</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div>
          <label>{t("auth.password")}</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        </div>
        <div>
          <label>{t("auth.confirm_password")}</label>
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={6} />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? t("common.loading") : t("auth.register_button")}
        </button>
        <Link href="/login" className="hint center" style={{ display: "block" }}>
          {t("auth.have_account")}
        </Link>
      </form>
    </main>
  );
}
