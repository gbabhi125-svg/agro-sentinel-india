"use client";

// Thin wrapper over the browser's Web Speech API for a single yes/no answer.
// Feature-detected: returns null if the browser doesn't support it, and the
// caller should hide the mic button in that case rather than show a dead button.
export function speechRecognitionSupported(): boolean {
  if (typeof window === "undefined") return false;
  return !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
}

const YES_WORDS = ["yes", "yeah", "haan", "han", "houdu", "ಹೌದು", "हाँ", "हां"];
const NO_WORDS = ["no", "nahi", "nahin", "illa", "ಇಲ್ಲ", "नहीं", "नही"];

export function listenForYesNo(lang: string, onResult: (value: boolean | null, transcript: string) => void) {
  const SpeechRecognitionCtor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SpeechRecognitionCtor) {
    onResult(null, "");
    return () => {};
  }
  const recognizer = new SpeechRecognitionCtor();
  recognizer.lang = lang === "hi" ? "hi-IN" : lang === "kn" ? "kn-IN" : "en-IN";
  recognizer.interimResults = false;
  recognizer.maxAlternatives = 3;

  recognizer.onresult = (event: any) => {
    const transcript = (event.results?.[0]?.[0]?.transcript || "").toLowerCase().trim();
    const isYes = YES_WORDS.some((w) => transcript.includes(w));
    const isNo = NO_WORDS.some((w) => transcript.includes(w));
    onResult(isYes && !isNo ? true : isNo && !isYes ? false : null, transcript);
  };
  recognizer.onerror = () => onResult(null, "");
  recognizer.start();
  return () => recognizer.stop();
}
