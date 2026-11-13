# SentenScope

> **Tracing why an appellate court changed a criminal sentence**
> 항소심은 왜 형을 바꾸었는가?

**Repository (recommended):** `sentenscope` · **Product name:** SentenScope
**Track:** SKKU Information Visualization Term Project 2026 · `VIS + X (Application Study)`
**Status:** 실행 기반 구성 단계. 실제 데이터·시각화는 미구현이며 data linkage/legal reasoning labels는 **unverified**.

SentenScope는 한국 형사 판결문의 **1심–항소심** 관계를 연결해, 피고인별 선고 변화와 항소이유·법원의 판단·직권판단·적용 법령을 탐색하고 **판결문 원문에서 근거를 확인**할 수 있게 하는 인터랙티브 시각화 시스템이다. 형량의 타당성을 평가하거나 변경 원인을 자동으로 확정하는 프로그램이 아니다.

## 읽는 순서

[문서 전체 안내](docs/README.md)에서 명세·조사·개발·일정·기록을 구분해 볼 수 있습니다. [UI 런타임 검토](docs/research/FRAMEWORK_RUNTIME_REVIEW.md)는 React·Vanilla TS·Wasm·WebGPU의 확인 사실과 미결정 항목을 정리합니다.

| 순서 | 문서 | 목적 |
|---:|---|---|
| 1 | [REQUIREMENTS.md](docs/specs/REQUIREMENTS.md) | 공식 과제 조건·제출물·데드라인 (최우선) |
| 2 | [PAPER.md](docs/specs/PAPER.md) | 연구 문제·기여·가설·논문형 서술 |
| 3 | [RELATED_WORK.md](docs/research/RELATED_WORK.md) | InfoVis 및 법률 시각화 논문 정독 가이드 |
| 4 | [DATA.md](docs/specs/DATA.md) | 데이터 출처·단위·스키마·API·불확실성 |
| 5 | [VALIDATION.md](docs/specs/VALIDATION.md) | 사건/피고인 정렬·추출·원문 검증 절차 |
| 6 | [VISUAL_DESIGN.md](docs/specs/VISUAL_DESIGN.md) | 시각적 채널·범례·색·기호·연결된 뷰 |
| 7 | [ENGINEERING.md](docs/development/ENGINEERING.md) | D3·UI 런타임 경계, 데이터 파이프라인, 테스트 |
| 8 | [EVALUATION.md](docs/specs/EVALUATION.md) | Case Study 3개·사용성 평가·재현 가능성 |
| 9 | [PRESENTATION.md](docs/planning/PRESENTATION.md) | 10분 라이브 발표와 데모 시나리오 |
| 10 | [ROADMAP.md](docs/planning/ROADMAP.md) | 12/2 제출까지 우선순위·수용 기준 |
| 참고 | [DECISIONS.md](docs/records/DECISIONS.md) | 설계 결정 기록·미해결 질문 |
| 협업 | [AGENTS.md](AGENTS.md) | AI 코딩 에이전트의 공통 준수사항 |

## 이번 문서 검토와 학습 방식

2026-11-13 문서 검토: [검토 기록과 확인 범위](docs/records/REVIEW.md), [단계별 설계 탐구](docs/research/DESIGN_TUTOR.md), [추가 참고자료](docs/research/RESEARCH_REFERENCES.md).

축·색·도형·배치·상호작용의 선택권은 사용자에게 있다. 아래 인터페이스와 기존 명세의 구체 인코딩은 **기존 제안 후보이며 사용자 결정 전**이다. 에이전트는 사실·자료·비교 실마리를 제공하고 설계 답안을 대신 작성하지 않는다. 과제 PDF는 검토 중 추가되어 5쪽 전체를 대조했다. 제안서 PDF·실데이터는 현재 checkout에 없어 재확인하지 못했다.

## 세 가지 분석 과제

- **T1 · Find:** 1심과 항소심에서 징역 기간 또는 집행유예가 달라진 *피고인*을 찾는다.
- **T2 · Compare:** 항소이유별 제기 주체, 법원 판단(인용/배척/판단하지 않음), 판단 변화·직권판단을 구별한다.
- **T3 · Verify:** 시각화된 경로를 두 판결문의 해당 한국어 문장·적용 조문까지 추적하고 검증한다.

## 인터페이스: 하나의 워크플로, 연결된 세 뷰

```
V1  피고인별 형량 변화 Dumbbell
        │ 행 선택 / 필터 / 브러시
        ▼
V2  항소심 판단 경로 Map ──────┐
        │ 노드·경로 선택       │ 문장 역선택
        ▼                     │
V3  1심 ↔ 항소심 원문 비교 ◄───┘
```

과제 시각화는 **D3.js**로 구현하는 계획이다. UI 런타임은 미결정이며 Vanilla JS/TS·React·Vue·Svelte 조합을 비교한다. 현재 React 코드는 임시 개발 진입일 뿐 최종 채택 근거가 아니다. Chart.js/Recharts/Highcharts/Matplotlib/Tableau 등의 다른 시각화 라이브러리로 대체하지 않는다.

## 절대 원칙

1. `187 linked pairs`, `94 candidates`는 **제안서의 자동 생성 후보**이며 검증된 피고인별 통계가 아니다.
2. LLM이 추출한 법률 판단은 검증 전까지 `unverified`라고 표시한다.
3. `판결문에 등장함`과 `법령의 적용`을 혼동하지 않는다.
4. `법원 직권판단`은 `당사자의 항소이유 인용`과 다르다.
5. 집행유예 변화는 징역 기간 변화와 독립적이다.
6. 선택된 시각적 관계는 원문/근거 ID로 추적 가능해야 한다.
7. 색만으로 의미를 전달하지 않으며, 범례가 화면에서 접근 가능해야 한다.
8. 외부 원문·API 응답·인증정보를 공개 Git에 올리지 않는다. 배포권 확인 전 재배포하지 않는다.

## 원자료와 가정의 구분

- **[ASSIGNMENT]**: 교수자 제공 `InfoVis_Term_Project_2026.pdf` (2026-10-04). 정식 조건은 이 PDF가 우선한다.
- **[PROPOSAL]**: 사용자가 제출한 `slides(1).pdf` (7페이지, SentenScope); 수치/구조는 *당시 제안·추출 결과*이며 재검증 필요.
- **[RESEARCH]**: 논문 및 공식 API 문서 링크 (RELATED_WORK.md 참조).
- **[PLAN]**: 이 저장소의 개발·평가 전략. 실제 완료 사항이 아니다.

**중요:** 보고서의 실제 마감 제출 ZIP은 이 개발 저장소 전체가 아니라, 공식 지시대로 `report.pdf`, `src/`, `image.png`를 ZIP *루트*에 배치해야 한다. 자세한 내용은 REQUIREMENTS.md.

## 개발 시작

개발 방식은 [DEVELOPMENT_METHOD.md](docs/development/DEVELOPMENT_METHOD.md), 구조 참고 조사는 [ENGINEERING_REFERENCE.md](docs/research/ENGINEERING_REFERENCE.md), 실제 확인 결과는 [FOUNDATION_STATUS.md](docs/records/FOUNDATION_STATUS.md)에 있다. AI/외부 자료 사용은 [ATTRIBUTION.md](docs/records/ATTRIBUTION.md)에 기록한다.

Node.js 22.12 이상이 필요하다. 현재 로컬 검증 환경은 Node 26.8.1이다.

```bash
npm ci
npm run check
npm test
npm run build
npm run dev
```

개발 서버는 기본 `http://127.0.0.1:5173`이며 포트 사용 중에는 Vite가 출력하는 실제 주소를 따른다. 현재 화면은 React로 만든 임시 개발 진입 안내뿐이며, 성능 비교나 최종 채택은 완료하지 않았다. D3는 설치 기반만 준비했고 차트·시각적 인코딩·실제 판결 데이터는 연결하지 않았다. `npm run preview`로 빌드 결과를 로컬에서 확인할 수 있다.

폴더 책임: [src](src/README.md), [scripts](scripts/README.md), [tests](tests/README.md), [data](data/README.md), [public](public/README.md), [artifacts](artifacts/README.md). 비공개 원본은 data/raw·private·processed에 보관하며 공개 export를 검토하기 전 `publicDir`을 활성화하지 않는다. 파이프라인 폴더는 현재 자리만 마련되어 있다.
