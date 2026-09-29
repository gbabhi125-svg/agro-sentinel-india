"use client";

import { createContext, useContext, useEffect, useState } from "react";
import en from "../messages/en.json";
import hi from "../messages/hi.json";
import kn from "../messages/kn.json";
import ta from "../messages/ta.json";
import te from "../messages/te.json";
import ml from "../messages/ml.json";

export type Lang = "en" | "hi" | "kn" | "ta" | "te" | "ml";
const DICTS: Record<Lang, Record<string, string>> = { en, hi, kn, ta, te, ml };
export const LANG_LABELS: Record<Lang, string> = {
  en: "English", hi: "हिन्दी", kn: "ಕನ್ನಡ", ta: "தமிழ்", te: "తెలుగు", ml: "മലയാളം",
};

const I18nContext = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (key: string) => string }>({
  lang: "en",
  setLang: () => {},
  t: (key: string) => key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("agrosentinel_lang") as Lang | null;
      if (saved && DICTS[saved]) setLangState(saved);
    } catch {
      // ignore
    }
  }, []);

  const setLang = (l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem("agrosentinel_lang", l);
    } catch {
      // ignore
    }
  };

  const t = (key: string) => DICTS[lang][key] ?? DICTS.en[key] ?? key;

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
