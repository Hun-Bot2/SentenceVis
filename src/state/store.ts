// AI-assisted (Claude Code, 2026-11-16). Single state store (D-011 decision: Vanilla TS + D3).
// Every view reads from and writes to this one object, so selection has exactly one path.

export type Stage = 1 | 2;

export interface AppState {
  stage: Stage; // V1: 1심 only, or 1심 → 2심 (animated transition)
  selectedPairId: string | null;
  selectedCue: { kind: string; index: number } | null; // V2 node whose source sentence is shown
  focus: { side: 'trial' | 'appeal'; span: number[] } | null; // V3 passage to highlight and scroll to
  article: { law: string; article: string; title: string | null; version_date: string | null; paragraph: string | null } | null;
  group: { kind: 'k1' | 'k2'; value: string } | null; // same-type group shown in V2 and highlighted in V1
}

type Listener = (state: AppState, prev: AppState) => void;

export function createStore(initial: AppState) {
  let state = initial;
  const listeners = new Set<Listener>();
  return {
    get: (): AppState => state,
    set(patch: Partial<AppState>): void {
      const prev = state;
      state = { ...state, ...patch };
      listeners.forEach((l) => l(state, prev));
    },
    subscribe(l: Listener): () => void {
      listeners.add(l);
      return () => listeners.delete(l);
    },
  };
}

export type Store = ReturnType<typeof createStore>;
