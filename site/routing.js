/* Madrid en bici: the route planner (Dijkstra in the browser on site/route-graph.json) and the proposed
   protected-lane plan (window.MC.plan). Method: docs/ROUTING.md and docs/METHOD_LANES.md. */
(() => {
  const M = window.MC;
  const DOCS = "https://github.com/jaimeoliver1/madrid-en-bici/blob/main/docs/";
  const S = {
    es: {
      rt_k: "Tu ruta", rt_h: "¿Por dónde voy en bici?",
      rt_lede: "Toca el mapa para marcar la <b>salida</b> y la <b>llegada</b>. Calculamos al momento la ruta más cómoda con el mismo modelo que usamos para analizar la red, y tú decides cuánto te importa cada cosa.",
      loading: "Cargando la red ciclista de Madrid (unos 2 MB)…", load_err: "No se ha podido cargar la red. Recarga la página para intentarlo de nuevo.",
      pick_a: "Toca el mapa para poner la salida (A)", pick_b: "Toca el mapa para poner la llegada (B)", drag: "También puedes arrastrar A y B por el mapa.",
      chip_a: "Salida", chip_b: "Llegada", chip_set: "Toca el mapa", chip_near: "Junto a {n}", chip_here: "Punto fijado",
      from: "Salida", to: "Llegada", swap: "Invertir", clear: "Borrar", example: "Ejemplo: Atocha → Bernabéu",
      w_h: "¿Qué te importa más?", w_t: "Evitar calles con muchos coches", w_p: "Preferir carriles protegidos", w_s: "Evitar cuestas", w_a: "Evitar sitios con accidentes",
      w_def: "Valores publicados", w_note: "×1 = cómo eligen la ruta los ciclistas según Broach, Dill y Gliebe (2012). Accidentes: ×1 = el riesgo registrado valorado en euros frente al valor del tiempo.",
      plan_on: "Con los carriles protegidos propuestos", plan_note: "Añade los 21 km del plan que proponemos más abajo.",
      best: "Ruta recomendada", short: "Ruta más corta", km: "km", min: "min", prot: "por carril protegido", busy: "por calles con mucho tráfico",
      climb: "de subida", acc: "accidentes registrados en el camino (2019–2026)", via: "Por", same: "Coinciden: la ruta más corta ya es la recomendada.",
      vs: "{d} km más que la más corta · {p} por carril protegido (la más corta: {q}).", vs2: "Igual de larga que la más corta, por calles más cómodas.",
      lg_route: "Ruta recomendada", lg_short: "Más corta", lg_lane: "Carril separado actual", lg_plan: "Carril propuesto",
      rt_more: "Cómo funciona", far: "Ese punto está fuera de la zona con datos.",
      // plan
      pl_h: "¿Dónde poner los próximos carriles protegidos?",
      pl_lede: "Calculamos qué calles conviene proteger primero: para cada opción rehacemos la ruta de todos los viajes y sumamos en euros el tiempo y la comodidad que ganan los ciclistas y los heridos que se evitan, frente a lo que cuesta construirla. Todas las cifras vienen de fuentes publicadas o de datos de Madrid.",
      pl_km: "km de carril protegido nuevo", pl_cost: "de inversión", pl_bcr: "euros de beneficio por cada euro", pl_net: "de beneficio neto al año",
      pl_map: "El plan, por orden de construcción", pl_map_n: "Primero lo que más rinde por euro. El eje Atocha – Prado – Recoletos – Castellana se completa con los primeros 10 millones.",
      ph1: "Primeros 5 M€", ph2: "De 5 a 10 M€", ph3: "De 10 a 20 M€", lane_now: "Carril separado que ya existe",
      pl_list: "Los 12 primeros pasos", c_step: "#", c_what: "Tramo", c_cost: "Coste", c_bcr: "€/€", c_trips: "Ciclistas/día",
      pl_cmp: "Dos formas de crecer la red", pl_cmp_n: "Con el mismo presupuesto, empezar por lo que más rinde y ampliarlo con conexiones da más que empezar por el gran eje y añadir otros ejes largos. Los dos acaban incluyendo el eje completo.",
      bf: "Lo que más rinde primero", af: "Primero el eje Atocha – Castellana", c_ben: "Beneficio/año", c_net: "Neto/año",
      pl_caveat: "No cuenta a la gente nueva que se animaría a ir en bici, ni comprueba si cada calle tiene sitio para el carril. Los viajes son de BiciMAD (2023) escalados a todos los ciclistas con los contadores.",
      pl_more: "Método completo y fuentes", axis: "Eje Atocha – Prado – Recoletos – Castellana",
    },
    en: {
      rt_k: "Your route", rt_h: "Which way should I ride?",
      rt_lede: "Tap the map to set your <b>start</b> and <b>finish</b>. We work out the most comfortable route on the spot, with the same model we used to analyse the network, and you decide how much each thing matters to you.",
      loading: "Loading Madrid's bike network (about 2 MB)…", load_err: "Couldn't load the network. Reload the page to try again.",
      pick_a: "Tap the map to set the start (A)", pick_b: "Tap the map to set the finish (B)", drag: "You can also drag A and B around the map.",
      chip_a: "Start", chip_b: "Finish", chip_set: "Tap the map", chip_near: "Near {n}", chip_here: "Point set",
      from: "Start", to: "Finish", swap: "Swap", clear: "Clear", example: "Example: Atocha → Bernabéu",
      w_h: "What matters most to you?", w_t: "Avoid streets with heavy traffic", w_p: "Prefer protected lanes", w_s: "Avoid hills", w_a: "Avoid places with accidents",
      w_def: "Published values", w_note: "×1 = how cyclists choose routes according to Broach, Dill & Gliebe (2012). Accidents: ×1 = recorded risk valued in euros against the value of time.",
      plan_on: "With the proposed protected lanes", plan_note: "Adds the 21 km of the plan we propose further down.",
      best: "Recommended route", short: "Shortest route", km: "km", min: "min", prot: "on protected lanes", busy: "on streets with heavy traffic",
      climb: "uphill", acc: "recorded accidents along the way (2019–2026)", via: "Via", same: "They match: the shortest route is already the recommended one.",
      vs: "{d} km longer than the shortest · {p} on protected lanes (shortest: {q}).", vs2: "As long as the shortest, on more comfortable streets.",
      lg_route: "Recommended route", lg_short: "Shortest", lg_lane: "Existing separated lane", lg_plan: "Proposed lane",
      rt_more: "How it works", far: "That point is outside the area we have data for.",
      pl_h: "Where should the next protected lanes go?",
      pl_lede: "We worked out which streets to protect first: for each option we re-route every trip and add up, in euros, the time and comfort cyclists gain and the injuries avoided, against what it costs to build. Every number comes from a published source or from Madrid's data.",
      pl_km: "km of new protected lane", pl_cost: "of investment", pl_bcr: "euros back for every euro", pl_net: "net benefit a year",
      pl_map: "The plan, in build order", pl_map_n: "Best value per euro first. The Atocha – Prado – Recoletos – Castellana axis is complete within the first 10 million.",
      ph1: "First €5M", ph2: "€5–10M", ph3: "€10–20M", lane_now: "Existing separated lane",
      pl_list: "The first 12 steps", c_step: "#", c_what: "Stretch", c_cost: "Cost", c_bcr: "€/€", c_trips: "Cyclists/day",
      pl_cmp: "Two ways to grow the network", pl_cmp_n: "With the same budget, starting with the best value and extending it with connections beats starting with the big axis and adding other long axes. Both end up with the full axis.",
      bf: "Best value first", af: "Atocha – Castellana axis first", c_ben: "Benefit/yr", c_net: "Net/yr",
      pl_caveat: "It doesn't count new people who would start cycling, or check whether each street has room for a lane. Trips are BiciMAD's (2023), scaled to all cyclists with the bike counters.",
      pl_more: "Full method and sources", axis: "Atocha – Prado – Recoletos – Castellana axis",
    },
  };
  let I = null;  // window.MCI, set on each render
  const tt = (k, v = {}) => (S[I.lang()][k] || S.es[k] || k).replace(/\{(\w+)\}/g, (_, x) => v[x] ?? "");
  const eur = v => I.lang() === "es" ? I.n1(v / 1e6) + " M€" : "€" + I.n1(v / 1e6) + "M";

  // ================= the proposed plan =================
  function planSection() {
    const P = M.plan; if (!P) return;
    const best = P.summary[P.summary.headline], other = P.summary[P.summary.headline === "bestfirst" ? "axisfirst" : "bestfirst"];
    document.getElementById("pl-h").textContent = tt("pl_h");
    document.getElementById("pl-lede").textContent = tt("pl_lede");
    const k = document.getElementById("pl-kpis"); k.replaceChildren();
    [[I.n1(best.km), tt("pl_km")], [eur(best.build_eur), tt("pl_cost")], [I.n1(best.bcr), tt("pl_bcr")], [eur(best.net_benefit_eur_yr), tt("pl_net")]].forEach(([v, l]) => {
      const d = I.el("div", "bign"); d.append(I.el("span", "v", v), I.el("span", "l", l)); k.append(d);
    });
    document.getElementById("pl-map-h").textContent = tt("pl_map"); document.getElementById("pl-map-n").textContent = tt("pl_map_n");
    const col = c => c <= 5e6 ? I.css("--bad") : c <= 10e6 ? I.css("--brick") : I.css("--mid");
    const lg = document.getElementById("lg-plan"); lg.replaceChildren();
    [[I.css("--bad"), "ph1"], [I.css("--brick"), "ph2"], [I.css("--mid"), "ph3"], [I.css("--lane"), "lane_now"]].forEach(([c, key]) => {
      const s = I.el("span"); const i = I.el("i", "sw"); i.style.background = c; s.append(i, document.createTextNode(tt(key))); lg.append(s);
    });
    const box = document.getElementById("ch-plan"), { g, F } = I.mapBase(box, 600);
    g.selectAll("path.b").data(M.barrios).join("path").attr("class", "b").attr("d", b => b[5].split("|").map(r => F.path(r) + "Z").join(""))
      .attr("fill", I.css("--grey-map")).attr("stroke", I.css("--card")).attr("stroke-width", 0.8);
    I.context(g, F);
    g.selectAll("path.ln").data(M.lanes.filter(l => l[0] === "x")).join("path").attr("class", "ln").attr("d", l => F.path(l[1]))
      .attr("fill", "none").attr("stroke", I.css("--lane")).attr("stroke-width", 1.6).attr("stroke-opacity", 0.55);
    const tp = I.tip(box);
    const steps = P.steps.slice().reverse();
    g.selectAll("path.pl").data(steps.flatMap(s => s[10].split("|").map(p => [s, p]))).join("path").attr("class", "pl").attr("d", ([, p]) => F.path(p))
      .attr("fill", "none").attr("stroke", ([s]) => col(s[7])).attr("stroke-width", ([s]) => s[7] <= 5e6 ? 4.5 : 3.5).attr("stroke-linecap", "round")
      .on("pointermove", (ev, [s]) => { const [a, b] = d3.pointer(ev, box); tp.show(a, b, `${s[0]}. ${label(s[1])}`, [`${I.n1(s[3])} km · ${eur(s[4])} · ${I.n1(s[6])} €/€`, `${I.nf(s[8])} → ${I.nf(s[9])} ${tt("c_trips").toLowerCase()}`]); })
      .on("pointerleave", () => tp.hide());
    I.places(g, F);
    // first steps
    const L = document.getElementById("pl-list"); L.replaceChildren(I.el("h3", null, tt("pl_list")));
    const tb = I.el("table", "freshtab"), hr = I.el("tr");
    ["c_step", "c_what", "c_cost", "c_bcr", "c_trips"].forEach(c => hr.append(I.el("th", null, tt(c))));
    const th = I.el("thead"); th.append(hr); const body = I.el("tbody");
    P.steps.slice(0, 12).forEach(s => {
      const tr = I.el("tr"); const sw = I.el("i", "dot"); sw.style.background = col(s[7]); sw.style.marginRight = "6px";
      const td = I.el("td"); td.append(sw, document.createTextNode(label(s[1])));
      tr.append(I.el("td", null, s[0]), td, I.el("td", null, eur(s[4])), I.el("td", null, I.n1(s[6])), I.el("td", null, `${I.nf(s[8])} → ${I.nf(s[9])}`)); body.append(tr);
    });
    tb.append(th, body); L.append(tb);
    // two plans
    const C = document.getElementById("pl-cmp"); C.replaceChildren(I.el("h3", null, tt("pl_cmp")), I.el("p", "note", tt("pl_cmp_n")));
    const t2 = I.el("table", "freshtab"), h2 = I.el("tr");
    ["", "km", "c_cost", "c_ben", "c_net", "c_bcr"].forEach(c => h2.append(I.el("th", null, c && c !== "km" ? tt(c) : c)));
    const t2h = I.el("thead"); t2h.append(h2); const t2b = I.el("tbody");
    [["bestfirst", "bf"], ["axisfirst", "af"]].forEach(([key, lab]) => {
      const r = P.summary[key], tr = I.el("tr");
      tr.append(I.el("td", null, tt(lab) + (P.summary.headline === key ? " ✓" : "")), I.el("td", null, I.n1(r.km)), I.el("td", null, eur(r.build_eur)),
        I.el("td", null, eur(r.benefit_eur_yr)), I.el("td", null, eur(r.net_benefit_eur_yr)), I.el("td", null, I.n1(r.bcr)));
      t2b.append(tr);
    });
    t2.append(t2h, t2b); C.append(t2);
    const n = document.getElementById("pl-caveat"); n.replaceChildren(document.createTextNode(tt("pl_caveat") + " "));
    const a = I.el("a", null, tt("pl_more")); a.href = DOCS + "METHOD_LANES.md"; a.target = "_blank"; a.rel = "noopener"; n.append(a);
  }
  const label = s => s.startsWith("Atocha - Prado") ? tt("axis") : s.replace(" (whole street)", I.lang() === "es" ? " (calle entera)" : " (whole street)");

  // ================= the route planner =================
  const RT = { G: null, loading: false, a: null, b: null, mode: "a", w: { t: 1, p: 1, s: 1, a: 0 }, plan: false };
  let mapRef = null;

  function load() {
    if (RT.G || RT.loading) return;
    RT.loading = true; status(tt("loading"));
    fetch("route-graph.json").then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(j => {
      RT.G = build(j); RT.loading = false;
      if (RT.a == null) example(); else update();
    }).catch(() => { RT.loading = false; status(tt("load_err")); });
  }
  function build(j) {
    const F = j.fields, K = F.length, ix = Object.fromEntries(F.map((f, i) => [f, i]));
    const n = j.nodes.length / 2, lon = new Float64Array(n), lat = new Float64Array(n);
    for (let i = 0; i < n; i++) { lon[i] = j.nodes[2 * i] / 1e5; lat[i] = j.nodes[2 * i + 1] / 1e5; }
    const E = new Float64Array(j.edges), m = E.length / K;
    // arcs: each link one or both ways, plus a contraflow arc that only exists with the plan switched on
    const au = [], av = [], ae = [], ar = [], aplan = [];
    for (let e = 0; e < m; e++) {
      const o = e * K, a = E[o + ix.a], b = E[o + ix.b], dir = E[o + ix.dir];
      const f = dir & 1, bk = dir & 2, pr = dir & 4;
      if (f) { au.push(a); av.push(b); ae.push(e); ar.push(0); aplan.push(0); }
      if (bk) { au.push(b); av.push(a); ae.push(e); ar.push(1); aplan.push(0); }
      if (pr && !f) { au.push(a); av.push(b); ae.push(e); ar.push(0); aplan.push(1); }
      if (pr && !bk) { au.push(b); av.push(a); ae.push(e); ar.push(1); aplan.push(1); }
    }
    const na = au.length, start = new Int32Array(n + 1);
    for (const u of au) start[u + 1]++;
    for (let i = 0; i < n; i++) start[i + 1] += start[i];
    const pos = start.slice(0, n), to = new Int32Array(na), from = new Int32Array(na), edge = new Int32Array(na), rev = new Uint8Array(na), plan = new Uint8Array(na);
    for (let k = 0; k < na; k++) { const p = pos[au[k]]++; to[p] = av[k]; from[p] = au[k]; edge[p] = ae[k]; rev[p] = ar[k]; plan[p] = aplan[k]; }
    return { n, lon, lat, E, K, ix, start, to, from, edge, rev, plan, geom: j.geom, names: j.names, P: j.params, cost: new Float64Array(na), len: new Float64Array(na) };
  }
  // perceived length of every arc in metres, for the current weights (same model as 15_lane_network.py)
  function weigh(G) {
    const { E, K, ix, P } = G, w = RT.w, k1 = P.traffic[0], k2 = P.traffic[1], k3 = P.traffic[2], s1 = P.slope[0], s2 = P.slope[1], s3 = P.slope[2];
    const perKmEur = P.vot_eur_h / P.speed_kmh, accM = w.a / perKmEur;  // 1 euro of expected injury cost = 1/perKmEur km
    for (let p = 0; p < G.to.length; p++) {
      const o = G.edge[p] * K, back = G.rev[p], L = E[o + ix.L];
      G.len[p] = G.plan[p] && !RT.plan ? Infinity : L;
      if (G.plan[p] && !RT.plan) { G.cost[p] = Infinity; continue; }
      let traffic = k1 * E[o + ix.T1] + k2 * E[o + ix.T2] + k3 * E[o + ix.T3], walk = E[o + ix.W], prot = E[o + ix.S], inj = E[o + ix.I] / 1000;
      if (RT.plan) {
        traffic -= k1 * E[o + ix.PT1] + k2 * E[o + ix.PT2] + k3 * E[o + ix.PT3]; walk -= E[o + ix.PW]; prot += E[o + ix.P];
        inj -= (1 - P.cmf) * E[o + ix.IP] / 1000;
      }
      const up = back ? s1 * E[o + ix.U1b] + s2 * E[o + ix.U2b] + s3 * E[o + ix.U3b] : s1 * E[o + ix.U1f] + s2 * E[o + ix.U2f] + s3 * E[o + ix.U3f];
      const c = L + walk + w.t * traffic + w.p * P.path * prot + w.s * up + accM * inj * 1000;
      G.cost[p] = Math.max(c, 0.05 * L);
    }
  }
  function dijkstra(G, src, dst, W) {
    const n = G.n, dist = new Float64Array(n).fill(Infinity), prev = new Int32Array(n).fill(-1);
    const heap = [], hn = [];  // binary heap of (dist, node)
    const push = (d, v) => { heap.push(d); hn.push(v); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p] <= heap[i]) break; [heap[p], heap[i]] = [heap[i], heap[p]]; [hn[p], hn[i]] = [hn[i], hn[p]]; i = p; } };
    const pop = () => { const d = heap[0], v = hn[0], ld = heap.pop(), lv = hn.pop(); if (heap.length) { heap[0] = ld; hn[0] = lv; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < heap.length && heap[l] < heap[m]) m = l; if (r < heap.length && heap[r] < heap[m]) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; [hn[m], hn[i]] = [hn[i], hn[m]]; i = m; } } return [d, v]; };
    dist[src] = 0; push(0, src);
    while (heap.length) {
      const [d, u] = pop();
      if (d > dist[u]) continue;
      if (u === dst) break;
      for (let p = G.start[u]; p < G.start[u + 1]; p++) {
        const c = W[p]; if (c === Infinity) continue;
        const nd = d + c, v = G.to[p];
        if (nd < dist[v]) { dist[v] = nd; prev[v] = p; push(nd, v); }
      }
    }
    if (prev[dst] < 0 && src !== dst) return null;
    const arcs = []; let v = dst;
    while (v !== src) { const p = prev[v]; arcs.push(p); v = G.from[p]; }
    return arcs.reverse();
  }
  function stats(G, arcs) {
    const { E, K, ix } = G; let L = 0, prot = 0, busy = 0, climb = 0, acc = 0; const nm = new Map();
    for (const p of arcs) {
      const o = G.edge[p] * K, l = E[o + ix.L]; L += l;
      let pr = E[o + ix.S], bz = E[o + ix.T1] + E[o + ix.T2] + E[o + ix.T3];
      if (RT.plan) { pr += E[o + ix.P]; bz -= E[o + ix.PT1] + E[o + ix.PT2] + E[o + ix.PT3]; }
      prot += pr; busy += bz; climb += G.rev[p] ? E[o + ix.Gb] : E[o + ix.Gf]; acc += E[o + ix.A];
      const name = G.names[E[o + ix.name]]; if (name) nm.set(name, (nm.get(name) || 0) + l);
    }
    const via = [...nm.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3).map(d => d[0]);
    return { L, prot: prot / Math.max(L, 1), busy: busy / Math.max(L, 1), climb, acc, via, min: L / 1000 / G.P.speed_kmh * 60 };
  }
  function nearest(G, lon, lat) {
    const k = Math.cos(40.43 * Math.PI / 180); let best = -1, bd = Infinity;
    for (let i = 0; i < G.n; i++) { if (G.start[i + 1] === G.start[i]) continue; const dx = (G.lon[i] - lon) * k, dy = G.lat[i] - lat, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = i; } }
    return Math.sqrt(bd) * 111.2 > 0.4 ? -1 : best;
  }
  function edgeCoords(G, e) {
    const f = G.geom[e], out = []; let x = f[0], y = f[1]; out.push([x / 1e5, y / 1e5]);
    for (let i = 2; i < f.length; i += 2) { x += f[i]; y += f[i + 1]; out.push([x / 1e5, y / 1e5]); }
    return out;
  }
  function example() {
    const G = RT.G; RT.a = nearest(G, -3.6905, 40.4075); RT.b = nearest(G, -3.6890, 40.4520); RT.mode = "b"; update(true);
  }
  function status(s) { const e = document.getElementById("rt-status"); if (e) e.textContent = s; }

  function plannerUI() {
    document.getElementById("rt-k").textContent = tt("rt_k");
    document.getElementById("rt-h").textContent = tt("rt_h");
    document.getElementById("rt-lede").innerHTML = tt("rt_lede");
    const c = document.getElementById("rt-controls"); c.replaceChildren();
    const st = I.el("p", "rt-status"); st.id = "rt-status"; c.append(st);
    // which point the next tap on the map sets
    const chips = I.el("div", "chips"); chips.id = "rt-chips";
    [["a", "A", "--good"], ["b", "B", "--bad"]].forEach(([k, lab, col]) => {
      const b = I.el("button", "chip"); b.type = "button"; b.dataset.k = k;
      const i = I.el("i", null, lab); i.style.background = I.css(col);
      const txt = I.el("span"); txt.append(document.createTextNode(tt("chip_" + k)), I.el("small"));
      b.append(i, txt); b.addEventListener("click", () => { RT.mode = k; chipsUpdate(); status(tt(k === "a" ? "pick_a" : "pick_b")); });
      chips.append(b);
    });
    c.append(chips);
    const bt = I.el("div", "controls");
    [["swap", () => { [RT.a, RT.b] = [RT.b, RT.a]; update(); }], ["clear", () => { RT.a = RT.b = null; RT.mode = "a"; update(); }], ["example", () => RT.G && example()]].forEach(([k, f]) => {
      const b = I.el("button", "btn ghost", tt(k)); b.type = "button"; b.addEventListener("click", f); bt.append(b);
    });
    c.append(bt, I.el("h3", null, tt("w_h")));
    [["t", "w_t"], ["p", "w_p"], ["s", "w_s"], ["a", "w_a"]].forEach(([k, l]) => {
      const row = I.el("label", "slider"), top = I.el("span", "sl-top"), val = I.el("b", null, "×" + I.n1(RT.w[k]));
      top.append(I.el("span", null, tt(l)), val);
      const inp = document.createElement("input"); inp.type = "range"; inp.min = 0; inp.max = 3; inp.step = 0.25; inp.value = RT.w[k];
      inp.addEventListener("input", () => { RT.w[k] = +inp.value; val.textContent = "×" + I.n1(RT.w[k]); schedule(); });
      row.append(top, inp); c.append(row);
    });
    const def = I.el("button", "linkbtn", tt("w_def")); def.type = "button";
    def.addEventListener("click", () => { RT.w = { t: 1, p: 1, s: 1, a: 0 }; plannerUI(); update(); });
    c.append(def, I.el("p", "note", tt("w_note")));
    const tg = I.el("label", "toggle"), cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = RT.plan;
    cb.addEventListener("change", () => { RT.plan = cb.checked; update(); });
    tg.append(cb, I.el("span", null, tt("plan_on"))); c.append(tg, I.el("p", "note", tt("plan_note")));
    const res = I.el("div", "rt-results"); res.id = "rt-results"; c.append(res);
    const more = I.el("p", "note"), a = I.el("a", null, tt("rt_more")); a.href = DOCS + "ROUTING.md"; a.target = "_blank"; a.rel = "noopener"; more.append(a); c.append(more);
    const lg = document.getElementById("lg-route"); lg.replaceChildren();
    [[I.css("--sky"), "lg_route", ""], [I.css("--muted"), "lg_short", "dash"], [I.css("--lane"), "lg_lane", ""], [I.css("--brick"), "lg_plan", "dash"]].forEach(([col, key, cls]) => {
      const s = I.el("span"), i = I.el("i", "sw"); i.style.background = cls ? `repeating-linear-gradient(90deg, ${col} 0 5px, transparent 5px 9px)` : col;
      s.append(i, document.createTextNode(tt(key))); lg.append(s);
    });
    drawMap();
  }
  let pend = 0;
  function schedule() { cancelAnimationFrame(pend); pend = requestAnimationFrame(update); }

  function drawMap() {
    const box = document.getElementById("ch-route"); if (!box) return;
    const { svg, g, F, W } = I.mapBase(box, 620);
    g.selectAll("path.b").data(M.barrios).join("path").attr("class", "b").attr("d", b => b[5].split("|").map(r => F.path(r) + "Z").join(""))
      .attr("fill", I.css("--grey-map")).attr("stroke", I.css("--card")).attr("stroke-width", 0.8);
    I.context(g, F);
    g.selectAll("path.ln").data(M.lanes.filter(l => l[0] === "x")).join("path").attr("class", "ln").attr("d", l => F.path(l[1]))
      .attr("fill", "none").attr("stroke", I.css("--lane")).attr("stroke-width", 1.4).attr("stroke-opacity", 0.5);
    const gp = g.append("g").attr("class", "plan"), gr = g.append("g").attr("class", "routes"), gm = g.append("g").attr("class", "marks");
    I.places(g, F);
    mapRef = { F, gp, gr, gm, svg, W, H: F.h };
    svg.on("click", ev => {
      if (!RT.G) return;
      const [x, y] = d3.pointer(ev, g.node()), [lon, lat] = F.inv(x, y), v = nearest(RT.G, lon, lat);
      if (v < 0) { status(tt("far")); return; }
      RT[RT.mode] = v;
      if (RT.mode === "a") RT.mode = "b";   // after the start, the next tap sets the finish
      update(true);
    });
    svg.style("cursor", "crosshair");
    if (RT.G) update(); else status(RT.loading ? tt("loading") : "");
  }

  function nearName(v) {
    const G = RT.G; if (!G || v == null) return "";
    for (let p = G.start[v]; p < G.start[v + 1]; p++) { const nm = G.names[G.E[G.edge[p] * G.K + G.ix.name]]; if (nm) return nm; }
    return "";
  }
  function chipsUpdate() {
    document.querySelectorAll("#rt-chips .chip").forEach(b => {
      const k = b.dataset.k, v = RT[k]; b.setAttribute("aria-pressed", String(RT.mode === k));
      b.querySelector("small").textContent = v == null ? tt("chip_set") : nearName(v) ? tt("chip_near", { n: nearName(v) }) : tt("chip_here");
    });
  }
  // zoom the map to the route (or to the two points) when they change
  function fitTo(pts) {
    const { svg, W, H } = mapRef, z = svg.node().__zoomer; if (!z || pts.length < 2) return;
    const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const k = Math.max(1, Math.min(5, 0.75 * Math.min(W / Math.max(x1 - x0, 1), H / Math.max(y1 - y0, 1))));
    const t = d3.zoomIdentity.translate(W / 2 - k * (x0 + x1) / 2, H / 2 - k * (y0 + y1) / 2).scale(k);
    svg.transition().duration(650).call(z.transform, t);
  }
  function update(fit) {
    if (!mapRef) return;
    const { F, gp, gr, gm } = mapRef, G = RT.G;
    const line = pts => "M" + pts.map(([lo, la]) => F.P(lo, la).map(v => v.toFixed(1)).join(" ")).join("L");
    gp.selectAll("*").remove();
    if (RT.plan && M.plan) gp.selectAll("path").data(M.plan.steps.flatMap(s => s[10].split("|"))).join("path").attr("d", p => F.path(p))
      .attr("fill", "none").attr("stroke", I.css("--brick")).attr("stroke-width", 3).attr("stroke-dasharray", "5 4").attr("stroke-linecap", "round").attr("opacity", 0.85);
    gr.selectAll("*").remove(); gm.selectAll("*").remove();
    const res = document.getElementById("rt-results"); if (res) res.replaceChildren();
    if (!G) return;
    status(tt(RT.mode === "a" ? "pick_a" : "pick_b") + (RT.a != null && RT.b != null ? ". " + tt("drag") : ""));
    chipsUpdate();
    const k0 = d3.zoomTransform(mapRef.svg.node()).k;
    [["a", "A", I.css("--good")], ["b", "B", I.css("--bad")]].forEach(([key, lab, col]) => {
      const v = RT[key]; if (v == null) return;
      const [x, y] = F.P(G.lon[v], G.lat[v]);
      const m = gm.append("g").attr("class", "rt-marker").attr("transform", `translate(${x},${y})`);
      m.append("circle").attr("r", 11).attr("fill", col).attr("stroke", I.css("--card")).attr("stroke-width", 2.5);
      m.append("text").attr("text-anchor", "middle").attr("dy", ".35em").style("fill", "#fff").style("font", "700 11px var(--body)").text(lab);
      m.selectAll("circle").each(function () { this.__r0 = 11; this.setAttribute("r", 11 / Math.pow(k0, 0.7)); });
      m.selectAll("text").each(function () { this.__f0 = 11; this.style.fontSize = (11 / k0) + "px"; });
      // drag a marker to move it; it snaps to the nearest street when dropped
      m.call(d3.drag().on("drag", ev => m.attr("transform", `translate(${ev.x},${ev.y})`)).on("end", ev => {
        const [lon, lat] = F.inv(ev.x, ev.y), w = nearest(G, lon, lat);
        if (w >= 0) { RT[key] = w; RT.mode = key; }
        update();
      }));
    });
    if (RT.a == null || RT.b == null || RT.a === RT.b) {
      if (fit && (RT.a ?? RT.b) != null) { const v = RT.a ?? RT.b, [x, y] = F.P(G.lon[v], G.lat[v]); fitTo([[x - 150, y - 150], [x + 150, y + 150]]); }
      return;
    }
    weigh(G);
    const best = dijkstra(G, RT.a, RT.b, G.cost), short = dijkstra(G, RT.a, RT.b, G.len);
    if (!best) return;
    const draw = (arcs, col, wdt, dash) => gr.append("path").attr("d", arcs.map(p => line(edgeCoords(G, G.edge[p]))).join(""))
      .attr("fill", "none").attr("stroke", col).attr("stroke-width", wdt).attr("stroke-linecap", "round").attr("stroke-linejoin", "round")
      .attr("stroke-dasharray", dash || null).attr("vector-effect", "non-scaling-stroke");
    if (short) draw(short, I.css("--muted"), 3, "6 5");
    draw(best, I.css("--card"), 7); draw(best, I.css("--sky"), 4.5);
    gm.raise();
    if (fit) fitTo(best.flatMap(p => { const c = edgeCoords(G, G.edge[p]); return [F.P(...c[0]), F.P(...c[c.length - 1])]; }));
    const sb = stats(G, best), ss = short ? stats(G, short) : null;
    const same = ss && Math.abs(sb.L - ss.L) < 1 && Math.abs(sb.prot - ss.prot) < 1e-3;
    const sum = I.el("p", "verdict");
    sum.textContent = same ? tt("same") : ss && sb.L - ss.L > 30 ? tt("vs", { d: I.n1((sb.L - ss.L) / 1000), p: I.pct(sb.prot * 100), q: I.pct(ss.prot * 100) }) : tt("vs2");
    // one compact table: recommended vs shortest
    const tb = I.el("table", "rt-table"), hr = I.el("tr");
    hr.append(I.el("th"), I.el("th", "best", tt("best")));
    if (ss && !same) hr.append(I.el("th", "short", tt("short")));
    const thead = I.el("thead"); thead.append(hr); const body = I.el("tbody");
    const row = (label, f) => { const tr = I.el("tr"); tr.append(I.el("td", null, label), I.el("td", "best", f(sb))); if (ss && !same) tr.append(I.el("td", "short", f(ss))); body.append(tr); };
    row(tt("km"), s => I.n1(s.L / 1000)); row(tt("min"), s => I.nf(Math.round(s.min)));
    row(tt("prot"), s => I.pct(s.prot * 100)); row(tt("busy"), s => I.pct(s.busy * 100));
    row("m " + tt("climb"), s => I.nf(Math.round(s.climb))); row(tt("acc"), s => I.nf(s.acc));
    tb.append(thead, body);
    res.append(sum, tb);
    if (sb.via.length) res.append(I.el("p", "note", tt("via") + ": " + sb.via.join(", ")));
  }

  // ================= wiring =================
  let io = null;
  function onRender() {
    I = window.MCI;
    try { planSection(); } catch (e) { console.error("plan", e); }
    try { plannerUI(); } catch (e) { console.error("planner", e); }
    const sec = document.getElementById("ruta");
    if (sec && !RT.G && !io && "IntersectionObserver" in window) {
      io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); load(); } }, { rootMargin: "600px" });
      io.observe(sec);
    } else if (sec && !("IntersectionObserver" in window)) load();
  }
  window.addEventListener("mc-render", onRender);
  if (window.MCI) onRender();  // app.js has already drawn the page
})();
