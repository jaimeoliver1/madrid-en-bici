/* Madrid en bici: the shareable "nota de mi barrio" image, drawn on a canvas in the visitor's browser (no server, no extra files).
   Always light, 1080 x 1350 (4:5, fits WhatsApp, Instagram and X without cropping). Called from app.js; texts come from its dictionary. */
(() => {
  const C = { paper: "#FBF7F0", card: "#FFFFFF", ink: "#1F2430", muted: "#676B74", line: "#E9E2D5", sky: "#2B4FC9", lane: "#1A2E7A", laneSoft: "#DEE4F7", brick: "#D9643A", good: "#3E8E5A" };
  const W = 1080, H = 1350, M = 72;
  const DISPLAY = '"Bricolage Grotesque", "Avenir Next", "Segoe UI", system-ui, sans-serif', BODY = 'Figtree, "Segoe UI", system-ui, sans-serif';

  async function fonts() {
    try { await Promise.all(['700 80px "Bricolage Grotesque"', '600 30px "Bricolage Grotesque"', '400 30px Figtree', '600 30px Figtree'].map(f => document.fonts.load(f))); } catch (e) { /* system fonts are fine */ }
  }
  function wrap(ctx, text, maxW) {
    const lines = []; let line = "";
    for (const w of text.split(" ")) { const tryL = line ? line + " " + w : w; if (ctx.measureText(tryL).width > maxW && line) { lines.push(line); line = w; } else line = tryL; }
    if (line) lines.push(line); return lines;
  }
  const rr = (ctx, x, y, w, h, r) => { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); };

  // o: { name, district, pop, rank, of, stations, dens, lane (m or null), acc, verdict, rings, pts:[[lon,lat]], url, t:{kicker, rank, st, dens, lane, acc, foot}, nf, n1 }
  async function barrio(o) {
    await fonts();
    const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
    const ctx = cv.getContext("2d"); ctx.textBaseline = "alphabetic";
    ctx.fillStyle = C.paper; ctx.fillRect(0, 0, W, H);

    // kicker
    ctx.fillStyle = C.sky; ctx.beginPath(); ctx.arc(M + 8, 92, 8, 0, 7); ctx.fill();
    ctx.font = `600 30px ${BODY}`; ctx.fillText(o.t.kicker.toUpperCase(), M + 28, 102);

    // name (shrinks to fit two lines)
    let size = 96, lines;
    for (; size >= 56; size -= 4) { ctx.font = `700 ${size}px ${DISPLAY}`; lines = wrap(ctx, o.name, W - 2 * M); if (lines.length <= 2) break; }
    ctx.fillStyle = C.ink; let y = 190;
    lines.forEach(l => { ctx.fillText(l, M, y); y += size * 1.06; });
    ctx.font = `400 32px ${BODY}`; ctx.fillStyle = C.muted; ctx.fillText(`${o.district} · ${o.pop}`, M, y + 4);

    // map: the barrio outline with its stations
    // the map takes whatever height is left between the name and the rank line + facts + footer
    ctx.font = `700 46px ${DISPLAY}`; const rankLines = wrap(ctx, o.t.rank, W - 2 * M), fh = 124, factsH = 2 * fh + 20, rankH = rankLines.length * 54 + 36;
    const my = y + 36, mh = Math.max(240, Math.min(470, H - 124 - 24 - factsH - rankH - 24 - my));
    ctx.fillStyle = C.card; rr(ctx, M, my, W - 2 * M, mh, 28); ctx.fill();
    const rings = o.rings.split("|").map(r => r.split(" ").map(q => q.split(",").map(Number))), all = rings.flat();
    const k = Math.cos(40.42 * Math.PI / 180), x0 = Math.min(...all.map(p => p[0] * k)), x1 = Math.max(...all.map(p => p[0] * k)), y0 = Math.min(...all.map(p => p[1])), y1 = Math.max(...all.map(p => p[1]));
    const pad = 40, s = Math.min((W - 2 * M - 2 * pad) / (x1 - x0), (mh - 2 * pad) / (y1 - y0)), ox = M + (W - 2 * M - (x1 - x0) * s) / 2, oy = my + (mh - (y1 - y0) * s) / 2;
    const P = (lon, lat) => [ox + (lon * k - x0) * s, oy + (y1 - lat) * s];
    ctx.save(); rr(ctx, M, my, W - 2 * M, mh, 28); ctx.clip();
    ctx.fillStyle = C.laneSoft; ctx.strokeStyle = C.lane; ctx.lineWidth = 3; ctx.lineJoin = "round";
    rings.forEach(r => { ctx.beginPath(); r.forEach(([a, b], i) => { const [px, py] = P(a, b); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }); ctx.closePath(); ctx.fill(); ctx.stroke(); });
    ctx.fillStyle = C.sky; ctx.strokeStyle = C.card; ctx.lineWidth = 3;
    (o.pts || []).forEach(([lon, lat]) => { const [px, py] = P(lon, lat); ctx.beginPath(); ctx.arc(px, py, 11, 0, 7); ctx.fill(); ctx.stroke(); });
    if (!(o.pts || []).length) { ctx.font = `600 30px ${BODY}`; ctx.fillStyle = C.brick; ctx.textAlign = "center"; ctx.fillText(o.verdict, W / 2, my + mh / 2); ctx.textAlign = "left"; }
    ctx.restore();

    // rank line
    y = my + mh + 70;
    ctx.font = `700 46px ${DISPLAY}`; ctx.fillStyle = o.dens >= 10 ? C.good : C.brick;
    rankLines.forEach(l => { ctx.fillText(l, M, y); y += 54; });

    // four facts
    const fy = y - 20, fw = (W - 2 * M - 24) / 2;
    [[o.nf(o.stations), o.t.st], [o.n1(o.dens), o.t.dens], [o.lane == null ? "–" : o.lane < 1000 ? o.nf(Math.round(o.lane / 10) * 10) + " m" : o.n1(o.lane / 1000) + " km", o.t.lane], [o.nf(o.acc), o.t.acc]].forEach(([v, l], i) => {
      const x = M + (i % 2) * (fw + 24), yy = fy + Math.floor(i / 2) * (fh + 20);
      ctx.fillStyle = C.card; rr(ctx, x, yy, fw, fh, 22); ctx.fill();
      ctx.fillStyle = C.ink; ctx.font = `700 52px ${DISPLAY}`; ctx.fillText(v, x + 26, yy + 58);
      ctx.fillStyle = C.muted; ctx.font = `400 25px ${BODY}`; ctx.fillText(wrap(ctx, l, fw - 52)[0], x + 26, yy + 96);
    });

    // footer
    ctx.fillStyle = C.line; ctx.fillRect(M, H - 124, W - 2 * M, 2);
    ctx.fillStyle = C.ink; ctx.font = `600 30px ${BODY}`; ctx.fillText(o.url, M, H - 72);
    ctx.fillStyle = C.muted; ctx.font = `400 24px ${BODY}`; ctx.fillText(o.t.foot, M, H - 34);
    return cv;
  }
  const blob = cv => new Promise(res => cv.toBlob(res, "image/png"));
  window.MCShare = { barrio, blob };
})();
