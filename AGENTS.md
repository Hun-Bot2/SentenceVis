# AGENTS — SentenScope AI 개발 에이전트 작업 규약

이 문서는 모든 코딩/리서치 에이전트(Codex, Claude 등)가 루트에서 먼저 읽는 작업 규약이다. 새로운 세션에서 프로젝트를 추측하지 말고 근거 문서를 사용한다.

## 1. 먼저 읽을 문서

1. `README.md`: 프로젝트의 목적과 구조.
2. `docs/specs/REQUIREMENTS.md`: 변경 불가능한 공식 과제 요구사항.
3. `docs/specs/PAPER.md`: RQ·태스크·논문 기여.
4. 작업 종류에 따라 `docs/specs/DATA.md`+`docs/specs/VALIDATION.md`, `docs/specs/VISUAL_DESIGN.md`, `docs/development/ENGINEERING.md`.
5. 디자인이나 데이터 해석 변경 시 `docs/records/DECISIONS.md`도 검토.

## 2. 절대적인 금지 사항

- 법적 인과를 임의로 확정하거나, 판결문에 없는 이유를 만들어내지 말 것.
- 자동 추출 후보 수를 검증된 관측치 수로 발표하지 말 것.
- LLM 추출 결과를 법원의 명시 판단으로 세탁하지 말 것.
- `법령의 적용`과 본문 단순 언급을 혼동하지 말 것.
- 공동피고인의 심급 간 대응을 근거 없이 생성하지 말 것.
- 형기 숫자와 집행유예 여부를 하나의 값으로 합치지 말 것.
- AI-Hub 원본, 데이터 사용권 미확인 원문, API 인증값, 개인정보를 공개 저장소/브라우저에 배포하지 말 것.
- D3/Vega 외 시각화 라이브러리로 과제 핵심 그래프를 구현하지 말 것.
- 외부 코드·AI 사용을 감추지 말 것.

## 3. 변경 전 확인 규칙

- **Data:** 데이터셋의 grain·키·관계·검증 상태가 동일한가? source ID를 보존하는가?
- **UI:** 각 시각 마크의 채널→속성 매핑이 `docs/specs/VISUAL_DESIGN.md`에 설명되는가? 범례가 일치하는가?
- **Interaction:** 한 뷰를 선택하면 다른 뷰와 원문 근거가 결정적으로 갱신되는가?
- **Evidence:** 원문 ID가 없으면 미확인으로 표시하며 텍스트 생성으로 채우지 않는가?
- **Paper:** 논문을 읽지 않은 내용을 읽은 것처럼 말하지 않는가? 실험 결과를 생성하지 않는가?
- **Submission:** 필수 3개 linked visualizations 및 제출 ZIP 구성에 영향이 없는가?

## 4. 산출물 완료 기준 (Definition of Done)

1. 실행/빌드/테스트 결과 또는 실행 불가능한 이유를 보고한다.
2. 수정한 파일 목록, 변경 목적, 근거 또는 ADR 번호를 기록한다.
3. 영향받는 Markdown 명세를 동기화한다.
4. 데이터 가정·원문 검증 불가 항목은 `unverified`로 보존한다.
5. AI 및 외부 코드 사용 출처를 문서/코드에 드러낸다.

## 5. 작업 지시 템플릿

```text
Read README.md, REQUIREMENTS.md, PAPER.md and the relevant root specifications.
Implement only the requested scope using D3.js for visualizations.
Preserve the defined data grain, legal provenance, verification statuses and linked-view semantics.
Do not invent legal findings, extracted ground truth, or source passages.
Update affected docs and tests; report trade-offs, remaining uncertainties, and AI/external-code attribution.
```

## 6. 문서 라벨

- `[ASSIGNMENT]`: 교수자 PDF 원문.
- `[PROPOSAL]`: 제출한 SentenScope 제안서에 적힌 내용; 검증을 보증하지 않음.
- `[RESEARCH]`: 논문/공식 문서에서 확인된 일반 연구 또는 사실.
- `[PLAN]`: 구현 전 선택·가설·수용 기준.
- `[VERIFIED]`: 원자료·원문 또는 동작 시험으로 실제 확인 후만 사용.

모든 데이터 통계·Case Study·사용자 평가 수치는 출처/확인 상태를 명시해야 한다.

## 7. 사용자 요청에 따른 Tutor 규칙 (2026-11-13)

- 설계의 “왜?”에 답을 대신 정하거나 추천 결론을 주지 않는다. 축·도형·색·레이아웃·상호작용 선택은 사용자에게 남긴다.
- 확인한 연구 사실과 프로젝트 적용 가설을 분리하고, 원문 링크·확인 범위를 제공한다.
- 힌트는 관찰 → 관련 개념/읽을 절 → 작은 비교 → 사용자 기록 순으로 나눈다. 다음 단계는 요청 시 제공하며 답을 암시하는 유도 질문을 피한다.
- 기존 제안 명세는 사용자 승인 증거가 없으면 후보로 취급한다. 사용자 답안을 AI가 채우지 않는다.
- 참고: `docs/research/DESIGN_TUTOR.md`, `docs/research/RESEARCH_REFERENCES.md`, `docs/records/REVIEW.md`.

## 8. 기술 선택의 확인 상태

React는 과제 필수가 아니다. 현재 React 진입은 임시 scaffold이며 최종 런타임은 D-011에 따라 미결정이다. 익숙함·정적 배포·타입만으로 선택을 정당화하지 않는다. 프레임워크/Vanilla·Worker·Rust/Wasm·WebGPU의 역할과 비용을 구분하고 비교 전 ms·메모리 우열을 단정하지 않는다. 원문 사실과 프로젝트 적용 추론·가설을 구분한다. 참조: `docs/research/FRAMEWORK_RUNTIME_REVIEW.md`, `docs/records/DECISIONS.md`.

문서 전체 안내는 `docs/README.md`이며 specs/research/development/planning/records의 책임을 유지한다.
