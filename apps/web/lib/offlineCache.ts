"use client";

const KEY = "agrosentinel_last_diagnosis";

export function cacheLastDiagnosis(crop: string, result: any) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ crop, result, cachedAt: new Date().toISOString() }));
  } catch {
    // localStorage unavailable — offline caching just silently doesn't happen
  }
}

export function readLastDiagnosis(): { crop: string; result: any; cachedAt: string } | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isOnline(): boolean {
  return typeof navigator === "undefined" ? true : navigator.onLine;
}
