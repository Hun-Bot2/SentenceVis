# 문서 안내

**현재 상태:** F0 개발 진입만 구현했다. D3 시각화·판결 데이터·사용자 평가·GPU/Wasm 기능은 미구현이다. UI 런타임은 재검토 중이며 현재 React scaffold의 존재가 최종 채택 근거는 아니다.

| 구분 | 문서 | 역할 |
|---|---|---|
| 공식 조건 | [REQUIREMENTS](specs/REQUIREMENTS.md) | 원본 과제에서 확인한 요구사항; 로컬 PDF·구두 피드백의 출처 구분 |
| 연구/데이터 명세 | [PAPER](specs/PAPER.md), [DATA](specs/DATA.md), [VALIDATION](specs/VALIDATION.md) | RQ·grain·검증·provenance 계약 |
| 시각 설계/평가 | [VISUAL_DESIGN](specs/VISUAL_DESIGN.md), [EVALUATION](specs/EVALUATION.md) | 기존 후보와 평가할 가설; 사용자 설계 결정 전 |
| 문헌·탐구 | [RELATED_WORK](research/RELATED_WORK.md), [REFERENCES](research/RESEARCH_REFERENCES.md), [TUTOR](research/DESIGN_TUTOR.md) | 사실 출처·확인 범위·단계별 힌트 |
| 기술 조사 | [Atlas](research/ENGINEERING_REFERENCE.md), [UI/WebGPU/Wasm 검토](research/FRAMEWORK_RUNTIME_REVIEW.md) | 참고 구조와 기술적 주장 교정; 실측 우열 아님 |
| 개발/운영 | [ENGINEERING](development/ENGINEERING.md), [METHOD](development/DEVELOPMENT_METHOD.md), [MCP_WORKFLOW](development/MCP_WORKFLOW.md) | 모듈 책임·개발 순서·데이터 운영 계획 |
| 일정/산출물 | [ROADMAP](planning/ROADMAP.md), [TASK](planning/TASK.md), [PRESENTATION](planning/PRESENTATION.md) | 기말 일정과 별도의 학회 확장 계획 |
| 결정/검토 기록 | [DECISIONS](records/DECISIONS.md), [REVIEW](records/REVIEW.md), [FOUNDATION_STATUS](records/FOUNDATION_STATUS.md), [ATTRIBUTION](records/ATTRIBUTION.md) | 의사결정·확인 결과·한계·AI 사용 |

## 읽기 경로

- 처음: 공식 조건 → PAPER → DATA/VALIDATION → Tutor → 시각 후보/평가.
- 개발 전: METHOD → ENGINEERING → UI 런타임 조사 → D-011의 미해결 판단.
- 실제 완료 확인: FOUNDATION_STATUS와 REVIEW. `[PLAN]` 문서는 실행 결과로 읽지 않는다.

## 구조와 유지 규칙

`specs/`는 요구/계약, `research/`는 외부 사실과 질문, `development/`는 구현/운영, `planning/`은 일정, `records/`는 결정·실행 기록을 담당한다. 같은 설명을 복제하지 않고 원래 문서를 링크한다. 실행 코드와 가장 가까운 README는 src/scripts/tests/data/public/artifacts에 둔다. 루트 AGENTS는 에이전트 진입점으로 유지한다.

과제 PDF는 로컬 참고자료이며 재배포권 확인 전 커밋하지 않는다. 문서의 PDF 전사 기록과 본인의 원본 대조 여부를 구별한다. 상태/버전·구체 수치가 바뀌면 기존 확인 날짜를 삭제하지 말고 후속 기록을 남긴다. `npm run check:docs`는 로컬 파일 대상·코드펜스를 검사하며 외부 링크와 anchor의 의미는 자동 검증하지 않는다.
