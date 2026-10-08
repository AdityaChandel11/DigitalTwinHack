/* Chhaya dashboard. It draws what the bundle holds and computes nothing: every number and every sentence of
   wording comes from data/index.json, data/evidence.json and data/patients/<id>.json (python -m chhaya.build). */
(() => {
  'use strict';

  const SCHEMA = 1;
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
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const hhmm = t => `${String(Math.floor(((t % 1440) + 1440) % 1440 / 60)).padStart(2, '0')}:${String(Math.round(t % 60)).padStart(2, '0')}`;
  const fill = (text, gaps) => text.replace(/\{(\w+)\}/g, (_, k) => gaps[k]);
  const json = url => fetch(url).then(r => { if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); });

  const state = { index: null, evidence: null, patients: {}, current: null, list: { key: 'name', dir: 1, cohort: 'all' } };
  const hero = { day: 0, reveal: 0, cross: null, nodes: null, sc: null };
  let W = {}; // wording, from the bundle

  /* ---------- shell ---------- */
  const top = $('#top');
  const setTop = () => root.style.setProperty('--top-h', `${top.offsetHeight}px`);
  new ResizeObserver(setTop).observe(top);
  setTop();
  try { const saved = localStorage.getItem('chhaya-theme'); if (saved) root.dataset.theme = saved; } catch { /* no storage */ }
  const qs = new URLSearchParams(location.search);
  if (['dark', 'light'].includes(qs.get('theme'))) root.dataset.theme = qs.get('theme');
  if (qs.get('reveal') === '1') hero.reveal = 1;
  $('#theme-btn').addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('chhaya-theme', root.dataset.theme); } catch { /* no storage */ }
  });

  const VIEWS = ['clinic', 'patient', 'evidence'];
  function show(view) {
    for (const n of VIEWS) $(`#view-${n}`).hidden = n !== view;
    for (const a of $$('.tabs a')) a.setAttribute('aria-current', a.dataset.view === view ? 'page' : 'false');
  }
  async function route() {
    const h = location.hash.replace('#', '');
    window.scrollTo(0, 0);
    if (h === 'evidence') { show('evidence'); return drawEvidence(); }
    if (h === 'patient' || h.startsWith('p-')) {
      const id = h.startsWith('p-') ? h.slice(2) : state.current || state.index.patients[0].id;
      show('patient');
      return openPatient(id);
    }
    show('clinic');
    drawClinic();
  }
  window.addEventListener('hashchange', () => route().catch(fail));

  function fail(err) {
    show('clinic');
    $('#view-clinic').innerHTML = `<h1>The bundle could not be read</h1>
      <p class="lede">${esc(err.message)}</p>
      <p class="small">Build it with <code>python -m chhaya.build</code>, then reload. This page draws only what that command writes.</p>`;
  }

  /* ---------- words that depend on whether dates are known ---------- */
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const dm = d => `${d.getDate()} ${MON[d.getMonth()]}`;
  const addDays = (iso, n) => { const [y, m, d] = iso.split('-').map(Number); return new Date(y, m - 1, d + n); };
  // real recordings are shown in days since the sensor; only the synthetic patient has calendar dates
  const wearWords = p => p.dates
    ? `${dm(addDays(p.dates.start, 0))} – ${dm(addDays(p.dates.start, p.dates.wear_days))}`
    : `the first ${p.wear_days ?? p.wear.days} days of the recording`;
  const dayWords = (p, day) => p.dates ? dm(addDays(p.dates.start, p.dates.wear_days + day - 1)) : `day ${day}`;
  const COHORT = { synthetic: 'Synthetic demo', supervised: 'Supervised care', 'free-living': 'Free-living' };
  const TX = { changed: ['delta', 'Changed'], none: ['minus', 'No change recorded'], not_recorded: ['slash', 'Not recorded'] };
  const PR = { raised: ['flag', 'Raised'], not_raised: ['minus', 'Not raised'], not_computed: ['slash', 'Not computed'] };
  const ORDER = { changed: 0, none: 1, not_recorded: 2, raised: 0, not_raised: 1, not_computed: 2 };

  /* ---------- clinic list ---------- */
  function stateCell(map, s, p) {
    const [icon, word] = map[s.state];
    const tail = s.day ? `<span class="dim"> · ${dayWords(p, s.day)}</span>` : s.reason ? `<span class="why">${W.not_computed_reasons[s.reason]}</span>` : '';
    return `<span class="st">${ic(icon)}<span>${word}${tail}</span></span>`;
  }
  function drawClinic() {
    const L = state.list, all = state.index.patients;
    const surname = p => p.name.replace(/^(Mr|Mrs|Ms)\.\s+/, '');
    const val = { name: surname, days: p => p.days_since, tx: p => ORDER[p.treatment.state], prompt: p => ORDER[p.prompt.state], fpd: p => p.sticks_per_day };
    const rows = all.filter(p => L.cohort === 'all' || p.cohort === L.cohort).sort((a, b) => {
      const x = val[L.key](a), y = val[L.key](b);
      return (x < y ? -1 : x > y ? 1 : surname(a).localeCompare(surname(b))) * L.dir;
    });
    const n = c => all.filter(p => c === 'all' || p.cohort === c).length;
    const cohorts = [['all', 'All'], ['supervised', 'Supervised care'], ['free-living', 'Free-living'], ['synthetic', 'Synthetic']].filter(([c]) => n(c));
    const th = (key, label, cls = '') => `<th scope="col" class="${cls}" data-key="${key}" aria-sort="${L.key === key ? (L.dir > 0 ? 'ascending' : 'descending') : 'none'}"><button type="button">${label}<svg class="ic arrow"><use href="#i-sort"/></svg></button></th>`;
    $('#view-clinic').innerHTML = `
      <div class="view-head">
        <div><h1>Clinic list</h1><p class="lede">How old each patient's sensor report is. Listed by name; nothing on this screen ranks patients.</p></div>
        <div class="filters">
          <div class="seg" role="group" aria-label="Cohort" id="cohort-seg">${cohorts.map(([c, l]) => `<button type="button" data-c="${c}" aria-pressed="${L.cohort === c}">${l}<span class="n">${n(c)}</span></button>`).join('')}</div>
          <label class="sort-sel">Sort by <select id="sort-sel">${[['name', 'Patient'], ['days', 'Days since the sensor'], ['tx', 'Treatment changed'], ['prompt', 'Prompt'], ['fpd', 'Fingersticks a day']].map(([k, l]) => `<option value="${k}"${L.key === k ? ' selected' : ''}>${l}</option>`).join('')}</select></label>
        </div>
      </div>
      <div class="table-wrap"><table class="list" id="clinic-table">
        <thead><tr>${th('name', 'Patient')}<th scope="col">Sensor wear</th>${th('days', 'Days since the sensor', 'r')}${th('tx', 'Treatment changed since the sensor (from the record)', 'w-tx')}${th('prompt', 'Prompt to consider a new sensor wear')}${th('fpd', 'Fingersticks a day', 'r')}<th scope="col"><span class="vh">Open</span></th></tr></thead>
        <tbody>${rows.map(p => `<tr tabindex="0" data-id="${esc(p.id)}" aria-label="Open ${esc(p.name)}">
          <td class="c-name" data-label="Patient"><span class="pname">${esc(p.name)}</span><span class="under"><span class="tag${p.synthetic ? ' tag-syn' : ''}">${COHORT[p.cohort]}</span><span class="pid">${esc(p.id)}</span></span></td>
          <td data-label="Sensor wear"><span>${p.dates ? `<span class="nw">${wearWords(p)}</span>` : '<span class="nw">Held-out recording</span>'}<span class="dim blk">${p.wear_days} days used</span></span></td>
          <td class="r" data-label="Days since the sensor"><span class="days">${p.days_since}</span></td>
          <td data-label="Treatment changed since the sensor (from the record)">${stateCell(TX, p.treatment, p)}</td>
          <td data-label="Prompt to consider a new sensor wear">${stateCell(PR, p.prompt, p)}</td>
          <td class="r" data-label="Fingersticks a day"><span>${p.sticks_per_day ? p.sticks_per_day.toFixed(1) : '<span class="dim">none</span>'}</span></td>
          <td class="c-go">${ic('chev')}</td></tr>`).join('')}</tbody>
      </table></div>
      <div class="under-list">
        <p class="small">${W.list_note}</p><p class="small">${W.list_note_prompt}</p><p class="small">${W.pseudonyms}</p>
        ${state.index.bundle === 'demo' ? '<p class="small">This is the demo bundle: the synthetic patient only. Held-out patients of both cohorts appear after <code>python -m chhaya.build --real --confirm</code> on a machine that has the datasets; their readings are never published.</p>' : '<p class="small">Every held-out patient the committed runs scored is listed, none left out. For each, the days after the sensor are a replay: the sensor was worn, and hidden from the estimate.</p>'}
      </div>`;
    const view = $('#view-clinic');
    $('thead', view).onclick = e => { const t = e.target.closest('th[data-key]'); if (!t) return; L.dir = L.key === t.dataset.key ? -L.dir : 1; L.key = t.dataset.key; drawClinic(); };
    $('#sort-sel').onchange = e => { L.key = e.target.value; L.dir = 1; drawClinic(); };
    $('#cohort-seg').onclick = e => { const b = e.target.closest('button'); if (b) { L.cohort = b.dataset.c; drawClinic(); } };
    const open = e => { const tr = e.target.closest('tr[data-id]'); if (tr) location.hash = `p-${tr.dataset.id}`; };
    $('tbody', view).onclick = open;
    $('tbody', view).onkeydown = e => { if (e.key === 'Enter') open(e); };
  }

  /* ---------- charts ---------- */
  function frame(box, { clock0 = 0, g0 = 40, g1 = 300, yTicks, xStep, m }) {
    const Wd = box.clientWidth, H = box.clientHeight;
    const X = t => m.l + (t / 1440) * (Wd - m.l - m.r);
    const Y = g => m.t + (1 - (clamp(g, g0, g1) - g0) / (g1 - g0)) * (H - m.t - m.b);
    const svg = S('svg', { viewBox: `0 0 ${Wd} ${H}`, width: Wd, height: H, 'aria-hidden': 'true' });
    svg.append(S('rect', { x: m.l, y: Y(180), width: Wd - m.l - m.r, height: Y(70) - Y(180), class: 'c-range' }));
    for (const g of yTicks) {
      svg.append(S('line', { x1: m.l, x2: Wd - m.r, y1: Y(g), y2: Y(g), class: g === 70 || g === 180 ? 'c-thr' : 'c-grid' }));
      svg.append(S('text', { x: m.l - 8, y: Y(g) + 4, 'text-anchor': 'end', class: 'c-tick' }, g));
    }
    // ticks at clock hours, wherever in the day this 24-hour block starts
    for (let c = Math.ceil(clock0 / xStep) * xStep; c <= clock0 + 1440; c += xStep) {
      const t = c - clock0, anchor = t < 30 ? 'start' : t > 1410 ? 'end' : 'middle';
      svg.append(S('text', { x: X(t), y: H - m.b + 16, 'text-anchor': anchor, class: 'c-tick' }, hhmm(c)));
    }
    box.querySelector('svg')?.remove();
    box.prepend(svg);
    return { svg, X, Y, W: Wd, H, m };
  }
  function zones(svg, id, { Y, W: Wd, H }) {
    const span = { hi: [0, Y(180)], in: [Y(180), Y(70)], lo: [Y(70), H] };
    for (const z in span) {
      const c = S('clipPath', { id: `${id}-${z}` });
      c.append(S('rect', { x: 0, y: span[z][0], width: Wd, height: span[z][1] - span[z][0] }));
      svg.append(c);
    }
  }
  const ZONES = ['in', 'hi', 'lo'];
  // a null is a gap in the sensor: the line stops and starts again, it is never bridged
  function line(ts, vs, X, Y) {
    let d = '', pen = false;
    ts.forEach((t, i) => {
      if (vs[i] == null) { pen = false; return; }
      d += `${pen ? 'L' : 'M'}${X(t).toFixed(1)} ${Y(vs[i]).toFixed(1)}`;
      pen = true;
    });
    return d;
  }
  function band(ts, lo, hi, X, Y) {
    let d = '', run = [];
    const flush = () => {
      if (run.length > 1) d += `${run.map((i, k) => `${k ? 'L' : 'M'}${X(ts[i]).toFixed(1)} ${Y(hi[i]).toFixed(1)}`).join('')}${run.slice().reverse().map(i => `L${X(ts[i]).toFixed(1)} ${Y(lo[i]).toFixed(1)}`).join('')}Z`;
      run = [];
    };
    ts.forEach((_, i) => { if (lo[i] == null || hi[i] == null) flush(); else run.push(i); });
    flush();
    return d;
  }
  const nearest = (ts, t) => ts.reduce((b, v, i) => (Math.abs(v - t) < Math.abs(ts[b] - t) ? i : b), 0);

  function drawHero() {
    const box = $('#hero-chart');
    if (!box || !box.clientWidth) return;
    const p = state.patients[state.current], d = p.days[hero.day];
    const narrow = box.clientWidth < 620;
    const m = { l: narrow ? 34 : 44, r: narrow ? 12 : 20, t: 26, b: 46 };
    const f = frame(box, { clock0: d.clock0, yTicks: [70, 120, 180, 240, 300], xStep: narrow ? 360 : 180, m });
    const { svg, X, Y, H } = f;
    hero.sc = f;
    svg.append(S('text', { x: 4, y: 13, class: 'c-tick' }, 'mg/dL'));
    svg.append(S('line', { x1: m.l, x2: f.W - m.r, y1: Y(40), y2: Y(40), class: 'c-thr' }));
    if (d.est) {
      svg.append(S('path', { d: band(d.t, d.lo, d.hi, X, Y), class: 'c-band' }));
      svg.append(S('path', { d: line(d.t, d.avg, X, Y), class: 'c-avg' }));
      svg.append(S('path', { d: line(d.t, d.est, X, Y), class: 'c-est' }));
    }
    const named = d.meals.filter(meal => meal.t >= 0);
    named.forEach((meal, i) => {
      svg.append(S('rect', { x: X(meal.t) - 2, y: Y(40) - 10, width: 4, height: 10, rx: 2, class: 'c-meal' }));
      const crowded = i && X(meal.t) - X(named[i - 1].t) < (narrow ? 34 : 96);
      if (meal.carbs != null && !crowded) svg.append(S('text', { x: X(meal.t), y: H - 6, 'text-anchor': 'middle', class: 'c-meal-t' }, narrow || meal.label.length > 12 ? `${meal.carbs} g` : `${meal.label} · ${meal.carbs} g`));
    });
    const clip = S('clipPath', { id: 'hero-clip' });
    const clipRect = S('rect', { x: m.l, y: 0, width: 0, height: H });
    clip.append(clipRect);
    svg.append(clip);
    zones(svg, 'hz', f);
    const sensor = S('g', { 'clip-path': 'url(#hero-clip)' });
    const dTruth = line(d.t, d.sensor, X, Y);
    for (const z of ZONES) sensor.append(S('path', { d: dTruth, class: `c-truth t-${z}`, 'clip-path': `url(#hz-${z})` }));
    svg.append(sensor);
    // the lowest sensor reading below 70 gets the label; it is revealed with the trace
    let lowNote = null, lowAt = -1;
    d.sensor.forEach((v, i) => { if (v != null && v < 70 && (lowAt < 0 || v < d.sensor[lowAt])) lowAt = i; });
    if (lowAt >= 0) {
      lowNote = S('g');
      const x0 = X(d.t[lowAt]), y0 = Y(d.sensor[lowAt]), right = x0 < f.W - 230;
      const xe = right ? x0 + 40 : x0 - 40, ye = Y(88);
      lowNote.append(S('path', { d: `M${x0 + (right ? 4 : -4)} ${y0 - 4}L${xe + (right ? -6 : 6)} ${ye + 1}`, class: 'c-note-line' }));
      lowNote.append(S('text', { x: xe, y: ye + 5, 'text-anchor': right ? 'start' : 'end', class: 'c-note' }, W.sensor_low));
      svg.append(lowNote);
    }
    for (const s of d.sticks) svg.append(S('rect', { x: -4, y: -4, width: 8, height: 8, transform: `translate(${X(s.t).toFixed(1)} ${Y(s.v).toFixed(1)}) rotate(45)`, class: 'c-stick' }));
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
    hero.nodes = { clipRect, edge, lowNote, lowT: lowAt >= 0 ? d.t[lowAt] : null, cLine, cEst, cTruth, cPill, cText };
    const scrub = $('#scrub');
    scrub.style.paddingLeft = `${m.l - 9}px`;
    scrub.style.paddingRight = `${Math.max(0, m.r - 9)}px`;
    applyReveal();
  }

  function applyReveal() {
    const p = state.patients[state.current], d = p.days[hero.day], n = hero.nodes;
    if (!n) return;
    const { X, m } = hero.sc, tEdge = hero.reveal * 1440, xEdge = X(tEdge);
    n.clipRect.setAttribute('width', Math.max(0, xEdge - m.l));
    n.edge.setAttribute('transform', `translate(${xEdge} 0)`);
    n.edge.style.display = hero.reveal > 0 && hero.reveal < 1 ? '' : 'none';
    if (n.lowNote) n.lowNote.style.display = tEdge >= n.lowT + 45 ? '' : 'none';
    const range = $('#reveal-range');
    range.value = Math.round(hero.reveal * 100);
    range.style.setProperty('--fill', `${hero.reveal * 100}%`);
    range.setAttribute('aria-valuetext', hero.reveal === 0 ? 'sensor hidden' : hero.reveal === 1 ? 'sensor revealed' : `sensor revealed up to ${hhmm(d.clock0 + tEdge)}`);
    const full = hero.reveal === 1;
    $('#cov-out').textContent = full && d.inside_band != null ? `${d.inside_band} %` : '–';
    $('#cov-label').textContent = full ? "of this day's sensor readings inside the band" : "of this day's sensor readings inside the band, shown after the reveal";
    const btn = $('#reveal-btn');
    btn.setAttribute('aria-pressed', String(hero.reveal > 0));
    btn.textContent = hero.reveal > 0 ? 'Hide the sensor' : 'Reveal the sensor';
    applyCross();
  }

  function applyCross() {
    const p = state.patients[state.current], d = p.days[hero.day], n = hero.nodes;
    if (!n) return;
    const src = d.est || d.sensor;
    const rest = src.reduce((b, v, k) => (v != null && (src[b] == null || v > src[b]) ? k : b), 0);
    const i = hero.cross == null ? rest : nearest(d.t, hero.cross);
    const { X, Y, W: Wd } = hero.sc, t = d.t[i], x = X(t);
    const seen = hero.reveal > 0 && t <= hero.reveal * 1440 && d.sensor[i] != null;
    n.cLine.setAttribute('x1', x); n.cLine.setAttribute('x2', x);
    const has = d.est && d.est[i] != null;
    n.cEst.style.display = has ? '' : 'none';
    if (has) { n.cEst.setAttribute('cx', x); n.cEst.setAttribute('cy', Y(d.est[i])); }
    n.cTruth.style.display = seen ? '' : 'none';
    if (seen) {
      n.cTruth.setAttribute('cx', x); n.cTruth.setAttribute('cy', Y(d.sensor[i]));
      n.cTruth.setAttribute('class', `c-dot-truth${d.sensor[i] > 180 ? ' hi' : d.sensor[i] < 70 ? ' lo' : ''}`);
    }
    const px = clamp(x, 23, Wd - 23);
    n.cPill.setAttribute('x', px - 23); n.cText.setAttribute('x', px);
    n.cText.textContent = hhmm(d.clock0 + t);
    $('#ro-time').innerHTML = hero.cross == null ? `${hhmm(d.clock0 + t)} <small>peak of the estimate</small>` : hhmm(d.clock0 + t);
    $('#ro-est').innerHTML = has ? `${Math.round(d.est[i])} <small>mg/dL</small>` : '<small>none</small>';
    $('#ro-band').innerHTML = has ? `${Math.round(d.lo[i])} <small>to</small> ${Math.round(d.hi[i])}` : '<small>none</small>';
    const v = seen ? Math.round(d.sensor[i]) : null, what = p.synthetic ? 'mg/dL, simulated' : 'mg/dL';
    $('#ro-truth').innerHTML = !seen ? '<small>hidden</small>' : v < 70 ? `${v} <small>${W.sensor_low}</small>` : `${v} <small>${what}</small>`;
  }

  let anim = 0;
  function revealTo(target) {
    cancelAnimationFrame(anim);
    if (reduced.matches) { hero.reveal = target; applyReveal(); return; }
    const from = hero.reveal, t0 = performance.now();
    const tick = now => {
      const q = clamp((now - t0) / 600, 0, 1);
      hero.reveal = q === 1 ? target : from + (target - from) * (1 - (1 - q) ** 3);
      applyReveal();
      if (q < 1) anim = requestAnimationFrame(tick);
    };
    anim = requestAnimationFrame(tick);
  }

  function drawProfile() {
    const box = $('#agp-chart');
    if (!box || !box.clientWidth) return;
    const pr = state.patients[state.current].wear.profile;
    const ts = pr.p50.map((_, i) => i * 30 + 15);
    const f = frame(box, { yTicks: [70, 180, 300], xStep: 360, m: { l: 30, r: 8, t: 8, b: 24 } });
    const { svg, X, Y } = f;
    zones(svg, 'az', f);
    const outer = band(ts, pr.p05, pr.p95, X, Y), inner = band(ts, pr.p25, pr.p75, X, Y), mid = line(ts, pr.p50, X, Y);
    for (const z of ZONES) {
      svg.append(S('path', { d: outer, class: `c-agp-o z-${z}`, 'clip-path': `url(#az-${z})` }));
      svg.append(S('path', { d: inner, class: `c-agp-i z-${z}`, 'clip-path': `url(#az-${z})` }));
    }
    for (const z of ZONES) svg.append(S('path', { d: mid, class: `c-truth t-${z}`, 'clip-path': `url(#az-${z})` }));
  }

  /* ---------- patient ---------- */
  async function openPatient(id) {
    if (!state.patients[id]) state.patients[id] = await json(`data/patients/${encodeURIComponent(id)}.json`);
    const p = state.patients[id];
    // open on the latest day the sensor covers almost fully: the last day of a recording is often a few hours
    const fullDays = p.days.map((x, i) => (x.sensor.filter(v => v != null).length >= 80 ? i : -1)).filter(i => i >= 0);
    if (state.current !== id) { hero.day = fullDays.length ? fullDays[fullDays.length - 1] : p.days.length - 1; hero.cross = null; if (qs.get('reveal') !== '1') hero.reveal = 0; }
    state.current = id;
    drawPatient();
  }

  function promptBlock(p) {
    const s = p.prompt;
    if (s.state === 'raised') {
      const diff = s.report_mean - s.stick_mean;
      return `<div class="prompt">
        <div class="prompt-state">${ic('flag')}Prompt raised on ${dayWords(p, s.day)}${s.outside ? ' <span class="chip chip-meas">outside the tested range</span>' : ''}</div>
        <p class="prompt-text">${fill(W.prompt, { dates: wearWords(p), date: dayWords(p, s.day) })}</p>
        ${compare(s, diff)}
        <p class="small">${W.prompt_about}</p></div>`;
    }
    if (s.state === 'not_raised')
      return `<div class="prompt"><div class="prompt-state">${ic('minus')}No prompt</div>
        <p class="prompt-text">${W.prompt_none}</p>${compare(s, s.report_mean - s.stick_mean)}<p class="small">${W.prompt_about}</p></div>`;
    return `<div class="prompt"><div class="prompt-state">${ic('slash')}Prompt not computed</div>
      <p class="prompt-text">${fill(W.prompt_not_computed, { reason: W.not_computed_reasons[s.reason] })}</p>
      <p class="small">The prompt was tested only with a sensor wear of three or five days, at least 4.6 fingersticks a day, and within 11 days of the sensor. What it showed there is on the Evidence screen.</p></div>`;
  }
  const compare = (s, diff) => `<dl class="compare" aria-label="The plain comparison">
    <div><dt>Sensor report, mean</dt><dd>${s.report_mean} mg/dL</dd></div>
    <div><dt>Fingerstick average, sensor-equivalent</dt><dd>${s.stick_mean} mg/dL</dd></div>
    <div><dt>Difference</dt><dd>${Math.abs(diff)} mg/dL ${diff > 0 ? 'lower' : diff < 0 ? 'higher' : ''}</dd></div></dl>`;

  function sinceBlock(p) {
    const s = p.since;
    if (s.state !== 'shown')
      return `<div class="prompt"><div class="prompt-state">${ic('slash')}Figures withheld</div>
        <p class="prompt-text">Withheld: ${W.not_computed_reasons[s.reason]} (${s.n} fingersticks over ${s.days} days).</p></div>
        <p class="small" style="margin-top:12px">${W.not_estimated}</p>`;
    return `<div class="pair">
        <div class="h"></div><div class="h est">Sensor-equivalent</div><div class="h">As read from the meter</div>
        <div class="k">Mean glucose</div><div class="v est">${s.sensor_equivalent.mean} <small>mg/dL</small></div><div class="v">${s.meter.mean} <small>mg/dL</small></div>
        <div class="k">Share of fingerstick readings above 180 mg/dL</div><div class="v est">${s.sensor_equivalent.above_180} <small>%</small></div><div class="v">${s.meter.above_180} <small>%</small></div>
      </div>
      ${s.outside ? '<p class="small"><b>Outside the tested range:</b> more than 11 days since the sensor.</p>' : ''}
      <p class="small">${fill(W.since_sensor, { date: wearWords(p), times: `about ${s.times.join(', ')}` })}</p>
      <p class="small">${W.not_estimated}</p>`;
  }

  function recordLine(p) {
    const res = p.record.entry.map(e => e.resource);
    const obs = t => res.find(r => r.resourceType === 'Observation' && r.code.text === t);
    const q = t => obs(t) && `${obs(t).valueQuantity.value} ${obs(t).valueQuantity.unit}`;
    const med = res.find(r => r.resourceType === 'MedicationStatement');
    return [obs('Age') && `${obs('Age').valueQuantity.value} years`, res.some(r => r.resourceType === 'Condition') && 'type 2 diabetes', med && esc(med.medicationCodeableConcept.text), q('HbA1c') && `HbA1c ${q('HbA1c')}`].filter(Boolean).join(' · ') || 'No record fields in the dataset';
  }

  function drawPatient() {
    const p = state.patients[state.current];
    hero.day = clamp(hero.day, 0, p.days.length - 1);
    const d = p.days[hero.day], twin = p.estimate && p.estimate.kind === 'twin';
    const dayLabel = x => `Day ${x.day}${x.day === p.days_since ? (p.synthetic ? ', today' : ', last') : ''}`;
    const tx = p.treatment;
    const txWord = TX[tx.state][1] + (tx.day ? ` · ${dayWords(p, tx.day)}` : '');
    $('#view-patient').innerHTML = `
      <a class="back" href="#clinic">${ic('back')}Clinic list</a>
      <div class="pt-head"><div>
        <h1>${esc(p.name)} <span class="chip ${p.synthetic ? 'chip-syn' : 'chip-meas'}">${p.synthetic ? 'Synthetic demo patient' : `${COHORT[p.cohort]} · held-out recording · pseudonym`}</span></h1>
        <p class="meta">${recordLine(p)}</p></div>
        <a class="btn" href="#patient" id="record-btn">${ic('file')}Record, FHIR-shaped JSON</a>
      </div>
      <div class="summary">
        <div class="sum-days"><div class="big">${p.days_since}</div><div><p class="big-label">days since<br>the sensor</p>
          <p class="sub">${p.dates ? `Sensor removed ${dm(addDays(p.dates.start, p.dates.wear_days))}` : 'A replay: the sensor was worn, and hidden from the estimate'}</p></div></div>
        <dl class="facts">
          <div><dt>Sensor wear</dt><dd>${p.dates ? wearWords(p) : `${p.wear.days} days`}<span>${p.dates ? `${p.wear.days} days` : 'used as the report'}</span></dd></div>
          <div><dt>Fingersticks since</dt><dd>${p.since.n}<span>${p.since.n ? `${p.since.per_day.toFixed(1)} a day` : 'none in the dataset'}</span></dd></div>
          <div><dt>Treatment <small>(from the record)</small></dt><dd>${TX[tx.state][1]}<span>${tx.day ? dayWords(p, tx.day) : tx.state === 'none' ? 'does not mean unchanged' : ''}</span></dd></div>
        </dl>
        <p class="small note">${W.days_note}</p>
      </div>

      <section class="hero" aria-labelledby="h-hero">
        <div class="hero-head"><div>
          <h2 id="h-hero">${p.synthetic ? "Today's shadow" : 'The shadow'} <span class="chip chip-est">estimated</span></h2>
          <p>${twin ? `Estimated from the sensor wear (${wearWords(p)}) and the meal log.` : `Rebuilt in hindsight from the sensor wear (${wearWords(p)}) and the fingersticks taken since.`} No sensor reading from these days was used.${p.prompt.state === 'raised' ? ` That report may be out of date: see the prompt of ${dayWords(p, p.prompt.day)} below.` : ''}</p></div>
          <div class="hero-ctl">
            <div class="seg" role="group" aria-label="Day since the sensor" id="day-seg">${p.days.map((x, i) => `<button type="button" aria-pressed="${i === hero.day}" data-day="${i}">${i === hero.day ? dayLabel(x) : x.day}</button>`).join('')}</div>
            <button class="btn btn-primary" id="reveal-btn" type="button" aria-pressed="false">Reveal the sensor</button>
          </div></div>
        <dl class="readout" aria-live="polite">
          <div><dt>Time</dt><dd id="ro-time">&nbsp;</dd></div>
          <div><dt><i class="key est"></i>Estimated</dt><dd id="ro-est">&nbsp;</dd></div>
          <div><dt><i class="key band"></i>80 % band</dt><dd id="ro-band">&nbsp;</dd></div>
          <div><dt><i class="key s-in"></i>Sensor</dt><dd id="ro-truth"><small>hidden</small></dd></div>
        </dl>
        <div class="chart" id="hero-chart" tabindex="0" role="group" aria-label="Glucose over the day: the estimate with its 80 percent band, meals and fingersticks. Use the left and right arrow keys to read values."></div>
        <div class="scrub" id="scrub"><label class="vh" for="reveal-range">Reveal the sensor up to a time of day</label>
          <input type="range" id="reveal-range" min="0" max="100" step="1" value="0"></div>
        <div class="chart-foot">
          <ul class="legend">
            <li><i class="key band"></i>80 % band</li><li><i class="key est"></i>Estimated glucose</li>
            <li><i class="key avg"></i>${twin ? 'Average day of the sensor wear' : 'Daily shape of the sensor wear'}</li>
            <li><i class="key s-in"></i>Sensor, within 70 to 180</li><li><i class="key s-hi"></i>Sensor, above 180</li>
            <li><i class="key s-lo"></i>${W.sensor_low[0].toUpperCase() + W.sensor_low.slice(1)}</li>
            <li><i class="key range"></i>Target range, 70 to 180 mg/dL</li>
            ${p.since.n ? '<li><i class="key stick"></i>Fingerstick, as read from the meter</li>' : ''}
            ${d.meals.length ? '<li><i class="key meal"></i>Logged meal</li>' : ''}
          </ul>
          <div class="cov"><b id="cov-out">–</b><span id="cov-label"></span></div>
          <p class="small">${twin ? W.band_twin : W.band_fingersticks}</p>
          <p class="small">${p.synthetic ? W.synthetic : 'The trace revealed here is the real sensor of a held-out recording. It was hidden from the estimate, and this patient was never used to tune any setting.'}</p>
          <details class="tbl"><summary>Show these values as a table</summary><div class="scroll"><table id="hero-table"></table></div></details>
        </div>
      </section>

      <div class="pt-grid">
        <div class="stack">
          <section class="panel"><div class="panel-head"><h2>Since the sensor, from fingersticks</h2><span class="chip chip-est">estimated</span>
            ${p.since.state === 'shown' ? `<span class="eyebrow">${fill(W.since_label, { n: p.since.n, days: p.since.days })}</span>` : ''}</div>${sinceBlock(p)}</section>
          <section class="panel"><div class="panel-head"><h2>Fingersticks</h2><span class="chip chip-meas">as read</span><span class="eyebrow">day ${d.day}, mg/dL</span></div>
            ${d.sticks.length ? `<ul class="sticks">${d.sticks.map(s => `<li><span>${hhmm(d.clock0 + s.t)}</span><b>${s.v}</b></li>`).join('')}</ul>` : '<p class="small" style="margin-bottom:16px">No fingersticks on this day.</p>'}
            ${promptBlock(p)}</section>
        </div>
        <div class="stack">
          <section class="panel"><div class="panel-head"><h2>Last sensor report</h2><span class="chip chip-meas">measured</span><span class="eyebrow">${p.wear.days} days</span></div>
            <div class="mini" id="agp-chart" role="img" aria-label="Daily profile of the sensor wear: median glucose with the range of the middle half of readings, by time of day."></div>
            <p class="small" style="margin-bottom:12px">Median, middle half and 5th to 95th percentile of the readings, by time of day. Teal inside the target range, amber above 180.</p>
            <dl class="trio"><div><dt>Mean glucose</dt><dd>${p.wear.mean} mg/dL</dd></div><div><dt>Readings above 180</dt><dd>${p.wear.above_180} %</dd></div>
              <div><dt>Readings below 70</dt><dd>${p.wear.below_70} %<small>${W.sensor_low}</small></dd></div></dl></section>
          <section class="panel"><div class="panel-head"><h2>Treatment since the sensor</h2><span class="eyebrow">from the record · ${txWord}</span></div>
            <p class="small">${tx.state === 'changed' ? W.treatment_changed : tx.state === 'none' ? 'No change of agent, insulin or pump is recorded. In a case series the sensor mean had moved by more than 20 mg/dL in 4 of 5 repeat wears after a change (3 of 4 patients) and in 0 of 4 without. No recorded change does not mean the report still holds.' : 'The dataset does not record treatment for this patient. Not recorded is not the same as unchanged.'}</p></section>
          <section class="panel"><div class="panel-head"><h2>What keeps the report true</h2></div>
            <ul class="keep"><li><b>The meal log</b><p class="small">${W.keep_meals}</p></li><li><b>Fingersticks</b><p class="small">${W.keep_fingersticks}</p></li></ul></section>
          <section class="panel" id="record-panel"><div class="panel-head"><h2>Record</h2>${p.synthetic ? '<span class="chip chip-syn">Synthetic</span>' : ''}<span class="eyebrow">FHIR-shaped JSON</span></div>
            <pre class="record" tabindex="0">${esc(JSON.stringify(p.record, null, 1))}</pre>
            <p class="small" style="margin-top:12px">The record sets the twin's starting point. Its measured effect on the estimate is nil: see Evidence, the record as the twin's prior.</p></section>
        </div>
      </div>`;
    wirePatient();
    drawHero();
    drawProfile();
    drawTable();
  }

  function drawTable() {
    const p = state.patients[state.current], d = p.days[hero.day];
    const rows = d.t.map((t, i) => ({ t, i })).filter(({ t, i }) => t % 120 === 0 && d.sensor[i] != null);
    $('#hero-table').innerHTML = `<thead><tr><th>Time</th><th>Estimated, mg/dL</th><th>80 % band</th></tr></thead><tbody>${rows.map(({ t, i }) => `<tr><td>${hhmm(d.clock0 + t)}</td><td>${d.est ? Math.round(d.est[i]) : ''}</td><td>${d.est ? `${Math.round(d.lo[i])} to ${Math.round(d.hi[i])}` : ''}</td></tr>`).join('')}</tbody>`;
  }

  function wirePatient() {
    $('#reveal-btn').onclick = () => revealTo(hero.reveal > 0 ? 0 : 1);
    $('#reveal-range').oninput = e => { cancelAnimationFrame(anim); hero.reveal = e.target.value / 100; applyReveal(); };
    $('#day-seg').onclick = e => { const b = e.target.closest('button'); if (!b) return; hero.day = Number(b.dataset.day); hero.reveal = 0; hero.cross = null; drawPatient(); };
    $('#record-btn').onclick = e => { e.preventDefault(); $('#record-panel').scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' }); };
    const box = $('#hero-chart');
    const pointAt = e => {
      const { m, W: Wd } = hero.sc, r = box.getBoundingClientRect();
      hero.cross = clamp((e.clientX - r.left - m.l) / (Wd - m.l - m.r), 0, 1) * 1440;
      applyCross();
    };
    box.onpointermove = pointAt;
    box.onpointerdown = pointAt;
    box.onpointerleave = () => { if (document.activeElement !== box) { hero.cross = null; applyCross(); } };
    box.onblur = () => { hero.cross = null; applyCross(); };
    box.onkeydown = e => {
      const step = e.shiftKey ? 60 : 15, cur = hero.cross ?? 720;
      const next = { ArrowLeft: cur - step, ArrowRight: cur + step, Home: 0, End: 1440 }[e.key];
      if (e.key === 'Escape') { hero.cross = null; applyCross(); return; }
      if (next == null) return;
      e.preventDefault();
      hero.cross = clamp(next, 0, 1440);
      applyCross();
    };
    let raf = 0;
    new ResizeObserver(() => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { if (!$('#view-patient').hidden) { drawHero(); drawProfile(); } }); }).observe(box);
  }

  /* ---------- evidence ---------- */
  const BADGE = { pass: ['check', 'Passed'], miss: ['x', 'Missed'], descriptive: ['span', 'Descriptive'] };
  const GRADE = { pass: 'pass', miss: 'miss', descriptive: 'desc' };
  function dots(f) {
    const ref = f.ref, atEdge = ref && ref.value === f.min;
    const rows = f.items.map(it => `<div class="dp-row${it.emph ? ' emph' : ''}"><span class="dp-l">${esc(it.label)}</span><span class="dp-t">${ref ? '<i class="dp-ref"></i>' : ''}${it.lo != null ? `<i class="dp-w" style="--lo:${Math.max(it.lo, f.min)};--hi:${Math.min(it.hi, f.max)}"></i>` : ''}<i class="dp-d" style="--v:${it.value}"></i></span><span class="dp-v">${it.text}${it.lo != null ? `<span class="vh">, ${it.lo.toFixed(2)} to ${it.hi.toFixed(2)}</span>` : ''}</span></div>`).join('');
    const axis = `<div class="dp-axis"><span class="scale"><span>${f.min}${atEdge ? `, ${ref.label}` : ''}</span>${ref && !atEdge ? `<span class="refl">${ref.label}</span>` : ''}<span>${f.max}</span></span><span></span></div>`;
    const counts = f.counts ? `<dl class="counts">${f.counts.map(c => `<div><dt>${c.label}</dt><dd>${c.text}</dd></div>`).join('')}</dl>` : '';
    return `<div class="dp" style="--min:${f.min};--max:${f.max}${ref ? `;--ref:${ref.value}` : ''}">${rows}${axis}</div>${counts}`;
  }
  function figure(f) {
    const head = `<h3>${f.title}<small>${f.unit}</small></h3>`;
    if (f.type === 'counts')
      return head + f.items.map(it => (it.of <= 100
        ? `<div class="waffle" role="img" aria-label="${it.n} of ${it.of} squares filled">${Array.from({ length: it.of }, (_, i) => `<i${i < it.n ? ' class="on"' : ''}></i>`).join('')}</div>`
        : `<div class="pbar" role="img" aria-label="${it.n} of ${it.of}"><i style="width:${(100 * it.n / it.of).toFixed(1)}%"></i></div>`)
        + `<p class="cap"><b>${it.n} of ${it.of}</b> ${it.label}. ${it.note}</p>`).join('');
    if (f.type === 'stat') return `${head}<div class="stat"><b>${f.items[0].text}</b><span>${f.items[1].text}. Nothing measurable from three days of sensor data.</span></div>`;
    return head + dots(f);
  }
  async function drawEvidence() {
    if (!state.evidence) state.evidence = await json('data/evidence.json');
    const ev = state.evidence, t = ev.tally;
    $('#view-evidence').innerHTML = `
      <div class="view-head"><div><h1>Evidence</h1>
        <p class="lede">Every result, beside the bar that was written before the run. Each was scored once on patients the model had never seen. Misses are shown as plainly as passes.</p></div></div>
      <div class="tally">
        <div><b>${t.passed}</b><span>of ${t.bars} bars passed <span class="badge pass">${ic('check')}Passed</span></span></div>
        <div><b>${t.missed}</b><span>of ${t.bars} bars missed <span class="badge miss">${ic('x')}Missed</span></span></div>
        <div><b>${t.descriptive}</b><span>results with no bar <span class="badge desc">${ic('span')}Descriptive</span></span></div>
      </div>
      <blockquote class="pull">${ev.fusion}<cite>Fusion, in one sentence</cite></blockquote>
      <div class="ev-wrap">
        <nav class="ev-nav" id="ev-nav" aria-label="Results"><p class="eyebrow" style="padding:0 8px 8px">Results</p>${ev.results.map(r => `<button type="button" data-to="ev-${r.id}"><i class="${GRADE[r.grade]}"></i><span>${r.title}</span></button>`).join('')}</nav>
        <div>${ev.results.map(r => `<article class="ev-item" id="ev-${r.id}"><div>
          <div class="ev-top"><span class="badge ${GRADE[r.grade]}">${ic(BADGE[r.grade][0])}${BADGE[r.grade][1]}</span><span class="bars">${r.bars.length ? r.bars.join(', ') : 'no bar'}</span></div>
          <h2>${r.title}<span>${r.sub}</span></h2>
          <p class="claim">${esc(r.claim)}</p>
          <div class="bar-box">${r.bar_text.map(b => `<p>${esc(b)}</p>`).join('')}</div>
          <div class="ev-meta"><span>${r.cohort}</span><span>Regenerate <code>${r.command}</code></span><span>Record <code>${r.record}</code></span></div>
        </div><figure class="fig">${figure(r.figure)}</figure></article>`).join('')}</div>
      </div>
      <div class="ev-tail">
        <section class="panel"><div class="panel-head"><h2>Limits</h2></div><ul class="limits-list">${ev.limits.map(l => `<li>${l}</li>`).join('')}</ul></section>
        <section class="panel"><div class="panel-head"><h2>Data and licences</h2></div><table class="prov">
          ${ev.data.map(x => `<tr><th scope="row">${x.name}</th><td>${x.what} ${x.licence}.</td></tr>`).join('')}
          <tr><th scope="row">Held out</th><td>Patients are split once, by a hash of the patient identifier. Settings are tuned on one half and every figure on this screen is from the other.</td></tr>
          <tr><th scope="row">Regenerate</th><td>Nothing is redistributed: <code>python -m chhaya.data.download</code> fetches both datasets, and each result names the command that regenerates it.</td></tr>
        </table></section>
      </div>`;
    $('#ev-nav').onclick = e => { const b = e.target.closest('button'); if (b) document.getElementById(b.dataset.to).scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' }); };
  }

  /* ---------- start ---------- */
  json('data/index.json').then(index => {
    if (index.schema !== SCHEMA) throw new Error(`this page reads bundle version ${SCHEMA}; the bundle is version ${index.schema}`);
    state.index = index;
    W = index.wording;
    $('#limits').textContent = W.limits;
    $('#foot').textContent = `Chhaya · SynapseX, IIT Kanpur · ${index.bundle === 'demo' ? 'demo bundle: the synthetic patient and the evidence' : 'local bundle: held-out patients, not for publication'} · built from ${index.commit}`;
    return route();
  }).catch(fail);
})();
