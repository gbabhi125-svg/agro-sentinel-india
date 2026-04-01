import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import { motion, AnimatePresence } from "framer-motion";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  RadialLinearScale, PointElement, LineElement, ArcElement,
  Filler, Title, Tooltip, Legend
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

ChartJS.register(
  CategoryScale, LinearScale, BarElement,
  RadialLinearScale, PointElement, LineElement, ArcElement,
  Filler, Title, Tooltip, Legend
);

// To your Railway URL:
const API = "https://agro-sentinel-india-production.up.railway.app";

// ── Global CSS ────────────────────────────────────────────────
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', sans-serif; overflow-x: hidden; transition: background 0.4s, color 0.4s; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #2d8a52; border-radius: 4px; }

  @keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position:  200% 0; }
  }
  @keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    33%       { transform: translateY(-12px) rotate(2deg); }
    66%       { transform: translateY(-6px) rotate(-2deg); }
  }
  @keyframes glow {
    0%, 100% { box-shadow: 0 0 20px rgba(45,138,82,0.3); }
    50%       { box-shadow: 0 0 40px rgba(45,138,82,0.7), 0 0 80px rgba(45,138,82,0.3); }
  }
  @keyframes pulse-ring {
    0%   { transform: scale(0.8); opacity: 1; }
    100% { transform: scale(2.0); opacity: 0; }
  }
  @keyframes rain {
    0%   { transform: translateY(-20px) rotate(15deg); opacity: 0; }
    10%  { opacity: 1; }
    90%  { opacity: 1; }
    100% { transform: translateY(110vh) rotate(15deg); opacity: 0; }
  }
  @keyframes counter {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes petalFall {
    0%   { transform: translateY(-20px) rotate(0deg) scale(0.5); opacity:0; }
    10%  { opacity: 1; }
    90%  { opacity: 0.8; }
    100% { transform: translateY(110vh) rotate(720deg) scale(1); opacity: 0; }
  }
  @keyframes bloomIn {
    0%   { transform: scale(0) rotate(-90deg); opacity:0; }
    60%  { transform: scale(1.15) rotate(5deg); opacity:1; }
    100% { transform: scale(1) rotate(0deg); opacity:1; }
  }
  @keyframes sunRotate {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  @keyframes soilPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139,90,43,0.4); }
    50%       { box-shadow: 0 0 0 12px rgba(139,90,43,0); }
  }
  @keyframes advisoryGlow {
    0%, 100% { border-color: rgba(34,197,94,0.3); }
    50%       { border-color: rgba(34,197,94,0.8); box-shadow: 0 0 20px rgba(34,197,94,0.2); }
  }

  .glass { backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%); }
  .glass-dark  { background: rgba(15,25,40,0.85) !important; border: 1px solid rgba(255,255,255,0.08) !important; }
  .glass-light { background: rgba(255,255,255,0.82) !important; border: 1px solid rgba(45,138,82,0.15) !important; }

  .shimmer-btn {
    background: linear-gradient(90deg,#1a5c34,#52b788,#2d8a52,#1a5c34);
    background-size: 300% 100%;
    animation: shimmer 3s linear infinite;
    border: none !important;
  }
  .shimmer-btn:disabled { animation: none; background: #6c757d !important; }

  .float-emoji { animation: float 4s ease-in-out infinite; }

  .result-card {
    transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.35s ease;
    border-radius: 20px !important;
  }
  .result-card:hover { transform: translateY(-6px) scale(1.01); box-shadow: 0 24px 60px rgba(0,0,0,0.2) !important; }

  .module-tab {
    transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1);
    cursor: pointer; border-radius: 50px !important; border: 2px solid transparent;
    padding: 8px 18px; font-size: 13px; font-weight: 600;
  }
  .module-tab:hover  { transform: translateY(-2px) scale(1.04); }
  .module-tab.active { border-color: #52b788 !important; background: rgba(82,183,136,0.15) !important; }

  .advisory-card { animation: advisoryGlow 4s ease-in-out infinite; }

  .flower-petal { animation: petalFall linear infinite; }
  .bloom        { animation: bloomIn 0.8s cubic-bezier(0.34,1.56,0.64,1) forwards; }
  .sun-rotate   { animation: sunRotate 12s linear infinite; }
  .soil-pulse   { animation: soilPulse 2s ease-in-out infinite; }

  select, input { transition: all 0.3s ease !important; }
  select:focus, input:focus { box-shadow: 0 0 0 3px rgba(82,183,136,0.3) !important; border-color: #52b788 !important; }

  .stat-number { animation: counter 0.8s ease forwards; font-variant-numeric: tabular-nums; }
  .season-bar { height: 8px; border-radius: 4px; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }

  .scheme-card { transition: all 0.3s ease; border-radius: 16px; }
  .scheme-card:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(0,0,0,0.15) !important; }

  .pest-item { transition: all 0.25s ease; }
  .pest-item:hover { transform: translateX(4px); }
`;

// ── Constants ─────────────────────────────────────────────────
const PARTICLES     = ["🌱","🌿","🍃","🌾","🌻","🍀","🌳","☘️","🌵","🍂","🌺","🌼"];
const FLOWER_PETALS = ["🌸","🌹","🌷","🌼","🌻","🌺","💮","🏵️"];
const SEASONS       = ["Kharif","Rabi","Whole Year","Autumn","Summer","Winter"];

const CROP_GRADIENTS = {
  "Rice":      ["#1a5c34","#52b788"],
  "Wheat":     ["#92400e","#f59e0b"],
  "Maize":     ["#78350f","#fbbf24"],
  "Cotton":    ["#1e3a5f","#60a5fa"],
  "Sugarcane": ["#14532d","#4ade80"],
  "Tomato":    ["#7f1d1d","#f87171"],
  "Potato":    ["#451a03","#d97706"],
  "Onion":     ["#4c1d95","#a78bfa"],
  "Coffee":    ["#1c1917","#78716c"],
  "Banana":    ["#713f12","#fde047"],
  "Mango":     ["#7c2d12","#fb923c"],
  "default":   ["#1a5c34","#52b788"],
};

const TRANSLATIONS = {
  en: {
    title:"AgroSentinel India", subtitle:"ML-Powered Farm Intelligence Platform",
    selectState:"Select State", selectCrop:"Select Crop",
    selectSeason:"Select Season", selectYear:"Year",
    rainfall:"Annual Rainfall (mm)", autoWeather:"🌤 Auto Weather",
    analyze:"🔍 Analyze Farm", analyzing:"⚙️ Analyzing...",
    yield:"Crop Yield", drought:"Drought Risk",
    failure:"Failure Risk", season:"Best Season",
    market:"Live Market Price", weather:"Live Weather",
    confidence:"Confidence", advice:"Advisory",
    grade:"Grade", perAcre:"Per Acre",
    history:"Analysis History", clearHistory:"Clear",
    downloadPDF:"📄 Download Report", retrain:"🔄 Retrain Models",
    darkMode:"🌙", lightMode:"☀️", tonnes:"tonnes/ha",
    noData:"Select state, crop and season to analyze",
    stats:"Platform Stats",
    aiAdvisory:"🤖 AI Advisory",
    soilHealth:"🌱 Soil Health Score",
    irrigation:"💧 Irrigation Calculator",
    pestRisk:"🐛 Pest & Disease Risk",
    priceForecast:"📈 Price Forecast",
    govtSchemes:"🏛️ Govt Schemes",
    areaHa:"Farm Area (Hectares)",
    calculate:"Calculate",
    analyzeModules:"Analyze Modules",
  },
  hi: {
    title:"एग्रोसेंटिनल इंडिया", subtitle:"ML-संचालित कृषि बुद्धिमत्ता मंच",
    selectState:"राज्य चुनें", selectCrop:"फसल चुनें",
    selectSeason:"मौसम चुनें", selectYear:"वर्ष",
    rainfall:"वार्षिक वर्षा (मिमी)", autoWeather:"🌤 मौसम",
    analyze:"🔍 विश्लेषण करें", analyzing:"⚙️ विश्लेषण...",
    yield:"फसल उपज", drought:"सूखा जोखिम",
    failure:"विफलता जोखिम", season:"सर्वश्रेष्ठ मौसम",
    market:"लाइव बाजार मूल्य", weather:"लाइव मौसम",
    confidence:"विश्वास", advice:"सलाह",
    grade:"ग्रेड", perAcre:"प्रति एकड़",
    history:"विश्लेषण इतिहास", clearHistory:"साफ करें",
    downloadPDF:"📄 रिपोर्ट", retrain:"🔄 पुनः प्रशिक्षण",
    darkMode:"🌙", lightMode:"☀️", tonnes:"टन/हेक्टेयर",
    noData:"राज्य, फसल और मौसम चुनें", stats:"आंकड़े",
    aiAdvisory:"🤖 AI सलाह", soilHealth:"🌱 मिट्टी स्वास्थ्य",
    irrigation:"💧 सिंचाई", pestRisk:"🐛 कीट जोखिम",
    priceForecast:"📈 मूल्य पूर्वानुमान", govtSchemes:"🏛️ सरकारी योजनाएं",
    areaHa:"खेत का क्षेत्रफल (हेक्टेयर)", calculate:"गणना करें",
    analyzeModules:"मॉड्यूल विश्लेषण",
  },
  ta: {
    title:"அக்ரோசெண்டினல் இந்தியா", subtitle:"ML-சக்தி வாய்ந்த விவசாய புலனாய்வு தளம்",
    selectState:"மாநிலம் தேர்வு", selectCrop:"பயிர் தேர்வு",
    selectSeason:"பருவம் தேர்வு", selectYear:"ஆண்டு",
    rainfall:"வருடாந்திர மழை (மிமீ)", autoWeather:"🌤 வானிலை",
    analyze:"🔍 பகுப்பாய்வு", analyzing:"⚙️ பகுப்பாய்கிறது...",
    yield:"பயிர் மகசூல்", drought:"வறட்சி அபாயம்",
    failure:"தோல்வி அபாயம்", season:"சிறந்த பருவம்",
    market:"நேரடி சந்தை விலை", weather:"நேரடி வானிலை",
    confidence:"நம்பிக்கை", advice:"ஆலோசனை",
    grade:"தரம்", perAcre:"ஏக்கருக்கு",
    history:"வரலாறு", clearHistory:"அழி",
    downloadPDF:"📄 அறிக்கை", retrain:"🔄 மீண்டும் பயிற்சி",
    darkMode:"🌙", lightMode:"☀️", tonnes:"டன்/ஹெக்டேர்",
    noData:"தேர்வு செய்யவும்", stats:"புள்ளிவிவரங்கள்",
    aiAdvisory:"🤖 AI ஆலோசனை", soilHealth:"🌱 மண் ஆரோக்கியம்",
    irrigation:"💧 நீர்ப்பாசனம்", pestRisk:"🐛 பூச்சி அபாயம்",
    priceForecast:"📈 விலை முன்னறிவிப்பு", govtSchemes:"🏛️ அரசு திட்டங்கள்",
    areaHa:"பண்ணை பரப்பளவு (ஹெக்டேர்)", calculate:"கணக்கிடு",
    analyzeModules:"தொகுதி பகுப்பாய்வு",
  },
  te: { title:"అగ్రోసెంటినల్ ఇండియా", subtitle:"ML-శక్తి వ్యవసాయ గూఢచారిత వేదిక", selectState:"రాష్ట్రం", selectCrop:"పంట", selectSeason:"సీజన్", selectYear:"సంవత్సరం", rainfall:"వర్షపాతం (మిమీ)", autoWeather:"🌤 వాతావరణం", analyze:"🔍 విశ్లేషించండి", analyzing:"⚙️ విశ్లేషిస్తోంది...", yield:"పంట దిగుబడి", drought:"కరువు", failure:"వైఫల్యం", season:"ఉత్తమ సీజన్", market:"మార్కెట్ ధర", weather:"వాతావరణం", confidence:"నమ్మకం", advice:"సలహా", grade:"గ్రేడ్", perAcre:"ఎకరాకు", history:"చరిత్ర", clearHistory:"తొలగించు", downloadPDF:"📄 నివేదిక", retrain:"🔄 రీట్రెయిన్", darkMode:"🌙", lightMode:"☀️", tonnes:"టన్నులు/హె.", noData:"ఎంచుకోండి", stats:"గణాంకాలు", aiAdvisory:"🤖 AI సలహా", soilHealth:"🌱 మట్టి ఆరోగ్యం", irrigation:"💧 నీటి పారుదల", pestRisk:"🐛 తెగులు ప్రమాదం", priceForecast:"📈 ధర అంచనా", govtSchemes:"🏛️ ప్రభుత్వ పథకాలు", areaHa:"వ్యవసాయ విస్తీర్ణం (హె.)", calculate:"లెక్కించండి", analyzeModules:"మాడ్యూల్ విశ్లేషణ" },
  kn: { title:"ಅಗ್ರೋಸೆಂಟಿನಲ್ ಇಂಡಿಯಾ", subtitle:"ML-ಚಾಲಿತ ಕೃಷಿ ಗುಪ್ತಚರ ವೇದಿಕೆ", selectState:"ರಾಜ್ಯ", selectCrop:"ಬೆಳೆ", selectSeason:"ಋತು", selectYear:"ವರ್ಷ", rainfall:"ಮಳೆ (ಮಿಮೀ)", autoWeather:"🌤 ಹವಾಮಾನ", analyze:"🔍 ವಿಶ್ಲೇಷಿಸಿ", analyzing:"⚙️ ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...", yield:"ಬೆಳೆ ಇಳುವರಿ", drought:"ಬರ", failure:"ವಿಫಲತೆ", season:"ಉತ್ತಮ ಋತು", market:"ಮಾರುಕಟ್ಟೆ ಬೆಲೆ", weather:"ಹವಾಮಾನ", confidence:"ವಿಶ್ವಾಸ", advice:"ಸಲಹೆ", grade:"ದರ್ಜೆ", perAcre:"ಎಕರೆಗೆ", history:"ಇತಿಹಾಸ", clearHistory:"ತೆರವು", downloadPDF:"📄 ವರದಿ", retrain:"🔄 ಮರು ತರಬೇತಿ", darkMode:"🌙", lightMode:"☀️", tonnes:"ಟನ್/ಹೆ.", noData:"ಆಯ್ಕೆ ಮಾಡಿ", stats:"ಅಂಕಿಅಂಶಗಳು", aiAdvisory:"🤖 AI ಸಲಹೆ", soilHealth:"🌱 ಮಣ್ಣು ಆರೋಗ್ಯ", irrigation:"💧 ನೀರಾವರಿ", pestRisk:"🐛 ಕೀಟ ಅಪಾಯ", priceForecast:"📈 ಬೆಲೆ ಮುನ್ಸೂಚನೆ", govtSchemes:"🏛️ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು", areaHa:"ಫಾರ್ಮ್ ಪ್ರದೇಶ (ಹೆ.)", calculate:"ಲೆಕ್ಕ ಹಾಕಿ", analyzeModules:"ಮಾಡ್ಯೂಲ್ ವಿಶ್ಲೇಷಣೆ" },
  ml: { title:"അഗ്രോസെന്റിനൽ ഇന്ത്യ", subtitle:"ML-ശക്തിയുള്ള കൃഷി ഗൂഢചര വേദി", selectState:"സംസ്ഥാനം", selectCrop:"വിള", selectSeason:"സീസൺ", selectYear:"വർഷം", rainfall:"മഴ (മിമി)", autoWeather:"🌤 കാലാവസ്ഥ", analyze:"🔍 വിശകലനം", analyzing:"⚙️ വിശകലനം...", yield:"വിള വിളവ്", drought:"വരൾച്ച", failure:"പരാജയം", season:"മികച്ച സീസൺ", market:"വിപണി വില", weather:"കാലാവസ്ഥ", confidence:"വിശ്വാസം", advice:"ഉപദേശം", grade:"ഗ്രേഡ്", perAcre:"ഏക്കറിന്", history:"ചരിത്രം", clearHistory:"മായ്ക്കുക", downloadPDF:"📄 റിപ്പോർട്ട്", retrain:"🔄 പുനഃപരിശീലനം", darkMode:"🌙", lightMode:"☀️", tonnes:"ടൺ/ഹെ.", noData:"തിരഞ്ഞെടുക്കുക", stats:"സ്ഥിതിവിവരക്കണക്കുകൾ", aiAdvisory:"🤖 AI ഉപദേശം", soilHealth:"🌱 മണ്ണ് ആരോഗ്യം", irrigation:"💧 ജലസേചനം", pestRisk:"🐛 കീട അപകടം", priceForecast:"📈 വില പ്രവചനം", govtSchemes:"🏛️ സർക്കാർ പദ്ധതികൾ", areaHa:"ഫാം വിസ്തൃതി (ഹെ.)", calculate:"കണക്കാക്കുക", analyzeModules:"മൊഡ്യൂൾ വിശകലനം" },
};

// ── Animated Counter ──────────────────────────────────────────
function AnimCounter({ value, decimals=0, suffix="" }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const end = parseFloat(value) || 0;
    if (end === 0) return;
    let start = 0, frame = 0;
    const steps = 60, inc = end / steps;
    const timer = setInterval(() => {
      frame++;
      start += inc;
      if (frame >= steps) { setDisplay(end); clearInterval(timer); }
      else setDisplay(start);
    }, 16);
    return () => clearInterval(timer);
  }, [value]);
  return <span className="stat-number">{display.toFixed(decimals)}{suffix}</span>;
}

// ── Floating Particles ────────────────────────────────────────
function FloatingParticles({ dark }) {
  const pts = React.useMemo(() =>
    Array.from({length:25}, (_,i) => ({
      id:i, emoji:PARTICLES[i%PARTICLES.length],
      x:Math.random()*100, dur:10+Math.random()*15,
      delay:Math.random()*12, size:14+Math.random()*18,
      opacity: dark ? 0.07 : 0.12,
    })), [dark]);
  return (
    <div style={{position:"fixed",inset:0,pointerEvents:"none",zIndex:0,overflow:"hidden"}}>
      {pts.map(p => (
        <motion.div key={p.id}
          style={{position:"absolute",left:`${p.x}%`,fontSize:p.size,opacity:p.opacity,filter:"blur(0.3px)"}}
          initial={{y:"110vh",rotate:0,scale:0.5}}
          animate={{y:"-10vh",rotate:[0,180,360],scale:[0.5,1,0.5]}}
          transition={{duration:p.dur,delay:p.delay,repeat:Infinity,ease:"linear"}}>
          {p.emoji}
        </motion.div>
      ))}
    </div>
  );
}

// ── Flower Animation Overlay ──────────────────────────────────
function FlowerAnimation({ show, dark }) {
  const petals = React.useMemo(() =>
    Array.from({length:35}, (_,i) => ({
      id:i,
      emoji: FLOWER_PETALS[i % FLOWER_PETALS.length],
      x: Math.random()*100,
      dur: 4+Math.random()*6,
      delay: Math.random()*5,
      size: 18+Math.random()*24,
    })), []);

  if (!show) return null;
  return (
    <div style={{position:"fixed",inset:0,pointerEvents:"none",zIndex:5,overflow:"hidden"}}>
      {petals.map(p => (
        <div key={p.id} className="flower-petal" style={{
          position:"absolute",
          left:`${p.x}%`,
          fontSize:p.size,
          animationDuration:`${p.dur}s`,
          animationDelay:`${p.delay}s`,
        }}>{p.emoji}</div>
      ))}
    </div>
  );
}

// ── Rain Effect ───────────────────────────────────────────────
function RainEffect() {
  const drops = Array.from({length:40},(_,i)=>i);
  return (
    <div style={{position:"fixed",inset:0,pointerEvents:"none",zIndex:0,overflow:"hidden"}}>
      {drops.map(i => (
        <div key={i} style={{
          position:"absolute", left:`${Math.random()*100}%`,
          width:2, height:`${20+Math.random()*30}px`,
          background:"linear-gradient(transparent,rgba(82,183,136,0.4))",
          animation:`rain ${0.8+Math.random()*1.2}s linear ${Math.random()*2}s infinite`,
          borderRadius:2,
        }}/>
      ))}
    </div>
  );
}

// ── Hero Header ───────────────────────────────────────────────
function HeroHeader({ dark, title, subtitle }) {
  return (
    <div style={{
      position:"relative", overflow:"hidden", borderRadius:28,
      background: dark
        ? "linear-gradient(135deg,#020c05,#0d2818,#1a4a2e,#0d3520)"
        : "linear-gradient(135deg,#052e16,#14532d,#166534,#15803d,#16a34a,#22c55e)",
      padding:"48px 24px 72px", marginBottom:28,
      boxShadow:"0 32px 80px rgba(34,197,94,0.25)",
    }}>
      {[...Array(6)].map((_,i) => (
        <motion.div key={i} style={{
          position:"absolute", borderRadius:"50%",
          background:`radial-gradient(circle,rgba(34,197,94,${0.06+i*0.02}),transparent)`,
          width: 120+i*80, height: 120+i*80, top: -40-i*20, right: -40-i*15, filter:"blur(1px)",
        }}
          animate={{rotate:360,scale:[1,1.08,1]}}
          transition={{duration:20+i*7,repeat:Infinity,ease:"linear"}}/>
      ))}
      <div style={{position:"absolute",inset:0,opacity:0.04,
        backgroundImage:`linear-gradient(rgba(255,255,255,0.5) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.5) 1px,transparent 1px)`,
        backgroundSize:"40px 40px"}}/>
      {[...Array(20)].map((_,i) => (
        <motion.div key={`s${i}`} style={{
          position:"absolute",left:`${5+Math.random()*90}%`,top:`${5+Math.random()*90}%`,
          width:2+Math.random()*3,height:2+Math.random()*3,borderRadius:"50%",
          background:"rgba(255,255,255,0.8)",}}
          animate={{opacity:[0,1,0],scale:[0,1,0]}}
          transition={{duration:1.5+Math.random()*3,delay:Math.random()*5,repeat:Infinity}}/>
      ))}
      <motion.div className="text-center" style={{position:"relative",zIndex:2}}
        initial={{opacity:0,y:-40,scale:0.9}} animate={{opacity:1,y:0,scale:1}}
        transition={{duration:1,ease:[0.34,1.56,0.64,1]}}>
        <motion.div className="float-emoji" style={{fontSize:64,lineHeight:1,filter:"drop-shadow(0 8px 24px rgba(0,0,0,0.4))"}}>
          🌾
        </motion.div>
        <motion.h1 style={{color:"#fff",fontWeight:900,fontSize:"clamp(24px,5vw,44px)",
          letterSpacing:"-1px",marginTop:12,textShadow:"0 4px 32px rgba(0,0,0,0.5)"}}>
          {title}
        </motion.h1>
        <motion.p style={{color:"rgba(255,255,255,0.82)",fontSize:16,marginTop:6,fontWeight:400}}
          initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.6}}>
          {subtitle}
        </motion.p>
        <motion.div className="d-flex flex-wrap justify-content-center gap-2 mt-4"
          initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.9}}>
          {["🤖 4 ML Models","📊 236K Records","🌍 33 States","🌾 105 Crops",
            "📡 Live Prices","🌤 Live Weather","💧 Irrigation AI","🐛 Pest Risk",
            "📈 Price Forecast","🏛️ Govt Schemes"].map((tag,i) => (
            <motion.span key={i} style={{
              background:"rgba(255,255,255,0.12)",backdropFilter:"blur(10px)",
              border:"1px solid rgba(255,255,255,0.2)",color:"#fff",
              padding:"5px 14px",borderRadius:50,fontSize:12,fontWeight:500,}}
              whileHover={{background:"rgba(255,255,255,0.22)",scale:1.05}}
              initial={{opacity:0,y:10}} animate={{opacity:1,y:0}}
              transition={{delay:0.9+i*0.06}}>
              {tag}
            </motion.span>
          ))}
        </motion.div>
      </motion.div>
      <div style={{position:"absolute",bottom:-2,left:0,right:0}}>
        <svg viewBox="0 0 1440 80" style={{display:"block",width:"100%"}}>
          <motion.path
            d="M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z"
            fill={dark?"#0a0f1a":"#f0fdf4"}
            animate={{d:["M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z","M0,25 C240,65 480,5 720,30 C960,60 1200,10 1440,25 L1440,80 L0,80 Z","M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z"]}}
            transition={{duration:6,repeat:Infinity,ease:"easeInOut"}}/>
        </svg>
      </div>
    </div>
  );
}

// ── Result Card ───────────────────────────────────────────────
function ResultCard({ title, value, sub, badge, color, icon, dark, delay=0, children }) {
  const colorMap = {
    success: dark?"rgba(20,83,45,0.9)":"rgba(240,253,244,0.95)",
    info:    dark?"rgba(12,74,110,0.9)":"rgba(240,249,255,0.95)",
    warning: dark?"rgba(120,53,15,0.9)":"rgba(255,251,235,0.95)",
    danger:  dark?"rgba(127,29,29,0.9)":"rgba(255,241,242,0.95)",
  };
  const borderMap = { success:"rgba(34,197,94,0.4)",info:"rgba(59,130,246,0.4)",warning:"rgba(245,158,11,0.4)",danger:"rgba(239,68,68,0.4)" };
  const textMap   = { success:"#16a34a",info:"#2563eb",warning:"#d97706",danger:"#dc2626" };

  return (
    <motion.div className="result-card glass h-100"
      style={{ background: colorMap[color]||colorMap.success, border:`1px solid ${borderMap[color]||borderMap.success}`, padding:24, position:"relative", overflow:"hidden" }}
      initial={{opacity:0,y:40,scale:0.9}} animate={{opacity:1,y:0,scale:1}}
      transition={{duration:0.6,delay,ease:[0.34,1.56,0.64,1]}}>
      <div style={{position:"absolute",right:-10,bottom:-10,fontSize:80,opacity:0.06,lineHeight:1,transform:"rotate(-15deg)"}}>{icon}</div>
      <div style={{color:textMap[color],fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:"1.5px",marginBottom:8}}>{title}</div>
      {value && <div style={{fontSize:36,fontWeight:900,color:dark?"#e2e8f0":"#1a2e1a",lineHeight:1,marginBottom:6}}>{value}</div>}
      {sub && <div style={{fontSize:13,color:dark?"#94a3b8":"#6b7280",fontWeight:400,marginBottom:8}}>{sub}</div>}
      {badge && (
        <motion.span style={{display:"inline-block",background:textMap[color],color:"#fff",padding:"4px 14px",borderRadius:50,fontSize:12,fontWeight:700}}
          initial={{scale:0,rotate:-180}} animate={{scale:1,rotate:0}}
          transition={{delay:delay+0.3,type:"spring",bounce:0.6}}>
          {badge}
        </motion.span>
      )}
      {children}
    </motion.div>
  );
}

// ── Soil Health Card ──────────────────────────────────────────
function SoilHealthCard({ soil, dark }) {
  if (!soil) return null;
  const scoreColor = soil.score >= 80 ? "#16a34a" : soil.score >= 65 ? "#ca8a04" : soil.score >= 50 ? "#ea580c" : "#dc2626";
  const bg = dark ? "rgba(120,53,15,0.6)" : "rgba(254,243,199,0.95)";

  return (
    <motion.div className="glass result-card" style={{
      background:bg, border:"1px solid rgba(139,90,43,0.3)",
      borderRadius:20, padding:24, position:"relative", overflow:"hidden",
    }}
      initial={{opacity:0,y:30,scale:0.95}} animate={{opacity:1,y:0,scale:1}}
      transition={{duration:0.6,delay:0.3,ease:[0.34,1.56,0.64,1]}}>

      {/* Animated soil orb */}
      <div style={{position:"absolute",right:-20,bottom:-20,width:120,height:120,
        borderRadius:"50%",background:"radial-gradient(circle,rgba(139,90,43,0.15),transparent)",
        animation:"soilPulse 2s ease-in-out infinite"}}/>

      <div style={{fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:"1.5px",color:"#92400e",marginBottom:12}}>
        🌱 Soil Health Score
      </div>

      <div style={{display:"flex",alignItems:"center",gap:16}}>
        {/* Circular score */}
        <div style={{position:"relative",width:90,height:90}}>
          <svg viewBox="0 0 90 90" style={{transform:"rotate(-90deg)",width:90,height:90}}>
            <circle cx="45" cy="45" r="38" fill="none" stroke={dark?"rgba(255,255,255,0.1)":"rgba(139,90,43,0.15)"} strokeWidth="8"/>
            <motion.circle cx="45" cy="45" r="38" fill="none" stroke={scoreColor} strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${2*Math.PI*38}`}
              initial={{strokeDashoffset: 2*Math.PI*38}}
              animate={{strokeDashoffset: 2*Math.PI*38*(1-soil.score/100)}}
              transition={{duration:1.5,ease:"easeOut",delay:0.5}}/>
          </svg>
          <div style={{position:"absolute",inset:0,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center"}}>
            <div style={{fontSize:22,fontWeight:900,color:scoreColor,lineHeight:1}}>
              <AnimCounter value={soil.score}/>
            </div>
            <div style={{fontSize:9,color:dark?"#94a3b8":"#6b7280"}}>/ 100</div>
          </div>
        </div>

        <div style={{flex:1}}>
          <div style={{fontSize:18,fontWeight:800,color:dark?"#fbbf24":"#92400e",marginBottom:4}}>
            {soil.grade}
          </div>
          <div style={{fontSize:12,color:dark?"#94a3b8":"#78716c",lineHeight:1.5}}>
            {soil.detail}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{marginTop:12,height:6,background:dark?"rgba(255,255,255,0.1)":"rgba(139,90,43,0.15)",borderRadius:3,overflow:"hidden"}}>
        <motion.div style={{height:"100%",borderRadius:3,background:`linear-gradient(90deg,${scoreColor},${scoreColor}aa)`}}
          initial={{width:0}} animate={{width:`${soil.score}%`}}
          transition={{duration:1.5,ease:"easeOut",delay:0.5}}/>
      </div>
    </motion.div>
  );
}

// ── AI Advisory Card ──────────────────────────────────────────
function AIAdvisoryCard({ advisory, dark }) {
  if (!advisory) return null;
  const sections = [
    { key:"why",    icon:"📊", title:"Why This Result?",     color:"#2563eb", bg: dark?"rgba(30,58,138,0.4)":"rgba(239,246,255,0.95)" },
    { key:"improve",icon:"💡", title:"What To Improve",      color:"#d97706", bg: dark?"rgba(120,53,15,0.4)":"rgba(255,251,235,0.95)" },
    { key:"future", icon:"🔮", title:"Future Outlook",        color:"#7c3aed", bg: dark?"rgba(88,28,135,0.4)":"rgba(245,243,255,0.95)" },
  ];

  return (
    <motion.div className="glass advisory-card" style={{
      background: dark?"rgba(15,25,35,0.9)":"rgba(255,255,255,0.95)",
      border:"1px solid rgba(34,197,94,0.3)",
      borderRadius:20, padding:24, marginBottom:20,
    }}
      initial={{opacity:0,y:30}} animate={{opacity:1,y:0}}
      transition={{duration:0.6,delay:0.4}}>

      <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:16}}>
        <motion.div style={{fontSize:28,filter:"drop-shadow(0 4px 8px rgba(0,0,0,0.2))"}}
          animate={{rotate:[0,5,-5,0]}} transition={{duration:3,repeat:Infinity}}>
          🤖
        </motion.div>
        <div>
          <div style={{fontSize:16,fontWeight:800,color:dark?"#e2e8f0":"#1a2e1a"}}>AI Advisory Intelligence</div>
          <div style={{fontSize:12,color:dark?"#94a3b8":"#6b7280"}}>Powered by AgroSentinel ML Engine</div>
        </div>
        <motion.div style={{marginLeft:"auto",padding:"4px 14px",borderRadius:50,
          background:"rgba(34,197,94,0.15)",color:"#16a34a",fontSize:11,fontWeight:700}}
          animate={{opacity:[1,0.5,1]}} transition={{duration:2,repeat:Infinity}}>
          🟢 LIVE
        </motion.div>
      </div>

      <div className="row g-3">
        {sections.map(({key,icon,title,color,bg},i) => (
          advisory[key] && (
            <div className="col-12" key={key}>
              <motion.div style={{background:bg,borderRadius:14,padding:"14px 16px",
                border:`1px solid ${color}33`}}
                initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}}
                transition={{delay:0.5+i*0.15}}>
                <div style={{fontSize:12,fontWeight:700,color,textTransform:"uppercase",
                  letterSpacing:"1px",marginBottom:6}}>
                  {icon} {title}
                </div>
                <div style={{fontSize:13,color:dark?"#cbd5e1":"#374151",lineHeight:1.65,
                  whiteSpace:"pre-wrap"}}>
                  {/* Strip markdown bold markers for clean display */}
                  {advisory[key].replace(/\*\*(.*?)\*\*/g,"$1").replace(/^[📊💡🔮]\s+\*\*[^*]+\*\*\s+/,"")}
                </div>
              </motion.div>
            </div>
          )
        ))}
      </div>
    </motion.div>
  );
}

// ── Irrigation Module ─────────────────────────────────────────
function IrrigationModule({ form, dark, dm }) {
  const [area, setArea] = useState("1");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const calculate = async () => {
    if (!form.crop || !form.state) return;
    setLoading(true);
    try {
      const r = await axios.post(`${API}/api/irrigation`, {
        crop: form.crop, season: form.season, state: form.state,
        area_ha: parseFloat(area)||1, rainfall: parseFloat(form.rainfall)||1000,
      });
      setResult(r.data);
    } catch(e) { console.error(e); }
    setLoading(false);
  };

  const inputStyle = { backgroundColor:dm.input, color:dm.inputTx, border:`1px solid ${dm.border}`,
    borderRadius:10, padding:"8px 12px", width:"100%", fontSize:13, outline:"none" };

  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.4}}>
      <div className="row g-2 mb-3">
        <div className="col-8">
          <label style={{fontSize:11,fontWeight:700,color:dm.muted,textTransform:"uppercase",letterSpacing:"1px",marginBottom:4,display:"block"}}>
            🌾 Farm Area (Hectares)
          </label>
          <input type="number" style={inputStyle} value={area} min="0.1" step="0.1"
            onChange={e=>setArea(e.target.value)} placeholder="e.g. 1.5"/>
        </div>
        <div className="col-4 d-flex align-items-end">
          <button onClick={calculate} disabled={loading||!form.crop}
            style={{width:"100%",padding:"9px",borderRadius:10,border:"none",
              background:"linear-gradient(135deg,#0369a1,#0ea5e9)",
              color:"#fff",fontWeight:700,fontSize:13,cursor:"pointer",opacity:form.crop?1:0.5}}>
            {loading?"⏳":"💧"} Calculate
          </button>
        </div>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div initial={{opacity:0,height:0}} animate={{opacity:1,height:"auto"}} exit={{opacity:0,height:0}}>
            {/* Main stat */}
            <div style={{background:dark?"rgba(14,165,233,0.15)":"rgba(224,242,254,0.8)",
              borderRadius:14,padding:16,border:"1px solid rgba(14,165,233,0.3)",marginBottom:12}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:8}}>
                <div>
                  <div style={{fontSize:11,fontWeight:700,color:"#0369a1",textTransform:"uppercase",marginBottom:4}}>
                    Irrigation Required
                  </div>
                  <div style={{fontSize:36,fontWeight:900,color:dark?"#7dd3fc":"#0c4a6e",lineHeight:1}}>
                    <AnimCounter value={result.irrigation_required_mm}/><span style={{fontSize:16,fontWeight:500}}>mm</span>
                  </div>
                  <div style={{fontSize:12,color:dm.muted,marginTop:2}}>
                    {result.volume_m3.toLocaleString()} m³ total · ₹{result.estimated_cost_inr.toLocaleString()} estimated
                  </div>
                </div>
                <div style={{textAlign:"right"}}>
                  <div style={{fontSize:24}}>{result.method_emoji}</div>
                  <div style={{fontSize:12,fontWeight:700,color:dark?"#e2e8f0":"#1a2e1a",maxWidth:180,marginTop:4}}>
                    {result.recommended_method}
                  </div>
                </div>
              </div>
              <div style={{marginTop:12,fontSize:12,color:dark?"#94a3b8":"#6b7280",
                background:dark?"rgba(255,255,255,0.05)":"rgba(0,0,0,0.04)",
                borderRadius:8,padding:"8px 12px"}}>
                📋 {result.efficiency_note}
              </div>
            </div>

            {/* Schedule */}
            <div style={{background:dark?"rgba(20,83,45,0.3)":"rgba(240,253,244,0.8)",
              borderRadius:12,padding:14,border:"1px solid rgba(34,197,94,0.25)"}}>
              <div style={{fontSize:11,fontWeight:700,color:"#16a34a",marginBottom:8}}>
                📅 Irrigation Schedule
              </div>
              <div style={{display:"flex",gap:12,flexWrap:"wrap",fontSize:12,color:dm.muted}}>
                <span>🌅 Morning: <strong style={{color:dm.text}}>{result.schedule.morning}</strong></span>
                <span>🌇 Evening: <strong style={{color:dm.text}}>{result.schedule.evening}</strong></span>
                <span>📆 Frequency: <strong style={{color:dm.text}}>{result.schedule.frequency}</strong></span>
                <span>💧 Daily total: <strong style={{color:dm.text}}>{result.daily_mm}mm</strong></span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Pest Risk Module ──────────────────────────────────────────
function PestRiskModule({ form, weatherData, dark, dm }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    if (!form.crop) return;
    setLoading(true);
    try {
      const r = await axios.post(`${API}/api/pest-risk`, {
        crop: form.crop, season: form.season, state: form.state,
        temperature: weatherData?.temperature||28,
        humidity: weatherData?.humidity||65,
        rainfall: parseFloat(form.rainfall)||1000,
      });
      setResult(r.data);
    } catch(e) { console.error(e); }
    setLoading(false);
  };

  const colorMap = { High:"#dc2626", Medium:"#d97706", Low:"#16a34a" };
  const bgMap    = { High: dark?"rgba(127,29,29,0.3)":"rgba(255,241,242,0.9)", Medium: dark?"rgba(120,53,15,0.3)":"rgba(255,251,235,0.9)", Low: dark?"rgba(20,83,45,0.3)":"rgba(240,253,244,0.9)" };

  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}}>
      <button onClick={analyze} disabled={loading||!form.crop}
        style={{width:"100%",padding:"10px",borderRadius:10,border:"none",
          background:"linear-gradient(135deg,#dc2626,#ef4444)",
          color:"#fff",fontWeight:700,fontSize:13,cursor:"pointer",
          marginBottom:16,opacity:form.crop?1:0.5}}>
        {loading?"⏳ Analyzing...":"🐛 Analyze Pest & Disease Risk"}
      </button>

      <AnimatePresence>
        {result && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}}>
            {/* Overall risk */}
            <div style={{background:bgMap[result.overall_risk_level],borderRadius:14,
              padding:14,border:`1px solid ${colorMap[result.overall_risk_level]}44`,marginBottom:14}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <div>
                  <div style={{fontSize:11,fontWeight:700,color:colorMap[result.overall_risk_level],
                    textTransform:"uppercase",marginBottom:4}}>Overall Risk</div>
                  <div style={{fontSize:32,fontWeight:900,color:colorMap[result.overall_risk_level]}}>
                    {result.overall_risk_level}
                  </div>
                </div>
                <div style={{fontSize:42,fontWeight:900,color:colorMap[result.overall_risk_level]}}>
                  <AnimCounter value={result.overall_risk_score} decimals={0} suffix="%"/>
                </div>
              </div>
            </div>

            {/* Pests */}
            <div style={{marginBottom:12}}>
              <div style={{fontSize:12,fontWeight:700,color:dm.muted,marginBottom:8}}>🐛 Pest Risks</div>
              {result.pests.map((p,i)=>(
                <motion.div key={i} className="pest-item" style={{
                  display:"flex",justifyContent:"space-between",alignItems:"center",
                  padding:"8px 12px",borderRadius:10,marginBottom:6,
                  background:dark?"rgba(255,255,255,0.05)":"rgba(0,0,0,0.03)",
                  border:`1px solid ${colorMap[p.risk_level]}22`}}
                  initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}} transition={{delay:i*0.05}}>
                  <span style={{fontSize:13,color:dm.text,fontWeight:500}}>{p.name}</span>
                  <span style={{fontSize:11,fontWeight:700,color:colorMap[p.risk_level],
                    background:`${colorMap[p.risk_level]}18`,padding:"3px 10px",borderRadius:50}}>
                    {p.risk_level} ({p.risk_score}%)
                  </span>
                </motion.div>
              ))}
            </div>

            {/* Diseases */}
            <div style={{marginBottom:12}}>
              <div style={{fontSize:12,fontWeight:700,color:dm.muted,marginBottom:8}}>🦠 Disease Risks</div>
              {result.diseases.map((d,i)=>(
                <motion.div key={i} className="pest-item" style={{
                  display:"flex",justifyContent:"space-between",alignItems:"center",
                  padding:"8px 12px",borderRadius:10,marginBottom:6,
                  background:dark?"rgba(255,255,255,0.05)":"rgba(0,0,0,0.03)",
                  border:`1px solid ${colorMap[d.risk_level]}22`}}
                  initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}} transition={{delay:0.2+i*0.05}}>
                  <span style={{fontSize:13,color:dm.text,fontWeight:500}}>{d.name}</span>
                  <span style={{fontSize:11,fontWeight:700,color:colorMap[d.risk_level],
                    background:`${colorMap[d.risk_level]}18`,padding:"3px 10px",borderRadius:50}}>
                    {d.risk_level} ({d.risk_score}%)
                  </span>
                </motion.div>
              ))}
            </div>

            {/* Prevention */}
            <div style={{background:dark?"rgba(14,165,233,0.1)":"rgba(224,242,254,0.8)",
              borderRadius:12,padding:14,border:"1px solid rgba(14,165,233,0.25)"}}>
              <div style={{fontSize:11,fontWeight:700,color:"#0369a1",marginBottom:8}}>
                🛡️ Prevention Measures
              </div>
              {result.prevention_measures.map((m,i)=>(
                <div key={i} style={{fontSize:12,color:dm.text,marginBottom:5,display:"flex",gap:8}}>
                  <span>✓</span><span>{m}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Price Forecast Module ─────────────────────────────────────
function PriceForecastModule({ form, dark, dm }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetch = async () => {
    if (!form.crop) return;
    setLoading(true);
    try {
      const r = await axios.get(`${API}/api/price-forecast/${form.crop.toLowerCase()}`);
      setResult(r.data);
    } catch(e) { console.error(e); }
    setLoading(false);
  };

  const chartData = result ? {
    labels: result.forecast.map(m => m.month),
    datasets:[{
      label:"Forecast Price (₹/quintal)",
      data: result.forecast.map(m => m.price),
      borderColor:"#f59e0b",
      backgroundColor:"rgba(245,158,11,0.15)",
      borderWidth:3, pointRadius:6,
      pointBackgroundColor:"#f59e0b",
      tension:0.4, fill:true,
    }]
  } : null;

  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}}>
      <button onClick={fetch} disabled={loading||!form.crop}
        style={{width:"100%",padding:"10px",borderRadius:10,border:"none",
          background:"linear-gradient(135deg,#92400e,#f59e0b)",
          color:"#fff",fontWeight:700,fontSize:13,cursor:"pointer",
          marginBottom:16,opacity:form.crop?1:0.5}}>
        {loading?"⏳ Fetching...":"📈 Generate 3-Month Price Forecast"}
      </button>

      <AnimatePresence>
        {result && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}}>
            {/* Summary */}
            <div style={{background:dark?"rgba(120,53,15,0.4)":"rgba(255,251,235,0.9)",
              borderRadius:14,padding:14,border:"1px solid rgba(245,158,11,0.3)",marginBottom:14}}>
              <div style={{fontSize:11,fontWeight:700,color:"#d97706",textTransform:"uppercase",marginBottom:6}}>
                💰 Current Price
              </div>
              <div style={{fontSize:32,fontWeight:900,color:dark?"#fbbf24":"#92400e"}}>
                ₹<AnimCounter value={result.current_price}/>
                <span style={{fontSize:13,fontWeight:400,color:dm.muted}}> /quintal</span>
              </div>
              <div style={{fontSize:12,color:dm.muted,marginTop:6}}>
                📊 {result.summary}
              </div>
            </div>

            {/* Chart */}
            {chartData && (
              <div style={{marginBottom:14}}>
                <Line data={chartData} options={{
                  responsive:true,
                  plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`₹${c.raw}/quintal`}}},
                  scales:{
                    y:{ticks:{color:dm.muted,callback:v=>`₹${v}`},grid:{color:dark?"rgba(255,255,255,0.05)":"rgba(0,0,0,0.05)"}},
                    x:{ticks:{color:dm.muted},grid:{display:false}},
                  }
                }}/>
              </div>
            )}

            {/* Monthly cards */}
            <div className="row g-2">
              {result.forecast.map((m,i) => (
                <div className="col-4" key={i}>
                  <motion.div style={{
                    background:dark?"rgba(255,255,255,0.05)":"rgba(255,255,255,0.9)",
                    borderRadius:12,padding:"10px 12px",textAlign:"center",
                    border:`1px solid ${m.change_pct>0?"rgba(34,197,94,0.3)":"rgba(239,68,68,0.3)"}`}}
                    initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{delay:0.1*i}}>
                    <div style={{fontSize:12,fontWeight:700,color:dm.muted}}>{m.month}</div>
                    <div style={{fontSize:20,fontWeight:900,color:dark?"#fbbf24":"#92400e"}}>
                      ₹{m.price.toLocaleString()}
                    </div>
                    <div style={{fontSize:10,color:m.change_pct>=0?"#16a34a":"#dc2626",fontWeight:600}}>
                      {m.change_pct>=0?"+":""}{m.change_pct}%
                    </div>
                    <div style={{fontSize:10,color:dm.muted,marginTop:4}}>{m.recommendation}</div>
                  </motion.div>
                </div>
              ))}
            </div>

            <div style={{fontSize:10,color:dm.muted,marginTop:10,fontStyle:"italic"}}>
              ⚠️ {result.disclaimer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Govt Schemes Module ───────────────────────────────────────
function GovtSchemesModule({ form, results, dark, dm }) {
  const [schemes, setSchemes] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetch = async () => {
    if (!form.crop) return;
    setLoading(true);
    try {
      const r = await axios.post(`${API}/api/schemes`, {
        crop: form.crop, state: form.state,
        drought_risk: results?.drought?.risk||"Low",
        yield_grade: results?.yield?.grade||"Good",
        area_ha: 1,
      });
      setSchemes(r.data);
    } catch(e) { console.error(e); }
    setLoading(false);
  };

  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}}>
      <button onClick={fetch} disabled={loading||!form.crop}
        style={{width:"100%",padding:"10px",borderRadius:10,border:"none",
          background:"linear-gradient(135deg,#1e3a5f,#3b82f6)",
          color:"#fff",fontWeight:700,fontSize:13,cursor:"pointer",
          marginBottom:16,opacity:form.crop?1:0.5}}>
        {loading?"⏳ Loading...":"🏛️ Find Applicable Government Schemes"}
      </button>

      <AnimatePresence>
        {schemes && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}}>
            <div style={{fontSize:12,color:dm.muted,marginBottom:12}}>
              ✅ {schemes.message}
            </div>
            {schemes.schemes.map((s,i) => (
              <motion.div key={s.id} className="scheme-card" style={{
                background: dark?"rgba(15,25,40,0.8)":"rgba(255,255,255,0.95)",
                border:`1px solid ${dm.border}`,padding:"14px 16px",marginBottom:10,
                position:"relative",overflow:"hidden",
              }}
                initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{delay:i*0.06}}>

                {/* Relevance badge */}
                <div style={{position:"absolute",top:10,right:12,
                  background:s.relevance_score>=80?"rgba(34,197,94,0.15)":"rgba(245,158,11,0.15)",
                  color:s.relevance_score>=80?"#16a34a":"#d97706",
                  fontSize:10,fontWeight:700,padding:"2px 10px",borderRadius:50}}>
                  {s.relevance_score}% match
                </div>

                <div style={{display:"flex",gap:12,alignItems:"flex-start"}}>
                  <div style={{fontSize:28,lineHeight:1}}>{s.emoji}</div>
                  <div style={{flex:1}}>
                    <div style={{fontSize:14,fontWeight:800,color:dark?"#e2e8f0":"#1a2e1a",marginBottom:2}}>
                      {s.id}
                    </div>
                    <div style={{fontSize:11,color:dm.muted,marginBottom:6}}>{s.full_name}</div>
                    <div style={{fontSize:12,color:dark?"#86efac":"#166534",fontWeight:600,marginBottom:4}}>
                      💰 {s.benefit}
                    </div>
                    <div style={{fontSize:11,color:dm.muted}}>
                      ✅ {s.eligibility}
                    </div>
                    <a href={s.link} target="_blank" rel="noopener noreferrer"
                      style={{display:"inline-block",marginTop:8,fontSize:11,
                        color:"#2563eb",fontWeight:600,textDecoration:"none"}}>
                      🔗 Apply / Learn More →
                    </a>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Main App ──────────────────────────────────────────────────
export default function App() {
  const [lang,          setLang]          = useState("en");
  const [dark,          setDark]          = useState(false);
  const [crops,         setCrops]         = useState([]);
  const [states,        setStates]        = useState([]);
  const [platformStats, setPlatformStats] = useState(null);
  const [form,          setForm]          = useState({
    state:"", crop:"", season:"Kharif",
    year: new Date().getFullYear(), rainfall:""
  });
  const [results,       setResults]       = useState(null);
  const [market,        setMarket]        = useState(null);
  const [weatherData,   setWeatherData]   = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [weatherLoad,   setWeatherLoad]   = useState(false);
  const [error,         setError]         = useState("");
  const [history,       setHistory]       = useState([]);
  const [retStatus,     setRetStatus]     = useState("idle");
  const [retMsg,        setRetMsg]        = useState("");
  const [showRain,      setShowRain]      = useState(false);
  const [showFlowers,   setShowFlowers]   = useState(false);
  const [activeModule,  setActiveModule]  = useState(null);
  const resultsRef = useRef(null);
  const t = TRANSLATIONS[lang];

  useEffect(() => {
    const el = document.getElementById("agro-css") || document.createElement("style");
    el.id = "agro-css"; el.textContent = GLOBAL_CSS;
    document.head.appendChild(el);
  }, []);

  useEffect(() => {
    document.body.style.background = dark ? "linear-gradient(135deg,#020c05,#0a0f1a)" : "#f0fdf4";
    document.body.style.color = dark ? "#e2e8f0" : "#1a2e1a";
    document.body.style.minHeight = "100vh";
  }, [dark]);

  useEffect(() => {
    axios.get(`${API}/api/crops`).then(r=>setCrops(r.data.crops)).catch(()=>{});
    axios.get(`${API}/api/states`).then(r=>setStates(r.data.states)).catch(()=>{});
    axios.get(`${API}/api/stats`).then(r=>setPlatformStats(r.data)).catch(()=>{});
  }, []);

  const dm = {
    card:    dark?"rgba(15,25,35,0.92)":"rgba(255,255,255,0.92)",
    text:    dark?"#e2e8f0":"#1a2e1a",
    muted:   dark?"#94a3b8":"#4a6741",
    border:  dark?"rgba(255,255,255,0.08)":"rgba(34,197,94,0.15)",
    input:   dark?"#0d1f12":"#f0fdf4",
    inputTx: dark?"#e2e8f0":"#1a2e1a",
  };

  const fetchWeather = async () => {
    if(!form.state) return;
    setWeatherLoad(true);
    try {
      const r = await axios.get(`${API}/api/weather/${form.state}`);
      const w = r.data;
      setWeatherData(w);
      setForm(p=>({...p, rainfall: Math.round(w.precipitation > 0 ? w.precipitation*365 : 1000)}));
      if(w.precipitation > 5) { setShowRain(true); setTimeout(()=>setShowRain(false), 5000); }
    } catch{}
    setWeatherLoad(false);
  };

  const analyze = async () => {
    if(!form.state||!form.crop||!form.season) {
      setError("Please select State, Crop and Season"); return;
    }
    setError(""); setLoading(true); setResults(null); setMarket(null);
    try {
      const payload = {
        state: form.state, crop: form.crop, season: form.season,
        year: form.year, rainfall: parseFloat(form.rainfall)||1000,
      };
      const [res, mkt] = await Promise.all([
        axios.post(`${API}/api/predict-all`, payload),
        axios.get(`${API}/api/market-price/${form.crop.toLowerCase()}`),
      ]);
      setResults(res.data);
      setMarket(mkt.data);

      // Show flowers if excellent yield
      if (res.data.yield?.grade === "Excellent") {
        setShowFlowers(true);
        setTimeout(()=>setShowFlowers(false), 8000);
      }

      setHistory(prev=>[{
        time: new Date().toLocaleTimeString(),
        state:form.state, crop:form.crop, season:form.season, year:form.year,
        yield: res.data.yield?.value, drought: res.data.drought?.risk,
        failure: res.data.failure?.risk, season_best: res.data.season?.best,
      },...prev].slice(0,10));

      setTimeout(()=>resultsRef.current?.scrollIntoView({behavior:"smooth",block:"start"}),300);
    } catch(e) {
      setError(e.response?.data?.error || "Cannot connect to Flask API. Make sure backend is running on port 5000.");
    }
    setLoading(false);
  };

  const startRetrain = async () => {
    setRetStatus("running"); setRetMsg("");
    try {
      await axios.post(`${API}/api/retrain`);
      const poll = setInterval(async()=>{
        try {
          const r = await axios.get(`${API}/api/retrain-status`);
          if(r.data.status==="success") { setRetStatus("success"); setRetMsg(r.data.message); clearInterval(poll); }
          else if(r.data.status==="error") { setRetStatus("error"); setRetMsg(r.data.message); clearInterval(poll); }
        } catch{ clearInterval(poll); }
      }, 3000);
    } catch{ setRetStatus("error"); setRetMsg("Could not connect."); }
  };

  const downloadPDF = () => {
    const doc = new jsPDF();
    doc.setFillColor(20,83,45); doc.rect(0,0,210,30,"F");
    doc.setTextColor(255,255,255);
    doc.setFontSize(18); doc.setFont("helvetica","bold");
    doc.text("AgroSentinel India",14,14);
    doc.setFontSize(10); doc.setFont("helvetica","normal");
    doc.text("ML-Powered Farm Intelligence Report — v4.0",14,22);
    doc.text(`Generated: ${new Date().toLocaleString()}`,130,22);

    let y = 38;
    doc.setTextColor(0,0,0);
    doc.setFontSize(13); doc.setFont("helvetica","bold"); doc.setTextColor(20,83,45);
    doc.text("Input Parameters",14,y); y+=4;
    autoTable(doc,{startY:y,
      head:[["Parameter","Value","Parameter","Value"]],
      body:[
        ["State",form.state,"Crop",form.crop],
        ["Season",form.season,"Year",form.year],
        ["Rainfall",`${form.rainfall||"-"} mm`,"Yield",results?.yield?.value?`${results.yield.value} t/ha`:"-"],
      ],
      styles:{fontSize:10,cellPadding:3},
      headStyles:{fillColor:[20,83,45],textColor:255},
      alternateRowStyles:{fillColor:[240,253,244]},margin:{left:14,right:14}
    });

    y = doc.lastAutoTable.finalY+10;
    doc.setFontSize(13); doc.setFont("helvetica","bold"); doc.setTextColor(20,83,45);
    doc.text("AI Analysis Results",14,y); y+=4;

    const rows = [];
    if(results?.yield)   rows.push(["Crop Yield",`${results.yield.value} t/ha`,results.yield.grade]);
    if(results?.drought) rows.push(["Drought Risk",results.drought.risk,`${results.drought.confidence}%`]);
    if(results?.failure) rows.push(["Failure Risk",results.failure.risk,`${results.failure.probability}%`]);
    if(results?.season)  rows.push(["Best Season",results.season.best,`${results.season.confidence}%`]);
    if(results?.soil)    rows.push(["Soil Health",`${results.soil.score}/100`,results.soil.grade]);
    if(market)           rows.push(["Market Price",`₹${market.price}/quintal`,market.source]);

    autoTable(doc,{startY:y,
      head:[["Module","Result","Confidence/Detail"]],body:rows,
      styles:{fontSize:10,cellPadding:3},headStyles:{fillColor:[20,83,45],textColor:255},
      alternateRowStyles:{fillColor:[240,253,244]},margin:{left:14,right:14}
    });

    if(results?.advisory?.why){
      y = doc.lastAutoTable.finalY+10;
      doc.setFontSize(11); doc.setFont("helvetica","bold"); doc.setTextColor(20,83,45);
      doc.text("AI Advisory Intelligence",14,y); y+=6;
      doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(0,0,0);
      const full = results.advisory.full.replace(/\*\*(.*?)\*\*/g,"$1").replace(/[📊💡🔮]/g,"");
      doc.text(full,14,y,{maxWidth:180});
    }

    const pc = doc.internal.getNumberOfPages();
    for(let i=1;i<=pc;i++){
      doc.setPage(i);
      doc.setFontSize(8); doc.setTextColor(150,150,150);
      doc.text("AgroSentinel India v4.0 — 4 ML Models · 8 Modules · SDG 2 · SDG 15",14,290);
      doc.text(`Page ${i}/${pc}`,190,290);
    }
    doc.save(`AgroSentinel_${form.state}_${form.crop}_${new Date().toISOString().slice(0,10)}.pdf`);
  };

  const cropGrad = results ? (CROP_GRADIENTS[results.input?.crop]||CROP_GRADIENTS.default) : CROP_GRADIENTS.default;

  const seasonChartData = results?.season?.all ? {
    labels: Object.keys(results.season.all),
    datasets:[{
      label:"Season Probability %",
      data: Object.values(results.season.all),
      backgroundColor:["rgba(34,197,94,0.8)","rgba(59,130,246,0.8)","rgba(245,158,11,0.8)","rgba(239,68,68,0.8)","rgba(168,85,247,0.8)","rgba(20,184,166,0.8)"],
      borderRadius:8,borderWidth:0,
    }]
  } : null;

  const inputStyle = {
    backgroundColor:dm.input, color:dm.inputTx, border:`1px solid ${dm.border}`,
    borderRadius:12, padding:"10px 14px", width:"100%", fontSize:14, outline:"none",
    fontFamily:"Inter,sans-serif",
  };
  const cardBase = {
    backgroundColor:dm.card, color:dm.text, border:`1px solid ${dm.border}`,
    borderRadius:20, padding:24,
  };

  const MODULE_TABS = [
    { id:"irrigation",    label:t.irrigation,    icon:"💧" },
    { id:"pest",          label:t.pestRisk,       icon:"🐛" },
    { id:"forecast",      label:t.priceForecast,  icon:"📈" },
    { id:"schemes",       label:t.govtSchemes,    icon:"🏛️" },
  ];

  return (
    <div style={{minHeight:"100vh",position:"relative",paddingBottom:80}}>
      <style>{GLOBAL_CSS}</style>

      {showRain    && <RainEffect/>}
      <FlowerAnimation show={showFlowers} dark={dark}/>
      <FloatingParticles dark={dark}/>

      {/* Fixed top bar */}
      <motion.div style={{
        position:"fixed",top:16,right:16,zIndex:1000,
        display:"flex",gap:8,alignItems:"center",
        background: dark?"rgba(10,15,26,0.9)":"rgba(255,255,255,0.9)",
        backdropFilter:"blur(16px)", border:`1px solid ${dm.border}`,
        borderRadius:50, padding:"8px 14px",
        boxShadow:"0 8px 32px rgba(0,0,0,0.15)",
      }}
        initial={{y:-60,opacity:0}} animate={{y:0,opacity:1}}
        transition={{delay:0.5,type:"spring",bounce:0.4}}>

        {/* Language */}
        <div className="dropdown">
          <button style={{background:"transparent",border:"none",color:dm.text,fontSize:18,cursor:"pointer",padding:"0 4px"}}
            data-bs-toggle="dropdown">🌐</button>
          <ul className="dropdown-menu dropdown-menu-end"
            style={{background:dm.card,border:`1px solid ${dm.border}`,borderRadius:16,padding:8,minWidth:160}}>
            {[{c:"en",l:"🇬🇧 English"},{c:"hi",l:"🇮🇳 हिन्दी"},{c:"ta",l:"🇮🇳 தமிழ்"},
              {c:"te",l:"🇮🇳 తెలుగు"},{c:"kn",l:"🇮🇳 ಕನ್ನಡ"},{c:"ml",l:"🇮🇳 മലയാളം"}]
              .map(({c,l})=>(
              <li key={c}>
                <button className="dropdown-item" onClick={()=>setLang(c)}
                  style={{color:dm.text,borderRadius:10,fontSize:13,
                    background:lang===c?(dark?"#14532d":"#dcfce7"):"transparent",
                    fontWeight:lang===c?"700":"400"}}>
                  {l} {lang===c&&"✓"}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Dark toggle */}
        <motion.button onClick={()=>setDark(!dark)}
          style={{background:dark?"linear-gradient(135deg,#fbbf24,#f59e0b)":"linear-gradient(135deg,#1e40af,#3b82f6)",
            border:"none",color:"#fff",borderRadius:50,width:36,height:36,fontSize:16,
            cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center"}}
          whileHover={{scale:1.15}} whileTap={{scale:0.9}}>
          {dark?"☀️":"🌙"}
        </motion.button>
      </motion.div>

      <div className="container py-4" style={{position:"relative",zIndex:1,maxWidth:1140}}>

        <HeroHeader dark={dark} title={t.title} subtitle={t.subtitle}/>

        {/* Platform Stats */}
        {platformStats && (
          <motion.div className="glass row g-3 mb-4" style={{...cardBase,padding:20}}
            initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.6}}>
            <div className="col-12 mb-1">
              <span style={{fontSize:12,fontWeight:700,textTransform:"uppercase",letterSpacing:"1.5px",color:dm.muted}}>
                📊 {t.stats}
              </span>
            </div>
            {[
              {label:"Records",value:platformStats.total_records?.toLocaleString(),icon:"🗄️"},
              {label:"Crops",value:platformStats.total_crops,icon:"🌾"},
              {label:"States",value:platformStats.total_states,icon:"🗺️"},
              {label:"Yield R²",value:`${(platformStats.yield_r2*100).toFixed(1)}%`,icon:"📈"},
              {label:"Drought Acc",value:`${(platformStats.drought_accuracy*100).toFixed(1)}%`,icon:"🌧️"},
              {label:"Failure Acc",value:`${(platformStats.failure_accuracy*100).toFixed(1)}%`,icon:"⚠️"},
            ].map(({label,value,icon},i)=>(
              <div className="col-6 col-md-2" key={i}>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22}}>{icon}</div>
                  <div style={{fontSize:18,fontWeight:800,color:dm.text}}>{value}</div>
                  <div style={{fontSize:11,color:dm.muted,fontWeight:500}}>{label}</div>
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Retrain */}
        <motion.div className="glass mb-4" style={cardBase}
          initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.1}}>
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
              <div style={{fontWeight:700,fontSize:15,color:dm.text}}>🔄 {t.retrain}</div>
              <div style={{fontSize:12,color:dm.muted}}>Retrain all 4 ML models with latest dataset</div>
            </div>
            <motion.button onClick={startRetrain} disabled={retStatus==="running"}
              style={{background:retStatus==="success"?"#16a34a":retStatus==="error"?"#dc2626":retStatus==="running"?"#6b7280":"linear-gradient(135deg,#d97706,#f59e0b)",
                border:"none",color:"#fff",borderRadius:50,padding:"10px 24px",fontWeight:700,fontSize:13,
                cursor:retStatus==="running"?"not-allowed":"pointer"}}
              whileHover={retStatus!=="running"?{scale:1.05}:{}} whileTap={retStatus!=="running"?{scale:0.95}:{}}>
              {retStatus==="running"?"⏳ Training...":retStatus==="success"?"✅ Done!":retStatus==="error"?"❌ Failed":t.retrain}
            </motion.button>
          </div>
          {retStatus==="running"&&(
            <div className="mt-3">
              <div style={{height:6,background:dark?"#1a2e1a":"#dcfce7",borderRadius:3,overflow:"hidden"}}>
                <motion.div style={{height:"100%",background:"linear-gradient(90deg,#16a34a,#22c55e,#16a34a)",backgroundSize:"200% 100%",animation:"shimmer 1.5s linear infinite"}}
                  animate={{width:["0%","100%"]}} transition={{duration:120,ease:"linear"}}/>
              </div>
              <div style={{fontSize:12,color:dm.muted,marginTop:4}}>Training 4 models on 236K records — 1–3 minutes...</div>
            </div>
          )}
          {retMsg&&retStatus!=="running"&&(
            <div style={{marginTop:10,padding:"8px 14px",borderRadius:10,fontSize:12,
              background:retStatus==="success"?"rgba(34,197,94,0.12)":"rgba(239,68,68,0.12)",
              color:retStatus==="success"?"#16a34a":"#dc2626"}}>{retMsg}</div>
          )}
        </motion.div>

        {/* Input Form */}
        <motion.div className="glass mb-4" style={cardBase}
          initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:0.5,delay:0.15}}>

          <div className="d-flex justify-content-between align-items-center mb-4">
            <div style={{fontWeight:700,fontSize:16,color:dm.text}}>🌿 Farm Parameters</div>
            <motion.button onClick={fetchWeather} disabled={!form.state||weatherLoad}
              style={{background:"linear-gradient(135deg,#0369a1,#0ea5e9)",border:"none",color:"#fff",
                borderRadius:50,padding:"8px 18px",fontSize:13,fontWeight:600,
                cursor:!form.state||weatherLoad?"not-allowed":"pointer",opacity:!form.state?0.6:1}}
              whileHover={form.state&&!weatherLoad?{scale:1.05}:{}} whileTap={form.state&&!weatherLoad?{scale:0.95}:{}}>
              {weatherLoad?"⏳ Fetching...":t.autoWeather}
            </motion.button>
          </div>

          {/* Weather bar */}
          <AnimatePresence>
            {weatherData&&(
              <motion.div style={{display:"flex",flexWrap:"wrap",gap:12,padding:"12px 16px",
                borderRadius:12,marginBottom:16,
                background:dark?"rgba(14,165,233,0.12)":"rgba(224,242,254,0.8)",
                border:"1px solid rgba(14,165,233,0.25)",fontSize:13,color:dm.text}}
                initial={{opacity:0,height:0}} animate={{opacity:1,height:"auto"}} exit={{opacity:0,height:0}}>
                <span>🌡 {weatherData.temperature}°C</span>
                <span>💧 {weatherData.humidity}%</span>
                <span>🌧 {weatherData.precipitation}mm</span>
                <span>💨 {weatherData.wind_speed}km/h</span>
                <span style={{color:dm.muted,fontSize:11}}>📡 {weatherData.source}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="row g-3">
            {/* State */}
            <div className="col-md-4 col-6">
              <label style={{fontSize:11,fontWeight:700,color:dm.muted,textTransform:"uppercase",letterSpacing:"1px",marginBottom:6,display:"block"}}>
                🗺️ {t.selectState}
              </label>
              <select style={inputStyle} value={form.state}
                onChange={e=>setForm(p=>({...p,state:e.target.value,
                  rainfall:String(Math.round({"Andhra Pradesh":980,"Kerala":3055,"Rajasthan":531,"Gujarat":820,"Maharashtra":1177,"Karnataka":1139,"Tamil Nadu":998,"West Bengal":1582,"Punjab":649}[e.target.value]||1000))}))}>
                <option value="">-- Select State --</option>
                {states.map(s=><option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Crop */}
            <div className="col-md-4 col-6">
              <label style={{fontSize:11,fontWeight:700,color:dm.muted,textTransform:"uppercase",letterSpacing:"1px",marginBottom:6,display:"block"}}>
                🌾 {t.selectCrop}
              </label>
              <select style={inputStyle} value={form.crop}
                onChange={e=>setForm(p=>({...p,crop:e.target.value}))}>
                <option value="">-- Select Crop --</option>
                {crops.map(c=><option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {/* Season */}
            <div className="col-md-4 col-6">
              <label style={{fontSize:11,fontWeight:700,color:dm.muted,textTransform:"uppercase",letterSpacing:"1px",marginBottom:6,display:"block"}}>
                📅 {t.selectSeason}
              </label>
              <select style={inputStyle} value={form.season}
                onChange={e=>setForm(p=>({...p,season:e.target.value}))}>
                {SEASONS.map(s=><option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Year */}
            <div className="col-md-4 col-6">
              <label style={{fontSize:11,fontWeight:700,color:dm.muted,textTransform:"uppercase",letterSpacing:"1px",marginBottom:6,display:"block"}}>
                📆 {t.selectYear}
              </label>
              <input type="number" style={inputStyle} value={form.year} min={1990} max={2030}
                onChange={e=>setForm(p=>({...p,year:e.target.value}))}/>
            </div>

            {/* Rainfall */}
            <div className="col-md-4 col-6">
              <label style={{fontSize:11,fontWeight:700,color:dm.muted,textTransform:"uppercase",letterSpacing:"1px",marginBottom:6,display:"block"}}>
                🌧️ {t.rainfall}
              </label>
              <input type="number" style={inputStyle} value={form.rainfall} placeholder="e.g. 1000"
                onChange={e=>setForm(p=>({...p,rainfall:e.target.value}))}/>
            </div>

            {/* Crop preview */}
            {form.crop && (
              <div className="col-md-4 d-flex align-items-end">
                <motion.div style={{width:"100%",padding:"10px 14px",borderRadius:12,
                  background:`linear-gradient(135deg,${cropGrad[0]},${cropGrad[1]})`,
                  color:"#fff",textAlign:"center",fontWeight:700,fontSize:14}}
                  initial={{scale:0.8,opacity:0}} animate={{scale:1,opacity:1}}
                  transition={{type:"spring",bounce:0.5}}>
                  {results?.emoji||"🌱"} {form.crop}
                  {form.state&&<span style={{fontWeight:400,fontSize:12,marginLeft:6,opacity:0.8}}>· {form.state}</span>}
                </motion.div>
              </div>
            )}
          </div>

          {error && (
            <motion.div style={{marginTop:12,padding:"10px 16px",borderRadius:10,
              background:"rgba(239,68,68,0.12)",border:"1px solid rgba(239,68,68,0.3)",
              color:"#dc2626",fontSize:13}}
              initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}}>
              ⚠️ {error}
            </motion.div>
          )}

          <motion.button onClick={analyze} disabled={loading} className="shimmer-btn"
            style={{width:"100%",marginTop:20,padding:"16px",borderRadius:14,color:"#fff",
              fontSize:17,fontWeight:800,letterSpacing:"0.3px",cursor:loading?"wait":"pointer",
              boxShadow:"0 8px 32px rgba(34,197,94,0.4)"}}
            whileHover={!loading?{scale:1.02,boxShadow:"0 12px 40px rgba(34,197,94,0.55)"}:{}}
            whileTap={!loading?{scale:0.98}:{}}>
            {loading?(
              <span style={{display:"flex",alignItems:"center",justifyContent:"center",gap:10}}>
                <motion.span animate={{rotate:360}} transition={{duration:1,repeat:Infinity,ease:"linear"}}>⚙️</motion.span>
                {t.analyzing}
              </span>
            ):t.analyze}
          </motion.button>
        </motion.div>

        {/* Results */}
        <div ref={resultsRef}/>
        <AnimatePresence>
          {results&&(
            <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>

              {/* Header */}
              <div className="d-flex justify-content-between align-items-center mb-3">
                <motion.div initial={{x:-30,opacity:0}} animate={{x:0,opacity:1}}>
                  <div style={{fontWeight:800,fontSize:18,color:dm.text}}>✨ Analysis Results</div>
                  <div style={{fontSize:12,color:dm.muted}}>{results.summary}</div>
                </motion.div>
                <motion.button onClick={downloadPDF}
                  style={{background:"linear-gradient(135deg,#dc2626,#ef4444)",border:"none",color:"#fff",
                    borderRadius:50,padding:"10px 20px",fontWeight:700,fontSize:13,cursor:"pointer",
                    boxShadow:"0 4px 16px rgba(239,68,68,0.3)"}}
                  whileHover={{scale:1.05}} whileTap={{scale:0.95}}
                  initial={{x:30,opacity:0}} animate={{x:0,opacity:1}}>
                  {t.downloadPDF}
                </motion.button>
              </div>

              {/* Crop Hero */}
              <motion.div style={{
                borderRadius:24,overflow:"hidden",
                background:`linear-gradient(135deg,${cropGrad[0]},${cropGrad[1]})`,
                padding:"32px 24px",marginBottom:20,position:"relative",
                boxShadow:`0 20px 60px ${cropGrad[0]}66`,
              }}
                initial={{opacity:0,scale:0.95}} animate={{opacity:1,scale:1}}
                transition={{duration:0.6,ease:[0.34,1.56,0.64,1]}}>
                <div style={{position:"absolute",inset:0,opacity:0.06,
                  backgroundImage:`radial-gradient(circle at 25% 25%,#fff 2px,transparent 2px),radial-gradient(circle at 75% 75%,#fff 2px,transparent 2px)`,
                  backgroundSize:"40px 40px"}}/>
                <div className="d-flex align-items-center gap-4 flex-wrap" style={{position:"relative",zIndex:1}}>
                  <motion.div className="float-emoji"
                    style={{fontSize:80,filter:"drop-shadow(0 8px 24px rgba(0,0,0,0.3))"}}>
                    {results.emoji}
                  </motion.div>
                  <div style={{color:"#fff"}}>
                    <div style={{fontSize:32,fontWeight:900,textShadow:"0 2px 16px rgba(0,0,0,0.4)"}}>{results.input.crop}</div>
                    <div style={{fontSize:16,opacity:0.85}}>{results.input.state} · {results.input.season} · {results.input.year}</div>
                    <div style={{fontSize:13,opacity:0.7,marginTop:4}}>Annual Rainfall: {results.input.rainfall}mm</div>
                  </div>
                  <div style={{marginLeft:"auto",textAlign:"right",color:"#fff"}}>
                    <div style={{fontSize:48,fontWeight:900,lineHeight:1}}>
                      <AnimCounter value={results.yield.value} decimals={2}/>
                    </div>
                    <div style={{fontSize:14,opacity:0.8}}>{t.tonnes}</div>
                    <motion.div style={{display:"inline-block",background:"rgba(255,255,255,0.2)",
                      backdropFilter:"blur(10px)",padding:"4px 16px",borderRadius:50,fontSize:13,fontWeight:700,marginTop:6}}
                      initial={{scale:0}} animate={{scale:1}}
                      transition={{delay:0.5,type:"spring",bounce:0.6}}>
                      {results.yield.grade}
                    </motion.div>
                  </div>
                </div>
              </motion.div>

              {/* 4 Result Cards */}
              <div className="row g-3 mb-4">
                <div className="col-md-6 col-lg-3">
                  <ResultCard title={t.yield} icon="📈" color={results.yield.color} dark={dark} delay={0}
                    value={<AnimCounter value={results.yield.value} decimals={2} suffix=" t/ha"/>}
                    sub={`${results.yield.per_acre} t/acre`} badge={results.yield.grade}>
                    <div style={{marginTop:10}}>
                      <div style={{height:6,background:dark?"#1a2e1a":"#dcfce7",borderRadius:3,overflow:"hidden"}}>
                        <motion.div style={{height:"100%",borderRadius:3,background:"linear-gradient(90deg,#16a34a,#22c55e)"}}
                          initial={{width:0}} animate={{width:`${Math.min(100,results.yield.value*20)}%`}}
                          transition={{duration:1.5,ease:"easeOut"}}/>
                      </div>
                    </div>
                  </ResultCard>
                </div>
                <div className="col-md-6 col-lg-3">
                  <ResultCard title={t.drought} icon="🌧️" color={results.drought.color} dark={dark} delay={0.1}
                    value={results.drought.risk} sub={results.drought.advice?.slice(0,60)+"..."}
                    badge={`${results.drought.confidence}% ${t.confidence}`}>
                    <div style={{marginTop:10}}>
                      <div style={{height:6,background:dark?"#1a2e1a":"#fef3c7",borderRadius:3,overflow:"hidden"}}>
                        <motion.div style={{height:"100%",borderRadius:3,
                          background:results.drought.risk==="High"?"linear-gradient(90deg,#dc2626,#ef4444)":results.drought.risk==="Medium"?"linear-gradient(90deg,#d97706,#f59e0b)":"linear-gradient(90deg,#16a34a,#22c55e)"}}
                          initial={{width:0}} animate={{width:`${results.drought.confidence}%`}}
                          transition={{duration:1.5,ease:"easeOut"}}/>
                      </div>
                    </div>
                  </ResultCard>
                </div>
                <div className="col-md-6 col-lg-3">
                  <ResultCard title={t.failure} icon="⚠️" color={results.failure.color} dark={dark} delay={0.2}
                    value={results.failure.risk} sub={`${results.failure.probability}% failure probability`}
                    badge={results.failure.probability<35?"Safe Zone":results.failure.probability<60?"Monitor":"High Alert"}>
                    <div style={{marginTop:10}}>
                      <div style={{height:6,background:dark?"#1a2e1a":"#fef2f2",borderRadius:3,overflow:"hidden"}}>
                        <motion.div style={{height:"100%",borderRadius:3,
                          background:results.failure.color==="danger"?"linear-gradient(90deg,#dc2626,#ef4444)":results.failure.color==="warning"?"linear-gradient(90deg,#d97706,#f59e0b)":"linear-gradient(90deg,#16a34a,#22c55e)"}}
                          initial={{width:0}} animate={{width:`${results.failure.probability}%`}}
                          transition={{duration:1.5,ease:"easeOut"}}/>
                      </div>
                    </div>
                  </ResultCard>
                </div>
                <div className="col-md-6 col-lg-3">
                  <ResultCard title={t.season} icon="📅" color="info" dark={dark} delay={0.3}
                    value={results.season.best} sub={`${results.season.confidence}% confidence`} badge="AI Recommended">
                    <div style={{marginTop:10}}>
                      {Object.entries(results.season.all).slice(0,3).map(([s,p])=>(
                        <div key={s} style={{marginBottom:4}}>
                          <div style={{display:"flex",justifyContent:"space-between",fontSize:10,color:dm.muted,marginBottom:2}}>
                            <span>{s}</span><span>{p}%</span>
                          </div>
                          <div style={{height:4,background:dark?"#1e3a5f":"#e0f2fe",borderRadius:2,overflow:"hidden"}}>
                            <motion.div className="season-bar" style={{height:"100%",background:"linear-gradient(90deg,#0369a1,#0ea5e9)"}}
                              initial={{width:0}} animate={{width:`${p}%`}} transition={{duration:1.2,delay:0.4,ease:"easeOut"}}/>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ResultCard>
                </div>
              </div>

              {/* Soil Health Card */}
              {results.soil && (
                <div className="mb-4">
                  <SoilHealthCard soil={results.soil} dark={dark}/>
                </div>
              )}

              {/* AI Advisory */}
              {results.advisory && (
                <AIAdvisoryCard advisory={results.advisory} dark={dark}/>
              )}

              {/* Market + Weather + Season Chart */}
              <div className="row g-3 mb-4">
                {market && (
                  <div className="col-md-4">
                    <motion.div className="glass h-100" style={{...cardBase,
                      background:dark?"rgba(120,53,15,0.9)":"rgba(255,251,235,0.95)",
                      border:"1px solid rgba(245,158,11,0.3)"}}
                      initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{delay:0.5}}>
                      <div style={{fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:"1.5px",color:"#d97706",marginBottom:12}}>
                        💰 {t.market}
                      </div>
                      <motion.div style={{fontSize:42,fontWeight:900,color:dark?"#fbbf24":"#92400e",lineHeight:1}}
                        initial={{scale:0}} animate={{scale:1}} transition={{delay:0.7,type:"spring",bounce:0.5}}>
                        ₹<AnimCounter value={market.price}/>
                      </motion.div>
                      <div style={{fontSize:13,color:dm.muted,marginTop:4}}>{market.unit}</div>
                      <div style={{marginTop:10,fontSize:12,color:dm.muted}}>
                        <div>📍 {market.market}{market.state&&`, ${market.state}`}</div>
                        <div>🗓️ {market.date}</div>
                      </div>
                      <motion.div style={{marginTop:10,display:"inline-block",
                        background:market.is_live?"rgba(34,197,94,0.15)":"rgba(107,114,128,0.15)",
                        color:market.is_live?"#16a34a":"#6b7280",padding:"3px 12px",borderRadius:50,fontSize:11,fontWeight:600}}
                        animate={market.is_live?{opacity:[1,0.6,1]}:{}} transition={{duration:2,repeat:Infinity}}>
                        {market.is_live?"🟢 Live — Agmarknet":"⚪ Est. MSP"}
                      </motion.div>
                    </motion.div>
                  </div>
                )}

                {weatherData && (
                  <div className="col-md-4">
                    <motion.div className="glass h-100" style={{...cardBase,
                      background:dark?"rgba(12,74,110,0.9)":"rgba(240,249,255,0.95)",
                      border:"1px solid rgba(14,165,233,0.3)"}}
                      initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{delay:0.6}}>
                      <div style={{fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:"1.5px",color:"#0369a1",marginBottom:12}}>
                        🌤 {t.weather}
                      </div>
                      <div className="row g-2">
                        {[
                          {icon:"🌡",label:"Temperature",value:`${weatherData.temperature}°C`},
                          {icon:"💧",label:"Humidity",value:`${weatherData.humidity}%`},
                          {icon:"🌧",label:"Precipitation",value:`${weatherData.precipitation}mm`},
                          {icon:"💨",label:"Wind",value:`${weatherData.wind_speed}km/h`},
                        ].map(({icon,label,value},i)=>(
                          <div className="col-6" key={i}>
                            <motion.div style={{background:dark?"rgba(14,165,233,0.1)":"rgba(186,230,253,0.5)",borderRadius:10,padding:"8px 10px"}}
                              initial={{opacity:0,scale:0.8}} animate={{opacity:1,scale:1}} transition={{delay:0.7+i*0.1}}>
                              <div style={{fontSize:18}}>{icon}</div>
                              <div style={{fontSize:15,fontWeight:700,color:dm.text}}>{value}</div>
                              <div style={{fontSize:10,color:dm.muted}}>{label}</div>
                            </motion.div>
                          </div>
                        ))}
                      </div>
                      <div style={{fontSize:10,color:dm.muted,marginTop:8}}>📡 {weatherData.source}</div>
                    </motion.div>
                  </div>
                )}

                {seasonChartData && (
                  <div className={`col-md-${weatherData&&market?4:market||weatherData?8:12}`}>
                    <motion.div className="glass h-100" style={cardBase}
                      initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{delay:0.7}}>
                      <div style={{fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:"1.5px",color:dm.muted,marginBottom:12}}>
                        📅 Season Suitability Analysis
                      </div>
                      <Bar data={seasonChartData} options={{
                        responsive:true,
                        plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.raw}% probability`}}},
                        scales:{
                          y:{beginAtZero:true,max:100,ticks:{color:dm.muted,font:{size:10}},grid:{color:dark?"rgba(255,255,255,0.05)":"rgba(0,0,0,0.05)"}},
                          x:{ticks:{color:dm.muted,font:{size:11}},grid:{display:false}},
                        }
                      }}/>
                    </motion.div>
                  </div>
                )}
              </div>

              {/* Advisory Box (existing brief one) */}
              {results.drought?.advice && (
                <motion.div style={{borderRadius:16,padding:"16px 20px",marginBottom:20,
                  background:dark?"rgba(120,53,15,0.3)":"rgba(255,251,235,0.9)",
                  border:`1px solid ${results.drought.risk==="High"?"rgba(239,68,68,0.4)":results.drought.risk==="Medium"?"rgba(245,158,11,0.4)":"rgba(34,197,94,0.4)"}`,
                  color:dm.text}}
                  initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} transition={{delay:0.8}}>
                  <div style={{fontWeight:700,marginBottom:4,fontSize:14}}>🎯 {t.advice}</div>
                  <div style={{fontSize:14,lineHeight:1.6}}>{results.drought.advice}</div>
                </motion.div>
              )}

              {/* ── NEW MODULE TABS ── */}
              <motion.div className="glass mb-4" style={cardBase}
                initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.6}}>

                <div style={{fontWeight:700,fontSize:16,color:dm.text,marginBottom:16}}>
                  🔬 {t.analyzeModules}
                </div>

                {/* Tab buttons */}
                <div style={{display:"flex",flexWrap:"wrap",gap:8,marginBottom:20}}>
                  {MODULE_TABS.map(tab => (
                    <button key={tab.id}
                      className={`module-tab ${activeModule===tab.id?"active":""}`}
                      onClick={()=>setActiveModule(activeModule===tab.id?null:tab.id)}
                      style={{
                        background: activeModule===tab.id
                          ? dark?"rgba(82,183,136,0.2)":"rgba(82,183,136,0.1)"
                          : dark?"rgba(255,255,255,0.06)":"rgba(0,0,0,0.04)",
                        color:dm.text, border:`2px solid ${activeModule===tab.id?"#52b788":dm.border}`,
                      }}>
                      {tab.icon} {tab.label.split(" ").slice(1).join(" ")}
                    </button>
                  ))}
                </div>

                {/* Module content */}
                <AnimatePresence mode="wait">
                  {activeModule === "irrigation" && (
                    <motion.div key="irrigation" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}}>
                      <IrrigationModule form={form} dark={dark} dm={dm}/>
                    </motion.div>
                  )}
                  {activeModule === "pest" && (
                    <motion.div key="pest" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}}>
                      <PestRiskModule form={form} weatherData={weatherData} dark={dark} dm={dm}/>
                    </motion.div>
                  )}
                  {activeModule === "forecast" && (
                    <motion.div key="forecast" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}}>
                      <PriceForecastModule form={form} dark={dark} dm={dm}/>
                    </motion.div>
                  )}
                  {activeModule === "schemes" && (
                    <motion.div key="schemes" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}}>
                      <GovtSchemesModule form={form} results={results} dark={dark} dm={dm}/>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>

            </motion.div>
          )}
        </AnimatePresence>

        {/* History */}
        {history.length>0 && (
          <motion.div className="glass mb-4" style={cardBase}
            initial={{opacity:0}} animate={{opacity:1}}>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <div style={{fontWeight:700,fontSize:15,color:dm.text}}>📋 {t.history}</div>
              <button onClick={()=>setHistory([])}
                style={{background:"transparent",border:"none",color:"#dc2626",cursor:"pointer",fontSize:13,fontWeight:600}}>
                🗑 {t.clearHistory}
              </button>
            </div>
            <div style={{overflowX:"auto"}}>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,color:dm.text}}>
                <thead>
                  <tr style={{borderBottom:`2px solid ${dm.border}`}}>
                    {["Time","State","Crop","Season","Year","Yield","Drought","Failure","Best Season"].map(h=>(
                      <th key={h} style={{padding:"8px 10px",textAlign:"left",fontWeight:700,color:dm.muted,whiteSpace:"nowrap"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {history.map((h,i)=>(
                    <motion.tr key={i} initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} transition={{delay:i*0.04}}
                      style={{borderBottom:`1px solid ${dm.border}`,background:i%2===0?"transparent":dark?"rgba(255,255,255,0.02)":"rgba(34,197,94,0.03)"}}>
                      <td style={{padding:"8px 10px",whiteSpace:"nowrap"}}>{h.time}</td>
                      <td style={{padding:"8px 10px"}}>{h.state}</td>
                      <td style={{padding:"8px 10px",fontWeight:600}}>{h.crop}</td>
                      <td style={{padding:"8px 10px"}}>{h.season}</td>
                      <td style={{padding:"8px 10px"}}>{h.year}</td>
                      <td style={{padding:"8px 10px"}}>
                        <span style={{background:"rgba(34,197,94,0.15)",color:"#16a34a",padding:"2px 8px",borderRadius:50,fontWeight:600}}>
                          {h.yield} t/ha
                        </span>
                      </td>
                      <td style={{padding:"8px 10px"}}>
                        <span style={{background:h.drought==="High"?"rgba(239,68,68,0.15)":h.drought==="Medium"?"rgba(245,158,11,0.15)":"rgba(34,197,94,0.15)",color:h.drought==="High"?"#dc2626":h.drought==="Medium"?"#d97706":"#16a34a",padding:"2px 8px",borderRadius:50,fontWeight:600}}>
                          {h.drought}
                        </span>
                      </td>
                      <td style={{padding:"8px 10px"}}>
                        <span style={{background:h.failure?.includes("High")?"rgba(239,68,68,0.15)":h.failure?.includes("Medium")?"rgba(245,158,11,0.15)":"rgba(34,197,94,0.15)",color:h.failure?.includes("High")?"#dc2626":h.failure?.includes("Medium")?"#d97706":"#16a34a",padding:"2px 8px",borderRadius:50,fontWeight:600}}>
                          {h.failure}
                        </span>
                      </td>
                      <td style={{padding:"8px 10px",fontWeight:600,color:"#0369a1"}}>{h.season_best}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}

        {/* Footer */}
        <motion.div style={{textAlign:"center",paddingTop:20,color:dm.muted,fontSize:12}}
          initial={{opacity:0}} animate={{opacity:1}} transition={{delay:1.2}}>
          🌾 AgroSentinel India v4.0 · 4 ML Models · 8 Modules · 236K Records · 33 States · 105 Crops
          · SDG 2 Zero Hunger · SDG 15 Life on Land
        </motion.div>
      </div>
    </div>
  );
}