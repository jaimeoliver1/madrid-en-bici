/* The "24h of BiciMAD" film as an in-page player: same data, routes and look, plus play/pause, scrubbing and zoom. */
(() => {
  const F = window.FILM;
  const stage = document.getElementById("pl-stage"), canvas = document.getElementById("pl-canvas");
  if (!F || !stage || !canvas) return;
  const ctx = canvas.getContext("2d");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const T = k => (window.MCI ? window.MCI.t(k) : k);

  // ---------- data: trips "start(4) dur(3) from(2) to(2)" in base 36; routes "a,b:" + 2 chars per coordinate in base 64 ----------
  const S = F.stations, n = Math.floor(F.trips.length / 11), P = (a, b) => parseInt(F.trips.slice(a, b), 36);
  const st = new Float32Array(n), en = new Float32Array(n), A = new Uint16Array(n), B = new Uint16Array(n);
  const routes = new Map(), ALPH = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_", V = new Int16Array(128);
  for (let i = 0; i < 64; i++) V[ALPH.charCodeAt(i)] = i;
  for (const ln of F.routes.split("\n")) {
    const c = ln.indexOf(":"); if (c < 0) continue;
    const k = (ln.length - c - 1) >> 2, xs = new Float32Array(k), ys = new Float32Array(k), cum = new Float32Array(k);
    for (let j = 0, q = c + 1; j < k; j++, q += 4) {
      xs[j] = (V[ln.charCodeAt(q)] * 64 + V[ln.charCodeAt(q + 1)]) / 2;
      ys[j] = (V[ln.charCodeAt(q + 2)] * 64 + V[ln.charCodeAt(q + 3)]) / 2;
      cum[j] = j ? cum[j - 1] + Math.hypot(xs[j] - xs[j - 1], ys[j] - ys[j - 1]) : 0;
    }
    routes.set(ln.slice(0, c), { xs, ys, cum, len: cum[k - 1] || 1 });
  }
  const R = new Array(n), CX = new Float32Array(n), CY = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const o = i * 11; st[i] = (P(o, o + 4) - 3600) / 3600; en[i] = st[i] + P(o + 4, o + 7) / 3600; A[i] = P(o + 7, o + 9); B[i] = P(o + 9, o + 11);
    R[i] = routes.get(A[i] + "," + B[i]) || null;
    const a = S[A[i]], b = S[B[i]], dx = b[0] - a[0], dy = b[1] - a[1];
    CX[i] = (a[0] + b[0]) / 2 - dy * 0.16; CY[i] = (a[1] + b[1]) / 2 + dx * 0.16;
  }
  const seg = (r, L) => { let lo = 0, hi = r.cum.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (r.cum[m] <= L) lo = m; else hi = m; } return lo; };
  function pt(i, p) {
    const r = R[i];
    if (!r) { const a = S[A[i]], b = S[B[i]], q = 1 - p; return [q * q * a[0] + 2 * q * p * CX[i] + p * p * b[0], q * q * a[1] + 2 * q * p * CY[i] + p * p * b[1]]; }
    const L = p * r.len, j = seg(r, L), j2 = Math.min(j + 1, r.xs.length - 1), sl = r.cum[j2] - r.cum[j], f = sl > 0 ? (L - r.cum[j]) / sl : 0;
    return [r.xs[j] + (r.xs[j2] - r.xs[j]) * f, r.ys[j] + (r.ys[j2] - r.ys[j]) * f];
  }
  function whole(i) {
    const r = R[i];
    if (!r) { const a = S[A[i]], b = S[B[i]]; ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo(CX[i], CY[i], b[0], b[1]); return; }
    ctx.moveTo(r.xs[0], r.ys[0]); for (let j = 1; j < r.xs.length; j++) ctx.lineTo(r.xs[j], r.ys[j]);
  }
  function sub(i, p0, p1) {
    const a = pt(i, p0), b = pt(i, p1), r = R[i];
    ctx.moveTo(a[0], a[1]);
    if (r) { const j0 = seg(r, p0 * r.len) + 1, j1 = seg(r, p1 * r.len); for (let j = j0; j <= j1; j++) ctx.lineTo(r.xs[j], r.ys[j]); }
    ctx.lineTo(b[0], b[1]);
  }
  const districts = new Path2D(F.districts);
  const xs = S.map(s => s[0]), ys = S.map(s => s[1]);
  const X0 = Math.min(...xs) - 40, X1 = Math.max(...xs) + 40, Y0 = Math.min(...ys) - 30, Y1 = Math.max(...ys) + 30;

  // ---------- view, sizing and zoom ----------
  let W = 0, H = 0, dpr = 1, s0 = 1, ox = 0, oy = 0, tz = d3.zoomIdentity, col = {};
  function readColors() {
    const cs = getComputedStyle(document.documentElement), g = k => cs.getPropertyValue(k).trim();
    col = { main: g("--sky"), accent: g("--brick"), card: g("--card"), map: g("--map"), edge: g("--map-edge"), ink: g("--ink") };
  }
  function size() {
    W = stage.clientWidth; H = Math.max(380, Math.min(720, W * (Y1 - Y0) / (X1 - X0)));
    stage.style.height = H + "px";
    dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    s0 = Math.min(W / (X1 - X0), H / (Y1 - Y0)); ox = (W - (X1 - X0) * s0) / 2 - X0 * s0; oy = (H - (Y1 - Y0) * s0) / 2 - Y0 * s0;
    zoom.extent([[0, 0], [W, H]]).translateExtent([[0, 0], [W, H]]);
  }
  const zoom = d3.zoom().scaleExtent([1, 12])
    .filter(ev => ev.type === "wheel" ? (ev.ctrlKey || ev.metaKey) : ev.type === "touchstart" ? ev.touches.length > 1 : !ev.button)
    .on("zoom", ev => { tz = ev.transform; if (!playing) draw(); });
  d3.select(canvas).call(zoom).on("dblclick.zoom", null);
  canvas.style.touchAction = "pan-y";
  let hintT = null;
  canvas.addEventListener("wheel", ev => {
    if (ev.ctrlKey || ev.metaKey) return;
    let h = stage.querySelector(".zoomhint"); if (!h) { h = document.createElement("div"); h.className = "zoomhint"; stage.append(h); }
    h.textContent = T("zoom_hint"); h.hidden = false; clearTimeout(hintT); hintT = setTimeout(() => { h.hidden = true; }, 1400);
  }, { passive: true });
  const ui = document.createElement("div"); ui.className = "zoomui";
  [["+", "zoom_in", () => d3.select(canvas).transition().duration(350).call(zoom.scaleBy, 1.8)], ["−", "zoom_out", () => d3.select(canvas).transition().duration(350).call(zoom.scaleBy, 1 / 1.8)],
   ["⟲", "zoom_reset", () => d3.select(canvas).transition().duration(450).call(zoom.transform, d3.zoomIdentity)]].forEach(([s, k, f]) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = s; b.dataset.k = k; b.addEventListener("click", f); ui.append(b);
  });
  stage.append(ui);

  // ---------- HUD ----------
  const clock = document.getElementById("pl-clock"), count = document.getElementById("pl-count"), slider = document.getElementById("pl-time");
  const playBtn = document.getElementById("pl-play"), speedBtn = document.getElementById("pl-speed"), barsBox = document.getElementById("pl-bars");
  let bars = [];
  function buildBars() {
    barsBox.replaceChildren();
    const w = Math.max(220, barsBox.clientWidth), h = 86, mx = Math.max(...F.hourly), slot = w / 24, bw = Math.max(3, slot - 3);
    const svg = d3.select(barsBox).append("svg").attr("viewBox", `0 0 ${w} ${h + 18}`).attr("width", w).attr("height", h + 18);
    bars = F.hourly.map((v, i) => {
      const hh = Math.max(3, v / mx * h), x = i * slot + (slot - bw) / 2;
      svg.append("rect").attr("x", x).attr("y", h - hh).attr("width", bw).attr("height", hh).attr("rx", 2).attr("fill", col.map);
      const r = svg.append("rect").attr("x", x).attr("width", bw).attr("rx", 2);
      return { r, hh };
    });
    [0, 6, 12, 18].forEach(v => svg.append("text").attr("x", v * slot + slot / 2).attr("y", h + 14).attr("text-anchor", "middle").text(String(v).padStart(2, "0") + "h"));
    svg.append("title").text(T("pl_hour_trips"));
  }

  // ---------- drawing ----------
  let Hh = 8.5, playing = false, speed = 1, last = 0, lastClock = "";
  function draw() {
    const k = tz.k * s0, px = 1 / k;
    ctx.setTransform(dpr * k, 0, 0, dpr * k, dpr * (tz.x + tz.k * ox), dpr * (tz.y + tz.k * oy));
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = col.card; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore();
    ctx.fillStyle = col.map; ctx.fill(districts); ctx.strokeStyle = col.edge; ctx.lineWidth = 1.2 * px; ctx.stroke(districts);
    ctx.fillStyle = col.main; ctx.globalAlpha = 0.28; ctx.beginPath();
    for (const s of S) { ctx.moveTo(s[0] + 2.4 * px, s[1]); ctx.arc(s[0], s[1], 2.4 * px, 0, Math.PI * 2); }
    ctx.fill();
    ctx.lineCap = "round"; ctx.lineJoin = "round";
    const lv = [[], [], []];
    for (let i = 0; i < n; i++) {
      const s = st[i], e = en[i];
      if (Hh < s - 0.15 || Hh > e + 0.85) continue;
      const w = Hh <= e ? 1 : 1 - (Hh - e) / 0.85;
      lv[w > 0.66 ? 0 : w > 0.33 ? 1 : 2].push(i);
    }
    ctx.strokeStyle = col.main; ctx.lineWidth = 2.2 * px;
    [0.085, 0.05, 0.025].forEach((a, j) => { if (!lv[j].length) return; ctx.globalAlpha = a; ctx.beginPath(); for (const i of lv[j]) whole(i); ctx.stroke(); });
    let moving = 0; const heads = [], rings = [];
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const s = st[i], e = en[i];
      if (Hh >= s && Hh - s < 0.22) rings.push(i, (Hh - s) / 0.22);
      if (Hh < s || Hh >= e) continue;
      moving++;
      const p = (Hh - s) / (e - s), q = p * p * (3 - 2 * p), p0 = Math.max(0, p - 0.16), q0 = p0 * p0 * (3 - 2 * p0);
      sub(i, q0, q); const b = pt(i, q); heads.push(b[0], b[1]);
    }
    ctx.globalAlpha = 0.45; ctx.lineWidth = 2.6 * px; ctx.stroke();
    ctx.strokeStyle = col.accent; ctx.lineWidth = 1.2 * px;
    for (let j = 0; j < rings.length; j += 2) {
      const i = rings[j], p = rings[j + 1], a = S[A[i]];
      ctx.globalAlpha = 0.55 * (1 - p); ctx.beginPath(); ctx.arc(a[0], a[1], (2 + 6 * (1 - Math.pow(1 - p, 3))) * px, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.globalAlpha = 1; ctx.fillStyle = col.main; ctx.strokeStyle = col.card; ctx.lineWidth = 1.2 * px; ctx.beginPath();
    for (let j = 0; j < heads.length; j += 2) { ctx.moveTo(heads[j] + 3.4 * px, heads[j + 1]); ctx.arc(heads[j], heads[j + 1], 3.4 * px, 0, Math.PI * 2); }
    ctx.fill(); ctx.stroke();
    // HUD
    const mins = Math.min(1439, Math.floor(Hh * 60)), txt = String(Math.floor(mins / 60)).padStart(2, "0") + ":" + String(mins % 60).padStart(2, "0");
    if (txt !== lastClock) { clock.textContent = txt; lastClock = txt; slider.value = mins; }
    count.textContent = window.MCI ? window.MCI.nf(moving) : moving;
    const cur = Math.floor(Hh);
    bars.forEach((b, i) => { const f = i < cur ? 1 : i > cur ? 0 : Hh - cur; b.r.attr("y", 86 - b.hh * f).attr("height", b.hh * f).attr("fill", i === cur ? col.accent : col.main); });
  }
  function frame(ts) {
    if (!playing) return;
    const dt = last ? Math.min(0.1, (ts - last) / 1000) : 0; last = ts;
    Hh += dt * speed; if (Hh >= 24) Hh -= 24;
    draw(); requestAnimationFrame(frame);
  }
  const ICON = { play: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M3 1.5 L12 7 L3 12.5 Z" fill="currentColor"/></svg>', pause: '<svg viewBox="0 0 14 14" aria-hidden="true"><rect x="2.5" y="1.5" width="3" height="11" rx="1" fill="currentColor"/><rect x="8.5" y="1.5" width="3" height="11" rx="1" fill="currentColor"/></svg>' };
  function labelPlay() { playBtn.innerHTML = (playing ? ICON.pause : ICON.play) + `<span>${T(playing ? "pl_pause" : "pl_play")}</span>`; playBtn.setAttribute("aria-pressed", String(playing)); }
  function setPlaying(v) { if (playing === v) return; playing = v; last = 0; labelPlay(); if (v) requestAnimationFrame(frame); }
  playBtn.addEventListener("click", () => { userPaused = playing; setPlaying(!playing); });
  speedBtn.addEventListener("click", () => { speed = speed === 1 ? 2 : speed === 2 ? 0.5 : 1; speedBtn.textContent = speed === 0.5 ? "½×" : speed + "×"; });
  slider.addEventListener("input", () => { Hh = +slider.value / 60; if (!playing) draw(); });
  let userPaused = false;
  if ("IntersectionObserver" in window) new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { if (!reduce && !userPaused) setPlaying(true); } else setPlaying(false);
  }), { threshold: 0.3 }).observe(stage);

  function setup() { readColors(); size(); buildBars(); labelPlay(); ui.querySelectorAll("button").forEach(b => { b.title = T(b.dataset.k); b.setAttribute("aria-label", T(b.dataset.k)); }); draw(); }
  window.addEventListener("mc-render", setup);
  matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", setup);
  setup();
})();
