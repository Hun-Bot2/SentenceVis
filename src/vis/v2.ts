// AI-assisted (Claude Code, 2026-11-16). V2 — appeal reasoning path (5 lanes), prototype.
// Decided: 5 lanes, origin = text badge, disposition = line-end mark + text (V2_ENCODING §1–2).
// Not decided yet (shown as one candidate, marked in the UI): change display, source/verification line style,
// how to collapse very long judgments, how statute/factor details open (V2_ENCODING "남은 결정").
import * as d3 from 'd3';
import type { Appeal, Pair } from '../domain/types';

export interface CueRef { kind: 'ground' | 'disp' | 'exo' | 'factor'; index: number }
export interface GroupItem { id: string; label: string; detail: string }
export interface V2Group { kind: 'k1' | 'k2'; items: GroupItem[] }
export interface V2Handle { render(pair: Pair | null, appeal: Appeal | null, counts: { k1: number; k2: number }, cue: CueRef | null, group: V2Group | null): void }

const DISP_KO = { accepted: '인용', rejected: '배척', not_reached: '판단 안 함', reversal: '파기' } as const;
const MAX_DISP = 8; // prototype cap; the collapse rule is still undecided

export interface ArticleRef { law: string; article: string; title: string | null; version_date: string | null; paragraph: string | null }

export function createV2(container: HTMLElement, onCue: (c: CueRef) => void, onArticle: (a: ArticleRef) => void,
  onGroup: (kind: 'k1' | 'k2' | null) => void, onPick: (pairId: string) => void): V2Handle {
  const root = d3.select(container).append('div').attr('class', 'v2');
  const summary = root.append('div').attr('class', 'v2-summary');
  const groupBox = root.append('div').attr('class', 'v2-group');
  const grid = root.append('div').attr('class', 'v2-grid');
  const overlay = root.append('svg').attr('class', 'v2-edges');
  const defs = overlay.append('defs');
  defs.append('marker').attr('id', 'm-accepted').attr('viewBox', '0 0 10 10').attr('refX', 9).attr('refY', 5)
    .attr('markerWidth', 7).attr('markerHeight', 7).attr('orient', 'auto').append('path').attr('d', 'M0,0L10,5L0,10Z').attr('class', 'mk-fill');
  defs.append('marker').attr('id', 'm-rejected').attr('viewBox', '0 0 4 12').attr('refX', 3).attr('refY', 6)
    .attr('markerWidth', 4).attr('markerHeight', 10).attr('orient', 'auto').append('rect').attr('width', 3).attr('height', 12).attr('class', 'mk-fill');
  defs.append('marker').attr('id', 'm-not_reached').attr('viewBox', '0 0 12 12').attr('refX', 11).attr('refY', 6)
    .attr('markerWidth', 8).attr('markerHeight', 8).attr('orient', 'auto').append('circle').attr('cx', 6).attr('cy', 6).attr('r', 4.5).attr('class', 'mk-open');

  const lanes = ['항소이유 · 제기', '판단', '법령의 적용 (양형 단계)', '양형 요소', '원문'];
  const cols = grid.selectAll('div.lane').data(lanes).join('div').attr('class', 'lane');
  cols.append('div').attr('class', 'lane-title').text((d) => d);
  const body = cols.append('div').attr('class', 'lane-body');
  const lane = (i: number) => d3.select(body.nodes()[i] as HTMLDivElement);

  function render(pair: Pair | null, appeal: Appeal | null, counts: { k1: number; k2: number }, cue: CueRef | null, group: V2Group | null): void {
    body.html('');
    overlay.selectAll('path.edge').remove();
    edgeSpecs = [];
    if (!pair || !appeal) {
      summary.text('V1에서 행을 누르면 그 사건의 항소 경로가 나옵니다.');
      groupBox.html('');
      return;
    }
    summary.html('');
    summary.append('strong').text(`${pair.trial.case_no} → ${pair.appeal.case_no}`);
    // Same-type summary (V2_ENCODING §1: K1 and K2). Clicking opens the list and highlights the rows in V1.
    const link = (kind: 'k1' | 'k2', text: string) => summary.append('button').attr('class', `group-link ${group?.kind === kind ? 'on' : ''}`)
      .text(text).on('click', () => onGroup(group?.kind === kind ? null : kind));
    summary.append('span').text('  ');
    link('k1', `같은 항소이유 조합(${pair.k1}) ${counts.k1}건`);
    link('k2', `같은 결과·직권(${pair.k2}) ${counts.k2}건`);
    summary.append('span').attr('class', 'muted tiny').text(' — 이 자료 안의 건수');
    groupBox.html('');
    if (group) {
      groupBox.append('div').attr('class', 'tiny muted').text(`${group.kind === 'k1' ? '같은 항소이유 조합' : '같은 결과·직권'} ${group.items.length}건 · V1에서 강조됨 · 눌러서 그 사건으로 이동`);
      const list = groupBox.append('div').attr('class', 'group-list');
      group.items.forEach((it) => list.append('button').attr('class', `group-item ${it.id === pair.id ? 'on' : ''}`)
        .attr('title', it.detail).text(it.label).on('click', () => onPick(it.id)));
    }

    // Lane 1: grounds (one node per ground type in the 항소이유 요지) + ex officio node
    const gmap = d3.group(appeal.grounds.map((g, i) => ({ g, i })).filter((d) => d.g.in_summary), (d) => d.g.label);
    const gnodes = [...gmap].map(([label, items]) => ({ label, origins: [...new Set(items.map((d) => d.g.origin))], first: items[0]?.i ?? 0 }));
    const l1 = lane(0);
    gnodes.forEach((n) => {
      const el = l1.append('div').attr('class', 'node').attr('data-ground', n.label)
        .classed('active', cue?.kind === 'ground' && cue.index === n.first)
        .on('click', () => onCue({ kind: 'ground', index: n.first }));
      el.append('span').text(n.label);
      n.origins.forEach((o) => el.append('span').attr('class', `badge badge-${o}`).text(o));
    });
    if (appeal.ex_officio.length) {
      const el = l1.append('div').attr('class', 'node').attr('data-ground', '직권')
        .classed('active', cue?.kind === 'exo').on('click', () => onCue({ kind: 'exo', index: 0 }));
      el.append('span').text('직권 판단');
      el.append('span').attr('class', 'badge badge-직권').text('직권');
    }
    if (!gnodes.length && !appeal.ex_officio.length) l1.append('div').attr('class', 'muted').text('항소이유를 찾지 못함');

    // Lane 2: dispositions (first MAX_DISP), each linked to its proposed ground (rule_proximity, unverified)
    const l2 = lane(1);
    const disp = appeal.dispositions.map((d, i) => ({ d, i }));
    disp.slice(0, MAX_DISP).forEach(({ d, i }) => {
      l2.append('div').attr('class', `node disp disp-${d.type}`).attr('data-disp', i)
        .classed('active', cue?.kind === 'disp' && cue.index === i)
        .on('click', () => onCue({ kind: 'disp', index: i }))
        .text(d.target ? `${d.target} → ${DISP_KO[d.type]}` : DISP_KO[d.type]);
    });
    if (disp.length > MAX_DISP) l2.append('div').attr('class', 'muted small').text(`+${disp.length - MAX_DISP}개 더 (묶는 규칙 미정)`);
    if (!disp.length) l2.append('div').attr('class', 'muted').text('판단 단서를 찾지 못함');
    l2.append('div').attr('class', 'muted tiny').text('연결: 규칙이 제안한 관계 · 미검증');

    // Lane 3: law application steps + statute change candidate (unreviewed)
    const l3 = lane(2);
    if (appeal.statute_change && (appeal.statute_change.added.length || appeal.statute_change.removed.length)) {
      const ch = l3.append('div').attr('class', 'change');
      ch.append('div').attr('class', 'tiny muted').text('1심 대비 범죄 조문 변화 (미검증 후보)');
      appeal.statute_change.removed.forEach((s) => ch.append('div').attr('class', 'small').text(`− ${s}`));
      appeal.statute_change.added.forEach((s) => ch.append('div').attr('class', 'small').text(`+ ${s}`));
    }
    if (!appeal.steps.length) l3.append('div').attr('class', 'muted').text('항소심 판결에 법령의 적용이 없음');
    appeal.steps.filter((s) => s.articles.length || s.step !== 'unlabeled').forEach((s) => {
      const st = l3.append('div').attr('class', 'step');
      st.append('div').attr('class', 'step-label').text(s.label);
      s.articles.slice(0, 6).forEach((a) => {
        st.append('span').attr('class', `chip ${a.kb_status === 'contextual' ? '' : 'chip-missing'}`)
          .on('click', () => onArticle({ law: a.law, article: a.article, title: a.title, version_date: a.version_date, paragraph: a.first_paragraph }))
          .text(`${a.law} ${a.article.replace('-', '조의')}조`)
          .attr('title', a.title
            ? `${a.title}\n${a.first_paragraph ?? ''}\n(지식베이스 ${a.version_date} 판본 — 판결 당시와 다를 수 있음)`
            : '조문 본문이 이 자료에 없음');
      });
    });

    // Lane 4: sentencing factors
    const l4 = lane(3);
    if (!appeal.factors.length) l4.append('div').attr('class', 'muted').text('양형 요소를 찾지 못함')
      .attr('title', appeal.factor_status === 'absent_in_text' ? '판결문에 양형이유 절이 없음' : '양형이유 절은 있으나 자동 추출에서 찾지 못함');
    appeal.factors.forEach((f, i) => {
      l4.append('div').attr('class', 'node factor').classed('active', cue?.kind === 'factor' && cue.index === i)
        .on('click', () => onCue({ kind: 'factor', index: i }))
        .text(f.label + (f.polarity === 'mitigating' ? ' · 유리한 정상' : f.polarity === 'aggravating' ? ' · 불리한 정상' : ''));
    });

    // Lane 5: source sentence of the selected node (V3 will replace this lane's role)
    const l5 = lane(4);
    const pick = cue?.kind === 'ground' ? appeal.grounds[cue.index] : cue?.kind === 'disp' ? appeal.dispositions[cue.index]
      : cue?.kind === 'exo' ? appeal.ex_officio[cue.index] : cue?.kind === 'factor' ? appeal.factors[cue.index] : undefined;
    if (!pick) l5.append('div').attr('class', 'muted').text('노드를 누르면 그 근거 문장이 여기에 나옵니다.');
    else if (pick.text == null) {
      const w = l5.append('div').attr('class', 'withheld');
      [140, 110, 150].forEach((wd) => w.append('div').attr('class', 'bar').style('width', `${wd}px`));
      w.append('div').attr('class', 'tiny muted').text('개인정보 보호로 가림');
    } else l5.append('blockquote').text(pick.text);

    // Edges: ground → disposition (line-end mark = disposition). Element references are kept and
    // positions are re-measured whenever the V2 box changes size (layout can change after render).
    edgeSpecs = [];
    l2.selectAll<HTMLDivElement, unknown>('div.disp').each(function () {
      const d = appeal.dispositions[Number(this.dataset.disp)];
      const srcLabel = d?.type === 'reversal' ? '직권' : d?.target;
      const src = srcLabel ? l1.select<HTMLDivElement>(`div[data-ground="${srcLabel}"]`).node() : null;
      if (d && src) edgeSpecs.push({ s: src, t: this, type: d.type });
    });
    requestAnimationFrame(drawEdges);
  }

  let edgeSpecs: { s: HTMLElement; t: HTMLElement; type: string }[] = [];
  function drawEdges(): void {
    const box = (root.node() as HTMLDivElement).getBoundingClientRect();
    overlay.attr('width', box.width).attr('height', box.height);
    overlay.selectAll('path.edge').data(edgeSpecs).join('path').attr('class', (e) => `edge edge-${e.type}`)
      .attr('d', (e) => {
        const a = e.s.getBoundingClientRect();
        const b = e.t.getBoundingClientRect();
        const x1 = a.right - box.left, y1 = a.top + a.height / 2 - box.top;
        const x2 = b.left - box.left - 2, y2 = b.top + b.height / 2 - box.top;
        return `M${x1},${y1}C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`;
      })
      .attr('marker-end', (e) => (['accepted', 'rejected', 'not_reached'].includes(e.type) ? `url(#m-${e.type})` : null));
  }
  new ResizeObserver(() => drawEdges()).observe(root.node() as HTMLDivElement);
  return { render };
}
