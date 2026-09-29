const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}

export type FarmPredictRequest = {
  state: string;
  crop: string;
  season: string;
  year: number;
  rainfall_mm: number;
  fertilizer_kg?: number;
  pesticide_kg?: number;
};

export const api = {
  crops: () => req<{ crops: string[] }>("/api/farm/crops"),
  states: () => req<{ states: string[] }>("/api/farm/states"),
  modelCard: () => req<any>("/api/farm/model-card"),
  farmPredict: (body: FarmPredictRequest) =>
    req<any>("/api/farm/predict", { method: "POST", body: JSON.stringify(body) }),

  irrigationPlan: (body: {
    crop: string; state?: string; latitude?: number; longitude?: number;
    days_since_sowing: number; area_ha: number; forecast_days?: number;
  }) => req<any>("/api/water/irrigation-plan", { method: "POST", body: JSON.stringify(body) }),

  marketPrice: (crop: string) => req<any>(`/api/market/price/${encodeURIComponent(crop)}`),
  marketForecast: (crop: string) => req<any>(`/api/market/forecast/${encodeURIComponent(crop)}`),

  schemesMatch: (body: { crop?: string; drought_risk?: string; land_ha?: number }) =>
    req<any>("/api/schemes/match", { method: "POST", body: JSON.stringify(body) }),

  riskAlerts: (crop: string, state: string) =>
    req<any>(`/api/risk/alerts?crop=${encodeURIComponent(crop)}&state=${encodeURIComponent(state)}`),

  doctorObservations: () => req<{ observations: any[] }>("/api/doctor/observations"),

  doctorDiagnose: async (form: {
    crop: string; answers: Record<string, boolean>; asked: string[];
    state?: string; image?: File | null;
  }) => {
    const fd = new FormData();
    fd.append("crop", form.crop);
    fd.append("answers_json", JSON.stringify(form.answers));
    fd.append("asked_json", JSON.stringify(form.asked));
    if (form.state) fd.append("state", form.state);
    if (form.image) fd.append("image", form.image);
    const res = await fetch(`${API_URL}/api/doctor/diagnose`, { method: "POST", body: fd });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || res.statusText);
    }
    return res.json();
  },

  doctorFeedback: (diagnosisId: string, improved: boolean | null, notes: string) =>
    req<any>(`/api/doctor/feedback/${diagnosisId}`, {
      method: "POST", body: JSON.stringify({ improved, notes }),
    }),

  doctorHistory: () => req<{ history: any[] }>("/api/doctor/history"),
};
