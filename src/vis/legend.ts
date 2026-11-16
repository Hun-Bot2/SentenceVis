// AI-assisted (Claude Code, 2026-11-16). Always-visible global legend (professor feedback; V1_ENCODING §7).
import * as d3 from 'd3';
import { GLYPHS } from './glyphs.generated';

const ITEMS: [string, string][] = [
  ['observed', '판결 주문에 적힌 징역'],
  ['observed_merged', '1심과 2심의 징역이 같음'],
  ['derived', '항소기각으로 1심 형이 유지됨(유도한 값)'],
  ['not_scalar', '형이 여러 개라 숫자 하나로 보이지 않음'],
  ['absent_in_text', '주문에 해당 조항 없음(예: 집행유예 없음 = 실형)'],
  ['not_applicable', '이 형 종류에는 해당 없음(벌금·무죄 등)'],
  ['not_extracted', '원문은 있으나 자동 추출 실패'],
  ['supreme_dismissed', '대법원 상고기각: 2심 판결 확정'],
  ['supreme_reversed', '대법원 파기환송: 2심 형은 최종 형이 아님'],
  ['judgment_document', '판결 문서'],
];

export function renderLegend(container: HTMLElement): void {
  const root = d3.select(container).append('div').attr('class', 'legend');
  root.append('div').attr('class', 'legend-title').text('범례');
  root.append('div').attr('class', 'tiny muted').text('도형: 빈 모양·가는 선 = 1심 · 채운 모양·굵은 선 = 2심');
  ITEMS.forEach(([name, text]) => {
    const def = GLYPHS[name];
    const row = root.append('div').attr('class', 'legend-row');
    row.append('svg').attr('width', 34).attr('height', 16).attr('viewBox', '-2 -2 32 24')
      .html(def ? `${def.first}<g transform="translate(14 0)">${name === 'observed' ? def.second : ''}</g>` : '');
    row.append('span').text(text);
  });
  const lines: [string, string][] = [
    ['<path d="M0,7L30,4L30,10Z"/>', '1심→2심 징역: 늘어난 쪽으로 굵어짐'],
    ['<line x1="0" y1="7" x2="30" y2="7" stroke-dasharray="4 2"/>', '징역 → 징역이 아닌 형(무죄·벌금 등)'],
    ['<line x1="0" y1="7" x2="18" y2="7"/><line x1="22" y1="7" x2="30" y2="7" stroke-dasharray="1 3"/>', '대법원 판결이 이 자료에 없음'],
  ];
  lines.forEach(([svg, text]) => {
    const row = root.append('div').attr('class', 'legend-row');
    row.append('svg').attr('class', 'legend-line').attr('width', 34).attr('height', 14).html(svg);
    row.append('span').text(text);
  });
  root.append('div').attr('class', 'legend-sub').text('V2 판단 (선 끝)');
  ([['M0,7L22,7', 'M22,3L30,7L22,11Z', '인용'], ['M0,7L28,7', 'M28,1H31V13H28Z', '배척'], ['M0,7L22,7', '', '판단 안 함']] as const).forEach(([l, m, t]) => {
    const row = root.append('div').attr('class', 'legend-row');
    row.append('svg').attr('class', 'legend-line').attr('width', 34).attr('height', 14)
      .html(`<path d="${l}" fill="none"/>${m ? `<path d="${m}" class="mk-fill"/>` : '<circle cx="26" cy="7" r="4" class="mk-open"/>'}`);
    row.append('span').text(t);
  });
  root.append('div').attr('class', 'tiny muted').text('모든 값은 자동 추출 후보이며 사람 검증 전입니다.');
}
