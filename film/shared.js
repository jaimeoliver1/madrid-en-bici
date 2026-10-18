window.BM = {
  data(kit) {
    if (window.BM._d) return window.BM._d;
    const m = kit.json('map.json'), s = kit.module('trips.txt') || '';
    const n = Math.floor(s.length / 11), P = (a, b) => parseInt(s.slice(a, b), 36);
    const F = () => new Float32Array(n);
    const d = { m, n, st: F(), en: F(), ax: F(), ay: F(), cx: F(), cy: F(), bx: F(), by: F(), route: new Array(n) };
    const R = window.BM.routes(kit);
    for (let i = 0; i < n; i++) {
      const o = i * 11, start = P(o, o + 4) - 3600, dur = P(o + 4, o + 7), a = P(o + 7, o + 9), b = P(o + 9, o + 11);
      const A = m.stations[a], B = m.stations[b];
      d.st[i] = start / 3600; d.en[i] = (start + dur) / 3600;
      d.ax[i] = A[0]; d.ay[i] = A[1]; d.bx[i] = B[0]; d.by[i] = B[1];
      const dx = B[0] - A[0], dy = B[1] - A[1];
      d.cx[i] = (A[0] + B[0]) / 2 - dy * 0.16; d.cy[i] = (A[1] + B[1]) / 2 + dx * 0.16;
      d.route[i] = R.get(a + ',' + b) || null;
    }
    return (window.BM._d = d);
  },
  // likely street routes per station pair: "a,b:" then 2 chars per coordinate (half pixels, base 64)
  routes(kit) {
    const R = new Map(), A = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_', V = new Int16Array(128);
    for (let i = 0; i < 64; i++) V[A.charCodeAt(i)] = i;
    for (let p = 1; p <= 9; p++) {
      const txt = kit.module('routes-' + p + '.txt');
      if (txt == null) break;
      for (const ln of txt.split('\n')) {
        const c = ln.indexOf(':'); if (c < 0) continue;
        const k = (ln.length - c - 1) >> 2, xs = new Float32Array(k), ys = new Float32Array(k), cum = new Float32Array(k);
        for (let j = 0, q = c + 1; j < k; j++, q += 4) {
          xs[j] = (V[ln.charCodeAt(q)] * 64 + V[ln.charCodeAt(q + 1)]) / 2;
          ys[j] = (V[ln.charCodeAt(q + 2)] * 64 + V[ln.charCodeAt(q + 3)]) / 2;
          cum[j] = j ? cum[j - 1] + Math.hypot(xs[j] - xs[j - 1], ys[j] - ys[j - 1]) : 0;
        }
        R.set(ln.slice(0, c), { xs, ys, cum, len: cum[k - 1] || 1 });
      }
    }
    return R;
  },
  map(kit, cls) {
    const d = window.BM.data(kit);
    const dots = d.m.stations.map(p => '<circle class="stn" cx="' + p[0] + '" cy="' + p[1] + '" r="3.4"/>').join('');
    return kit.h('<svg class="bm-map ' + (cls || '') + '" viewBox="0 0 1920 1080"><path class="dist" d="' + d.m.districts + '"/><g class="stns">' + dots + '</g></svg>');
  },
  colors(kit) {
    const cs = getComputedStyle(kit.stage), g = k => cs.getPropertyValue(k).trim();
    return { main: g('--main'), accent: g('--accent'), ground: g('--ground'), second: g('--second') };
  },
  // index of the route vertex at or before distance L
  seg(r, L) {
    let lo = 0, hi = r.cum.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (r.cum[mid] <= L) lo = mid; else hi = mid; }
    return lo;
  },
  pt(d, i, p) {
    const r = d.route[i];
    if (!r) {
      const q = 1 - p;
      return [q * q * d.ax[i] + 2 * q * p * d.cx[i] + p * p * d.bx[i], q * q * d.ay[i] + 2 * q * p * d.cy[i] + p * p * d.by[i]];
    }
    const L = p * r.len, j = window.BM.seg(r, L), j2 = Math.min(j + 1, r.xs.length - 1), sl = r.cum[j2] - r.cum[j], f = sl > 0 ? (L - r.cum[j]) / sl : 0;
    return [r.xs[j] + (r.xs[j2] - r.xs[j]) * f, r.ys[j] + (r.ys[j2] - r.ys[j]) * f];
  },
  // add the part of trip i's path between progress p0 and p1 to the current canvas path
  sub(ctx, d, i, p0, p1) {
    const A = window.BM.pt(d, i, p0), B = window.BM.pt(d, i, p1), r = d.route[i];
    ctx.moveTo(A[0], A[1]);
    if (r) { const j0 = window.BM.seg(r, p0 * r.len) + 1, j1 = window.BM.seg(r, p1 * r.len); for (let j = j0; j <= j1; j++) ctx.lineTo(r.xs[j], r.ys[j]); }
    ctx.lineTo(B[0], B[1]);
  },
  // add trip i's whole path to the current canvas path
  whole(ctx, d, i) {
    const r = d.route[i];
    if (!r) { ctx.moveTo(d.ax[i], d.ay[i]); ctx.quadraticCurveTo(d.cx[i], d.cy[i], d.bx[i], d.by[i]); return; }
    ctx.moveTo(r.xs[0], r.ys[0]);
    for (let j = 1; j < r.xs.length; j++) ctx.lineTo(r.xs[j], r.ys[j]);
  },
};
