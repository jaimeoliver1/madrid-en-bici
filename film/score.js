kit.score(function (S, T) {
  // one beat = half an hour of the day; beat 0 = midnight, beat 48 = the end card
  S.tempo(120, { t0: T.day });
  S.program('pad', 'pad', { rev: 0.6 });
  S.program('pluck', 'pluck', { rev: 0.4, pan: -0.2 });
  S.program('mallet', 'marimba', { pan: 0.15 });
  S.program('bass', 'bass');
  S.program('keys', 'ep', { rev: 0.3 });
  const prog = [['D3', 'A3', 'F#4'], ['B2', 'F#3', 'D4'], ['G2', 'D3', 'B3'], ['A2', 'E3', 'C#4']];
  const roots = ['D2', 'B1', 'G1', 'A1'];
  // title: a soft pad under the map
  S.chord('pad', ['D3', 'A3', 'E4'], { t: 0, dur: T.day + 1, vel: 26 });
  S.note('pluck', 'A4', { t: 0.4, dur: 1.5, vel: 34 });
  // the whole day: one chord per 2 hours, the pad always there
  for (let b = 0; b < 12; b++) S.chord('pad', prog[b % 4], { beat: b * 4, beats: 4, vel: b < 3 || b > 10 ? 24 : 32 });
  // night: sparse plucks
  S.pattern('pluck', 'x.......', { from: 0, repeat: 3, pitch: ['F#5', 'D5', 'B4'], vel: 34 });
  // dawn 06-08: bass and ghost hats come in
  S.note('bass', roots[3], { beat: 12, beats: 2, vel: 58 }); S.note('bass', roots[3], { beat: 14, beats: 2, vel: 62 });
  S.drums({ hat: 'o.o.o.oo' }, { from: 12, repeat: 1 });
  // the day's groove, louder in the rush hours
  const busy = { 4: 1, 7: 0.85, 9: 1, 8: 0.8 };
  for (let b = 4; b < 11; b++) {
    const k = busy[b] || 0.6, root = roots[b % 4];
    S.note('bass', root, { beat: b * 4, beats: 1.5, vel: Math.round(70 * k + 10) });
    S.note('bass', root, { beat: b * 4 + 2, beats: 1.5, vel: Math.round(62 * k + 10) });
    S.pattern('mallet', b === 9 ? 'x.xXx.xX' : 'x.x.X.xx', { from: b * 4, repeat: 1, pitch: [prog[b % 4][2].replace('4', '5'), prog[b % 4][1].replace('3', '4')], vel: Math.round(56 * k + 8) });
    S.drums(k > 0.8 ? { kick: 'x...x...', sidestick: '..x...x.', hat: 'xoxoxoxo' } : { kick: 'x.......', hat: 'o.o.o.o.' }, { from: b * 4, repeat: 1, vel: Math.round(70 * k + 20) });
  }
  // late evening winds down
  S.pattern('pluck', 'x...x...', { from: 44, repeat: 1, pitch: ['A4', 'F#4'], vel: 30 });
  // into the end card
  S.fx('revswell', T.end, { dur: 1.4, vel: 50 });
  S.run('mallet', ['D5', 'E5', 'F#5', 'A5', 'B5', 'D6'], { t: T.end - 0.6, step: 0.1, vel: 46, cresc: 8 });
  S.chord('keys', ['D3', 'A3', 'D4', 'F#4', 'A4'], { t: T.end, dur: 3, vel: 70 });
  S.note('bass', 'D2', { t: T.end, dur: 2.6, vel: 80 });
  S.drum('kick', { t: T.end, vel: 90 });
  S.chord('pad', ['D3', 'A3', 'F#4'], { t: T.end, dur: 3, vel: 36 });
  S.master({ gain: -6, fadeOut: 1.2 });
});