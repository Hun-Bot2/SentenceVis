// AI-assisted (Claude Code, 2026-11-16). Wires the single store (src/state) to V1, V2, V3 and the legend.
// Selection has one path: view callback → store.set → subscribers re-render.
import { loadPrototype } from '../data/load';
import { createStore } from '../state/store';
import { createV1 } from '../vis/v1';
import { createV2, type CueRef } from '../vis/v2';
import { createV3 } from '../vis/v3';
import { renderLegend } from '../vis/legend';
import type { Appeal } from '../domain/types';
import '../styles/main.css';

function cueSpan(appeal: Appeal, c: CueRef): number[] | null {
  const item = c.kind === 'ground' ? appeal.grounds[c.index] : c.kind === 'disp' ? appeal.dispositions[c.index]
    : c.kind === 'exo' ? appeal.ex_officio[c.index] : appeal.factors[c.index];
  return item?.span ?? null;
}

export async function start(root: HTMLElement): Promise<void> {
  root.innerHTML = `
    <header class="top"><strong>SentenScope</strong><span class="muted"> · 항소심은 왜 형을 바꾸었는가</span>
      <span class="muted tiny"> (프로토타입 · 배치 잠정)</span><span class="spacer"></span>
      <div class="stage" role="group" aria-label="심급">
        <button data-stage="1">1심</button><button data-stage="2">2심으로 ▶</button>
      </div></header>
    <main class="screen">
      <section class="panel p-v1" aria-label="V1 피고인별 형량"></section>
      <section class="panel p-v2" aria-label="V2 항소 이유 경로"></section>
      <section class="panel p-v3" aria-label="V3 원문 대조"></section>
      <aside class="panel p-legend"></aside>
    </main>`;
  const data = await loadPrototype().catch((e: unknown) => {
    root.querySelector('.p-v1')!.textContent = e instanceof Error ? e.message : String(e);
    return null;
  });
  if (!data) return;
  const store = createStore({ stage: 1, selectedPairId: null, selectedCue: null, focus: null, article: null, group: null });
  const pairById = new Map(data.pairs.map((p) => [p.id, p]));
  const appealOf = (pairId: string | null) => {
    const p = pairId ? pairById.get(pairId) : undefined;
    return p ? data.appeals[p.appeal.id] ?? null : null;
  };
  const v1 = createV1(root.querySelector<HTMLElement>('.p-v1')!, data.pairs, {
    onSelect: (id) => store.set({ selectedPairId: id, selectedCue: null, focus: null, article: null }),
    onValue: (id, side, span) => store.set({ selectedPairId: id, selectedCue: null, focus: { side, span } }),
  });
  const v2 = createV2(root.querySelector<HTMLElement>('.p-v2')!,
    (c) => selectCue(c),
    (a) => store.set({ article: a }),
    (kind) => {
      const pair = pairById.get(store.get().selectedPairId ?? '');
      store.set({ group: kind && pair ? { kind, value: pair[kind] } : null });
    },
    (id) => store.set({ selectedPairId: id, selectedCue: null, focus: null, article: null }));
  const selectCue = (c: CueRef): void => {
    const appeal = appealOf(store.get().selectedPairId);
    const span = appeal ? cueSpan(appeal, c) : null;
    store.set({ selectedCue: c, focus: span ? { side: 'appeal', span } : null });
  };
  const v3 = createV3(root.querySelector<HTMLElement>('.p-v3')!, selectCue);
  renderLegend(root.querySelector<HTMLElement>('.p-legend')!);
  const buttons = root.querySelectorAll<HTMLButtonElement>('.stage button');
  buttons.forEach((b) => b.addEventListener('click', () => store.set({ stage: b.dataset.stage === '2' ? 2 : 1 })));

  const draw = (s = store.get(), prev?: ReturnType<typeof store.get>): void => {
    buttons.forEach((b) => b.classList.toggle('on', Number(b.dataset.stage) === s.stage));
    const groupIds = s.group ? new Set(data.pairs.filter((p) => p[s.group!.kind] === s.group!.value).map((p) => p.id)) : null;
    v1.update(s.stage, s.selectedPairId, groupIds);
    const pair = s.selectedPairId ? pairById.get(s.selectedPairId) ?? null : null;
    const appeal = appealOf(s.selectedPairId);
    if (!prev || prev.selectedPairId !== s.selectedPairId || prev.selectedCue !== s.selectedCue || prev.group !== s.group) {
      const group = s.group ? {
        kind: s.group.kind,
        items: data.pairs.filter((p) => p[s.group!.kind] === s.group!.value)
          .map((p) => ({ id: p.id, label: p.appeal.case_no, detail: `${p.trial.case_no} → ${p.appeal.case_no} · ${p.k1} · ${p.k2}` })),
      } : null;
      v2.render(pair, appeal, { k1: pair ? data.meta.k1_counts[pair.k1] ?? 0 : 0, k2: pair ? data.meta.k2_counts[pair.k2] ?? 0 : 0 },
        s.selectedCue as CueRef | null, group);
    }
    if (!prev || prev.selectedPairId !== s.selectedPairId || prev.focus !== s.focus || prev.article !== s.article || prev.selectedCue !== s.selectedCue) {
      const def = pair?.defendants[0];
      const marks = def ? (['trial', 'appeal'] as const).flatMap((side) =>
        (def.fields[side].prison_months.spans ?? []).map((span) => ({ side, span }))) : [];
      const docs: Parameters<typeof v3.render>[1] = {};
      if (pair) {
        const t = data.documents[pair.trial.id], a = data.documents[pair.appeal.id];
        if (t) docs.trial = t;
        if (a) docs.appeal = a;
      }
      const cues = appeal ? [
        ...appeal.grounds.map((g, index) => ({ span: g.span, ref: { kind: 'ground' as const, index }, label: `항소이유: ${g.label}` })),
        ...appeal.dispositions.map((d, index) => ({ span: d.span, ref: { kind: 'disp' as const, index }, label: `판단: ${({ accepted: '인용', rejected: '배척', not_reached: '판단 안 함', reversal: '파기' } as const)[d.type]}` })),
        ...appeal.ex_officio.map((e, index) => ({ span: e.span, ref: { kind: 'exo' as const, index }, label: '직권 판단' })),
        ...appeal.factors.map((f, index) => ({ span: f.span, ref: { kind: 'factor' as const, index }, label: `양형 요소: ${f.label}` })),
      ] : [];
      v3.render(pair, docs, s.focus, marks, s.article, cues);
    }
  };
  store.subscribe((s, prev) => draw(s, prev));
  draw();
}
