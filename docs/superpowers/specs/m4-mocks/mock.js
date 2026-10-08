/* Chhaya design mock, Milestone 4. Every patient value here is synthetic and generated below from a fixed
   seed; the Evidence figures are quoted from docs/decisions. Nothing in this file is a result. */
(() => {
  'use strict';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const NS = 'http://www.w3.org/2000/svg';
  const S = (tag, attrs = {}, text) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  };
  const ic = id => `<svg class="ic"><use href="#i-${id}"/></svg>`;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const hhmm = t => `${String(Math.floor(t / 60) % 24).padStart(2, '0')}:${String(Math.round(t % 60)).padStart(2, '0')}`;

  /* ---------- shell: header height, theme, routes ---------- */
  const top = $('#top');
  const setTop = () => root.style.setProperty('--top-h', `${top.offsetHeight}px`);
  new ResizeObserver(setTop).observe(top);
  setTop();

  $('#theme-btn').addEventListener('click', () => {
    const dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
  });

  const VIEWS = ['clinic', 'patient', 'evidence'];
  function route() {
    const h = location.hash.replace('#', '');
    const v = VIEWS.includes(h) ? h : 'clinic';
    for (const n of VIEWS) $(`#view-${n}`).hidden = n !== v;
    for (const a of $$('.tabs a')) a.setAttribute('aria-current', a.dataset.view === v ? 'page' : 'false');
    window.scrollTo(0, 0);
    if (v === 'patient') requestAnimationFrame(drawPatient);
  }
  window.addEventListener('hashchange', route);

  /* ---------- clinic list (placeholder rows, see the design note on the page) ---------- */
  const TODAY = new Date(2026, 9, 8);
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
  const dm = d => `${d.getDate()} ${MON[d.getMonth()]}`;
  const span = (a, b) => (a.getMonth() === b.getMonth() ? `${a.getDate()} – ${dm(b)}` : `${dm(a)} – ${dm(b)}`);
  const COHORT = { syn: 'Synthetic demo', sup: 'Supervised care', free: 'Free-living' };
  const FEW = 'fewer fingersticks than in the tested recordings';
  const ROWS = [
    { name: 'Mrs. R.', cohort: 'syn', wearDays: 5, days: 6, tx: ['changed', 2], prompt: ['raised', 3], fpd: 6.2 },
    { name: 'Patient S-03', cohort: 'sup', wearDays: 3, days: 9, tx: ['changed', 1], prompt: ['not-raised'], fpd: 6.4 },
    { name: 'Patient S-08', cohort: 'sup', wearDays: 3, days: 11, tx: ['none'], prompt: ['raised', 4], fpd: 5.9 },
    { name: 'Patient S-12', cohort: 'sup', wearDays: 5, days: 4, tx: ['changed', 3], prompt: ['not-raised'], fpd: 6.8 },
    { name: 'Patient S-19', cohort: 'sup', wearDays: 3, days: 7, tx: ['not-recorded'], prompt: ['not-computed', FEW], fpd: 2.3 },
    { name: 'Patient S-27', cohort: 'sup', wearDays: 14, days: 5, tx: ['none'], prompt: ['not-computed', 'a sensor wear of a length that was not tested'], fpd: 6.1 },
    { name: 'Patient S-31', cohort: 'sup', wearDays: 3, days: 38, tx: ['changed', 9], prompt: ['not-computed', 'more than 11 days since the sensor'], fpd: 5.2 },
    { name: 'Participant F-02', cohort: 'free', wearDays: 5, days: 5, tx: ['not-recorded'], prompt: ['not-computed', FEW], fpd: 0 },
    { name: 'Participant F-07', cohort: 'free', wearDays: 3, days: 7, tx: ['not-recorded'], prompt: ['not-computed', FEW], fpd: 0 },
    { name: 'Participant F-11', cohort: 'free', wearDays: 5, days: 3, tx: ['not-recorded'], prompt: ['not-computed', FEW], fpd: 0 },
  ];
  const TX = { changed: ['delta', 'Changed'], none: ['minus', 'No change recorded'], 'not-recorded': ['slash', 'Not recorded'] };
  const PR = { raised: ['flag', 'Raised'], 'not-raised': ['minus', 'Not raised'], 'not-computed': ['slash', 'Not computed'] };
  const ORDER = { changed: 0, none: 1, 'not-recorded': 2, raised: 0, 'not-raised': 1, 'not-computed': 2 };
  const list = { key: 'name', dir: 1, cohort: 'all' };

  function stateCell(map, [state, extra], removed) {
    const [icon, word] = map[state];
    const tail =
      typeof extra === 'number' ? `<span class="dim"> · ${dm(addDays(removed, extra))}</span>` : extra ? `<span class="why">${extra}</span>` : '';
    return `<span class="st">${ic(icon)}<span>${word}${tail}</span></span>`;
  }

  function drawClinic() {
    const val = { name: r => r.name, days: r => r.days, tx: r => ORDER[r.tx[0]], prompt: r => ORDER[r.prompt[0]], fpd: r => r.fpd };
    const rows = ROWS.filter(r => list.cohort === 'all' || r.cohort === list.cohort).sort((a, b) => {
      const x = val[list.key](a), y = val[list.key](b);
      return (x < y ? -1 : x > y ? 1 : a.name.localeCompare(b.name)) * list.dir;
    });
    $('#clinic-table tbody').innerHTML = rows
      .map(r => {
        const removed = addDays(TODAY, -r.days);
        const wear = span(addDays(removed, -r.wearDays), removed);
        return `<tr tabindex="0" aria-label="Open ${r.name}">
          <td class="c-name" data-label="Patient"><span class="pname">${r.name}</span><span class="tag${r.cohort === 'syn' ? ' tag-syn' : ''}">${COHORT[r.cohort]}</span></td>
          <td data-label="Sensor wear"><span><span class="nw">${wear}</span><span class="dim blk">${r.wearDays} days</span></span></td>
          <td class="r" data-label="Days since the sensor"><span class="days">${r.days}</span></td>
          <td data-label="Treatment changed since the sensor (from the record)">${stateCell(TX, r.tx, removed)}</td>
          <td data-label="Prompt to consider a new sensor wear">${stateCell(PR, r.prompt, removed)}</td>
          <td class="r" data-label="Fingersticks a day"><span>${r.fpd ? r.fpd.toFixed(1) : '<span class="dim">none</span>'}</span></td>
          <td class="c-go">${ic('chev')}</td></tr>`;
      })
      .join('');
    for (const th of $$('#clinic-table th[data-key]'))
      th.setAttribute('aria-sort', th.dataset.key === list.key ? (list.dir > 0 ? 'ascending' : 'descending') : 'none');
    $('#sort-sel').value = list.key;
    const n = c => ROWS.filter(r => c === 'all' || r.cohort === c).length;
    $('#cohort-seg').innerHTML = [['all', 'All'], ['sup', 'Supervised care'], ['free', 'Free-living'], ['syn', 'Synthetic']]
      .map(([c, label]) => `<button type="button" data-c="${c}" aria-pressed="${list.cohort === c}">${label}<span class="n">${n(c)}</span></button>`)
      .join('');
  }
  $('#clinic-table thead').addEventListener('click', e => {
    const th = e.target.closest('th[data-key]');
    if (!th) return;
    list.dir = list.key === th.dataset.key ? -list.dir : 1;
    list.key = th.dataset.key;
    drawClinic();
  });
  $('#sort-sel').addEventListener('change', e => { list.key = e.target.value; list.dir = 1; drawClinic(); });
  $('#cohort-seg').addEventListener('click', e => {
    const b = e.target.closest('button');
    if (b) { list.cohort = b.dataset.c; drawClinic(); }
  });
  const openPatient = () => { location.hash = 'patient'; };
  $('#clinic-table tbody').addEventListener('click', openPatient);
  $('#clinic-table tbody').addEventListener('keydown', e => { if (e.key === 'Enter') openPatient(); });

  /* ---------- synthetic days for Mrs. R. ---------- */
  function mulberry32(a) {
    return () => {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const gauss = r => Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r());
  const STEP = 5;
  const TS = Array.from({ length: 289 }, (_, i) => i * STEP);
  const MEALS = [
    { t: 7 * 60 + 40, carbs: 45, name: 'Breakfast' },
    { t: 13 * 60 + 10, carbs: 70, name: 'Lunch' },
    { t: 16 * 60 + 45, carbs: 20, name: 'Snack' },
    { t: 20 * 60 + 10, carbs: 60, name: 'Dinner' },
  ];
  const STICK_T = [7 * 60, 9 * 60 + 45, 12 * 60 + 50, 15 * 60 + 15, 19 * 60 + 50, 22 * 60 + 10];
  const withEve = meals => meals.concat(meals.map(m => ({ ...m, t: m.t - 1440 })));
  const bump = (t, tm, tau) => { const x = (t - tm) / tau; return x > 0 ? x * Math.exp(1 - x) : 0; };
  const mealPart = (t, meals, tau) => meals.reduce((s, m) => s + 1.12 * m.carbs * (m.f || 1) * bump(t, m.t + (m.shift || 0), tau), 0);
  const basal = t => 135 + 16 * Math.exp(-(((t - 390) / 140) ** 2)) - 6 * Math.exp(-(((t - 180) / 120) ** 2));
  const halfWidth = (t, mp) => 19 + 0.22 * mp + 3 * Math.sin((t / 1440) * Math.PI);
  const shadow = (t, logged) => {
    const mp = mealPart(t, logged, 58), e = basal(t) + mp, hw = halfWidth(t, mp);
    return [e, e - 0.92 * hw, e + 1.08 * hw];
  };
  const AVG = withEve(MEALS);

  function makeDay(seed, bias, low) {
    const r = mulberry32(seed);
    const meals = MEALS.map(m => ({
      ...m,
      t: m.t + Math.round((gauss(r) * 14) / 5) * 5,
      carbs: Math.max(10, Math.round((m.carbs + gauss(r) * 8) / 5) * 5),
    }));
    const logged = withEve(meals);
    // what was really eaten differs from the log, and one evening snack was never logged
    const eaten = logged.map(m => ({ ...m, shift: gauss(r) * 12, f: 1 + gauss(r) * 0.2 })).concat([{ t: 21 * 60 + 55, carbs: 16 }]);
    const d = { meals, logged, est: [], lo: [], hi: [], truth: [], avg: [] };
    let ar = 0;
    for (const t of TS) {
      const [e, lo, hi] = shadow(t, logged);
      d.est.push(e); d.lo.push(lo); d.hi.push(hi);
      d.avg.push(basal(t) + 0.94 * mealPart(t, AVG, 66));
      ar = 0.9 * ar + gauss(r) * 4.2;
      const dip = low ? 40 * Math.exp(-(((t - 205) / 30) ** 2)) : 0;
      d.truth.push(Math.max(45, basal(t) + mealPart(t, eaten, 52) + bias + ar - dip));
    }
    d.sticks = STICK_T.map(t0 => {
      const t = t0 + Math.round(gauss(r) * 2) * 5;
      return { t, v: Math.round(d.truth[Math.round(t / STEP)] * 1.05 + 10 + gauss(r) * 6) };
    });
    d.cov = Math.round((100 * d.truth.filter((v, i) => v >= d.lo[i] && v <= d.hi[i]).length) / d.truth.length);
    const lowIdx = d.truth.map((v, i) => (v < 70 ? i : -1)).filter(i => i >= 0);
    d.low = lowIdx.length ? { a: lowIdx[0], b: lowIdx[lowIdx.length - 1], at: lowIdx.reduce((m, i) => (d.truth[i] < d.truth[m] ? i : m), lowIdx[0]) } : null;
    return d;
  }
  const DAYS = [makeDay(41, -3, false), makeDay(17, -12, false), makeDay(29, -20, true)];
  const hero = { day: 2, reveal: 0, cross: null, nodes: null, sc: null };

  /* ---------- chart frame shared by the three charts ---------- */
  function frame(box, { t0 = 0, t1 = 1440, g0 = 40, g1 = 300, yTicks, xStep, m }) {
    const W = box.clientWidth, H = box.clientHeight;
    const X = t => m.l + ((t - t0) / (t1 - t0)) * (W - m.l - m.r);
    const Y = g => m.t + (1 - (clamp(g, g0, g1) - g0) / (g1 - g0)) * (H - m.t - m.b);
    const svg = S('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, 'aria-hidden': 'true' });
    svg.append(S('rect', { x: m.l, y: Y(180), width: W - m.l - m.r, height: Y(70) - Y(180), class: 'c-range' }));
    for (const g of yTicks) {
      svg.append(S('line', { x1: m.l, x2: W - m.r, y1: Y(g), y2: Y(g), class: g === 70 || g === 180 ? 'c-thr' : 'c-grid' }));
      svg.append(S('text', { x: m.l - 8, y: Y(g) + 4, 'text-anchor': 'end', class: 'c-tick' }, g));
    }
    for (let t = Math.ceil(t0 / xStep) * xStep; t <= t1; t += xStep) {
      const anchor = t === t0 ? 'start' : t === t1 ? 'end' : 'middle';
      svg.append(S('text', { x: X(t), y: H - m.b + 16, 'text-anchor': anchor, class: 'c-tick' }, hhmm(t)));
    }
    box.querySelector('svg')?.remove();
    box.prepend(svg);
    return { svg, X, Y, W, H, m };
  }
  const line = (ts, vs, X, Y) => ts.map((t, i) => `${i ? 'L' : 'M'}${X(t).toFixed(1)} ${Y(vs[i]).toFixed(1)}`).join('');
  const band = (ts, lo, hi, X, Y) =>
    `${line(ts, hi, X, Y)}${ts.map((_, k) => { const i = ts.length - 1 - k; return `L${X(ts[i]).toFixed(1)} ${Y(lo[i]).toFixed(1)}`; }).join('')}Z`;

  /* ---------- the hero ---------- */
  function drawHero() {
    const box = $('#hero-chart');
    if (!box.clientWidth) return;
    const narrow = box.clientWidth < 620;
    const m = { l: narrow ? 34 : 44, r: narrow ? 12 : 20, t: 26, b: 46 };
    const d = DAYS[hero.day];
    const f = frame(box, { yTicks: [70, 120, 180, 240, 300], xStep: narrow ? 360 : 180, m });
    const { svg, X, Y, W, H } = f;
    hero.sc = f;
    svg.append(S('text', { x: 4, y: 13, class: 'c-tick' }, 'mg/dL'));
    svg.append(S('line', { x1: m.l, x2: W - m.r, y1: Y(40), y2: Y(40), class: 'c-thr' }));
    svg.append(S('path', { d: band(TS, d.lo, d.hi, X, Y), class: 'c-band' }));
    svg.append(S('path', { d: line(TS, d.avg, X, Y), class: 'c-avg' }));
    svg.append(S('path', { d: line(TS, d.est, X, Y), class: 'c-est' }));

    // meals sit on the baseline, labelled under the time axis
    for (const meal of d.meals) {
      svg.append(S('rect', { x: X(meal.t) - 2, y: Y(40) - 10, width: 4, height: 10, rx: 2, class: 'c-meal' }));
      svg.append(S('text', { x: X(meal.t), y: H - 6, 'text-anchor': 'middle', class: 'c-meal-t' }, narrow ? `${meal.carbs} g` : `${meal.name} · ${meal.carbs} g`));
    }

    // the sensor, behind a clip that the scrubber opens from the left
    const clip = S('clipPath', { id: 'hero-clip' });
    const clipRect = S('rect', { x: m.l, y: 0, width: 0, height: H });
    clip.append(clipRect);
    svg.append(clip);
    const sensor = S('g', { 'clip-path': 'url(#hero-clip)' });
    sensor.append(S('path', { d: line(TS, d.truth, X, Y), class: 'c-truth' }));
    let lowNote = null;
    if (d.low) {
      const idx = TS.map((_, i) => i).filter(i => i >= d.low.a - 1 && i <= d.low.b + 1);
      sensor.append(S('path', { d: line(idx.map(i => TS[i]), idx.map(i => d.truth[i]), X, Y), class: 'c-low' }));
      lowNote = S('g');
      const x0 = X(TS[d.low.at]), y0 = Y(d.truth[d.low.at]);
      const xe = X(TS[d.low.b]) + 26, ye = Y(88);
      lowNote.append(S('path', { d: `M${x0 + 4} ${y0 - 4}L${xe - 6} ${ye + 1}`, class: 'c-note-line' }));
      lowNote.append(S('text', { x: xe, y: ye + 5, class: 'c-note' }, 'sensor low, unconfirmed'));
    }
    svg.append(sensor);
    if (lowNote) svg.append(lowNote);

    for (const s of d.sticks)
      svg.append(S('rect', { x: -4, y: -4, width: 8, height: 8, transform: `translate(${X(s.t).toFixed(1)} ${Y(s.v).toFixed(1)}) rotate(45)`, class: 'c-stick' }));

    const edge = S('g');
    edge.append(S('line', { x1: 0, x2: 0, y1: m.t, y2: Y(40), class: 'c-edge' }));
    edge.append(S('rect', { x: -3, y: m.t - 6, width: 6, height: 12, rx: 3, class: 'c-edge-grip' }));
    svg.append(edge);

    const cross = S('g');
    const cLine = S('line', { y1: m.t, y2: Y(40), class: 'c-cross' });
    const cEst = S('circle', { r: 5, class: 'c-dot-est' });
    const cTruth = S('circle', { r: 5, class: 'c-dot-truth' });
    const cPill = S('rect', { y: Y(40) + 4, width: 46, height: 18, rx: 4, class: 'c-time' });
    const cText = S('text', { y: Y(40) + 17, 'text-anchor': 'middle', class: 'c-time-t' });
    cross.append(cLine, cEst, cTruth, cPill, cText);
    svg.append(cross);

    hero.nodes = { clipRect, edge, lowNote, cross, cLine, cEst, cTruth, cPill, cText };
    const scrub = $('#scrub');
    scrub.style.paddingLeft = `${m.l - 9}px`;
    scrub.style.paddingRight = `${Math.max(0, m.r - 9)}px`;
    applyReveal();
    applyCross();
  }

  function applyReveal() {
    const { X, m } = hero.sc, n = hero.nodes, d = DAYS[hero.day];
    const tEdge = hero.reveal * 1440, xEdge = X(tEdge);
    n.clipRect.setAttribute('width', Math.max(0, xEdge - m.l));
    n.edge.setAttribute('transform', `translate(${xEdge} 0)`);
    n.edge.style.display = hero.reveal > 0 && hero.reveal < 1 ? '' : 'none';
    if (n.lowNote) n.lowNote.style.display = d.low && tEdge >= TS[d.low.b] ? '' : 'none';
    const range = $('#reveal-range');
    range.value = Math.round(hero.reveal * 100);
    range.style.setProperty('--fill', `${hero.reveal * 100}%`);
    range.setAttribute('aria-valuetext', hero.reveal === 0 ? 'sensor hidden' : hero.reveal === 1 ? 'sensor revealed' : `sensor revealed up to ${hhmm(tEdge)}`);
    const full = hero.reveal === 1;
    $('#cov-out').textContent = full ? `${d.cov} %` : '–';
    $('#cov-label').textContent = full ? "of the day's readings inside the band" : "of the day's readings inside the band, shown after the reveal";
    const btn = $('#reveal-btn');
    btn.setAttribute('aria-pressed', String(hero.reveal > 0));
    btn.textContent = hero.reveal > 0 ? 'Hide the sensor' : 'Reveal the sensor';
    applyCross();
    drawTable();
  }

  function applyCross() {
    const n = hero.nodes, d = DAYS[hero.day];
    if (!n) return;
    const rest = TS[d.est.reduce((b, v, k) => (v > d.est[b] ? k : b), 0)];
    const { X, Y, W } = hero.sc, t = hero.cross ?? rest, i = Math.round(t / STEP), x = X(t);
    const seen = hero.reveal > 0 && t <= hero.reveal * 1440;
    n.cross.style.display = '';
    n.cLine.setAttribute('x1', x); n.cLine.setAttribute('x2', x);
    n.cEst.setAttribute('cx', x); n.cEst.setAttribute('cy', Y(d.est[i]));
    n.cTruth.setAttribute('cx', x); n.cTruth.setAttribute('cy', Y(d.truth[i]));
    n.cTruth.style.display = seen ? '' : 'none';
    const px = clamp(x, 23, W - 23);
    n.cPill.setAttribute('x', px - 23); n.cText.setAttribute('x', px);
    n.cText.textContent = hhmm(t);
    $('#ro-time').innerHTML = hero.cross == null ? `${hhmm(t)} <small>peak of the estimate</small>` : hhmm(t);
    $('#ro-est').innerHTML = `${Math.round(d.est[i])} <small>mg/dL</small>`;
    $('#ro-band').innerHTML = `${Math.round(d.lo[i])} <small>to</small> ${Math.round(d.hi[i])}`;
    const v = Math.round(d.truth[i]);
    $('#ro-truth').innerHTML = !seen ? '<small>hidden</small>' : v < 70 ? `${v} <small>sensor low, unconfirmed</small>` : `${v} <small>mg/dL, simulated</small>`;
  }

  function drawTable() {
    const d = DAYS[hero.day], full = hero.reveal === 1;
    const rows = TS.filter(t => t % 120 === 0 && t < 1440).map(t => {
      const i = t / STEP;
      return `<tr><td>${hhmm(t)}</td><td>${Math.round(d.est[i])}</td><td>${Math.round(d.lo[i])} to ${Math.round(d.hi[i])}</td><td>${full ? Math.round(d.truth[i]) : 'hidden'}</td></tr>`;
    });
    $('#hero-table').innerHTML = `<thead><tr><th>Time</th><th>Estimated, mg/dL</th><th>80 % band</th><th>Sensor, simulated</th></tr></thead><tbody>${rows.join('')}</tbody>`;
  }

  let anim = 0;
  function revealTo(target) {
    cancelAnimationFrame(anim);
    if (reduced.matches) { hero.reveal = target; applyReveal(); return; }
    const from = hero.reveal, t0 = performance.now(), dur = 600;
    const tick = now => {
      const p = clamp((now - t0) / dur, 0, 1), e = 1 - (1 - p) ** 3;
      hero.reveal = from + (target - from) * e;
      if (p === 1) hero.reveal = target;
      applyReveal();
      if (p < 1) anim = requestAnimationFrame(tick);
    };
    anim = requestAnimationFrame(tick);
  }
  $('#reveal-btn').addEventListener('click', () => revealTo(hero.reveal > 0 ? 0 : 1));
  $('#reveal-range').addEventListener('input', e => { cancelAnimationFrame(anim); hero.reveal = e.target.value / 100; applyReveal(); });
  $('#day-seg').addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    hero.day = Number(b.dataset.day);
    hero.reveal = 0;
    for (const x of $$('#day-seg button')) x.setAttribute('aria-pressed', String(x === b));
    drawPatient();
  });
  const heroBox = $('#hero-chart');
  const pointAt = e => {
    const { m, W } = hero.sc, r = heroBox.getBoundingClientRect();
    hero.cross = Math.round((clamp((e.clientX - r.left - m.l) / (W - m.l - m.r), 0, 1) * 1440) / STEP) * STEP;
    applyCross();
  };
  heroBox.addEventListener('pointermove', pointAt);
  heroBox.addEventListener('pointerdown', pointAt);
  heroBox.addEventListener('pointerleave', () => { if (document.activeElement !== heroBox) { hero.cross = null; applyCross(); } });
  heroBox.addEventListener('blur', () => { hero.cross = null; applyCross(); });
  heroBox.addEventListener('keydown', e => {
    const step = e.shiftKey ? 60 : 15, cur = hero.cross ?? 720;
    const next = { ArrowLeft: cur - step, ArrowRight: cur + step, Home: 0, End: 1440 }[e.key];
    if (e.key === 'Escape') { hero.cross = null; applyCross(); return; }
    if (next == null) return;
    e.preventDefault();
    hero.cross = clamp(next, 0, 1440);
    applyCross();
  });

  /* ---------- the two small charts ---------- */
  function drawAgp() {
    const box = $('#agp-chart');
    if (!box.clientWidth) return;
    const { svg, X, Y } = frame(box, { yTicks: [70, 180, 300], xStep: 360, m: { l: 30, r: 8, t: 8, b: 24 } });
    const med = TS.map(t => basal(t) + 0.94 * mealPart(t, AVG, 66));
    const sp = TS.map(t => 15 + 0.1 * mealPart(t, AVG, 66));
    svg.append(S('path', { d: band(TS, med.map((v, i) => v - 2.2 * sp[i]), med.map((v, i) => v + 2.4 * sp[i]), X, Y), class: 'c-agp-o' }));
    svg.append(S('path', { d: band(TS, med.map((v, i) => v - sp[i]), med.map((v, i) => v + sp[i]), X, Y), class: 'c-agp-i' }));
    svg.append(S('path', { d: line(TS, med, X, Y), class: 'c-truth' }));
  }

  function drawWhatIf() {
    const box = $('#wi-chart');
    if (!box.clientWidth) return;
    const d = DAYS[2], lunch = d.meals[1], carbs = Number($('#wi-range').value);
    const ts = TS.filter(t => t >= 720 && t <= 1110);
    const sim = withEve(d.meals.map(mm => (mm === lunch ? { ...mm, carbs } : mm)));
    const as = ts.map(t => shadow(t, d.logged)), si = ts.map(t => shadow(t, sim));
    const { svg, X, Y } = frame(box, { t0: 720, t1: 1110, g1: 280, yTicks: [70, 180, 280], xStep: 120, m: { l: 30, r: 8, t: 8, b: 24 } });
    svg.append(S('path', { d: band(ts, si.map(v => v[1]), si.map(v => v[2]), X, Y), class: 'c-band' }));
    svg.append(S('path', { d: line(ts, as.map(v => v[0]), X, Y), class: 'c-avg', style: 'stroke-width:1.5' }));
    svg.append(S('path', { d: line(ts, si.map(v => v[0]), X, Y), class: 'c-sim' }));
    const peak = arr => arr.reduce((b, v, i) => (v[0] > arr[b][0] ? i : b), 0);
    const pa = peak(as), ps = peak(si);
    $('#wi-out').textContent = `${carbs} g`;
    $('#wi-text').innerHTML = `Simulated peak <b>${Math.round(si[ps][0])} mg/dL</b> (80 % band ${Math.round(si[ps][1])} to ${Math.round(si[ps][2])}) at ${hhmm(ts[ps])}, dashed. As logged with ${lunch.carbs} g, the estimated peak is ${Math.round(as[pa][0])} mg/dL, thin line.`;
  }
  $('#wi-range').addEventListener('input', drawWhatIf);

  function drawPatient() {
    const d = DAYS[hero.day];
    $('#sticks-list').innerHTML = d.sticks.map(s => `<li><span>${hhmm(s.t)}</span><b>${s.v}</b></li>`).join('');
    $('#sticks-day').textContent = `${$$('#day-seg button')[hero.day].textContent.toLowerCase()}, mg/dL`;
    drawHero();
    drawAgp();
    drawWhatIf();
  }
  let raf = 0;
  new ResizeObserver(() => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { if (!$('#view-patient').hidden) { drawHero(); drawAgp(); drawWhatIf(); } }); }).observe(heroBox);
  $('#record-btn').addEventListener('click', e => { e.preventDefault(); $('#record-panel').scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'center' }); });

  /* ---------- evidence: figures quoted from the decision records ---------- */
  const EV = [
    {
      id: 'gate2', grade: 'pass', bars: 'P1, P2 and P3', title: 'The reveal', sub: 'Gate 2',
      claim: `On 19 held-out patients, 5 days after the sensor comes off, Chhaya's estimate is 1.4 mg/dL (6 %) closer to the hidden sensor than the patient's own average day (p = 4e-05) and about 0.35 mg/dL closer than a control that uses no meals (p = 0.04). The gain comes from the meal log and is small. It was not seen to fade with days since the sensor; with three days of calibration the median favours the twin over its control on each of the seven following days (0.4 to 2.0 mg/dL; the interval excludes zero on three of them; 19 held-out participants), and it reverses only on the last days of the recording, which fewer than half of the participants reach.`,
      bar: ['<b>Bar, written before the run.</b> P1: the median over patients of (twin RMSE minus average-day RMSE) is below 0, and a one-sided Wilcoxon signed-rank test gives p &lt; 0.05.', 'P2 passes only because its bar cannot discriminate: time in range is not a strength, and no time in range is shown from any estimate.'],
      cohort: 'CGMacros, free-living · 19 held-out participants', cmd: 'python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7', rec: 'docs/decisions/2026-10-04-gate2-corrected.md',
      fig: { type: 'dp', title: 'Distance from the hidden sensor', unit: 'RMSE in mg/dL, lower is closer', min: 20, max: 25, items: [{ l: 'Chhaya', v: 21.9, e: 1 }, { l: "The patient's average day", v: 23.3 }] },
    },
    {
      id: 'label', grade: 'desc', bars: 'no bar', title: 'Which readings not to believe', sub: 'Label check',
      claim: 'Of 64 sensor readings below 70 mg/dL with a fingerstick within 10 minutes, 8 (12.5 %) were confirmed, and 0 of 9 at night; of 809 sensor readings above 180, 732 (90.5 %) were confirmed.',
      bar: ['<b>No bar.</b> A check of the labels, run before any model was built on them. It is why there is no low-glucose estimate anywhere, and why a sensor low on screen reads "sensor low, unconfirmed".'],
      cohort: 'ShanghaiT2DM, supervised care · all patients', cmd: 'python -m chhaya.data.audit', rec: 'results/audit/label_validity.json',
      fig: { type: 'label' },
    },
    {
      id: 'gate3', grade: 'miss', bars: 'M1, M2 and M3', title: 'Post-meal excursions without the sensor', sub: 'Gate 3',
      claim: `On 47 held-out Shanghai patients (1,205 meals, 39 % followed by an excursion above 180 mg/dL), a model fusing the record, the sensor week and fingersticks predicted the excursion at meal time with AUPRC 0.60, which was not better than any single stream (fingersticks only: 0.64) nor than the patient's own excursion rate from the sensor week (0.59; difference 0.01, 95 % interval -0.09 to 0.14); with the sensor on, the same model reaches 0.76.`,
      bar: ['<b>Bars, written before the run.</b> M1: fused (sensor off) minus each of record only, sensor history only and fingersticks only, the lower end of the interval for the AUPRC difference is above 0 for all three. M2: fused minus the personal rate, lower end of the interval above 0. M3: calibration slope between 0.8 and 1.2.', 'All three missed. There is no meal alert, and no probability is shown.'],
      cohort: 'ShanghaiT2DM, supervised care · 47 held-out patients', cmd: 'python -m chhaya.eval.gate3 --confirm', rec: 'docs/decisions/2026-10-08-gate3.md',
      fig: { type: 'dp', title: 'Predicting an excursion at meal time', unit: 'AUPRC, higher is better', min: 0.2, max: 0.8, ref: 0.39, refLabel: 'event rate 0.39', items: [{ l: 'Record only', v: 0.57 }, { l: 'Sensor week only', v: 0.63 }, { l: 'Fingersticks only', v: 0.64 }, { l: 'Fused, sensor off', v: 0.6, t: '0.60', e: 1 }, { l: "The patient's own rate", v: 0.59 }, { l: 'Sensor on', v: 0.76 }] },
    },
    {
      id: 'prior', grade: 'miss', bars: 'P1', title: "The record as the twin's prior", sub: 'Fusion, second test',
      claim: `On 20 held-out CGMacros patients with one day of sensor data, giving the twin the record's fasting glucose as its prior changed the error of the estimate by a median of 0.02 mg/dL (p = 0.16), and with three or more days by nothing measurable: the record, as it enters the twin today, is not worth any sensor days.`,
      bar: ['<b>Bar, written before the run.</b> At k = 1, the estimate with the record prior has lower RMSE than with the population prior: median paired difference below 0, p &lt; 0.05.', 'Fusion is built and measured. It is not a gain.'],
      cohort: 'CGMacros, free-living · 20 held-out participants', cmd: 'python -m chhaya.eval.fusion', rec: 'docs/decisions/2026-10-08-record-prior.md',
      fig: { type: 'stat', title: 'Change in the error of the estimate', unit: 'with one day of sensor data', big: '0.02 mg/dL', sub: 'median, p = 0.16. Nothing measurable from three days of sensor data.' },
    },
    {
      id: 'sticks', grade: 'pass', bars: 'F1 and F2', title: 'Fingersticks keep the report truer', sub: 'Experiment F',
      claim: `On 29 held-out Shanghai patients, calibrated on three days of sensor data, fingersticks taken afterwards brought the running estimate 2.8 mg/dL closer to the hidden sensor than the patient's daily shape alone (median paired RMSE difference; 95 % interval 1.6 to 4.7; 86 % of patients; p = 4e-06) and 9.5 mg/dL closer in hindsight (interval 4.6 to 12.1); with one fingerstick a day the running gain was 0.3 mg/dL.`,
      bar: ['<b>Bars, written before the run.</b> F1: live estimate against the control, median paired RMSE difference below 0, p &lt; 0.05. F2: the in-hindsight estimate against the control, the same test.', 'To be told with it: the filter was chosen on development patients by a criterion other than the plan\'s written rule (dated note in the registration, before the test run), and the estimate is still about 22 % off the next fingerstick where a real sensor is about 12 %.'],
      cohort: 'ShanghaiT2DM, supervised care · 29 held-out patients', cmd: 'python -m chhaya.eval.fingersticks --confirm', rec: 'docs/decisions/2026-10-08-fingersticks.md',
      fig: { type: 'dp', title: 'Closer to the hidden sensor than the daily shape alone', unit: 'mg/dL, with 95 % intervals', min: 0, max: 13, items: [{ l: 'As fingersticks arrive', v: 2.8, lo: 1.6, hi: 4.7, e: 1 }, { l: 'In hindsight', v: 9.5, lo: 4.6, hi: 12.1, e: 1 }, { l: 'One fingerstick a day', v: 0.3 }] },
    },
    {
      id: 'report', grade: 'desc', bars: 'no bar', title: 'Fingersticks at report level', sub: 'A plain baseline beats our estimator',
      claim: `On 29 held-out Shanghai patients under supervised care who were tested about six times a day, with the hidden sensor as the yardstick, a three-day sensor report missed the mean sensor glucose of the following days (up to eleven) by a median of 13.0 mg/dL. Chhaya's report rebuilt in hindsight from those fingersticks missed it by 8.9 (median paired difference 3.4, 95 % interval 1.6 to 8.9, 83 % of patients), but was no closer than the plain average of the same fingersticks converted to the sensor's scale by a line learned during the wear (6.4). The share of those converted readings above 180 mg/dL and within 70 to 180 was also closer to the sensor's time above 180 and time in range (3.1 against 8.8 points; 5.0 against 15.2). As read from the meter the same average lay 18.3 mg/dL from the sensor's mean; sensor-scale figures are not meter values. Lower testing frequencies were not measured, and this is not a recommendation to test at any frequency.`,
      bar: ['<b>No bar.</b> Registered as descriptive before the run. The figures on the patient screen therefore come from the plain converted average, not from our estimator.'],
      cohort: 'ShanghaiT2DM, supervised care · 29 held-out patients', cmd: 'python -m chhaya.eval.fingersticks_report --confirm', rec: 'docs/decisions/2026-10-08-fingersticks-report.md',
      fig: { type: 'dp', title: 'Miss in mean glucose over the following days', unit: 'median, mg/dL, lower is closer', min: 0, max: 20, items: [{ l: 'Three-day sensor report', v: 13.0, t: '13.0' }, { l: 'Chhaya, rebuilt from fingersticks', v: 8.9, e: 1 }, { l: "Plain average, sensor's scale", v: 6.4 }, { l: 'Plain average, as read', v: 18.3 }] },
    },
    {
      id: 'expiry', grade: 'desc', bars: 'no bar', title: 'How long the report stays true', sub: 'Expiry',
      claim: `"Report" means mean glucose only, and a three-day report stands in for a fourteen-day one. On 47 held-out Shanghai patients under supervised care with treatment being adjusted, a day's mean sensor glucose lay a median of 13.5 mg/dL from a three-day sensor report's mean inside the wear and 11 to 16 on the four days after it; inside each patient that distance grew by 1.0 mg/dL per day (95 % interval 0.7 to 2.6) over at most eleven days, with glucose moving downward. On 19 held-out free-living CGMacros participants (7 with type 2 diabetes; medication not recorded) no growth was detected over seven days (0.1 mg/dL per day, interval -0.8 to 0.8). In a case series of eight Shanghai patients recorded again (nine later wears, five beginning within three days of the first sensor coming off and four 33 to 154 days after it), four wears in three patients had a mean more than 20 mg/dL lower, all four with a change of treatment in the files; of the five that had not moved, four had no change and one had, and the old daily profile fitted them no worse than a fresh one. No test; not a rule for when a patient should wear a sensor.`,
      bar: ['<b>No bar.</b> Registered as descriptive before the run. These data do not give a number of days.'],
      cohort: 'Both cohorts · 47 and 19 held-out; a case series of 8', cmd: 'python -m chhaya.eval.expiry shanghai --confirm', rec: 'docs/decisions/2026-10-08-expiry.md',
      fig: { type: 'dp', title: 'Growth of the distance from the report', unit: 'mg/dL per day, with 95 % intervals', min: -1, max: 3, ref: 0, refLabel: 'no growth', items: [{ l: 'Supervised care, 47', v: 1.0, t: '1.0', lo: 0.7, hi: 2.6 }, { l: 'Free-living, 19', v: 0.1, lo: -0.8, hi: 0.8 }] },
    },
    {
      id: 'band', grade: 'desc', bars: 'no bar', title: 'The band', sub: 'The recalibration did not transfer',
      claim: 'On 19 held-out participants the 80 % band held 83.5 % of hidden readings on average and between 60 % and 98.5 % for an individual, with 10 of 19 participants within 70 to 90 %. A recalibration factor chosen on development patients (0.78) moved the average to 75.7 %, further from 80 % than before, so it is not used: the band is calibrated on average, not per patient.',
      bar: ['<b>Rule, written before the run.</b> The recalibrated band is used only if, on held-out participants, mean coverage is no further from 80 % than before and no fewer participants fall within 70 to 90 %. It was further, so the band is drawn as Gate 2 scored it.'],
      cohort: 'CGMacros, free-living · 19 held-out participants', cmd: 'python -m chhaya.eval.calibrate --confirm', rec: 'docs/decisions/2026-10-08-band.md',
      fig: { type: 'dp', title: 'Hidden readings inside the 80 % band', unit: 'per cent; the line spans individuals', min: 50, max: 100, ref: 80, refLabel: 'target 80', items: [{ l: 'As scored, shown', v: 83.5, lo: 60, hi: 98.5, e: 1 }, { l: 'Recalibrated, not used', v: 75.7 }] },
    },
    {
      id: 'stale', grade: 'desc', bars: 'no bar', title: 'The prompt to consider a new sensor wear', sub: 'A plain baseline does as well',
      claim: `On 32 held-out Shanghai recordings (29 patients under supervised care, tested about six times a day, for up to eleven days after a three-day sensor report), 11 of which drifted by more than 20 mg/dL in mean sensor glucose (9 downward, 2 upward), a running sum of fingerstick surprises, used only as a prompt to consider a new sensor wear, separated drifted from stable recordings with AUROC 0.82 (95 % interval 0.63 to 0.98), against 0.82 (0.61 to 0.97) for the plain fingerstick average compared with the report's mean (difference 0.00, interval -0.16 to 0.18): it was not shown to do better than that comparison. At a threshold set on development recordings so that at most 10 % of stable ones would raise it, the prompt was raised in 7 of 11 drifted recordings (64 %) and 2 of 21 stable ones (10 %); in those 7, a median of 2.6 days after the split. With a five-day report (24 recordings, 6 drifted) it was not shown to separate them (0.67, interval 0.35 to 0.92). The label and the score look back over the same days. It is not a finding about a patient's glucose, not advice on treatment and not a rule for when to wear a sensor, and it was not tested in outpatient care, at lower testing frequencies or over longer periods.`,
      bar: ['<b>No bar.</b> Registered as descriptive before the run. Not shown to do better than comparing the fingerstick average with the report. On a patient screen it appears only inside the tested range; everywhere else it lives here.'],
      cohort: 'ShanghaiT2DM, supervised care · 32 held-out recordings', cmd: 'python -m chhaya.eval.staleness --confirm', rec: 'docs/decisions/2026-10-08-staleness.md',
      fig: { type: 'dp', title: 'Telling drifted from stable reports', unit: 'AUROC with 95 % intervals', min: 0.5, max: 1, ref: 0.5, refLabel: 'chance', items: [{ l: 'Running sum of fingerstick surprises', v: 0.82, lo: 0.63, hi: 0.98, e: 1 }, { l: 'Fingerstick average against the report', v: 0.82, lo: 0.61, hi: 0.97 }], counts: [['Raised in', '7 of 11 drifted'], ['False prompts', '2 of 21 stable']] },
    },
  ];
  const BADGE = { pass: ['check', 'Passed'], miss: ['x', 'Missed'], desc: ['span', 'Descriptive'] };

  function dotPlot(f) {
    const atEdge = f.ref != null && f.ref === f.min;
    const rows = f.items
      .map(it => {
        const whisker = it.lo != null ? `<i class="dp-w" style="--lo:${it.lo};--hi:${it.hi}"></i>` : '';
        const heard = it.lo != null ? `<span class="vh">, ${it.lo} to ${it.hi}</span>` : '';
        return `<div class="dp-row${it.e ? ' emph' : ''}"><span class="dp-l">${it.l}</span><span class="dp-t">${f.ref != null ? '<i class="dp-ref"></i>' : ''}${whisker}<i class="dp-d" style="--v:${it.v}"></i></span><span class="dp-v">${it.t ?? it.v}${heard}</span></div>`;
      })
      .join('');
    const refl = f.ref != null && !atEdge ? `<span class="refl">${f.refLabel}</span>` : '';
    const axis = `<div class="dp-axis"><span class="scale"><span>${f.min}${atEdge ? `, ${f.refLabel}` : ''}</span>${refl}<span>${f.max}</span></span><span></span></div>`;
    const counts = f.counts ? `<dl class="counts">${f.counts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>` : '';
    return `<div class="dp" style="--min:${f.min};--max:${f.max}${f.ref != null ? `;--ref:${f.ref}` : ''}">${rows}${axis}</div>${counts}`;
  }
  function figure(f) {
    if (f.type === 'label')
      return `<h3>Sensor readings confirmed by a fingerstick<small>taken within 10 minutes</small></h3>
        <div class="waffle" role="img" aria-label="8 of 64 squares filled">${Array.from({ length: 64 }, (_, i) => `<i${i < 8 ? ' class="on"' : ''}></i>`).join('')}</div>
        <p class="cap"><b>8 of 64</b> sensor lows, below 70 mg/dL. At night, 0 of 9.</p>
        <div class="pbar" role="img" aria-label="90.5 per cent filled"><i style="width:90.5%"></i></div>
        <p class="cap" style="margin-bottom:0"><b>732 of 809</b> sensor highs, above 180 mg/dL.</p>`;
    if (f.type === 'stat') return `<h3>${f.title}<small>${f.unit}</small></h3><div class="stat"><b>${f.big}</b><span>${f.sub}</span></div>`;
    return `<h3>${f.title}<small>${f.unit}</small></h3>${dotPlot(f)}`;
  }
  function drawEvidence() {
    $('#ev-list').innerHTML = EV.map(e => {
      const [icon, word] = BADGE[e.grade];
      return `<article class="ev-item" id="ev-${e.id}">
        <div>
          <div class="ev-top"><span class="badge ${e.grade}">${ic(icon)}${word}</span><span class="bars">${e.bars}</span></div>
          <h2>${e.title}<span>${e.sub}</span></h2>
          <p class="claim">${e.claim}</p>
          <div class="bar-box">${e.bar.map(b => `<p>${b}</p>`).join('')}</div>
          <div class="ev-meta"><span>${e.cohort}</span><span>Regenerate <code>${e.cmd}</code></span><span>Record <code>${e.rec}</code></span></div>
        </div>
        <figure class="fig">${figure(e.fig)}</figure>
      </article>`;
    }).join('');
    $('#ev-nav').innerHTML = `<p class="eyebrow" style="padding:0 8px 8px">Results</p>${EV.map(e => `<button type="button" data-to="ev-${e.id}"><i class="${e.grade}"></i><span>${e.title}</span></button>`).join('')}`;
  }
  $('#ev-nav').addEventListener('click', e => {
    const b = e.target.closest('button');
    if (b) document.getElementById(b.dataset.to).scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' });
  });

  /* ---------- patient search ---------- */
  const pal = $('#palette'), palIn = $('#pal-input'), palList = $('#pal-list');
  let palSel = 0, palRows = [];
  function palRender() {
    const q = palIn.value.trim().toLowerCase();
    palRows = ROWS.filter(r => r.name.toLowerCase().includes(q));
    palSel = clamp(palSel, 0, Math.max(0, palRows.length - 1));
    palList.innerHTML = palRows.length
      ? palRows.map((r, i) => `<li role="option" aria-selected="${i === palSel}" data-i="${i}"><b>${r.name}</b><span class="tag${r.cohort === 'syn' ? ' tag-syn' : ''}">${COHORT[r.cohort]}</span><span class="dim">${r.days} days since the sensor</span></li>`).join('')
      : '<li class="pal-empty">No patient matches. Clear the search to see everyone.</li>';
  }
  const palOpen = () => { palIn.value = ''; palSel = 0; palRender(); pal.showModal(); palIn.focus(); };
  const palGo = () => { if (palRows.length) { pal.close(); openPatient(); } };
  $('#find-btn').addEventListener('click', palOpen);
  palIn.addEventListener('input', () => { palSel = 0; palRender(); });
  palIn.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); palSel += e.key === 'ArrowDown' ? 1 : -1; palRender(); }
    if (e.key === 'Enter') palGo();
  });
  palList.addEventListener('click', e => { const li = e.target.closest('li[data-i]'); if (li) { palSel = Number(li.dataset.i); palGo(); } });
  pal.addEventListener('click', e => { if (e.target === pal) pal.close(); });
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); if (!pal.open) palOpen(); }
  });

  // for screenshots and the walkthrough: ?theme=dark|light and ?reveal=1 set the starting state
  const qs = new URLSearchParams(location.search);
  if (['dark', 'light'].includes(qs.get('theme'))) root.dataset.theme = qs.get('theme');
  if (qs.get('reveal') === '1') hero.reveal = 1;

  drawClinic();
  drawEvidence();
  route();
})();
