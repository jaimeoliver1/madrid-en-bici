const { seg, eo, eio, lerp } = kit;
kit.scene('end', {
  init(kit) {
    const d = window.BM.data(kit), c = window.BM.colors(kit), S = d.m.stats, f = n => n.toLocaleString('en');
    this.S = S;
    const g = kit.h('<div class="ground"></div>');
    this.map = window.BM.map(kit, 'end-map');
    g.append(this.map);
    const cv = document.createElement('canvas');
    cv.width = 1920; cv.height = 1080; cv.className = 'end-web';
    cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    const x = cv.getContext('2d');
    x.strokeStyle = c.main; x.globalAlpha = 0.04; x.lineWidth = 1.6; x.lineCap = 'round'; x.lineJoin = 'round';
    for (let i = 0; i < d.n; i++) {
      if (d.st[i] < 0) continue;
      x.beginPath(); window.BM.whole(x, d, i); x.stroke();
    }
    g.append(cv);
    g.append(kit.h('<div class="panel"></div>'));
    g.append(kit.h('<div class="words" style="left:120px;top:110px;width:700px;gap:10px"><p class="eyebrow">BiciMAD · Madrid</p><p class="sub">Thursday 12 January 2023</p></div>'));
    g.append(kit.h('<div class="words" style="left:120px;top:330px;width:700px;gap:26px"><h2 class="line"><span class="num end-trips">' + f(S.trips) + '</span> trips</h2><div class="rule end-rule" style="position:relative;width:220px"></div><p class="sub end-a">' + f(S.bikes) + ' bikes, ' + S.stations + ' stations, one day</p><p class="sub end-b">At the busiest moment, ' + S.peakAt + ', ' + S.peakMoving + ' bikes were riding at once.</p></div>'));
    g.append(kit.h('<div class="words end-src" style="left:120px;top:960px;width:760px"><p class="label">Data: EMT Madrid open data, BiciMAD trip records. Routes are likely bike paths along OpenStreetMap streets.</p></div>'));
    kit.stage.append(g);
    this.web = cv.style; this.trips = g.querySelector('.end-trips');
    this.ln = g.querySelector('.line').style; this.rule = g.querySelector('.end-rule').style;
    this.a = g.querySelector('.end-a').style; this.b = g.querySelector('.end-b').style; this.src = g.querySelector('.end-src').style;
    this.mapS = this.map.style; this.mapS.transformOrigin = '1250px 540px';
    this.last = '';
  },
  render(t) {
    const S = this.S, rise = (s, a) => { const p = eo(seg(t, a, a + 0.5)); s.opacity = p; s.transform = 'translateX(' + lerp(26, 0, p) + 'px)'; };
    this.web.opacity = eio(seg(t, 0, 1.4));
    this.mapS.transform = 'scale(' + lerp(1, 1.02, eio(seg(t, 0, 3.5))) + ')';
    this.web.transform = this.mapS.transform; this.web.transformOrigin = '1250px 540px';
    rise(this.ln, 0);
    const n = Math.round(lerp(S.trips * 0.6, S.trips, eo(seg(t, 0, 1.1))));
    const s = n.toLocaleString('en');
    if (s !== this.last) { this.trips.textContent = s; this.last = s; }
    this.rule.transform = 'scaleX(' + eo(seg(t, 0.7, 1.15)) + ')';
    rise(this.a, 0.45); rise(this.b, 0.7); rise(this.src, 1.0);
  },
});