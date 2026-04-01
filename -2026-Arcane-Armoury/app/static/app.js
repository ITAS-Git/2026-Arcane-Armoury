/* app.js
   - Stores state in localStorage (so refresh keeps it)
   - DM broadcasts updates via WebSocket (Socket.IO)
   - Player listens and re-renders immediately
   - hp_delta / slot_delta re-broadcast so all screens stay in sync
   - Portrait img falls back to Tiefling.png on load error
*/
console.log("app.js loaded");
const STORAGE_KEY = "arcane_armoury_state_v3";
const SPELL_LEVELS = 6;
const IS_DM = document.body.classList.contains("mode-dm");
// WebSocket connection to Flask-SocketIO server
const socket = io({ transports: ["websocket"] });

socket.on("connect", () => {
  console.log("[Socket] Connected. SID:", socket.id);
  socket.emit("request_state");
});
socket.on("disconnect", (reason) => console.warn("[Socket] Disconnected:", reason));
socket.on("connect_error", (err) => console.error("[Socket] Error:", err.message));

function clamp(n, min, max) {
  n = Number(n);
  if (Number.isNaN(n)) n = min;
  return Math.max(min, Math.min(max, n));
}

function makeDefaultSlots() {
  const slots = {};
  for (let lvl = 1; lvl <= SPELL_LEVELS; lvl++) {
    slots[lvl] = { t: 0, f: 0 };
  }
  slots[1] = { t: 4, f: 4 };
  return slots;
}

function defaultState() {
  return {
    players: [
      { name: "Player 1", hp: 30, maxHp: 30, slots: makeDefaultSlots(), portrait: ""},
      { name: "Player 2", hp: 25, maxHp: 25, slots: makeDefaultSlots(), portrait: "" },
      { name: "Player 3", hp: 18, maxHp: 18, slots: makeDefaultSlots(), portrait: "" },
      { name: "Player 4", hp: 40, maxHp: 40, slots: makeDefaultSlots(), portrait: "" },
    ],
    turnIndex: 0,
    turnNote: "Status: Ready",
    portrait: "",
    background: "oldpaper.png"
  };
}

async function loadPortraitOptions() {
  try {
    const res = await fetch("/api/portraits");
    const files = await res.json();
    document.querySelectorAll(".portrait-select").forEach(sel => {
      const current = sel.value;
      sel.innerHTML = `<option value="">-- None --</option>`;
      files.forEach(f => {
        const opt = document.createElement("option");
        opt.value = f;
        opt.textContent = f;
        if (f === current) opt.selected = true;
        sel.appendChild(opt);
      });
    });
  } catch (e) {
    console.error("Could not load portraits:", e);
  }
}

/** Ensure saved state always has L1..L6 and valid numbers */
function normalizeState(s) {
  const base = defaultState();

  if (!s || !Array.isArray(s.players) || s.players.length === 0) return base;

  const out = structuredClone(base);

  out.players = s.players.slice(0, 4).map((p, idx) => {
    const n = idx + 1;
    const maxHp = clamp(p?.maxHp ?? base.players[idx].maxHp, 1, 9999);
    const hp = clamp(p?.hp ?? base.players[idx].hp, 0, maxHp);

    const slots = makeDefaultSlots();
    for (let lvl = 1; lvl <= SPELL_LEVELS; lvl++) {
      const t = clamp(p?.slots?.[lvl]?.t ?? slots[lvl].t, 0, 99);
      const f = clamp(p?.slots?.[lvl]?.f ?? slots[lvl].f, 0, t);
      slots[lvl] = { t, f };
    }

    return {
      name: (p?.name ?? `Player ${n}`) || `Player ${n}`,
      hp,
      maxHp,
      slots,
      portrait: p?.portrait || ""
    };
  });

  out.turnIndex = clamp(s.turnIndex ?? 0, 0, 3);
  out.turnNote = (s.turnNote ?? out.turnNote) || "";
  out.background = s.background || "oldpaper.png";
  return out;
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    return normalizeState(JSON.parse(raw));
  } catch {
    return defaultState();
  }
}

function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setImg(id, src) {
  const el = document.getElementById(id);
  if (!el) return;
  el.src = src || "";
  // Fall back to default portrait if the URL is broken
  el.onerror = () => { el.src = "/static/Tiefling.png"; el.onerror = null; };
}

function renderHp(i, hp, maxHp) {
  const fill = document.getElementById(`p${i}-hp-fill`);
  const text = document.getElementById(`p${i}-hp-text`);
  if (!fill || !text) return;

  const safeMax = Math.max(1, Number(maxHp) || 1);
  const safeHp = clamp(hp, 0, safeMax);
  const pct = (safeHp / safeMax) * 100;

  fill.style.width = `${pct}%`;
  text.textContent = `HP: ${safeHp} / ${safeMax}`;
}

function renderSlots(i, slots) {
  const wrap = document.getElementById(`p${i}-slots`);
  if (!wrap) return;

  wrap.innerHTML = "";

  for (let level = 1; level <= SPELL_LEVELS; level++) {
    const t = clamp(slots?.[level]?.t ?? 0, 0, 99);
    const f = clamp(slots?.[level]?.f ?? 0, 0, t);

    const row = document.createElement("div");
    row.className = "slot-row";

    const label = document.createElement("div");
    label.className = "slot-label";
    label.textContent = `L${level}`;
    row.appendChild(label);

    for (let n = 1; n <= t; n++) {
      const dot = document.createElement("span");
      dot.className = "slot" + (n <= f ? " slot--filled" : "");
      row.appendChild(dot);
    }

    wrap.appendChild(row);
  }
}

function render(state) {
  state.players.forEach((p, idx) => {
    const n = idx + 1;
    setText(`p${n}-name`, p.name || `Player ${n}`);
    renderHp(n, p.hp, p.maxHp);
    renderSlots(n, p.slots);
  });

  const current = state.players[state.turnIndex] || state.players[0];
  setText("turn-name", current?.name || "Player 1");
  setText("turn-note", state.turnNote || "");
  setImg(
  "turn-portrait",
  current?.portrait ? `/static/${current.portrait}` : "/static/Tiefling.png");
  document.body.style.backgroundImage = `url('/static/${state.background || "oldpaper.png"}')`; 
}

/* WebSocket broadcast (DM -> server -> everyone) */
let _suppressNextUpdate = false;
function broadcastState(state) {
  _suppressNextUpdate = true;
  socket.emit("state_set", state);
}


/* DM: read inputs and push state */
function wireDm(state) {
  const applyBtn = document.getElementById("dm-apply");
  const resetBtn = document.getElementById("dm-reset");
  if (!applyBtn) return;

  const hpDirty = [false, false, false, false];

  function readPlayer(n, oldPlayer) {
    const name = document.getElementById(`dm-p${n}-name`)?.value?.trim() || `Player ${n}`;
    const maxHp = clamp(document.getElementById(`dm-p${n}-max`)?.value, 1, 9999);
    const hpInput = clamp(document.getElementById(`dm-p${n}-hp`)?.value, 0, maxHp);
    const portrait = document.getElementById(`dm-p${n}-portrait`)?.value?.trim() || "";

    const slots = {};
    for (let lvl = 1; lvl <= SPELL_LEVELS; lvl++) {
      const t = clamp(document.getElementById(`dm-p${n}-l${lvl}t`)?.value, 0, 99);
      const f = clamp(document.getElementById(`dm-p${n}-l${lvl}f`)?.value, 0, t);
      slots[lvl] = { t, f };
    }

    let hp;
    if (hpDirty[n - 1]) {
      hp = hpInput;
    } else {
      hp = clamp(oldPlayer?.hp ?? hpInput, 0, maxHp);
    }

    return { name, hp, maxHp, slots, portrait };
  }

  function writeInputsFromState(s) {
    s.players.forEach((p, idx) => {
      const n = idx + 1;
      const setVal = (id, v) => {
        const el = document.getElementById(id);
        if (el) el.value = v;
      };

      setVal(`dm-p${n}-name`, p.name || "");
      setVal(`dm-p${n}-max`, p.maxHp ?? 1);
      setVal(`dm-p${n}-hp`, p.hp ?? 0);
      setVal(`dm-p${n}-portrait`, p.portrait || "");

      for (let lvl = 1; lvl <= SPELL_LEVELS; lvl++) {
        setVal(`dm-p${n}-l${lvl}t`, p.slots?.[lvl]?.t ?? 0);
        setVal(`dm-p${n}-l${lvl}f`, p.slots?.[lvl]?.f ?? 0);
      }

      hpDirty[idx] = false;
    });

    const turnSel = document.getElementById("dm-turn");
    if (turnSel) turnSel.value = String((s.turnIndex ?? 0) + 1);

    const note = document.getElementById("dm-note");
    if (note) note.value = s.turnNote || "";

    const bg = document.getElementById("dm-background");
    if (bg) bg.value = s.background || "oldpaper.png";
  }

  for (let n = 1; n <= 4; n++) {
    const hpEl = document.getElementById(`dm-p${n}-hp`);
    if (hpEl) {
      hpEl.addEventListener("input", () => {
        hpDirty[n - 1] = true;
      });
    }
  }

  writeInputsFromState(state);

  applyBtn.addEventListener("click", () => {
    const next = normalizeState(structuredClone(state));

    next.players = [1, 2, 3, 4].map((n, idx) => readPlayer(n, state.players[idx]));

    const turnVal = clamp(document.getElementById("dm-turn")?.value, 1, 4);
    next.turnIndex = turnVal - 1;

    next.turnNote = document.getElementById("dm-note")?.value?.trim() || "";
    next.background = document.getElementById("dm-background")?.value || "oldpaper.png";

    saveState(next);
    render(next);
    broadcastState(next);
    writeInputsFromState(next);
    Object.assign(state, next);
  });

  resetBtn?.addEventListener("click", () => {
    localStorage.removeItem(STORAGE_KEY);
    const fresh = defaultState();
    saveState(fresh);
    render(fresh);
    broadcastState(fresh);
    writeInputsFromState(fresh);
    Object.assign(state, fresh);
  });
}

/* WebSocket receive: full state update from server */
socket.on("state_updated", (incoming) => {
  console.log("[Socket] state_updated received");

  if (_suppressNextUpdate) {
    _suppressNextUpdate = false;
    console.log("[Socket] suppressed echo on DM tab");
    return;
  }

  const s = normalizeState(incoming);
  saveState(s);
  render(s);

  Object.assign(state, structuredClone(s));

  if (IS_DM) {
    for (let i = 0; i < s.players.length; i++) {
      const hpEl = document.getElementById(`dm-p${i + 1}-hp`);
      const maxEl = document.getElementById(`dm-p${i + 1}-max`);
      if (hpEl) hpEl.value = s.players[i].hp;
      if (maxEl) maxEl.value = s.players[i].maxHp;
    }
  }
});

/* Optional: receive HP delta events */
socket.on("hp_delta", ({ player, delta }) => {
  const s = loadState();
  const idx = clamp(player, 1, 4) - 1;
  const p = s.players[idx];

  p.hp = clamp((p.hp ?? 0) + Number(delta), 0, p.maxHp ?? 1);

  const normalized = normalizeState(s);
  saveState(normalized);
  render(normalized);
  Object.assign(state, structuredClone(normalized));

  if (IS_DM) {
    broadcastState(normalized);
  }
});

/* Optional: receive spell slot delta events */
socket.on("slot_delta", ({ player, level, delta }) => {
  const s = loadState();
  const idx = clamp(player, 1, 4) - 1;
  const lvl = clamp(level, 1, SPELL_LEVELS);
  const p = s.players[idx];

  const slot = p.slots[lvl] || { t: 0, f: 0 };
  slot.t = clamp(slot.t, 0, 99);
  slot.f = clamp((slot.f ?? 0) + Number(delta), 0, slot.t);

  p.slots[lvl] = slot;

  const normalized = normalizeState(s);
  saveState(normalized);
  render(normalized);
  Object.assign(state, structuredClone(normalized));

  if (IS_DM) {
    broadcastState(normalized);
  }
});

const state = loadState();
render(state);
wireDm(state);
loadPortraitOptions();