# ENGINEERING — 구현 아키텍처와 기술 수용 기준

> **2026-11-13 검토:** 구체적인 축·도형·색·뷰 배치·인터랙션은 기존 제안 후보이며 사용자 결정 전이다. 아래 선택 문구는 확정/승인 기록이 아니다. 선택 이유를 에이전트가 대신 결론내리지 않는다. [단계별 힌트](../research/DESIGN_TUTOR.md) · [근거와 확인 범위](../research/RESEARCH_REFERENCES.md) · [검토 기록](../records/REVIEW.md).

**상태:** 개발 기반 F0 구성; 앱 진입·검사 코드만 구현. ZIP inventory·비공개 metadata catalog를 추가했다. 법률 처리기·차트·배포는 미구현. [방법론](DEVELOPMENT_METHOD.md) · [기반 상태](../records/FOUNDATION_STATUS.md) · [Atlas 조사](../research/ENGINEERING_REFERENCE.md).
**강제 제약:** 과제 PDF에 따라 시각화는 **D3.js 혹은 Vega/Vega-Lite**여야 한다. 본 프로젝트는 **D3.js** 채택.

## 1. 기술 선택 상태 (D-011 재검토)

| 계층 | 제안 | 선택 근거 |
|---|---|---|
| 웹 | 현재 Vite+TS+React 임시 진입; 최종 UI 런타임 미결정 | 정적 배포·타입·상태 동기화는 React 고유 근거가 아님. Vanilla TS·React·Vue·Svelte를 동일 기능으로 검토 |
| 시각화 | **D3.js** (`d3-scale`, `d3-axis`, `d3-shape`, `d3-selection`, `d3-brush`) | 과제 명시 허용, 세 시각화의 시각적 제어 |
| 레이아웃 | CSS Grid/Flex, SVG | 도식과 원문 뷰의 분리, 반응형 설계 |
| 상태 | framework-neutral 상태 전이·조회 계약; UI 연결 방식 미정 | view 간 ID 연동·해제·필터 의미를 런타임과 분리 |
| 데이터 전처리 | Python 또는 Node/TS scripts | 수집·정규화·법령 조회·검증 단계가 UI와 독립적 |
| 런타임 데이터 | 사전 검증한 JSON 스냅샷 | 오프라인 데모·API 안정성 확보 |
| 테스트 | 현재 Node test runner(경계 규칙); 기능 단계에서 Vitest/RTL/Playwright 검토 | data invariants, 경로 선택, 데모 회귀 테스트 |
| 배포 | 정적 호스팅 후보: GitHub Pages/Cloudflare Pages/Vercel | 무료/저비용 가능, API 인증값 클라이언트 노출 방지 |

**금지:** Recharts, Chart.js, Highcharts, ECharts, Plotly, Tableau, Matplotlib을 *시각화 구현*에 사용하는 것. 스타일 라이브러리·UI 컴포넌트 등은 시각화와 역할을 분리하면 가능하지만 최종 과제 규정을 확인한다.

## 2. 실제 기반 폴더와 구현 경계

```text
src/       app / domain / data / state / vis / components / features / styles
scripts/   ingest / align / annotate / statutes / publish / checks
tests/     unit / integration / e2e / fixtures/synthetic
data/      raw / private / processed (비공개)
public/    data (export 검토 전 자동 제공 비활성)
artifacts/ validation / design / evaluation / submission (로컬 출력)
docs/      명세 / 조사 / 사용자 결정 / 검증 기록
```

[소스 의존성 규칙](../../src/README.md)을 따른다. 현재 app 진입·checks/unit·ingest inventory/검증·data 테스트를 구현했다. 나머지 기능 폴더는 책임을 예약한 상태다. 이전 SentenceDumbbell 등 구체 차트 파일명은 확정하지 않는다. 기술 도구 기반은 D-010이며 시각화 선택은 D-009를 따른다.

## 3. 데이터 파이프라인 — 온라인 서비스와 분리

```text
AI-Hub private raw ────┐
                       ├→ normalize → pair → align → annotate → verify → export
법령 API + snapshot ───┘                                     │
                                                          ▼
                                             publishable JSON snapshot
                                                          │
                                                          ▼
                                             Shared state + D3 linked views
```

- 원본은 비공개 저장. 파이프라인으로 만든 **배포 허용된 최소값**만 `public/data`에 둔다.
- API 호출에 필요한 인증 토큰과 URL 파라미터는 `scripts/`의 로컬/서버 환경에서만 사용.
- **브라우저에서 원본 API를 실시간 호출하지 않는다.** 특히 API 인증값이 HTML/JS 번들에 들어가지 않게 한다.
- 재현성 메타데이터: `schema_version`, `data_snapshot_id`, `generated_at`, `source_hashes`, `review_status_summary`.
- 원문을 배포할 권한이 없다면 공식 원문 링크 또는 라이선스 허용 범위의 요약/짧은 발췌만 제공하고, V3 범위를 조정한다.

## 4. UI 런타임–D3 경계 (프레임워크 미결정)

- UI 계층(후보 미결정): 뷰의 폭, 선택된 `case_pair_id/defendant_id/ground_id`, 필터·정렬·문맥/범례 확장 상태.
- D3: scale/axis/path/brush/geometry; SVG 마크는 D3 또는 선택할 UI 렌더러 중 한 방식으로 책임 명확화 (동일 요소를 두 렌더러가 동시에 소유하지 않음).
- 한 방향 상태 흐름: `V1 행 선택 → selectedDefendant → V2 경로 정렬/강조 → V3 근거 추출`.
- 역상호작용: `V3 구절 선택 → evidence_id → V2 해당 경로 강조`.
- 선택 가능한 영역은 tooltip뿐 아니라 키보드 및 텍스트 대체 수단도 제공.

### 예시 State 계약

```ts
interface VisSelection {
  casePairId: string | null;
  defendantId: string | null;
  appealGroundId: string | null;
  evidenceId: string | null;
}

interface VisFilters {
  sentenceDirection: 'all' | 'decreased' | 'unchanged' | 'increased';
  suspension: 'all' | 'changed' | 'unchanged';
  origin: 'all' | 'defendant' | 'prosecutor' | 'court_ex_officio';
  verification: 'all' | 'reviewed_only';
}
```

이는 구조 설계를 위한 예시로, 실제 데이터 계약 확정 후 타입을 변경할 수 있다.

## 5. MVP 수용 기준

### V1
- [ ] 사건쌍 내 피고인별 1심·2심 수치가 같은 축에 렌더링
- [ ] 징역 기간, 집행유예 변화가 따로 필터링
- [ ] 공동피고인 정렬 보류 항목은 연결선/차이 계산 없음
- [ ] 정렬·클릭·선택 상태로 V2 연결

### V2
- [ ] 한 항소이유의 제기 주체·법원 판단을 구분해서 표시
- [ ] 직권판단은 당사자 항소이유와 구분
- [ ] 선택 경로 강조, 출처 유형 명시, V3 원문 이동
- [ ] `unreviewed` 상태를 배경색만이 아닌 텍스트로 표시

### V3
- [ ] 두 심급의 원문 근거 문장 동기화
- [ ] 판결문 섹션/출처 ID 표시
- [ ] 원문 부재·권한 제한 시 솔직한 대체 UI
- [ ] 근거 선택 시 V2 역선택

### 공통
- [ ] 화면에서 전역 범례 항상 접근 가능
- [ ] D3 사용이 코드에서 확인 가능
- [ ] 배포 URL과 로컬 시작 명령으로 데모 가능
- [ ] AI 사용 및 외부 코드 출처 표기

## 6. 테스트 / 재현성과 신뢰성

- **Schema tests:** 모든 레코드의 key 비어 있지 않음; valid reference ID; enum values; null handling.
- **Referential integrity:** 각 ground/evidence의 pair/defendant/judgment ID가 실제 레코드로 연결.
- **Semantics:** same term + suspension changed; verdict appeal ex officio; unreviewed path; mentioned-only law.
- **Rendering:** hover/selection/brush; filter changes; linked highlighting; legend sync; disable animations (demo).
- **E2E:** ‘감형 찾기→직권 쟁점 선택→원문 확인’ 경로를 브라우저에서 끝까지 확인.
- **Demo fallback:** 인터넷/법령 API 장애 시에도 저장된 정적 스냅샷으로 동작.
- **Performance:** 모든 데이터 건수에 대해 브러시/스크롤이 끊기지 않는지 측정; 임계치는 실측 후 설정.

## 7. 외부 라이브러리/AI 출처 기록

과제의 공식 규정: **AI나 다른 사람이 작성/수정한 코드 및 보고서 부분을 공개해야 한다.** `report.pdf`에 간략히 쓰는 것으로 끝내지 말고 코드 주석·README·필요하면 `AI_DISCLOSURE` 섹션으로 추적 가능하게 관리.

권장 기록: 도구 이름/버전, 작업 범위, 인간 검토, 외부 코드 출처, 수정 사항. AI가 작성한 법률 해석은 원문 검증 전 결과로 사용하지 않는다.

## 8. 공식 기술 문서

- D3 API: https://d3js.org/api
- D3 Brush: https://d3js.org/d3-brush
- React docs: https://react.dev/
- Vite docs: https://vite.dev/
- WCAG 2.2: https://www.w3.org/TR/WCAG22/

## 9. UI 런타임·가속 기술의 재검토

[FRAMEWORK_RUNTIME_REVIEW.md](../research/FRAMEWORK_RUNTIME_REVIEW.md)의 사실/미확인 구분과 측정 계획을 따른다. React는 과제 필수가 아니며 초기 선택은 비교 근거가 부족했다. 현재 package/source는 임시 scaffold로 보존한다. 실제 상호작용·메모리·번들 비교 전 ‘항상 무겁다/빠르다’고 결론내리지 않는다. Rust/Wasm/WebGPU는 별도 계산·메모리 경계로 검토하며 HTML이나 UI 런타임이 성능을 자동 보장하지 않는다. 핵심 시각화 렌더러 제약은 그대로 지킨다.

## 10. 데이터 조사 도구 (D-012)

[LOCAL_DATA](../specs/LOCAL_DATA.md)의 archive/member hash·원래 경로·표현별 source_id를 유지한다. ZIP을 읽기만 하고 원본 본문을 생성/교정하지 않는다. 비공개 SQLite는 본문 없는 메타데이터 조회용이며 public JSON export가 아니다. `data/` 전체를 기본 Git 제외하고 프로젝트 루트 data 경로를 Vite deny에 포함했다. src/data 모듈을 차단하는 광범위 경로 규칙과 구별한다.
