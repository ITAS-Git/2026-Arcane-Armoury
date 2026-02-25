/* app.js
   - Stores state in localStorage (so refresh keeps it)
   - DM broadcasts updates via BroadcastChannel to Player screen
   - Player listens and re-renders immediately
*/

const STORAGE_KEY = "arcane_armoury_state_v3"; // bump key so old broken saves don't haunt you
const CHANNEL_NAME = "arcane_armoury_channel";
const bc = new BroadcastChannel(CHANNEL_NAME);

const SPELL_LEVELS = 6;

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
  // D&D-ish default: L1 starts with 4/4, everything else 0/0
  slots[1] = { t: 4, f: 4 };
  return slots;
}

function defaultState() {
  return {
    players: [
      { name: "Player 1", hp: 30, maxHp: 30, slots: makeDefaultSlots() },
      { name: "Player 2", hp: 25, maxHp: 25, slots: makeDefaultSlots() },
      { name: "Player 3", hp: 18, maxHp: 18, slots: makeDefaultSlots() },
      { name: "Player 4", hp: 40, maxHp: 40, slots: makeDefaultSlots() },
    ],
    turnIndex: 0,
    turnNote: "Status: Ready",
    portrait: ""
  };
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

    // start with clean defaults, then overlay anything saved
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
      slots
    };
  });

  out.turnIndex = clamp(s.turnIndex ?? 0, 0, 3);
  out.turnNote = (s.turnNote ?? out.turnNote) || "";
  out.portrait = (s.portrait ?? out.portrait) || "";

  return out;
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    return normalizeState(parsed);
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

  // Always render L1..L6 in a vertical list
  for (let level = 1; level <= SPELL_LEVELS; level++) {
    const t = clamp(slots?.[level]?.t ?? 0, 0, 99);
    const f = clamp(slots?.[level]?.f ?? 0, 0, t);

    const row = document.createElement("div");
    row.className = "slot-row";

    const label = document.createElement("div");
    label.className = "slot-label";
    label.textContent = `L${level}`; // keep it simple + safe
    row.appendChild(label);

    // dots (only if total > 0)
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
  setImg("turn-portrait", state.portrait || "Tiefling.png");
}

function broadcast(state) {
  bc.postMessage({ type: "STATE", payload: state });
}

/* DM: read inputs and push state */
function wireDm(state) {
  const applyBtn = document.getElementById("dm-apply");
  const resetBtn = document.getElementById("dm-reset");
  if (!applyBtn) return; // not DM page

  function readPlayer(n) {
    const name = document.getElementById(`dm-p${n}-name`)?.value?.trim() || `Player ${n}`;
    const maxHp = clamp(document.getElementById(`dm-p${n}-max`)?.value, 1, 9999);
    const hp = clamp(document.getElementById(`dm-p${n}-hp`)?.value, 0, maxHp);

    const slots = {};
    for (let lvl = 1; lvl <= SPELL_LEVELS; lvl++) {
      const t = clamp(document.getElementById(`dm-p${n}-l${lvl}t`)?.value, 0, 99);
      const f = clamp(document.getElementById(`dm-p${n}-l${lvl}f`)?.value, 0, t);
      slots[lvl] = { t, f };
    }

    return { name, hp, maxHp, slots };
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

      for (let lvl = 1; lvl <= SPELL_LEVELS; lvl++) {
        setVal(`dm-p${n}-l${lvl}t`, p.slots?.[lvl]?.t ?? 0);
        setVal(`dm-p${n}-l${lvl}f`, p.slots?.[lvl]?.f ?? 0);
      }
    });

    const turnSel = document.getElementById("dm-turn");
    if (turnSel) turnSel.value = String((s.turnIndex ?? 0) + 1);

    const note = document.getElementById("dm-note");
    if (note) note.value = s.turnNote || "";

    const portrait = document.getElementById("dm-portrait");
    if (portrait) portrait.value = s.portrait || "";
  }

  // Populate DM inputs from saved state on load (normalized)
  writeInputsFromState(state);

  applyBtn.addEventListener("click", () => {
    const next = normalizeState(structuredClone(state));

    next.players = [1, 2, 3, 4].map(readPlayer);

    const turnVal = clamp(document.getElementById("dm-turn")?.value, 1, 4);
    next.turnIndex = turnVal - 1;

    next.turnNote = document.getElementById("dm-note")?.value?.trim() || "";
    next.portrait = document.getElementById("dm-portrait")?.value?.trim() || "";

    saveState(next);
    render(next);
    broadcast(next);

    Object.assign(state, next);
  });

  resetBtn?.addEventListener("click", () => {
    localStorage.removeItem(STORAGE_KEY);
    const fresh = defaultState();
    saveState(fresh);
    render(fresh);
    broadcast(fresh);
    writeInputsFromState(fresh);

    Object.assign(state, fresh);
  });
}

/* Player: listen for DM updates */
bc.onmessage = (ev) => {
  if (ev?.data?.type !== "STATE") return;
  const incoming = normalizeState(ev.data.payload);
  saveState(incoming);
  render(incoming);
};

const state = loadState();
render(state);
wireDm(state);