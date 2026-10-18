const { seg, eo, lerp, clamp } = kit;
kit.scene('day', {
  init(kit) {
    this.d = window.BM.data(kit);
    this.c = window.BM.colors(kit);
    const g = kit.h('<div class="ground"></div>');
    g.append(window.BM.map(kit, 'day-map'));
    g.append(kit.h('<div class="panel"></div>'));
    g.append(kit.h('<div class="words" style="left:120px;top:110px;width:700px;gap:10px"><p class="eyebrow">BiciMAD · Madrid</p><p class="sub">Thursday 12 January 2023</p></div>'));
    g.append(kit.h('<div class="words day-clockbox" style="left:112px;top:262px"><p class="num big day-clock">00:00</p></div>'));
    g.append(kit.h('<div class="words day-countbox" style="left:120px;top:490px;gap:6px"><p class="num stat day-count">0</p><p class="label">bikes on the move</p><p class="label day-flow">Darker streets: more bikes in the last hour</p></div>'));
    g.append(kit.h('<div class="words day-barlabel" style="left:120px;top:684px"><p class="label">Trips started each hour</p></div>'));
    const hourly = this.d.m.hourly, mx = Math.max(...hourly), W = 680, slot = W / 24, bw = 20, BH = 180;
    let bars = '', ticks = '';
    hourly.forEach((v, h) => {
      const x = h * slot + (slot - bw) / 2, hh = Math.max(4, v / mx * BH);
      bars += '<rect class="todo" x="' + x + '" y="' + (BH - hh) + '" width="' + bw + '" height="' + hh + '" rx="4"/>';
      bars += '<rect class="done day-b' + h + '" x="' + x + '" y="' + (BH - hh) + '" width="' + bw + '" height="' + hh + '" rx="4"/>';
      if (h % 6 === 0) ticks += '<text class="tick" x="' + (h * slot + slot / 2) + '" y="' + (BH + 34) + '" text-anchor="middle">' + String(h).padStart(2, '0') + ':00</text>';
    });
    g.append(kit.h('<svg class="bars" style="position:absolute;left:120px;top:740px;overflow:visible" width="' + W + '" height="' + (BH + 40) + '" viewBox="0 0 ' + W + ' ' + (BH + 40) + '">' + bars + ticks + '</svg>'));
    kit.stage.append(g);
    this.clock = g.querySelector('.day-clock');
    this.count = g.querySelector('.day-count');
    this.fadeIn = ['.day-clockbox', '.day-countbox', '.day-barlabel', '.bars'].map(s => g.querySelector(s).style);
    this.bars = hourly.map((v, h) => {
      const r = g.querySelector('.day-b' + h), hh = Math.max(4, v / mx * BH);
      return { r, hh };
    });
    this.lastClock = ''; this.lastCount = '';
  },
  render(t, kit) {
    const d = this.d, c = this.c, H = clamp(t, 0, 24), ctx = kit.fx;
    this.fadeIn.forEach((s, k) => { const p = eo(seg(t, 0.05 + k * 0.12, 0.55 + k * 0.12)); s.opacity = p; s.transform = 'translateX(' + lerp(26, 0, p) + 'px)'; });
    const mins = Math.min(1439, Math.floor(H * 60));
    const txt = String(Math.floor(mins / 60)).padStart(2, '0') + ':' + String(mins % 60).padStart(2, '0');
    if (txt !== this.lastClock) { this.clock.textContent = txt; this.lastClock = txt; }
    const cur = Math.floor(H);
    this.bars.forEach((b, h) => {
      const f = h < cur ? 1 : h > cur ? 0 : H - cur;
      b.r.setAttribute('class', h === cur && t < 24 ? 'now' : 'done');
      b.r.setAttribute('height', b.hh * f);
      b.r.setAttribute('y', 180 - b.hh * f);
    });
    ctx.save();
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    // expected traffic: each trip's street route, weighted by how close in time it is to now
    const lv = [[], [], []];
    for (let i = 0; i < d.n; i++) {
      const s = d.st[i], e = d.en[i];
      if (H < s - 0.15 || H > e + 0.85) continue;
      const w = H <= e ? 1 : 1 - (H - e) / 0.85;
      lv[w > 0.66 ? 0 : w > 0.33 ? 1 : 2].push(i);
    }
    ctx.strokeStyle = c.main; ctx.lineWidth = 2.2;
    [0.075, 0.045, 0.022].forEach((a, k) => {
      if (!lv[k].length) return;
      ctx.globalAlpha = a; ctx.beginPath();
      for (const i of lv[k]) window.BM.whole(ctx, d, i);
      ctx.stroke();
    });
    let n = 0;
    const heads = [], rings = [];
    ctx.beginPath();
    for (let i = 0; i < d.n; i++) {
      const s = d.st[i], e = d.en[i];
      if (H >= s && H - s < 0.22) rings.push(i, (H - s) / 0.22);
      if (H < s || H >= e) continue;
      n++;
      const p = (H - s) / (e - s), q = p * p * (3 - 2 * p);
      const p0 = Math.max(0, p - 0.16), q0 = p0 * p0 * (3 - 2 * p0);
      window.BM.sub(ctx, d, i, q0, q);
      const B = window.BM.pt(d, i, q);
      heads.push(B[0], B[1]);
    }
    ctx.strokeStyle = c.main; ctx.globalAlpha = 0.45; ctx.lineWidth = 2.6; ctx.stroke();
    ctx.globalAlpha = 1; ctx.lineWidth = 1.6; ctx.strokeStyle = c.accent;
    for (let k = 0; k < rings.length; k += 2) {
      const i = rings[k], p = rings[k + 1];
      ctx.globalAlpha = 0.8 * (1 - p);
      ctx.beginPath(); ctx.arc(d.ax[i], d.ay[i], 4 + 14 * eo(p), 0, Math.PI * 2); ctx.stroke();
    }
    ctx.globalAlpha = 1; ctx.fillStyle = c.main; ctx.strokeStyle = c.ground; ctx.lineWidth = 1.2;
    ctx.beginPath();
    for (let k = 0; k < heads.length; k += 2) { ctx.moveTo(heads[k] + 3.6, heads[k + 1]); ctx.arc(heads[k], heads[k + 1], 3.6, 0, Math.PI * 2); }
    ctx.fill(); ctx.stroke();
    ctx.restore();
    const ct = String(n);
    if (ct !== this.lastCount) { this.count.textContent = ct; this.lastCount = ct; }
  },
});