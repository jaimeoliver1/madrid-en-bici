const { seg, eo, ei, eio, lerp, TextFx } = kit;
kit.scene('open', {
  init(kit) {
    const g = kit.h('<div class="ground"></div>');
    this.map = window.BM.map(kit, 'open-map');
    g.append(this.map);
    g.append(kit.h('<div class="panel"></div>'));
    g.append(kit.h('<div class="words" style="left:120px;top:110px;width:700px;gap:10px"><p class="eyebrow">BiciMAD · Madrid</p><p class="sub open-date">Thursday 12 January 2023</p></div>'));
    g.append(kit.h('<div class="words open-title" style="left:120px;top:360px;width:700px;gap:34px"><h1 class="line">24 hours of BiciMAD</h1><p class="sub open-sub">Each dot is one bike, riding from the station where it was unlocked to the one where it was docked.</p></div>'));
    kit.stage.append(g);
    this.line = g.querySelector('.line');
    this.sub = g.querySelector('.open-sub').style;
    this.mapS = this.map.style;
    this.mapS.transformOrigin = '1250px 540px';
    this.stn = [...this.map.querySelectorAll('.stn')].map(c => ({ s: c.style, y: +c.getAttribute('cy') }));
    this.dist = this.map.querySelector('.dist').style;
  },
  render(t) {
    TextFx.fadeFromRight(this.line, t, -0.6, { dx: 30 });
    if (t > 2.35) TextFx.fadeOutLeft(this.line, t, 2.35);
    this.sub.opacity = eo(seg(t, 0.15, 0.7)) * (1 - ei(seg(t, 2.45, 2.85)));
    this.sub.transform = 'translateX(' + (lerp(26, 0, eo(seg(t, 0.15, 0.7))) - 30 * ei(seg(t, 2.45, 2.85))) + 'px)';
    this.mapS.transform = 'scale(' + lerp(1.035, 1, eio(seg(t, -0.5, 3))) + ')';
    this.dist.opacity = lerp(0.55, 1, eo(seg(t, 0, 1.2)));
    for (const c of this.stn) {
      const a = 0.2 + (c.y / 1080) * 1.4;
      c.s.opacity = 0.35 + 0.65 * eo(seg(t, a, a + 0.4));
    }
  },
});