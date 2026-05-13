// AI-R Launcher · gère mode + liste des drones + Démarrer

const state = {
  mode: "tello",
  selectedId: null,
  adding: false,
  draft: { name: "", ssid: "", pw: "", ip: "" },
  testing: null, // null | "pending" | "ok"
  drones: [],
};

// ============ API ============
async function api(path, opts = {}) {
  const r = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  if (r.headers.get("content-type")?.includes("json")) return r.json();
  return null;
}

async function loadDrones() {
  try {
    const data = await api("/api/drones");
    state.drones = data.drones || [];
    if (!state.selectedId && state.drones.length > 0) {
      state.selectedId = state.drones[0].id;
    }
  } catch (e) {
    console.error("loadDrones failed", e);
    state.drones = [];
  }
}

async function saveDrone(drone) {
  const isUpdate = !!drone.id;
  if (isUpdate) {
    await api(`/api/drones/${drone.id}`, { method: "PUT", body: JSON.stringify(drone) });
  } else {
    const created = await api("/api/drones", { method: "POST", body: JSON.stringify(drone) });
    return created;
  }
}

async function deleteDrone(id) {
  await api(`/api/drones/${id}`, { method: "DELETE" });
}

// ============ Render ============
const dronesListEl = document.getElementById("drones-list");
const droneCountEl = document.getElementById("drone-count");
const simCardEl = document.getElementById("sim-card");
const rightBodyEl = document.getElementById("right-body");
const footerDotEl = document.getElementById("footer-dot");
const footerTargetEl = document.getElementById("footer-target");
const btnStart = document.getElementById("btn-start");
const btnAdd = document.getElementById("btn-add");

function renderModeToggle() {
  document.querySelectorAll(".mode-opt").forEach(btn => {
    btn.classList.toggle("selected", btn.dataset.mode === state.mode);
  });
  btnAdd.disabled = state.mode === "sim";
}

function renderDroneList() {
  droneCountEl.textContent = state.drones.length;
  if (state.mode === "sim") {
    dronesListEl.style.display = "none";
    simCardEl.style.display = "block";
    return;
  }
  dronesListEl.style.display = "flex";
  simCardEl.style.display = "none";

  dronesListEl.innerHTML = state.drones.map(d => droneRowHtml(d)).join("");
  if (state.adding) {
    dronesListEl.innerHTML += `
      <div class="drone-row" style="background:var(--accent-soft);border:1px dashed var(--accent)">
        <div class="drone-icon" style="border:1px dashed var(--accent);color:var(--accent)">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 3v10M3 8h10" stroke-linecap="round"/></svg>
        </div>
        <div class="drone-main">
          <div class="drone-name"><b>Nouveau drone</b></div>
          <div class="drone-meta">Renseigne la config à droite →</div>
        </div>
      </div>`;
  }
  // attach handlers
  dronesListEl.querySelectorAll(".drone-row[data-id]").forEach(row => {
    const id = row.dataset.id;
    row.addEventListener("click", (e) => {
      if (e.target.closest(".drone-del")) return;
      state.adding = false;
      state.selectedId = id;
      state.testing = null;
      renderAll();
    });
    row.querySelector(".drone-del")?.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Oublier ce drone ?")) return;
      await deleteDrone(id);
      state.drones = state.drones.filter(d => d.id !== id);
      if (state.selectedId === id) state.selectedId = state.drones[0]?.id || null;
      renderAll();
    });
  });
}

function droneRowHtml(d) {
  const sel = !state.adding && state.selectedId === d.id;
  const battCls = d.battery > 50 ? "" : d.battery > 20 ? "low" : "crit";
  return `
    <div class="drone-row ${sel ? "selected" : ""}" data-id="${d.id}">
      <div class="drone-icon">
        <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="4" cy="4" r="2"/><circle cx="16" cy="4" r="2"/><circle cx="4" cy="16" r="2"/><circle cx="16" cy="16" r="2"/><path d="M5.5 5.5 9 9M14.5 5.5 11 9M5.5 14.5 9 11M14.5 14.5 11 11"/><rect x="8" y="8" width="4" height="4" rx="0.8"/></svg>
      </div>
      <div class="drone-main">
        <div class="drone-name">
          <b>${escapeHtml(d.name)}</b>
          <span class="status-pill ${d.status || "offline"}"><span class="dot"></span>${d.status || "offline"}</span>
        </div>
        <div class="drone-meta">
          <span class="ip">${escapeHtml(d.ip || "")}</span>
          <span class="batt">
            <span class="batt-bar ${battCls}" style="position:relative">
              <span style="position:absolute;left:1px;top:1px;bottom:1px;width:${Math.max(0, Math.min(100, d.battery || 0)) * 0.18}px;background:currentColor;border-radius:1px"></span>
            </span>
            ${d.battery ?? "—"}%
          </span>
          <span class="last">· vu ${d.last_seen || "il y a longtemps"}</span>
        </div>
      </div>
      <button class="drone-del" title="Oublier ce drone">
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3 4h10M6 4V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1M5 4l.5 9a1.5 1.5 0 0 0 1.5 1.4h2a1.5 1.5 0 0 0 1.5-1.4L11 4"/></svg>
      </button>
    </div>`;
}

function renderRightPanel() {
  if (state.mode === "sim") {
    rightBodyEl.innerHTML = `
      <h2 style="font-size:15px;font-weight:600;margin:0 0 4px">Simulateur prêt</h2>
      <p style="font-size:12.5px;color:var(--muted);margin:0 0 18px;line-height:1.5">
        Le simulateur charge un drone virtuel. La <b>webcam du PC</b> est utilisée comme caméra
        du drone, ce qui permet de tester YOLO et l'évitement d'obstacles sans matériel.
      </p>
      <ul style="font-size:12px;color:var(--text-2);line-height:1.8;padding-left:18px;margin:0">
        <li>Tu peux taper des ordres vocaux ou texte</li>
        <li>Le drone est animé en 3D sur la carte top-down</li>
        <li>YOLO annote les frames en temps réel</li>
        <li>Si un objet est dans l'axe : l'ordre frontal est annulé</li>
      </ul>
    `;
    return;
  }

  const current = state.adding ? state.draft : state.drones.find(d => d.id === state.selectedId);
  if (!current) {
    rightBodyEl.innerHTML = `<div class="right-empty">Sélectionne un drone à gauche ou clique sur <em>+ Ajouter</em>.</div>`;
    return;
  }

  rightBodyEl.innerHTML = `
    <h2 style="font-size:15px;font-weight:600;margin:0 0 4px">${state.adding ? "Nouveau Tello" : escapeHtml(current.name)}</h2>
    <p style="font-size:12px;color:var(--muted);margin:0 0 18px">Configurer la connexion réseau</p>

    <div class="step-row"><div class="step-badge">1</div><div class="step-title">Nom du drone</div></div>
    <div class="field">
      <div class="field-input-wrap">
        <input id="f-name" placeholder="Tello-Salon" value="${escapeAttr(current.name || "")}" />
      </div>
    </div>

    <div class="step-row"><div class="step-badge">2</div><div class="step-title">Wifi auquel le drone doit se connecter</div></div>
    <div class="field">
      <div class="field-label">SSID</div>
      <div class="field-input-wrap">
        <input id="f-ssid" placeholder="MaBox" value="${escapeAttr(current.ssid || "")}" />
      </div>
    </div>
    <div class="field">
      <div class="field-label">Mot de passe</div>
      <div class="field-input-wrap">
        <input id="f-pw" type="password" placeholder="••••••••" value="${escapeAttr(current.pw || "")}" />
        <button class="field-eye" type="button" id="toggle-pw"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M1.5 8s2.5-4.5 6.5-4.5S14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8Z"/><circle cx="8" cy="8" r="2"/></svg></button>
      </div>
      <div class="field-hint">Stocké en clair dans le profil local — ne pas réutiliser un mot de passe sensible.</div>
    </div>

    <div class="step-row"><div class="step-badge">3</div><div class="step-title">IP du drone sur ce wifi</div></div>
    <div class="field">
      <div class="field-input-wrap">
        <input id="f-ip" class="mono" placeholder="192.168.137.118" value="${escapeAttr(current.ip || "")}" />
      </div>
      <div class="field-hint">Une fois le drone configuré, trouve son IP avec <code class="mono">arp -a | findstr 60-60-1f</code>.</div>
    </div>

    <div style="display:flex;gap:8px;margin-top:18px">
      <button class="btn-test ${state.testing || ""}" id="btn-test">
        ${state.testing === "pending" ? "Test en cours…" : state.testing === "ok" ? "✓ Connexion OK" : "Tester la connexion"}
      </button>
      ${state.adding ? `<button class="btn-test" id="btn-save" style="border-color:var(--accent);color:var(--accent)">Enregistrer</button>` : ""}
    </div>
  `;

  // wire inputs
  ["name", "ssid", "pw", "ip"].forEach(k => {
    document.getElementById(`f-${k}`)?.addEventListener("input", (e) => updateField(k, e.target.value));
  });
  document.getElementById("toggle-pw")?.addEventListener("click", () => {
    const inp = document.getElementById("f-pw");
    inp.type = inp.type === "password" ? "text" : "password";
  });
  document.getElementById("btn-test")?.addEventListener("click", runTest);
  document.getElementById("btn-save")?.addEventListener("click", saveDraft);
}

function renderFooter() {
  const canStart = state.mode === "sim" || (state.selectedId && state.drones.find(d => d.id === state.selectedId));
  btnStart.disabled = !canStart;
  footerDotEl.classList.toggle("ok", !!canStart);

  if (state.mode === "sim") {
    footerTargetEl.innerHTML = "Simulateur prêt";
  } else if (!state.selectedId || state.adding) {
    footerTargetEl.innerHTML = state.adding ? "Renseigne le nouveau drone" : "Aucun drone sélectionné";
  } else {
    const d = state.drones.find(x => x.id === state.selectedId);
    if (d) footerTargetEl.innerHTML = `Cible · <span class="mono">${escapeHtml(d.name)} ${escapeHtml(d.ip || "")}</span>`;
  }
}

function renderAll() {
  renderModeToggle();
  renderDroneList();
  renderRightPanel();
  renderFooter();
}

// ============ Actions ============
function updateField(key, val) {
  if (state.adding) {
    state.draft[key] = val;
  } else {
    const d = state.drones.find(x => x.id === state.selectedId);
    if (d) d[key] = val;
    // debounce save to backend
    clearTimeout(updateField._t);
    updateField._t = setTimeout(() => saveDrone(d).catch(console.error), 500);
  }
  renderFooter();
}

async function saveDraft() {
  if (!state.draft.name || !state.draft.ip) {
    alert("Nom et IP requis.");
    return;
  }
  const created = await saveDrone({
    name: state.draft.name,
    ssid: state.draft.ssid,
    pw: state.draft.pw,
    ip: state.draft.ip,
    battery: 100,
    status: "new",
    last_seen: "à l'instant",
  });
  state.drones.push(created);
  state.selectedId = created.id;
  state.adding = false;
  renderAll();
}

async function runTest() {
  state.testing = "pending";
  renderRightPanel();
  const target = state.adding ? state.draft : state.drones.find(d => d.id === state.selectedId);
  try {
    const r = await api("/api/test-connection", {
      method: "POST",
      body: JSON.stringify({ ip: target.ip }),
    });
    state.testing = r.ok ? "ok" : null;
    if (r.ok && !state.adding) {
      const d = state.drones.find(x => x.id === state.selectedId);
      if (d) { d.status = "connected"; d.battery = r.battery ?? d.battery; d.last_seen = "à l'instant"; }
    } else if (!r.ok) {
      addLog && addLog(`Test échoué : ${r.message || "pas de réponse"}`);
    }
  } catch (e) {
    state.testing = null;
    alert("Erreur de test : " + e.message);
  }
  renderAll();
}

// ============ Mode toggle ============
document.querySelectorAll(".mode-opt").forEach(btn => {
  btn.addEventListener("click", () => {
    state.mode = btn.dataset.mode;
    state.adding = false;
    renderAll();
  });
});

btnAdd.addEventListener("click", () => {
  state.adding = true;
  state.selectedId = null;
  state.testing = null;
  state.draft = {
    name: `Tello-${String.fromCharCode(65 + state.drones.length)}`,
    ssid: "",
    pw: "",
    ip: "192.168.137." + (100 + state.drones.length),
  };
  renderAll();
});

btnStart.addEventListener("click", async () => {
  btnStart.disabled = true;
  btnStart.textContent = "Démarrage…";
  try {
    const body = state.mode === "sim"
      ? { mode: "simulator" }
      : { mode: "tello", drone_id: state.selectedId };
    await api("/api/launch", { method: "POST", body: JSON.stringify(body) });
    location.href = "/";
  } catch (e) {
    alert("Erreur démarrage : " + e.message);
    btnStart.disabled = false;
    btnStart.innerHTML = `<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M5 3.5v9l8-4.5z"/></svg> Démarrer`;
  }
});

// ============ Utils ============
function escapeHtml(s) {
  return String(s || "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s); }

// ============ Boot ============
(async () => {
  await loadDrones();
  renderAll();
})();
