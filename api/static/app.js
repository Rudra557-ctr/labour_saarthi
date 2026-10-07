/* LMIS dashboard — dependency-free, so the demo runs offline.
 *
 * Four invariants this file must never break:
 *  1. No value is computed here. Everything shown comes from an API response.
 *  2. Outputs B and C are rendered as ALLOCATION SIGNALS, with meta.limitations
 *     printed directly above the ranking they qualify.
 *  3. Evidence status is text + glyph + position — never colour alone.
 *  4. Every panel renders in one fixed order: what it is, how to read it, what
 *     qualifies it, then the figures. A table here is not self-explanatory, and a
 *     reader who meets the numbers first will misread them. `panel()` is the only
 *     way a table reaches the screen, so the order cannot drift per page.
 */
'use strict';

const API = '/api';
const S = { lang: 'en', t: {}, fallback: {}, page: 'landing', contract: null,
            states: [], divisions: [] };

/* ---------------------------------------------------------------- i18n ---- */
async function loadLang(lang) {
  if (!Object.keys(S.fallback).length) {
    S.fallback = await (await fetch('/static/i18n/en.json')).json();
  }
  S.t = lang === 'en' ? S.fallback
      : await (await fetch(`/static/i18n/${lang}.json`)).json();
  S.lang = lang;
  document.documentElement.lang = lang;
  document.documentElement.dir = (S.t._meta && S.t._meta.dir) || 'ltr';
  try { localStorage.setItem('lmis.lang', lang); } catch (e) { /* private mode */ }
}
/* Fall back to English rather than show a key or a machine translation. */
const t = (k, vars) => {
  let s = (S.t[k] !== undefined ? S.t[k] : S.fallback[k]);
  if (s === undefined) return k;
  /* substituted values are escaped: translated strings land in innerHTML */
  if (vars) for (const [n, v] of Object.entries(vars)) s = s.split(`{${n}}`).join(esc(v));
  return s;
};
/* An explanation is authored as a list. Missing or part-translated lists fall
 * back to English rather than rendering an empty panel header. */
const tl = k => {
  const v = (Array.isArray(S.t[k]) ? S.t[k] : null) || S.fallback[k];
  return Array.isArray(v) ? v : [];
};

/* ------------------------------------------------------------- helpers ---- */
/* Escapes for BOTH element and attribute context. The single quote and backtick
 * matter: a value placed in a single-quoted attribute - or in a JS string inside an
 * inline handler - escapes its delimiter without them. */
const esc = v => String(v == null ? '' : v)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/`/g, '&#96;');

/* Route arguments reach a URL and an attribute. Only the shapes the API actually
 * accepts are allowed through; anything else is dropped rather than forwarded or
 * rendered. */
const ROUTE_ARG = /^[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}$/;
const safeArg = a => (a != null && ROUTE_ARG.test(String(a))) ? String(a) : null;
const get = async (p, q) => {
  const u = new URL(API + p, location.origin);
  if (q) for (const [k, v] of Object.entries(q))
    if (v !== null && v !== undefined && v !== '') u.searchParams.set(k, v);
  const r = await fetch(u);
  if (!r.ok && r.status !== 200) throw new Error(`${r.status} ${p}`);
  return r.json();
};
/* Indian digit grouping for counts. A relative signal never passes through here. */
const count = n => n == null ? '—' : Number(n).toLocaleString('en-IN');
const sig = n => n == null ? '—' : Number(n).toLocaleString('en-IN',
  { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const pct = n => n == null ? '—' : (Number(n) * 100).toFixed(2) + '%';

const GLYPH = { OBSERVED: '■', ESTIMATED: '◪', SUPPORTING: '□', UNAVAILABLE: '⬚' };
const CLS = { OBSERVED: 'observed', ESTIMATED: 'estimated',
              SUPPORTING: 'supporting', UNAVAILABLE: 'unavailable' };

function badge(kind, extra) {
  const k = String(kind || 'UNAVAILABLE').toUpperCase();
  return `<span class="badge ${CLS[k] || 'unavailable'}" title="${esc(t('evidence.' + k + '.plain'))}">
    <span class="glyph" aria-hidden="true">${GLYPH[k] || '⬚'}</span>
    <span>${esc(t('evidence.' + k))}${extra ? ' · ' + esc(extra) : ''}</span></span>`;
}

/* The evidence strip: tier, evidence status, confidence, vintage, coverage, rows. */
function strip(meta) {
  const parts = [];
  const tier = meta.tier || (meta.evidence_status || [])[0];
  (meta.evidence_status || [tier]).forEach(s => parts.push(badge(s)));
  if (tier === 'SUPPORTING') parts.push(
    `<span class="badge supporting">${esc(t('notADemandMeasure'))}</span>`);
  if (meta.unit === 'relative_signal_unitless') parts.push(
    `<span class="badge estimated">${esc(t('notAVacancyCount'))}</span>`);
  (meta.confidence || []).forEach(c => {
    if (c === 'OBSERVED') return;
    parts.push(`<span class="chip" title="${esc(t('confidence.' + c + '.plain'))}">${
      esc(t('confidence.label'))}: ${esc(t('confidence.' + c) || c)}</span>`);
  });
  if (meta.transformation_depth || (meta.provenance || {}).transformation_depth)
    parts.push(`<span class="chip">depth ${esc(
      (meta.provenance || {}).transformation_depth || meta.transformation_depth)}</span>`);
  (meta.vintage || []).forEach(v => parts.push(
    `<span class="chip">${esc(t('vintage.label'))} ${esc(v)}</span>`));
  if (meta.returned_rows != null) parts.push(
    `<span class="chip">${esc(t('rows.label'))} ${count(meta.returned_rows)}</span>`);
  const src = ((meta.provenance || {}).source_ids || []).join(', ');
  if (src) parts.push(`<span class="chip">${esc(t('source.label'))}: ${esc(src)}</span>`);
  return `<div class="strip">${parts.join('')}</div>`;
}

/* meta.limitations comes from the output's own stored caveat columns. */
function caveats(meta) {
  const l = meta.limitations || [];
  if (!l.length) return '';
  return `<div class="caveat"><strong>${esc(t('notAVacancyCount'))}</strong>
    ${l.map(x => `<div>${esc(x)}</div>`).join('')}</div>`;
}
function prohibited(meta) {
  const p = meta.prohibited_interpretations || [];
  if (!p.length) return '';
  return `<p class="prohibited">Must not be read as: ${p.map(esc).join(' · ')}</p>`;
}
function coverageNotes(meta) {
  const c = meta.coverage || {};
  if (!Object.keys(c).length) return '';
  const row = (k, v) => `<div>${esc(v.label)}: <strong>${
    v.unit === 'ratio' ? pct(v.value) : count(v.value)}</strong></div>`;
  return `<div class="notice"><strong>${esc(t('coverage.label'))}</strong>
    ${Object.entries(c).map(([k, v]) => row(k, v)).join('')}</div>`;
}

/* ------------------------------------------------- explanation + panel ---- */
/* The reading guide. Each point is authored as "Label — sentence"; the label is
 * split out so the eye can scan the labels alone. A point beginning with "!" is
 * a caution and is marked by shape, not only by wording. */
function points(key) {
  const items = tl(key);
  if (!items.length) return '';
  return `<ul class="points">${items.map(raw => {
    const warn = raw.startsWith('!');
    const txt = warn ? raw.slice(1).trim() : raw;
    const i = txt.indexOf('—');
    const lab = i > 0 ? txt.slice(0, i).trim() : '';
    const rest = i > 0 ? txt.slice(i + 1).trim() : txt;
    return `<li class="${warn ? 'warn' : ''}">${
      lab ? `<span><b>${esc(lab)}</b> — ${esc(rest)}</span>` : `<span>${esc(rest)}</span>`
    }</li>`;
  }).join('')}</ul>`;
}

/* A page heading with its own one-sentence explanation. */
function pageHead(titleKey, ledeKey) {
  return `<div class="page-head"><h2>${esc(t(titleKey))}</h2>
    <p class="lede">${esc(t(ledeKey))}</p></div>`;
}

/* The ONLY route from data to screen. Fixed order:
 *   title + evidence badge -> what it is -> how to read it -> evidence strip
 *   -> qualifiers -> table -> export
 * `explain` names an i18n pair: `<explain>.what` and `<explain>.points`. */
function panel(o) {
  const head = `<div class="panel-head">
    <p class="panel-title">${o.tier ? badge(o.tier) : ''}
      <span>${esc(t(o.titleKey))}</span></p>
    ${o.explain ? `<p class="lede">${esc(t(o.explain + '.what'))}</p>` : ''}
  </div>`;
  return `<section class="panel">${head}
    ${o.explain ? points(o.explain + '.points') : ''}
    ${o.meta ? strip(o.meta) : ''}
    ${o.qualifiers || ''}
    ${o.body || ''}
    ${o.meta ? prohibited(o.meta) : ''}
    ${o.exportId ? exportBar(o.exportId) : ''}</section>`;
}

/* Accessible table: real caption, scoped headers, caveat linked by aria-describedby. */
/* An available output that matched nothing is NOT the same as an unavailable one.
 * It says so, so the three states stay distinct on screen as well as in the API. */
function noMatch(captionText) {
  return `<div class="notice"><strong>${esc(t('table.noMatch'))}</strong>
    <div>${esc(captionText)}</div>
    <div>${esc(t('table.noMatchVsUnavailable'))}</div></div>`;
}

function table(cols, rows, captionText, describedBy) {
  if (!rows || !rows.length) return noMatch(captionText);
  const id = 'cap' + Math.random().toString(36).slice(2, 8);
  const head = cols.map(c =>
    `<th scope="col" class="${c.num ? 'num' : ''}">${esc(c.label)}</th>`).join('');
  const body = rows.map(r => '<tr>' + cols.map(c => {
    const v = c.get ? c.get(r) : r[c.key];
    return `<td class="${c.num ? 'num' : ''} ${c.cls || ''}">${c.html ? v : esc(v)}</td>`;
  }).join('') + '</tr>').join('');
  /* The legend explains only the devices this table actually uses. */
  const hasBar = cols.some(c => c.cls === 'barcell');
  const hasRank = cols.some(c => c.cls === 'rank');
  const legend = (hasBar || hasRank) ? `<div class="legend">${
    hasBar ? `<span class="k"><span class="swatch" aria-hidden="true"></span>${
      esc(t('legend.bar'))}</span>` : ''}${
    hasRank ? `<span class="k">${esc(t('legend.rank'))}</span>` : ''}</div>` : '';
  return `<div class="tablewrap"><div class="scroll">
    <table aria-describedby="${describedBy || ''} ${id}">
    <caption id="${id}">${esc(captionText)}</caption>
    <thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>
    ${legend}</div>`;
}
/* A track behind the fill, so the eye reads a proportion of the largest row in
 * view. There is no axis and no unit: it is not a quantity of anything. */
const barCell = (v, max) =>
  `<span class="track"><span class="bar" style="width:${
    max ? Math.max(2, (v / max) * 100) : 2}%"
     role="img" aria-label="relative signal ${sig(v)}"></span></span>`;
const rankCell = v => `<span>${esc(v == null ? '—' : v)}</span>`;

function exportBar(outputId) {
  return `<div class="controls" style="margin:16px 0 0">
    <a class="btn" href="/api/export/${outputId}.csv">${esc(t('export.csv'))}</a>
    <a class="btn" href="/api/export/${outputId}.json">${esc(t('export.json'))}</a>
    <span class="plain">${esc(t('export.note'))}</span></div>`;
}

/* --------------------------------------------------------------- pages ---- */
const PAGES = ['landing', 'national', 'state', 'district', 'occupation',
               'methodology', 'coverage', 'unavailable'];

async function pageLanding() {
  const cov = await get('/coverage', { domain: 'demand' });
  const d = cov.meta.derived_disclosures || {};
  const g = k => d[k] ? d[k].value : null;
  return `${pageHead('landing.heading', 'landing.whatItIs')}
  <section class="panel">
    <p class="lede">${esc(t('landing.whatItIsNot'))}</p>
    ${points('landing.points')}
    <div class="notice"><strong>${esc(t('coverage.label'))}</strong>
      <div>${esc(t('coverage.residual', { pct: pct(g('pan_india_residual_share')) }))}</div>
      <div>${esc(t('coverage.attributable', { pct: pct(g('state_attributable_share')) }))}</div>
      <div>${esc(t('coverage.districtOccupation', {
        n: count(g('districts_with_occupation_signal')),
        total: count(g('districts_with_relative_signal')) }))}</div></div>
    <div class="caveat"><strong>${esc(t('landing.noTotal'))}</strong></div>
  </section>

  <section class="panel">
    <p class="panel-title"><span>${esc(t('landing.howToRead'))}</span></p>
    <ol class="steps">${tl('landing.steps').map((s, i) =>
      `<li><span class="n">${i + 1}</span><span>${esc(s)}</span></li>`).join('')}</ol>
    <div class="strip">${['OBSERVED', 'ESTIMATED', 'SUPPORTING', 'UNAVAILABLE']
      .map(k => badge(k)).join('')}</div>
    <p class="plain">${esc(t('evidence.vsUnavailable'))}</p>
    <div class="controls" style="margin:16px 0 0">
      <button class="btn primary" onclick="go('national')">${esc(t('landing.enter'))}</button>
      <button class="btn" onclick="go('unavailable')">${esc(t('nav.unavailable'))}</button>
    </div>
  </section>`;
}

async function pageNational() {
  const [ind, occ, plfs, st] = await Promise.all([
    get('/demand/national/industry'),
    get('/demand/national/occupation-composition'),
    get('/context/labour-force', { indicator: 'LFPR' }),
    get('/demand/states'),
  ]);
  const maxI = Math.max(0, ...ind.data.map(r => r.vacancies_cumulative || 0));
  const res = (st.meta.residual_disclosure || [])[0] || {};

  const indTbl = table([
    { label: 'NCS sector', key: 'ncs_sector_name', cls: 'name' },
    { label: 'NIC section', key: 'nic_section_code',
      get: r => r.nic_section_code == null ? '— (no NIC mapping)' : r.nic_section_code },
    { label: 'Vacancies (lakh)', num: true, get: r => sig(r.vacancies_cumulative) },
    { label: 'Share', num: true, get: r => pct(r.share_of_published_total) },
    { label: '', html: true, cls: 'barcell',
      get: r => barCell(r.vacancies_cumulative, maxI) },
    { label: 'Flag', get: r => r.is_heterogeneous_or_residual ? 'heterogeneous/residual' : '' },
  ], ind.data, t('table.caption.industry'));

  const occRows = occ.data.slice().sort((a, b) =>
    (b.estimated_occupation_demand || 0) - (a.estimated_occupation_demand || 0)).slice(0, 40);
  const occTbl = table([
    { label: 'NCO-2015 division', key: 'nco_2015_division', cls: 'name' },
    { label: 'NIC section', get: r => r.nic_section_code || '—' },
    { label: 'NCS sector', key: 'ncs_sector_name' },
    { label: 'Est. (lakh equiv.)', num: true, get: r => sig(r.estimated_occupation_demand) },
    { label: 'Share of division', num: true, get: r => pct(r.occupation_share_of_total) },
    { label: 'Confidence', html: true,
      get: r => `<span class="badge estimated">${esc(r.overall_confidence)}</span>` },
  ], occRows, 'Estimated occupation composition by NIC section (top 40 rows by estimate)');

  const plfsTbl = table([
    { label: 'Indicator', key: 'indicator', cls: 'name' }, { label: 'Area', key: 'area' },
    { label: 'Sex', key: 'sex' }, { label: 'Age group', key: 'age_group' },
    { label: 'Value (%)', num: true, get: r => sig(r.value_percent) },
    { label: 'Approach', key: 'approach' },
  ], plfs.data, 'PLFS labour-force participation rate — national, supporting context');

  return `${pageHead('national.heading', 'national.lede')}
  <section class="panel">
    <div class="caveat"><strong>${esc(t('landing.noTotal'))}</strong></div></section>

  ${panel({ tier: 'OBSERVED', titleKey: 'national.observed', explain: 'explain.industry',
    meta: ind.meta, exportId: 'analytical_demand_by_industry',
    qualifiers: `<p class="plain">${esc(t('national.observedNote'))}</p>
      <p class="plain">Filter key: <code>${esc(ind.meta.filter_key)}</code> —
        ${esc(ind.meta.filter_key_note)}</p>`,
    body: indTbl })}

  ${panel({ tier: 'ESTIMATED', titleKey: 'national.estimated', explain: 'explain.occcomp',
    meta: occ.meta, exportId: 'demand_national_occupation_composition',
    qualifiers: `<p class="plain">${esc(t('national.estimatedNote'))}</p>`,
    body: occTbl })}

  ${panel({ tier: 'SUPPORTING', titleKey: 'national.context', explain: 'explain.plfs',
    meta: plfs.meta,
    qualifiers: `<div class="notice"><strong>${esc(plfs.meta.display_banner)}</strong>
      <div>${esc(plfs.meta.state_or_district_breakdown)}</div></div>`,
    body: plfsTbl })}

  <section class="panel">
    <p class="panel-title"><span>${esc(t('national.residual'))}</span></p>
    <p class="lede">${esc(t('explain.residual.what'))}</p>
    ${points('explain.residual.points')}
    <div class="unavail"><strong>${esc(res.state_name_as_source || '')} —
      ${count(res.vacancies_cumulative)} (${pct(res.share_of_published_total)})</strong>
      <div>${esc(st.meta.residual_note)}</div></div></section>`;
}

async function pageState(stateCode) {
  const sel = stateCode || (S.states[0] || {}).state_lgd_code;
  const [st, dist] = await Promise.all([
    get('/demand/states'), get('/demand/districts', { state: sel }),
  ]);
  const tr = await get('/training/states', { state: sel });
  const row = st.data.find(r => String(r.lgd_code) === String(sel));
  const max = Math.max(0, ...dist.data.map(r => r.relative_demand_signal || 0));

  const options = S.states.map(s =>
    `<option value="${esc(s.state_lgd_code)}" ${String(s.state_lgd_code) === String(sel)
      ? 'selected' : ''}>${esc(s.state_name_lgd)}</option>`).join('');

  const distTbl = table([
    { label: t('district.rankWithinState'), cls: 'rank', html: true,
      get: r => rankCell(r.rank_within_state) },
    { label: 'District', html: true, cls: 'name', get: r =>
      `<a href="#district/${esc(r.lgd_code)}">${esc(r.district_name_lgd)}</a>` },
    { label: 'LGD', key: 'lgd_code' },
    { label: 'Allocation signal', num: true, get: r => sig(r.relative_demand_signal) },
    { label: '', html: true, cls: 'barcell',
      get: r => barCell(r.relative_demand_signal, max) },
    { label: 'Udyam enterprise share', num: true,
      get: r => pct(r.enterprise_share_within_state) },
    { label: 'Confidence', key: 'overall_confidence' },
  ], dist.data, t('table.caption.districts'), 'district-caveat');

  const trTbl = table([
    { label: 'Scheme', key: 'scheme', cls: 'name' },
    { label: 'Period', key: 'scheme_period' },
    { label: 'Measure', key: 'measure' },
    { label: 'Candidates', num: true,
      get: r => r.value_status === 'NO_DATA' ? 'NO_DATA' : count(r.value) },
    { label: 'Status', key: 'value_status' },
    { label: 'As on', get: r => r.as_on_date || '—' },
  ], tr.data, 'Training-system outcomes for this state, by scheme and measure');

  return `${pageHead('state.heading', 'state.lede')}
  <section class="panel">
    <div class="controls"><div class="field">
      <label for="state-sel">${esc(t('state.select'))}</label>
      <select id="state-sel" onchange="go('state', this.value)">${options}</select>
    </div></div>
    <div class="strip">${badge('OBSERVED')}
      <span class="stat">${count(row && row.vacancies_cumulative)}
        <span class="unit">${esc((row && row.unit) || '')}</span></span>
      <span class="chip">${esc(t('vintage.label'))} ${esc(row && row.snapshot_date)}</span>
      <span class="chip">share of published ${pct(row && row.share_of_published_total)}</span>
    </div>
    <p class="plain">${esc(t('state.observed'))} — ${esc(row && row.measure_basis)}</p>
    <div class="notice">${esc(t('state.residualExcluded'))}</div></section>

  ${panel({ tier: 'ESTIMATED', titleKey: 'state.districts', explain: 'explain.districts',
    meta: dist.meta, exportId: 'demand_district_relative_signal',
    qualifiers: `<div class="caveat" id="district-caveat">
      <strong>${esc(dist.meta.allowed_label)} — ${esc(t('notAVacancyCount'))}</strong>
      ${(dist.meta.limitations || []).map(x => `<div>${esc(x)}</div>`).join('')}</div>
      ${coverageNotes(dist.meta)}`,
    body: `${distTbl}
      <details><summary>${esc(t('derivation.heading'))}</summary>
        <p class="plain">${esc(t('derivation.note'))}</p>
        <ul class="reasons">${(dist.meta.derivation_inputs || [])
          .map(i => `<li><code>${esc(i)}</code></li>`).join('')}</ul></details>` })}

  ${panel({ tier: 'OBSERVED', titleKey: 'state.training', explain: 'explain.training',
    meta: tr.meta, exportId: 'fact_training_outcome',
    qualifiers: `<div class="notice">${esc(t('state.trainingNote'))}
      <div>${esc(tr.meta.no_data_note)}</div></div>`,
    body: trTbl })}`;
}

async function pageDistrict(lgd) {
  if (!lgd) {
    const d = await get('/demand/districts', { state: (S.states[0] || {}).state_lgd_code });
    lgd = d.data[0].lgd_code;
  }
  const r = await get(`/demand/districts/${lgd}`);
  const row = r.data[0], panelData = r.meta.occupation_panel;

  let occBlock;
  if (panelData.status === 'AVAILABLE') {
    const max = Math.max(0, ...panelData.rows.map(x => x.district_occupation_signal || 0));
    occBlock = `${strip({ tier: 'ESTIMATED', evidence_status: ['ESTIMATED'],
                          confidence: ['LOW'], unit: 'relative_signal_unitless',
                          returned_rows: panelData.divisions })}
      <div class="caveat" id="occ-caveat">
        <strong>${esc(t('district.occupation'))} — ${esc(t('notAVacancyCount'))}</strong>
        <div>${esc(panelData.rows[0].within_district_ranking_caveat)}</div>
        <div>Census occupation structure is 2011; the demand baseline is
          ${esc(row.baseline_period)}.</div>
        <div>Unclassified share excluded, not redistributed:
          ${pct(panelData.rows[0].unclassified_share_not_allocated)}</div></div>
      ${table([
        { label: 'Rank in district', cls: 'rank', html: true,
          get: x => rankCell(x.rank_within_district) },
        { label: 'NCO-2015 division', key: 'nco_2015_division' },
        { label: 'Division title', key: 'nco_name', cls: 'name' },
        { label: 'Allocation signal', num: true,
          get: x => sig(x.district_occupation_signal) },
        { label: '', html: true, cls: 'barcell',
          get: x => barCell(x.district_occupation_signal, max) },
        { label: 'Census occupation share', num: true,
          get: x => pct(x.occupation_share_of_district) },
        { label: 'Main workers (2011)', num: true, get: x => count(x.main_workers) },
      ], panelData.rows, t('table.caption.occupation'), 'occ-caveat')}
      ${exportBar('demand_district_occupation_signal')}`;
  } else {
    /* Explicit NOT_AVAILABLE with its reason. Never a zero, never a blank. */
    occBlock = `<div class="unavail">
      ${badge('UNAVAILABLE', panelData.status)}
      <p><strong>${esc(t('district.notAvailable'))} — ${esc(panelData.reason_code)}</strong></p>
      <p>${esc(panelData.reason)}</p>
      <p class="plain">${esc(t('evidence.vsUnavailable'))}</p></div>`;
  }

  return `
  <div class="page-head"><h2>${esc(t('district.heading'))}: ${esc(row.district_name_lgd)}
      <span class="sub">(${esc(row.state_name_lgd)})</span></h2>
    <p class="lede">${esc(t('district.lede'))}</p></div>

  <section class="panel">
    <p class="panel-title">${badge('ESTIMATED')}
      <span>${esc(t('district.signal'))}</span></p>
    <p class="lede">${esc(t('explain.districtdetail.what'))}</p>
    ${points('explain.districtdetail.points')}
    ${strip(r.meta)}
    <div class="strip"><span class="stat">${sig(row.relative_demand_signal)}</span>
      <span class="chip">${esc(t('district.signal'))}</span>
      <span class="chip">${esc(t('district.rankWithinState'))}
        ${count(row.rank_within_state)} / ${count(r.meta.districts_in_state)}</span>
      <span class="chip">LGD ${esc(row.lgd_code)}</span>
      <span class="chip">Census 2011 ${esc(row.census_2011_code || '—')}</span></div>
    <div class="caveat"><strong>${esc(t('district.signal'))} — ${esc(t('notAVacancyCount'))}</strong>
      ${(r.meta.limitations || []).map(x => `<div>${esc(x)}</div>`).join('')}</div>
    <dl class="kv">
      <dt>Udyam enterprise share in state</dt><dd>${pct(row.enterprise_share_within_state)}</dd>
      <dt>Udyam snapshot</dt><dd>${esc(row.udyam_snapshot_date)}</dd>
      <dt>Observed state vacancies</dt><dd>${count(row.observed_state_vacancies)}</dd>
      <dt>Demand baseline</dt><dd>${esc(row.baseline_period)}</dd>
      <dt>Transformation depth</dt><dd>${esc(row.transformation_depth)}</dd>
    </dl>
    <details><summary>${esc(t('derivation.heading'))}</summary>
      <p class="plain">${esc(t('derivation.note'))}</p>
      <p class="plain">${esc(row.methodology)}</p></details>
    ${prohibited(r.meta)}</section>

  <section class="panel">
    <p class="panel-title"><span>${esc(t('district.occupation'))}</span></p>
    <p class="lede">${esc(t('explain.districtocc.what'))}</p>
    ${points('explain.districtocc.points')}
    ${occBlock}</section>`;
}

async function pageOccupation(div) {
  const d = div || '7';
  const state = ((S.occStates || [])[0] || S.states[0]).state_lgd_code;
  const [nat, dist] = await Promise.all([
    get('/demand/national/occupation-composition', { nco_division: d }),
    get('/demand/district-occupation', { state, nco_division: d }),
  ]);
  const avail = dist.data.filter(r => r.occupation_prior_status === 'AVAILABLE');
  const max = Math.max(0, ...avail.map(r => r.district_occupation_signal || 0));
  const options = S.divisions.map(x =>
    `<option value="${esc(x.nco_2015_division)}" ${x.nco_2015_division === d ? 'selected' : ''}>
      ${esc(x.nco_2015_division)} — ${esc(x.nco_name)}</option>`).join('');
  const stOpts = (S.occStates || []).map(s =>
    `<option value="${esc(s.state_lgd_code)}" ${String(s.state_lgd_code) === String(state)
      ? 'selected' : ''}>${esc(s.state_name_lgd)}</option>`).join('');

  return `${pageHead('occupation.heading', 'occupation.lede')}
  <section class="panel">
    <div class="controls">
      <div class="field"><label for="occ-sel">${esc(t('occupation.select'))}</label>
        <select id="occ-sel" onchange="go('occupation', this.value)">${options}</select></div>
      <div class="field"><label for="occ-state">${esc(t('state.select'))}</label>
        <select id="occ-state" data-division="${esc(d)}"
          onchange="go('occupation', this.dataset.division)"
          aria-describedby="occ-state-note">${stOpts}</select>
        <span id="occ-state-note" class="plain">Occupation detail exists for these states only.</span></div>
    </div>
    <p class="plain">NCO-2015 division codes and titles are shown as published and are never translated.</p>
  </section>

  ${panel({ tier: 'ESTIMATED', titleKey: 'occupation.national', explain: 'explain.occnat',
    meta: nat.meta,
    body: table([
      { label: 'NIC section', get: r => r.nic_section_code || '—' },
      { label: 'NCS sector', key: 'ncs_sector_name', cls: 'name' },
      { label: 'Est. (lakh equiv.)', num: true, get: r => sig(r.estimated_occupation_demand) },
      { label: 'Conditional share', num: true, get: r => pct(r.occupation_conditional_share) },
      { label: 'Share of division', num: true, get: r => pct(r.occupation_share_of_total) },
      { label: 'Confidence', key: 'overall_confidence' },
    ], nat.data, `Estimated national composition for NCO-2015 division ${d}`) })}

  ${panel({ tier: 'ESTIMATED', titleKey: 'occupation.districts', explain: 'explain.occdist',
    meta: dist.meta, exportId: 'demand_district_occupation_signal',
    qualifiers: `<div class="caveat" id="occd-caveat">
      <strong>${esc(dist.meta.allowed_label)} — ${esc(t('notAVacancyCount'))}</strong>
      ${(dist.meta.limitations || []).map(x => `<div>${esc(x)}</div>`).join('')}</div>
      <div class="notice">${esc(t('occupation.informative'))}</div>
      ${coverageNotes(dist.meta)}`,
    body: table([
      { label: 'Rank across districts', cls: 'rank', html: true,
        get: r => rankCell(r.rank_within_occupation_across_districts) },
      { label: 'District', html: true, cls: 'name', get: r =>
        `<a href="#district/${esc(r.lgd_code)}">${esc(r.district_name_lgd)}</a>` },
      { label: 'Allocation signal', num: true, get: r => sig(r.district_occupation_signal) },
      { label: '', html: true, cls: 'barcell',
        get: r => barCell(r.district_occupation_signal, max) },
      { label: 'Census occupation share', num: true,
        get: r => pct(r.occupation_share_of_district) },
      { label: 'Confidence', key: 'overall_confidence' },
    ], avail, `Districts in the selected state for NCO-2015 division ${d}`, 'occd-caveat') })}`;
}

async function pageMethodology() {
  const [m, c] = await Promise.all([get('/meta/methodology'), get('/meta/contract')]);
  const mode = c.data.mode;
  const rows = m.data.map(o => `
    <details><summary>${esc(o.output_id)} — ${esc(o.allowed_label)}</summary>
      <div class="strip">${badge(o.tier)}
        ${(o.evidence_status || []).map(e => badge(e)).join('')}
        ${(o.vintage || []).map(v => `<span class="chip">${esc(t('vintage.label'))} ${esc(v)}</span>`).join('')}
      </div>
      ${(o.methodology || []).map(x => `<p class="plain">${esc(x)}</p>`).join('')}
      ${(o.limitations || []).map(x => `<div class="caveat">${esc(x)}</div>`).join('')}
      <dl class="kv"><dt>Unit</dt><dd>${esc(o.unit)}</dd>
        <dt>Measure basis</dt><dd>${esc(o.measure_basis)}</dd>
        <dt>Interpretation</dt><dd>${esc(o.interpretation)}</dd>
        <dt>Sources</dt><dd>${esc(((o.provenance || {}).source_ids || []).join(', '))}</dd>
        ${(o.derivation_inputs || []).length
          ? `<dt>Derivation inputs</dt><dd>${esc(o.derivation_inputs.join(', '))}</dd>` : ''}
      </dl>
      ${prohibited(o)}</details>`).join('');

  return `${pageHead('methodology.heading', 'methodology.lede')}
  <section class="panel">
    <p class="panel-title"><span>${esc(t('methodology.measures'))}</span></p>
    <p class="lede">${esc(t('landing.whatItIs'))}</p>
    <div class="strip">${['OBSERVED', 'ESTIMATED', 'SUPPORTING', 'UNAVAILABLE']
      .map(k => badge(k)).join('')}</div>
    <ul class="reasons">${['OBSERVED', 'ESTIMATED', 'SUPPORTING', 'UNAVAILABLE']
      .map(k => `<li><strong>${esc(t('evidence.' + k))}</strong> — ${
        esc(t('evidence.' + k + '.plain'))}</li>`).join('')}</ul>
    <div class="notice">${esc(t('evidence.vsUnavailable'))}</div>
    <p class="plain">${esc(t('confidence.notNumeric'))}</p></section>

  <section class="panel">
    <p class="panel-title"><span>${esc(t('methodology.gap'))}</span></p>
    <div class="unavail"><strong>NUMERIC_GAP: ${esc(mode.NUMERIC_GAP)}</strong>
      <p>${esc(t('methodology.gapBody'))}</p></div>
    <p class="panel-title" style="margin-top:14px">
      <span>${esc(t('methodology.hybrid'))}</span></p>
    <div class="notice"><strong>HYBRID_PRESSURE_INDICATOR:
      ${esc(mode.HYBRID_PRESSURE_INDICATOR)}</strong>
      <p>${esc(t('methodology.hybridBody'))}</p></div></section>

  ${panel({ titleKey: 'methodology.vintages', explain: 'explain.vintages',
    qualifiers: `<p class="plain">${esc(t('methodology.vintagesBody'))}</p>`,
    body: table([{ label: 'Output', get: r => r.output || r.input, cls: 'name' },
                 { label: 'Vintage column', key: 'vintage_column' }],
      (c.data.vintage_policy || {}).known_vintages || [],
      'Each output carries its own vintage column; no global date applies') })}

  <section class="panel">
    <p class="panel-title"><span>${esc(t('methodology.derivation'))}</span></p>
    <p class="lede">${esc(t('explain.derivation.what'))}</p>
    ${points('explain.derivation.points')}
    <div class="notice">${esc(t('derivation.note'))}</div>
    ${(c.data.derivation_inputs || []).map(d => `<details>
      <summary><code>${esc(d.input)}</code> → ${esc(d.is_input_to.join(', '))}</summary>
      <p class="plain">${esc(d.note)}</p>
      <p class="plain">May be shown under: ${esc(d.permitted_section_labels.join(' · '))}</p>
      <p class="prohibited">Must not be labelled: ${esc(d.prohibited_labels.join(' · '))}</p>
      </details>`).join('')}</section>

  <section class="panel">
    <p class="panel-title"><span>${esc(t('methodology.perOutput'))}</span></p>
    <p class="lede">${esc(t('explain.peroutput.what'))}</p>
    ${points('explain.peroutput.points')}
    ${rows}</section>`;
}

async function pageCoverage() {
  const [cov, q] = await Promise.all([get('/coverage'), get('/quality')]);
  const d = cov.meta.derived_disclosures || {};
  return `${pageHead('coverage.heading', 'coverage.lede')}
  ${panel({ titleKey: 'coverage.metrics', explain: 'explain.coverage',
    exportId: 'demand_coverage_summary',
    qualifiers: `<div class="notice"><strong>${esc(t('coverage.label'))} — derived from the warehouse</strong>
      ${Object.entries(d).map(([k, v]) => `<div>${esc(v.label)}:
        <strong>${v.unit === 'ratio' ? pct(v.value) : count(v.value)}</strong>
        <span class="plain">(${esc(v.derived_from)})</span></div>`).join('')}</div>`,
    body: `${table([{ label: 'Domain', get: r => r.domain_label || r.domain, cls: 'name' },
             { label: 'Metric', key: 'metric' },
             { label: 'Value', num: true, get: r => count(r.value) },
             { label: 'Unit', key: 'unit' }, { label: 'Note', key: 'note' }],
      cov.data, 'Coverage metrics as published by the pipeline')}
      <h3 style="margin-top:20px">${esc(t('coverage.barred'))}</h3>
      <p class="plain">${esc(t('coverage.barredNote'))}</p>
      <ul class="reasons">${(cov.meta.barred_fields || [])
        .map(f => `<li><code>${esc(f)}</code></li>`).join('')}</ul>` })}

  ${panel({ titleKey: 'coverage.quality', explain: 'explain.quality',
    body: table([{ label: 'Table', key: 'table_name', cls: 'name' },
             { label: 'Check', key: 'check_name' },
             { label: 'Status', key: 'status' }, { label: 'Observed', key: 'observed' },
             { label: 'Expected', key: 'expected' }, { label: 'Severity', key: 'severity' }],
      q.data, 'Pipeline contract checks') })}`;
}

async function pageUnavailable() {
  const c = await get('/capabilities');
  const grouped = c.meta.grouped_by_reason_code || {};
  const meaning = c.meta.reason_code_meaning || {};
  const byId = Object.fromEntries(c.data.map(r => [r.capability_id, r]));
  return `${pageHead('unavailable.heading', 'unavailable.intro')}
  <section class="panel">
    <p class="lede">${esc(t('explain.unavailable.what'))}</p>
    ${points('explain.unavailable.points')}</section>
  ${Object.entries(grouped).map(([code, ids]) => `
    <section class="panel">
      <p class="panel-title">${badge('UNAVAILABLE', code)}
        <span>${esc(ids.length === 1 ? t('unavailable.groupOne')
          : t('unavailable.group', { n: count(ids.length) }))}</span></p>
      <p class="lede">${esc(meaning[code] || t('reason.' + code))}</p>
      ${ids.map(id => { const r = byId[id]; return `<div class="unavail">
        <strong>${esc(r.capability_id)}</strong>
        <p>${esc(r.reason)}</p>
        <dl class="kv"><dt>${esc(t('unavailable.reason'))}</dt><dd>${esc(r.reason_code)}</dd>
          <dt>${esc(t('unavailable.gate'))}</dt><dd>${esc(r.blocking_gate)}</dd>
          <dt>is_measured_shortage</dt><dd>${esc(r.is_measured_shortage)}</dd></dl></div>`;
      }).join('')}</section>`).join('')}`;
}

/* ---------------------------------------------------------------- shell ---- */
const RENDER = {
  landing: pageLanding, national: pageNational, state: pageState,
  district: pageDistrict, occupation: pageOccupation,
  methodology: pageMethodology, coverage: pageCoverage, unavailable: pageUnavailable,
};

async function go(page, arg) {
  if (!PAGES.includes(page)) page = 'landing';
  arg = safeArg(arg);
  S.page = page;
  location.hash = arg ? `${page}/${arg}` : page;
  document.querySelectorAll('#nav button').forEach(b =>
    b.setAttribute('aria-current', b.dataset.page === page ? 'page' : 'false'));
  const side = document.getElementById('side');
  const tog = document.getElementById('side-toggle');
  if (side && side.classList.contains('open')) {
    side.classList.remove('open');
    if (tog) tog.setAttribute('aria-expanded', 'false');
  }
  const view = document.getElementById('view');
  view.setAttribute('aria-busy', 'true');
  view.innerHTML = `<div class="card">${esc(t('loading'))}</div>`;
  try {
    view.innerHTML = await RENDER[page](arg);
  } catch (e) {
    view.innerHTML = `<div class="card"><div class="unavail">
      <strong>${esc(t('error'))}</strong><p>${esc(e.message)}</p></div></div>`;
  }
  view.setAttribute('aria-busy', 'false');
}
window.go = go;

function applyStatic() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.title = t('app.title');
}

/* The rail is numbered so its order reads as a route through the system. */
function buildNav() {
  document.getElementById('nav').innerHTML = PAGES.map((p, i) =>
    `<li><button data-page="${p}" onclick="go('${p}')"
      aria-current="${p === S.page ? 'page' : 'false'}"><span class="n"
      aria-hidden="true">${i + 1}</span><span>${esc(t('nav.' + p))}</span></button></li>`
  ).join('');
}

async function boot() {
  const saved = (() => { try { return localStorage.getItem('lmis.lang'); }
                         catch (e) { return null; } })();
  await loadLang(saved || 'en');

  const langs = [{ code: 'en', name: 'English' }, { code: 'hi', name: 'हिन्दी' }];
  const sel = document.getElementById('lang');
  sel.innerHTML = langs.map(l =>
    `<option value="${l.code}" ${l.code === S.lang ? 'selected' : ''}>${esc(l.name)}</option>`
  ).join('');
  sel.onchange = async e => {
    await loadLang(e.target.value);
    applyStatic(); buildNav();
    const [p, a] = (location.hash.slice(1) || 'landing').split('/');
    go(p, a);
  };

  const tog = document.getElementById('side-toggle');
  tog.onclick = () => {
    const side = document.getElementById('side');
    const open = side.classList.toggle('open');
    tog.setAttribute('aria-expanded', open ? 'true' : 'false');
  };

  const c = await get('/meta/contract');
  S.contract = c.data;
  const mode = c.data.mode;
  document.getElementById('mode-chips').innerHTML = [
    t('baseline.chip', { date: '2024-11-15' }),
    `NUMERIC_GAP: ${mode.NUMERIC_GAP}`,
    `FORECASTING: ${mode.FORECASTING}`,
    `is_measured_shortage: ${mode.MEASURED_SHORTAGE}`,
    `MODE: ${mode.OFFICIAL_ANALYTICAL_MODE}`,
  ].map(x => `<span class="chip">${esc(x)}</span>`).join('');
  document.getElementById('footer-contract').textContent =
    `Publication contract ${c.data.contract_version}`;

  /* Filter domains come from the API, so no list is hard-coded in the UI. */
  const f = (await get('/meta/filters')).data;
  S.states = f.states;
  S.occStates = f.states_with_occupation_detail;
  S.divisions = f.nco_2015_divisions;
  S.sectors = f.ncs_sectors;

  applyStatic(); buildNav();
  window.addEventListener('hashchange', () => {
    const [p, a] = (location.hash.slice(1) || 'landing').split('/');
    if (p !== S.page || a) go(p, a);
  });
  const [p, a] = (location.hash.slice(1) || 'landing').split('/');
  go(p, a);
}
boot();
