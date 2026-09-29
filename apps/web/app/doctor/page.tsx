"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import TopBar from "@/components/TopBar";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";
import { speechRecognitionSupported, listenForYesNo } from "@/lib/speech";
import { cacheLastDiagnosis, readLastDiagnosis, isOnline } from "@/lib/offlineCache";
import { shareOnWhatsApp, printResult } from "@/lib/share";

type Stage = "setup" | "asking" | "loading" | "result";

export default function DoctorPage() {
  const { t, lang } = useI18n();
  const [stage, setStage] = useState<Stage>("setup");
  const [crop, setCrop] = useState("Rice");
  const [crops, setCrops] = useState<string[]>([]);
  const [states, setStates] = useState<string[]>([]);
  const [state, setState] = useState("Maharashtra");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [plantLabel, setPlantLabel] = useState("");
  const [optInCommunity, setOptInCommunity] = useState(false);
  const [answers, setAnswers] = useState<Record<string, boolean>>({});
  const [asked, setAsked] = useState<string[]>([]);
  const [question, setQuestion] = useState<{ id: string; text: string } | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [offlineNotice, setOfflineNotice] = useState(false);
  const [escalating, setEscalating] = useState(false);
  const [escalateStatus, setEscalateStatus] = useState<string | null>(null);
  const [nearbyReports, setNearbyReports] = useState<any[]>([]);
  const stopListenRef = useRef<() => void>(() => {});

  useEffect(() => {
    api.crops().then((r) => setCrops(r.crops)).catch(() => setCrops(["Rice", "Wheat", "Maize"]));
    api.states().then((r) => setStates(r.states)).catch(() => {});
    if (!isOnline()) {
      const cached = readLastDiagnosis();
      if (cached) {
        setResult(cached.result);
        setCrop(cached.crop);
        setStage("result");
        setOfflineNotice(true);
      }
    }
  }, []);

  useEffect(() => {
    if (!crop || !state) return;
    api.communityAlerts(state, crop).then((r) => setNearbyReports(r.reports)).catch(() => setNearbyReports([]));
  }, [crop, state]);

  async function runDiagnose(nextAnswers: Record<string, boolean>, nextAsked: string[]) {
    setError(null);
    setStage("loading");
    try {
      const res = await api.doctorDiagnose({
        crop, answers: nextAnswers, asked: nextAsked, image, state,
        plantLabel: plantLabel || undefined, optInCommunity,
      });
      if (res.status === "need_more_info") {
        setQuestion(res.question);
        setStage("asking");
      } else {
        setResult(res);
        setStage("result");
        cacheLastDiagnosis(crop, res);
      }
    } catch (e: any) {
      setError(e.message || "Something went wrong");
      setStage("setup");
    }
  }

  function handleStart() {
    setAnswers({});
    setAsked([]);
    setEscalateStatus(null);
    runDiagnose({}, []);
  }

  function handleAnswer(value: boolean) {
    if (!question) return;
    const nextAnswers = { ...answers, [question.id]: value };
    const nextAsked = [...asked, question.id];
    setAnswers(nextAnswers);
    setAsked(nextAsked);
    runDiagnose(nextAnswers, nextAsked);
  }

  function handleVoice() {
    if (!speechRecognitionSupported()) return;
    setListening(true);
    stopListenRef.current = listenForYesNo(lang, (value) => {
      setListening(false);
      if (value !== null) handleAnswer(value);
    });
  }

  function shareText(): string {
    if (!result) return "";
    if (result.status === "diagnosed") {
      return `AgroSentinel diagnosis for ${crop}: ${result.specific_name || result.cause_name} ` +
        `(confidence ${(result.confidence * 100).toFixed(0)}%).\nWhat to do: ${result.advice.join(" ")}`;
    }
    return `AgroSentinel: not confident on ${crop}'s issue. Top guesses: ` +
      `${result.top_candidates.map((c: any) => c.name).join(", ")}. Please consult a KVK officer.`;
  }

  async function submitFeedback(improved: boolean) {
    if (result?.diagnosis_id) {
      await api.doctorFeedback(result.diagnosis_id, improved, "");
      setResult({ ...result, _feedbackGiven: true });
    }
  }

  async function connectToExpert() {
    if (!result?.diagnosis_id) return;
    setEscalating(true);
    try {
      const res = await api.doctorEscalate(result.diagnosis_id);
      setEscalateStatus(res.sent ? "Sent to the expert helpline." : `Not sent: ${res.reason}`);
    } catch (e: any) {
      setEscalateStatus(`Not sent: ${e.message}`);
    } finally {
      setEscalating(false);
    }
  }

  return (
    <>
      <TopBar title={t("doctor.title")} />
      <main>
        {offlineNotice && <div className="card muted">{t("common.offline_cached")}</div>}
        {error && <div className="card" style={{ color: "var(--danger)" }}>{error}</div>}

        {stage === "setup" && (
          <div className="card stack">
            <div>
              <label>{t("doctor.pick_crop")}</label>
              <select value={crop} onChange={(e) => setCrop(e.target.value)}>
                {crops.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label>{t("farm.state")}</label>
              <select value={state} onChange={(e) => setState(e.target.value)}>
                {states.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <p className="hint" style={{ marginTop: -8 }}>Used for weather-aware diagnosis</p>
            </div>

            {nearbyReports.length > 0 && (
              <div className="card" style={{ background: "rgba(138,90,0,0.08)", margin: 0 }}>
                <p style={{ margin: 0, fontWeight: 600 }}>⚠️ Nearby farmers reported, last 14 days:</p>
                {nearbyReports.map((r: any) => (
                  <p key={r.cause_name} className="hint" style={{ margin: "4px 0 0" }}>
                    {r.cause_name} — {r.report_count} report{r.report_count > 1 ? "s" : ""} in {state}
                  </p>
                ))}
              </div>
            )}

            <div>
              <label>{t("doctor.upload_photo")}</label>
              <input
                type="file" accept="image/*" capture="environment"
                onChange={(e) => {
                  const f = e.target.files?.[0] || null;
                  setImage(f);
                  setImagePreview(f ? URL.createObjectURL(f) : null);
                }}
              />
              {imagePreview && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={imagePreview} alt="preview" style={{ width: "100%", borderRadius: 10, marginBottom: 12 }} />
              )}
            </div>
            <div>
              <label>Plant label (optional — track this plant&apos;s progress over weeks)</label>
              <input value={plantLabel} onChange={(e) => setPlantLabel(e.target.value)} placeholder="e.g. Tomato Plant A" />
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.85rem" }}>
              <input
                type="checkbox" checked={optInCommunity} onChange={(e) => setOptInCommunity(e.target.checked)}
                style={{ width: "auto", marginBottom: 0 }}
              />
              Share this diagnosis (crop + issue + state only) to alert nearby farmers
            </label>
            <button onClick={handleStart} type="button">{t("doctor.analyze")}</button>
            {plantLabel && (
              <Link href={`/doctor/progress?label=${encodeURIComponent(plantLabel)}`} className="btn-secondary btn" style={{ textAlign: "center" }}>
                View {plantLabel}&apos;s photo history
              </Link>
            )}
          </div>
        )}

        {stage === "loading" && (
          <div className="card center"><div className="spinner" /></div>
        )}

        {stage === "asking" && question && (
          <div className="card stack">
            <p className="muted" style={{ margin: 0 }}>{t("doctor.asking")}</p>
            <p style={{ fontSize: "1.1rem", fontWeight: 600 }}>{question.text}</p>
            <div className="btn-row">
              <button onClick={() => handleAnswer(true)} type="button">{t("common.yes")}</button>
              <button className="btn-secondary" onClick={() => handleAnswer(false)} type="button">{t("common.no")}</button>
            </div>
            {speechRecognitionSupported() && (
              <button className="btn-secondary" onClick={handleVoice} disabled={listening} type="button">
                🎤 {listening ? "..." : t("common.speak")}
              </button>
            )}
          </div>
        )}

        {stage === "result" && result && (
          <div className="stack">
            <div className="card">
              {result.status === "diagnosed" ? (
                <>
                  <p className="muted" style={{ margin: 0 }}>{t("doctor.diagnosed_title")}</p>
                  <h2 style={{ margin: "4px 0" }}>{result.specific_name || result.cause_name}</h2>
                  {result.specific_name && <p className="muted">{result.cause_name}</p>}
                  <span className={`badge badge-${result.confidence >= 0.6 ? "low" : "medium"}`}>
                    {t("doctor.confidence")}: {(result.confidence * 100).toFixed(0)}%
                  </span>
                  <hr className="divider" />
                  <p style={{ fontWeight: 600, marginBottom: 6 }}>{t("doctor.advice")}</p>
                  <ul style={{ paddingLeft: 18, margin: 0 }}>
                    {result.advice.map((a: string, i: number) => <li key={i} style={{ marginBottom: 6 }}>{a}</li>)}
                  </ul>
                  {result.escalate_if && (
                    <p className="hint" style={{ marginTop: 10 }}>⚠️ See a KVK officer if: {result.escalate_if}</p>
                  )}
                </>
              ) : (
                <>
                  <p className="muted" style={{ margin: 0 }}>{t("doctor.uncertain_title")}</p>
                  <p>{result.message}</p>
                  <p style={{ fontWeight: 600 }}>Top possibilities:</p>
                  <ul style={{ paddingLeft: 18 }}>
                    {result.top_candidates?.map((c: any) => (
                      <li key={c.cause_id}>{c.name} ({(c.probability * 100).toFixed(0)}%)</li>
                    ))}
                  </ul>
                </>
              )}
            </div>

            {result.diagnosis_id && (
              <div className="card no-print">
                <p className="muted" style={{ margin: "0 0 8px" }}>Connect to an expert</p>
                <button onClick={connectToExpert} disabled={escalating} type="button">
                  {escalating ? t("common.loading") : "📲 Send to KVK/expert via WhatsApp"}
                </button>
                {escalateStatus && <p className="hint" style={{ marginTop: 8 }}>{escalateStatus}</p>}
              </div>
            )}

            <div className="card no-print">
              <p className="muted" style={{ margin: "0 0 8px" }}>{t("doctor.feedback_prompt")}</p>
              {result._feedbackGiven ? (
                <p>{t("doctor.feedback_thanks")}</p>
              ) : (
                <div className="btn-row">
                  <button onClick={() => submitFeedback(true)} type="button">👍</button>
                  <button className="btn-secondary" onClick={() => submitFeedback(false)} type="button">👎</button>
                </div>
              )}
            </div>

            <div className="btn-row no-print">
              <button className="btn-secondary" onClick={() => shareOnWhatsApp(shareText())} type="button">
                {t("common.share_whatsapp")}
              </button>
              <button className="btn-secondary" onClick={printResult} type="button">
                {t("common.save_pdf")}
              </button>
            </div>
            <button className="btn-secondary no-print" onClick={() => { setStage("setup"); setResult(null); }} type="button">
              {t("doctor.title")}
            </button>
          </div>
        )}
      </main>
    </>
  );
}
