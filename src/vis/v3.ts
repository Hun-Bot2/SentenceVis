// AI-assisted (Claude Code, 2026-11-16). V3 — synchronized evidence view (D3), PROVISIONAL.
// Follows the slide / VISUAL_DESIGN §6 candidate as-is (not yet reviewed by the user):
// two document strips in reading order (block height ∝ section length), same-title sections joined by a
// ribbon (structural correspondence only, not a semantic or causal link), the selected passage highlighted,
// and a statute panel with the KB version warning. Withheld documents show bars, never text.
import * as d3 from 'd3';
import { GLYPHS } from './glyphs.generated';
import type { DocumentText, Pair } from '../domain/types';

export interface V3Focus { side: 'trial' | 'appeal'; span: number[] }
export interface V3Article { law: string; article: string; title: string | null; version_date: string | null; paragraph: string | null }
export interface V3Cue { span: number[]; ref: { kind: 'ground' | 'disp' | 'exo' | 'factor'; index: number }; label: string }
export interface V3Handle { render(pair: Pair | null, docs: { trial?: DocumentText; appeal?: DocumentText }, focus: V3Focus | null, marks: V3Focus[], article: V3Article | null, cues: V3Cue[]): void }

const STRIP_H = 220;
const TITLE_KO: Record<string, string> = { 주문: '주문', 이유: '이유', 원심판결: '원심판결', 법령의적용: '법령의 적용', 범죄사실: '범죄사실', 양형의이유: '양형의 이유', 양형이유: '양형이유' };

export function createV3(container: HTMLElement, onCue: (ref: V3Cue['ref']) => void): V3Handle {
  const root = d3.select(container).append('div').attr('class', 'v3');
  root.append('div').attr('class', 'v3-title').html('원문 대조 <span class="muted tiny">(잠정: 슬라이드 후보)</span>');
  const top = root.append('div').attr('class', 'v3-top');
  const ribbons = top.append('svg').attr('class', 'v3-ribbons');
  const sides = top.selectAll('div.v3-side').data(['trial', 'appeal'] as const).join('div').attr('class', 'v3-side');
  const statute = root.append('div').attr('class', 'v3-statute');

  function render(pair: Pair | null, docs: { trial?: DocumentText; appeal?: DocumentText }, focus: V3Focus | null, marks: V3Focus[], article: V3Article | null, cues: V3Cue[]): void {
    sides.html('');
    ribbons.selectAll('*').remove();
    statute.html('');
    if (!pair) {
      sides.filter((_d, i) => i === 0).append('div').attr('class', 'muted').text('V1에서 행을 고르면 1심·2심 판결문이 나란히 나옵니다.');
      return;
    }
    const stripBlocks: { trial: Map<string, DOMRect>; appeal: Map<string, DOMRect> } = { trial: new Map(), appeal: new Map() };
    sides.each(function (side) {
      const doc = docs[side];
      const el = d3.select(this);
      const head = el.append('div').attr('class', 'v3-head');
      head.append('svg').attr('width', 14).attr('height', 14).attr('viewBox', '-2 -2 24 24').html(GLYPHS.judgment_document?.first ?? '');
      // One line per header: long compound case numbers are cut with an ellipsis (full text in the tooltip),
      // court · date go on their own line so nothing wraps into the strip.
      const parts = pair[side].case_no.split(',');
      const title = head.append('div').attr('class', 'v3-head-text').attr('title', pair[side].case_no);
      title.append('strong').text(`${side === 'trial' ? '1심' : '2심'} ${parts[0]}${parts.length > 1 ? ` 외 ${parts.length - 1}건` : ''}`);
      title.append('div').attr('class', 'muted tiny').text(`${pair[side].court} · ${pair[side].date}`);
      if (!doc) { el.append('div').attr('class', 'muted').text('문서 없음'); return; }
      const body = el.append('div').attr('class', 'v3-body');
      const strip = body.append('div').attr('class', 'v3-strip').style('height', `${STRIP_H}px`);
      const total = Math.max(1, doc.length);
      doc.sections.forEach((s) => {
        const h = Math.max(3, ((s.end - s.start) / total) * STRIP_H);
        const b = strip.append('div').attr('class', 'v3-block').attr('data-title', s.title)
          .style('height', `${h}px`)
          .attr('title', TITLE_KO[s.title] ?? s.title)
          .on('click', () => (el.select(`[data-sec="${s.title}"]`).node() as HTMLElement | null)?.scrollIntoView({ block: 'start' }));
        // A label is written only when the block is tall enough for one line; otherwise the tooltip carries it.
        if (h >= 13) b.append('span').text(TITLE_KO[s.title] ?? s.title);
      });
      const textPane = body.append('div').attr('class', 'v3-text');
      if (doc.text == null) {
        const w = textPane.append('div').attr('class', 'withheld');
        [220, 180, 240, 200, 160].forEach((wd) => w.append('div').attr('class', 'bar').style('width', `${wd}px`));
        w.append('div').attr('class', 'tiny muted').text('개인정보 보호로 가림 (이 판결문은 실명이 남은 사본뿐임)');
      } else {
        const sideMarks = marks.filter((m) => m.side === side);
        doc.sections.forEach((s) => {
          const sec = textPane.append('section').attr('data-sec', s.title);
          sec.append('h4').text(TITLE_KO[s.title] ?? s.title);
          const p = sec.append('p');
          type Cut = { a: number; b: number; cls: string; cue?: V3Cue };
          const inSec = (sp: number[]) => (sp[0] ?? 0) < s.end && (sp[1] ?? 0) > s.start;
          const clamp = (sp: number[]) => ({ a: Math.max(s.start, sp[0] ?? 0), b: Math.min(s.end, sp[1] ?? 0) });
          const cuts: Cut[] = [
            ...(focus?.side === side && inSec(focus.span) ? [{ ...clamp(focus.span), cls: 'focus' }] : []),
            ...sideMarks.filter((m) => inSec(m.span)).map((m) => ({ ...clamp(m.span), cls: 'value' })),
            // Cue phrases of the appeal judgment are clickable: reverse selection V3 → V2 (VISUAL_DESIGN §6).
            ...(side === 'appeal' ? cues.filter((c) => inSec(c.span)).map((c) => ({ ...clamp(c.span), cls: 'cue', cue: c })) : []),
          ].sort((x, y) => x.a - y.a || (x.cls === 'focus' ? -1 : 1));
          let pos = s.start;
          cuts.forEach((c) => {
            if (c.a < pos) return;
            p.append('span').text(doc.text!.slice(pos, c.a));
            const m = p.append('mark').attr('class', c.cls).text(doc.text!.slice(c.a, c.b));
            const cue = c.cue ?? (c.cls === 'focus' ? cues.find((q) => q.span[0] === c.a) : undefined);
            if (cue) m.classed('cue', true).attr('title', `${cue.label} — 눌러서 V2에서 선택`).on('click', () => onCue(cue.ref));
            pos = c.b;
          });
          p.append('span').text(doc.text!.slice(pos, s.end));
        });
        requestAnimationFrame(() => (textPane.select('mark.focus').node() as HTMLElement | null)?.scrollIntoView({ block: 'center' }));
      }
      requestAnimationFrame(() => strip.selectAll<HTMLDivElement, unknown>('div.v3-block').each(function () {
        stripBlocks[side].set(this.dataset.title ?? '', this.getBoundingClientRect());
      }));
    });
    // Ribbons between same-title sections (drawn after both strips are laid out)
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const box = (top.node() as HTMLDivElement).getBoundingClientRect();
      ribbons.attr('width', box.width).attr('height', box.height);
      const pairs = [...stripBlocks.trial].filter(([t]) => stripBlocks.appeal.has(t) && t !== '');
      ribbons.selectAll('path').data(pairs).join('path').attr('class', 'ribbon')
        .attr('d', ([t, a]) => {
          const b = stripBlocks.appeal.get(t)!;
          const x1 = a.right - box.left, x2 = b.left - box.left, xm = (x1 + x2) / 2;
          const a1 = a.top - box.top, a2 = a.bottom - box.top, b1 = b.top - box.top, b2 = b.bottom - box.top;
          return `M${x1},${a1}C${xm},${a1} ${xm},${b1} ${x2},${b1}L${x2},${b2}C${xm},${b2} ${xm},${a2} ${x1},${a2}Z`;
        })
        .append('title').text(([t]) => `${TITLE_KO[t] ?? t}: 같은 이름의 구획(구조 대응이며 의미·인과 연결이 아님)`);
    }));
    // Statute panel
    if (article) {
      statute.append('div').attr('class', 'v3-statute-title').text(`${article.law} 제${article.article.replace('-', '조의')}조 ${article.title ?? ''}`);
      if (article.paragraph) statute.append('p').text(article.paragraph);
      statute.append('div').attr('class', 'tiny muted').text(article.title
        ? `AI-Hub 법률 지식베이스 ${article.version_date ?? ''} 판본 — 판결 당시 조문과 다를 수 있음`
        : '이 조문의 본문은 이 자료에 없음');
    } else statute.append('div').attr('class', 'tiny muted').text('V2의 조문을 누르면 조문 풀이가 여기에 나옵니다.');
  }
  return { render };
}
