// =================================================================
// AI-R · Cockpit — Slate Cockpit theme (port du design Claude Design)
// =================================================================

// ============ Map (top-down) ============
const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");
let W = 800;
let H = 280;
const SCALE = 35;

let drone = { x: 0, y: 0, z: 0, yaw: 0, battery: 100, is_flying: false };
const trail = [];

// Slate theme colors (en hex pour compatibilité maximale)
const COL_BG          = "#F1F5F9";
const COL_GRID_MINOR  = "#E2E8F0";
const COL_GRID_MAJOR  = "#CBD5E1";
const COL_AXIS        = "#94A3B8";
const COL_ACCENT      = "#4338CA";
const COL_ACCENT_SOFT = "rgba(99, 102, 241, 0.18)";
const COL_TEXT_MUTED  = "#64748B";

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return; // pas encore layouté
  W = Math.max(200, Math.floor(rect.width));
  H = Math.max(150, Math.floor(rect.height));
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = W * dpr;
  canvas.height = H * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function worldToScreen(x, y) {
  return [W / 2 + x * SCALE, H / 2 - y * SCALE];
}

function drawGrid() {
  // minor grid (0.5m)
  ctx.strokeStyle = COL_GRID_MINOR;
  ctx.lineWidth = 0.5;
  for (let v = -10; v <= 10; v += 0.5) {
    const [sx] = worldToScreen(v, 0);
    const [, sy] = worldToScreen(0, v);
    ctx.beginPath(); ctx.moveTo(sx, 0); ctx.lineTo(sx, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, sy); ctx.lineTo(W, sy); ctx.stroke();
  }
  // major grid (1m)
  ctx.strokeStyle = COL_GRID_MAJOR;
  ctx.lineWidth = 0.8;
  for (let v = -10; v <= 10; v++) {
    const [sx] = worldToScreen(v, 0);
    const [, sy] = worldToScreen(0, v);
    ctx.beginPath(); ctx.moveTo(sx, 0); ctx.lineTo(sx, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, sy); ctx.lineTo(W, sy); ctx.stroke();
  }
  // axes
  ctx.strokeStyle = COL_AXIS;
  ctx.lineWidth = 1;
  const [cx, cy] = worldToScreen(0, 0);
  ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(W, cy); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, H); ctx.stroke();

  // labels
  ctx.fillStyle = COL_TEXT_MUTED;
  ctx.font = '10px "JetBrains Mono", monospace';
  for (let v = -4; v <= 4; v++) {
    if (v === 0) continue;
    const [sx] = worldToScreen(v, 0);
    ctx.fillText(`${v}m`, sx + 3, cy + 12);
    const [, sy] = worldToScreen(0, v);
    ctx.fillText(`${v}m`, cx + 4, sy - 3);
  }
}

function drawTrail() {
  if (trail.length < 2) return;
  ctx.strokeStyle = COL_ACCENT;
  ctx.lineWidth = 1.6;
  ctx.beginPath();
  trail.forEach(([x, y], i) => {
    const [sx, sy] = worldToScreen(x, y);
    if (i === 0) ctx.moveTo(sx, sy);
    else ctx.lineTo(sx, sy);
  });
  ctx.stroke();
}

function drawDrone() {
  const [dx, dy] = worldToScreen(drone.x, drone.y);
  // outer halo
  ctx.beginPath(); ctx.arc(dx, dy, 16, 0, Math.PI * 2);
  ctx.fillStyle = COL_ACCENT_SOFT;
  ctx.fill();

  // direction wedge
  const yawRad = -drone.yaw * Math.PI / 180;
  ctx.save();
  ctx.translate(dx, dy);
  ctx.rotate(yawRad);
  ctx.fillStyle = COL_ACCENT;
  ctx.beginPath();
  ctx.moveTo(0, -14);
  ctx.lineTo(-7, 5);
  ctx.lineTo(0, 2);
  ctx.lineTo(7, 5);
  ctx.closePath();
  ctx.fill();
  // center dot
  ctx.fillStyle = "#fff";
  ctx.beginPath(); ctx.arc(0, 0, 2.5, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

function render() {
  ctx.fillStyle = COL_BG;
  ctx.fillRect(0, 0, W, H);
  drawGrid();
  drawTrail();
  drawDrone();
  requestAnimationFrame(render);
}

// ============ Status panel ============
function updateStatus() {
  const fmt2 = (v) => v.toFixed(2);
  const yawStr = String(Math.round(drone.yaw)).padStart(3, "0");
  const battColor = drone.battery > 50 ? "var(--ok)" : drone.battery > 20 ? "var(--warn)" : "var(--crit)";

  document.getElementById("row-x").innerHTML = `${fmt2(drone.x)}<span class="u">m</span>`;
  document.getElementById("row-y").innerHTML = `${fmt2(drone.y)}<span class="u">m</span>`;
  document.getElementById("row-z").innerHTML = `${fmt2(drone.z)}<span class="u">m</span>`;
  document.getElementById("row-yaw").innerHTML = `${yawStr}<span class="u">°</span>`;
  const battRow = document.getElementById("row-batt");
  battRow.innerHTML = `${drone.battery.toFixed(0)}<span class="u">%</span>`;
  battRow.style.color = battColor;
  document.getElementById("row-state").textContent = drone.is_flying ? "en vol" : "au sol";

  // stats strip
  document.getElementById("stat-x").innerHTML = `${fmt2(drone.x)}<span class="stat-unit">m</span>`;
  document.getElementById("stat-y").innerHTML = `${fmt2(drone.y)}<span class="stat-unit">m</span>`;
  document.getElementById("stat-z").innerHTML = `${fmt2(drone.z)}<span class="stat-unit">m</span>`;
  document.getElementById("stat-yaw").innerHTML = `${yawStr}<span class="stat-unit">°</span>`;
  const stB = document.getElementById("stat-batt");
  stB.innerHTML = `${drone.battery.toFixed(0)}<span class="stat-unit">%</span>`;
  stB.style.color = battColor;
}

// ============ Detections ============
const DANGER = new Set(["person", "dog", "cat", "bird", "horse"]);
const WARN = new Set(["chair", "couch", "potted plant", "tv", "laptop", "bottle", "cup"]);

function updateDetections(detections) {
  const el = document.getElementById("detections");
  if (!detections || detections.length === 0) {
    el.innerHTML = `<span class="muted">Aucune détection</span>`;
    return;
  }
  el.innerHTML = detections.map(d => {
    const cls = DANGER.has(d.label) ? "danger" : WARN.has(d.label) ? "warn" : "";
    return `<span class="detection-chip ${cls}">${d.label} ${(d.confidence * 100).toFixed(0)}%</span>`;
  }).join("");
}

function setObstacleBanner(blocked) {
  const banner = document.getElementById("obstacle-banner");
  if (blocked) banner.classList.remove("hidden");
  else banner.classList.add("hidden");
}

// ============ Logs + history ============
function addLog(text, kind = "") {
  const ul = document.getElementById("logs");
  const li = document.createElement("li");
  if (kind) li.className = kind;
  const t = new Date().toLocaleTimeString();
  li.innerHTML = `<time>${t}</time>${text}`;
  ul.prepend(li);
  while (ul.children.length > 50) ul.removeChild(ul.lastChild);
}

const historyEl = document.getElementById("history");
function addHistoryItem(text) {
  // remove empty placeholder
  if (historyEl.children.length === 1 && historyEl.firstElementChild.classList.contains("muted")) {
    historyEl.innerHTML = "";
  }
  const li = document.createElement("li");
  li.className = "history-item";
  li.innerHTML = `<span class="txt">${escapeHtml(text)}</span><span class="badge-mini">en cours</span>`;
  historyEl.prepend(li);
  while (historyEl.children.length > 20) historyEl.removeChild(historyEl.lastChild);
  return li;
}
function markHistoryLast(status) {
  const first = historyEl.firstElementChild;
  if (!first || !first.classList.contains("history-item")) return;
  const badge = first.querySelector(".badge-mini");
  if (!badge) return;
  if (status === "done") { first.classList.add("done"); badge.textContent = "ok"; }
  else if (status === "error") { first.classList.add("error"); badge.textContent = "err"; }
}
function escapeHtml(s) {
  return s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// ============ Pretty JSON ============
function prettyJson(obj) {
  if (!obj) return "—";
  return JSON.stringify(obj, null, 2)
    .replace(/("([^"]+)":)/g, '<span class="key">$1</span>')
    .replace(/: ("([^"]*)")/g, ': <span class="str">$1</span>');
}

// ============ WebSocket ============
function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  const pill = document.getElementById("live-pill");
  const label = document.getElementById("live-label");

  ws.onopen = () => {
    pill.classList.remove("offline");
    label.textContent = "Live";
  };
  ws.onclose = () => {
    pill.classList.add("offline");
    label.textContent = "offline";
    setTimeout(connectWS, 2000);
  };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "state") {
      drone = msg.state;
      if (drone.is_flying) {
        const last = trail[trail.length - 1];
        if (!last || Math.hypot(last[0] - drone.x, last[1] - drone.y) > 0.05) {
          trail.push([drone.x, drone.y]);
          if (trail.length > 600) trail.shift();
        }
      }
      updateStatus();
      updateDetections(msg.detections);
      setObstacleBanner(msg.path_blocked);
    } else if (msg.type === "plan") {
      document.getElementById("plan").innerHTML = prettyJson(msg.plan);
      addLog(`Plan reçu (${msg.plan.length} étapes)`, "cmd");
    } else if (msg.type === "obstacle") {
      addLog(`⚠ Obstacle évité : ${msg.labels.join(", ") || "objet inconnu"}`, "alert");
    } else if (msg.type === "done") {
      markHistoryLast("done");
      addLog("Plan terminé ✓", "cmd");
    } else if (msg.type === "error") {
      markHistoryLast("error");
      addLog(`Erreur: ${msg.message}`, "error");
    }
  };
}

// ============ Form / commands ============
const form = document.getElementById("cmd-form");
const input = document.getElementById("cmd-input");
const submitBtn = form.querySelector("button[type=submit]");

async function sendCommand(order) {
  if (!order) return;
  addLog(`> ${order}`, "cmd");
  addHistoryItem(order);
  submitBtn.disabled = true;
  try {
    const res = await fetch("/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  } catch (e) {
    addLog(`Erreur réseau: ${e.message}`, "error");
    markHistoryLast("error");
  } finally {
    submitBtn.disabled = false;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const order = input.value.trim();
  input.value = "";
  sendCommand(order);
});

document.querySelectorAll(".preset").forEach((btn) => {
  btn.addEventListener("click", () => {
    input.value = btn.dataset.cmd;
    sendCommand(btn.dataset.cmd);
    input.value = "";
  });
});

// ============ Voice (Web Speech API) ============
const voiceBtn = document.getElementById("voice-toggle");
const voiceLabel = document.getElementById("voice-label");
const voiceListening = document.getElementById("voice-listening");

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let voiceMode = false;
let listening = false;

function setVoiceUI(on, listeningNow) {
  voiceBtn.classList.toggle("on", on);
  voiceLabel.textContent = on
    ? (listeningNow ? "🎙 J'écoute…" : "Vocal · on")
    : "Vocal · off";
  if (on && listeningNow) voiceListening.classList.remove("hidden");
  else voiceListening.classList.add("hidden");
}

if (!SR) {
  voiceBtn.disabled = true;
  voiceBtn.title = "Web Speech API non supportée — utiliser Chrome ou Edge";
} else {
  recognition = new SR();
  recognition.lang = "fr-FR";
  recognition.continuous = false;     // une phrase puis stop, on redémarre en boucle
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    listening = true;
    setVoiceUI(voiceMode, true);
  };

  recognition.onend = () => {
    listening = false;
    setVoiceUI(voiceMode, false);
    // Auto-restart tant que le mode vocal est ON
    if (voiceMode) {
      try { recognition.start(); } catch (_) { /* déjà demandé */ }
    }
  };

  recognition.onerror = (e) => {
    listening = false;
    if (e.error === "not-allowed" || e.error === "service-not-allowed") {
      addLog("Voix : permission micro refusée — autorise le micro pour ce site", "error");
      voiceMode = false;
      setVoiceUI(false, false);
    } else if (e.error === "no-speech") {
      // silence — relancer si toujours en mode vocal (géré par onend)
    } else if (e.error === "aborted") {
      // utilisateur a coupé — ok
    } else {
      addLog(`Voix : ${e.error}`, "error");
    }
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript.trim();
    if (!transcript) return;
    input.value = transcript;
    sendCommand(transcript);
    input.value = "";
  };
}

voiceBtn.addEventListener("click", async () => {
  if (!recognition) return;
  voiceMode = !voiceMode;
  if (voiceMode) {
    // Tester l'accès micro avant de lancer (déclenche le prompt Windows)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(t => t.stop());
    } catch (err) {
      voiceMode = false;
      addLog("Voix : micro inaccessible — vérifie les permissions Windows/Chrome", "error");
      setVoiceUI(false, false);
      return;
    }
    try { recognition.start(); }
    catch (err) { /* déjà en cours, ignore */ }
    setVoiceUI(true, false);
  } else {
    try { recognition.abort(); } catch (_) {}
    setVoiceUI(false, false);
  }
});

// ============ Boot ============
// Réagit aux changements de taille du conteneur du canvas (resize fenêtre, fonts chargées, etc.)
if (window.ResizeObserver) {
  const ro = new ResizeObserver(resizeCanvas);
  ro.observe(canvas);
}
window.addEventListener("resize", resizeCanvas);
// Premier resize après layout
requestAnimationFrame(() => { resizeCanvas(); resizeCanvas(); });
render();
connectWS();
