// AI-assisted (Claude Code, 2026-11-16). V1 — defendant sentence view (D3).
// Encoding: docs/specs/V1_ENCODING.md. Glyphs come only from glyphs.generated.ts (registry).
// Positions are recomputed from a mutable x scale so the brush zoom (V1_ENCODING: near rows) keeps true months.
import * as d3 from 'd3';
import { GLYPHS } from './glyphs.generated';
import { MAX_MONTHS, type Defendant, type Field, type Pair, type Status } from '../domain/types';

export interface V1Handle { update(stage: 1 | 2, selectedPairId: string | null, groupIds: Set<string> | null): void }
export interface V1Callbacks { onSelect(pairId: string): void; onValue(pairId: string, side: 'trial' | 'appeal', span: number[]): void }

type DefRow = { kind: 'defendant'; key: string; pair: Pair; def: Defendant };
type Row = DefRow | { kind: 'unresolved'; key: string; pair: Pair };

const ROW_H = 26; // ≥ 20px so the small ⟳ above the 2심 glyph fits (V1_ENCODING §3)
const LABEL_W = 150;
const AX0 = LABEL_W + 10;
const AX_W = 480;
const AX1 = AX0 + AX_W;
const COL_X = AX1 + 46;
const SUP_X = COL_X + 86;
const WIDTH = SUP_X + 40;
const TOP = 80; // header band (y 0–40) is kept clear of the axis tick labels (y ≈ 56–66)
const ON_AXIS: Status[] = ['observed', 'derived'];
const REASON_KO: Record<string, string> = { fine: '벌금', acquittal: '무죄', confinement: '금고', exemption: '면소', dismissal: '공소기각', no_parse: '추출 실패' };
const widthOf = (m: number): number => 1 + (5 * m) / MAX_MONTHS; // V1_ENCODING §4 (fixed in months, not zoom)
const reduced = (): boolean => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const onAxis = (f: Field): boolean => ON_AXIS.includes(f.status) && f.value != null;

function glyph(sel: d3.Selection<SVGGElement, unknown, null, undefined>, name: string, second: boolean, size = 12): void {
  const def = GLYPHS[name];
  sel.classed(`glyph glyph-${name}`, true) // add, never overwrite: stage classes live on the same element
    .html(`<g transform="translate(${-size / 2},${-size / 2}) scale(${size / 20})">${def ? (second ? def.second : def.first) : ''}</g>`);
  sel.append('title').text(def?.label ?? name);
}

function suspLabel(f: Field): string {
  switch (f.status) {
    case 'observed':
    case 'derived': return f.value == null ? '유예' : `유예 ${Math.round(f.value / 12)}년`;
    case 'absent_in_text': return '실형';
    case 'not_applicable': return '해당 없음';
    case 'not_scalar': return '일부 유예';
    default: return '?';
  }
}
const suspGlyph = (f: Field): string => (f.status === 'observed' || f.status === 'derived' ? 'observed'
  : f.status === 'absent_in_text' ? 'absent_in_text' : f.status === 'not_applicable' ? 'not_applicable' : 'not_extracted');
const taper = (x1: number, w1: number, x2: number, w2: number): string => `M${x1},${-w1 / 2}L${x2},${-w2 / 2}L${x2},${w2 / 2}L${x1},${w1 / 2}Z`;

export function createV1(container: HTMLElement, pairs: Pair[], cb: V1Callbacks): V1Handle {
  const x = d3.scaleLinear([0, MAX_MONTHS], [AX0, AX1]);
  const rows: Row[] = [];
  pairs.filter((p) => p.defendants.length > 0).flatMap((p) => p.defendants.map((def) => ({ p, def })))
    .sort((a, b) => (b.def.fields.trial.prison_months.value ?? -1) - (a.def.fields.trial.prison_months.value ?? -1))
    .forEach(({ p, def }) => rows.push({ kind: 'defendant', key: def.id, pair: p, def }));
  pairs.filter((p) => p.unresolved_count > 0).forEach((p) => rows.push({ kind: 'unresolved', key: `${p.id}#u`, pair: p }));

  const reasons = d3.rollup(
    rows.flatMap((r) => (r.kind === 'defendant' ? [r.def.fields.trial.prison_months, r.def.fields.appeal.prison_months] : []))
      .filter((f) => f.status === 'not_applicable' || f.status === 'not_extracted'),
    (v) => v.length, (f) => REASON_KO[f.reason ?? ''] ?? (f.reason ?? '기타'));

  const H = TOP + rows.length * ROW_H + 10;
  const svg = d3.select(container).append('svg').attr('class', 'v1').attr('viewBox', `0 0 ${WIDTH} ${H}`).attr('width', '100%');
  svg.append('defs').append('clipPath').attr('id', 'v1-axis-clip').append('rect')
    .attr('x', AX0 - 8).attr('y', -10).attr('width', AX_W + 16).attr('height', H + 20);
  const axisG = svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${TOP - 14})`);
  svg.append('text').attr('x', AX0).attr('y', 14).attr('class', 'muted tiny').text('← 가벼움   징역 개월   무거움 →   (축 위를 끌어 확대 · 두 번 눌러 원래대로)');
  // Outside column header: auto-generated from the data (V1_ENCODING §2), two counts per line so the
  // block ends above the axis band instead of stacking into the tick labels.
  const hdr = svg.append('text').attr('x', COL_X).attr('y', 12).attr('text-anchor', 'middle').attr('class', 'muted tiny');
  hdr.append('tspan').attr('x', COL_X).text('개월로 표시 불가');
  const counts = [...reasons].sort((a, b) => b[1] - a[1]).map(([k, n]) => `${k} ${n}`);
  d3.range(0, counts.length, 2).forEach((i) => hdr.append('tspan').attr('x', COL_X).attr('dy', 12).text(counts.slice(i, i + 2).join(' · ')));
  svg.append('text').attr('x', SUP_X).attr('y', TOP - 8).attr('text-anchor', 'middle').attr('class', 'muted small').text('대법원');

  const g = svg.selectAll<SVGGElement, Row>('g.row').data(rows, (r) => r.key).join('g')
    .attr('class', 'row').attr('transform', (_r, i) => `translate(0,${TOP + i * ROW_H + ROW_H / 2})`)
    .on('click', (_e, r) => cb.onSelect(r.pair.id));
  g.append('rect').attr('class', 'row-bg').attr('x', 0).attr('y', -ROW_H / 2).attr('width', WIDTH).attr('height', ROW_H);
  // Compound case numbers ("2009노1014,2009전노16") are cut to the first number + 외 n; full text in the tooltip.
  const shortNo = (no: string): string => { const parts = no.split(','); return parts.length > 1 ? `${parts[0]} 외 ${parts.length - 1}` : no; };
  g.append('text').attr('x', 4).attr('y', 4).attr('class', 'label').text((r) => shortNo(r.pair.appeal.case_no))
    .append('title').text((r) => r.pair.appeal.case_no);
  g.append('line').attr('class', 'grid').attr('x1', AX0).attr('x2', AX1);

  g.each(function (r) { // Supreme Court margin (V1_ENCODING §3)
    const row = d3.select(this);
    const sup = r.kind === 'defendant' ? r.def.fields.supreme_outcome : r.pair.supreme;
    const m = row.append('g').attr('class', 'supreme stage2');
    if (sup.status === 'not_in_corpus') {
      m.append('line').attr('x1', AX1 + 70).attr('x2', SUP_X - 26).attr('class', 'sup-line');
      m.append('line').attr('x1', SUP_X - 20).attr('x2', SUP_X + 6).attr('class', 'sup-line dots');
      m.append('title').text('대법원 판결이 이 자료에 없음(상고가 없었다는 뜻이 아님)');
      return;
    }
    m.append('line').attr('x1', AX1 + 70).attr('x2', SUP_X - 9).attr('class', 'sup-line');
    const kinds = new Set((sup.value ?? []).map((a) => (a.action === 'dismissed' ? 'd' : 'r')));
    const gg = m.append('g').attr('transform', `translate(${SUP_X},0)`);
    if (sup.status === 'not_extracted' || kinds.size === 0) glyph(gg, 'not_extracted', false);
    else if (kinds.size === 2) gg.append('text').attr('class', 'small').attr('x', -16).attr('y', 4).text('일부 파기');
    else glyph(gg, kinds.has('d') ? 'supreme_dismissed' : 'supreme_reversed', false);
  });

  g.filter((r) => r.kind === 'unresolved').append('text').attr('x', AX0).attr('y', 4).attr('class', 'muted small')
    .text((r) => `▸ 공동피고인 ${r.pair.unresolved_count}명 · 정렬 전 (값 미배정)`);

  const dg = g.filter((r) => r.kind === 'defendant') as unknown as d3.Selection<SVGGElement, DefRow, SVGSVGElement, unknown>;
  dg.each(function (r) {
    const row = d3.select(this);
    const f = r.def.fields;
    const t = f.trial.prison_months, a = f.appeal.prison_months;
    const clip = row.append('g').attr('clip-path', 'url(#v1-axis-clip)');
    clip.append('path').attr('class', 'taper');
    clip.append('line').attr('class', 'connector stage2');
    // not_scalar: one ∅ per separate term at its true month (V1_ENCODING §2)
    (['trial', 'appeal'] as const).forEach((side) => {
      if (f[side].prison_months.status !== 'not_scalar') return;
      r.def.terms[side].forEach((term) => {
        const gg = clip.append('g').attr('class', `g-term ${side === 'appeal' ? 'stage2' : ''}`).attr('data-m', term.months);
        glyph(gg, 'not_scalar', side === 'appeal');
        gg.on('click', (e: Event) => { e.stopPropagation(); cb.onValue(r.pair.id, side, term.span); });
      });
    });
    const gt = (onAxis(t) ? clip : row).append('g').attr('class', 'g-trial');
    if (t.status !== 'not_scalar') glyph(gt, t.status, false);
    gt.on('click', (e: Event) => { e.stopPropagation(); if (t.spans?.[0]) cb.onValue(r.pair.id, 'trial', t.spans[0]); });
    const ga = (onAxis(a) ? clip : row).append('g').attr('class', 'g-appeal');
    if (a.status !== 'not_scalar') glyph(ga, a.status, true);
    ga.on('click', (e: Event) => { e.stopPropagation(); if (a.spans?.[0]) cb.onValue(r.pair.id, 'appeal', a.spans[0]); });
    glyph(clip.append('g').attr('class', 'g-merged stage2'), 'observed_merged', true);
    if ((f.supreme_outcome.value ?? []).some((s) => s.action !== 'dismissed')) glyph(clip.append('g').attr('class', 'g-notfinal stage2'), 'supreme_reversed', false, 7);
    row.append('g').attr('class', 'susp');
  });

  let stage: 1 | 2 = 1;
  let selected: string | null = null;
  let groupIds: Set<string> | null = null;
  function layout(dur: number): void {
    axisG.transition().duration(dur).call(d3.axisTop(x).ticks(8));
    g.classed('selected', (r) => r.pair.id === selected)
      .classed('in-group', (r) => !!groupIds && groupIds.has(r.pair.id))
      .classed('out-group', (r) => !!groupIds && !groupIds.has(r.pair.id));
    svg.selectAll('.stage2').transition().duration(dur).style('opacity', stage === 2 ? 1 : 0);
    dg.each(function (r) {
      const row = d3.select(this);
      const f = r.def.fields;
      const t = f.trial.prison_months, a = f.appeal.prison_months;
      const two = stage === 2;
      const tx = onAxis(t) ? x(t.value!) : COL_X - 9;
      const ax = onAxis(a) ? x(a.value!) : COL_X + 9;
      const both = onAxis(t) && onAxis(a);
      const same = both && t.value === a.value;
      const tw = widthOf(t.value ?? 0), aw = widthOf(a.value ?? 0);
      row.selectAll<SVGGElement, unknown>('g.g-term').attr('transform', function () { return `translate(${x(Number(this.dataset.m))},0)`; });
      // Taper grows thicker toward the heavier instance (V1_ENCODING §4); animated 1심 → 2심.
      row.select<SVGPathElement>('path.taper').style('display', both ? 'inline' : 'none').transition().duration(dur)
        .attrTween('d', function () {
          const el = this as SVGPathElement & { _p?: number[] };
          const from = el._p ?? [tx, tw, tx, tw];
          const to = two ? [tx, tw, ax, aw] : [tx, tw, tx, tw];
          el._p = to;
          const i = d3.interpolateArray(from, to);
          return (k: number) => { const v = i(k); return taper(v[0]!, v[1]!, v[2]!, v[3]!); };
        });
      row.select('.g-trial').transition().duration(dur).attr('transform', `translate(${tx},0)`).style('opacity', two && same ? 0 : 1);
      row.select('.g-appeal').transition().duration(dur).attr('transform', `translate(${two ? ax : tx},0)`).style('opacity', two && !same ? 1 : 0);
      row.select('.g-merged').attr('transform', `translate(${tx},0)`).style('display', same ? 'inline' : 'none');
      row.select('.g-notfinal').attr('transform', `translate(${ax},-11)`);
      row.select('line.connector').attr('x1', tx).attr('x2', ax).style('display', both ? 'none' : 'inline');
      // Suspension label (merged text, V1_ENCODING §5)
      const ts = f.trial.suspension_months, as = f.appeal.suspension_months;
      const a1 = suspLabel(ts), a2 = suspLabel(as);
      const text = !two ? a1 : a1 === a2 ? `${a2} 유지` : `${a1} → ${a2}`;
      const lo = Math.min(tx, two ? ax : tx), hi = Math.max(tx, two ? ax : tx);
      const flip = hi + 100 > AX1 + 30;
      const lx = flip ? lo - 12 : hi + 12;
      const s = row.select<SVGGElement>('g.susp').html('');
      // When zoomed, a label whose glyphs are all outside the visible months would point at nothing.
      if ((onAxis(t) || onAxis(a)) && (hi < AX0 - 8 || lo > AX1 + 8)) return;
      glyph(s.append('g').attr('transform', `translate(${flip ? lx - 4 : lx + 4},0)`), suspGlyph(two ? as : ts), false, 9);
      s.append('text').attr('class', 'susp-text').attr('x', flip ? lx - 12 : lx + 12).attr('y', 4).attr('text-anchor', flip ? 'end' : 'start').text(text);
    });
  }

  // Brush on the axis band: zoom keeps true positions (no jitter); double-click resets (V1_ENCODING, near rows).
  const brushG = svg.append('g').attr('class', 'brush');
  const brush = d3.brushX().extent([[AX0, TOP - 30], [AX1, TOP - 4]]).on('end', (e: d3.D3BrushEvent<unknown>) => {
    if (!e.selection) return;
    const [s0, s1] = e.selection as [number, number];
    brushG.call(brush.move, null);
    if (s1 - s0 < 6) return;
    x.domain([x.invert(s0), x.invert(s1)]);
    layout(reduced() ? 0 : 500);
  });
  brushG.call(brush).on('dblclick', () => { x.domain([0, MAX_MONTHS]); layout(reduced() ? 0 : 500); });

  return {
    update(nextStage, nextSelected, nextGroup) {
      const dur = nextStage !== stage && !reduced() ? 900 : 0;
      stage = nextStage;
      selected = nextSelected;
      groupIds = nextGroup;
      layout(dur);
    },
  };
}
