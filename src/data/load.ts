// AI-assisted (Claude Code, 2026-11-16). Loads the LOCAL prototype export through the dev-only route
// defined in vite.config.ts. A production build has no data route; the app then shows an explicit message.
import type { Dataset } from '../domain/types';

export async function loadPrototype(): Promise<Dataset> {
  const res = await fetch('/__local/prototype.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('로컬 데이터가 없습니다. scripts/publish/export_prototype.py를 먼저 실행하세요.');
  return (await res.json()) as Dataset;
}
