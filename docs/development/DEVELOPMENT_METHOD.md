# 개발 방법론과 구현 진입 순서

**기준:** 2026-11-13, D-010. `[RESEARCH]`는 출처에서 확인한 사실, `[PLAN]`은 SentenScope의 실행 절차다. 개발 방법론·폴더 책임의 결정과 사용자에게 남겨진 시각화 설계 결정을 구별한다.

## 1. 조사에서 확인한 방법과 적용 한계

| 방법 | 확인한 내용 | 이 프로젝트에서 검토할 지점 |
|---|---|---|
| Design Study Methodology | 실세계 도메인 문제 분석, 시스템 설계·검증·성찰을 다루는 9단계 프레임워크. 과정은 반복적이다. [M1] | 법률 데이터·사용자 태스크·설계·검증 기록을 함께 관리하는 연구 절차 |
| Nested Model | 도메인 → 데이터/태스크 → 인코딩/상호작용 → 알고리즘의 계층별 타당성 위협과 검증을 구별한다. [M2] | 빌드 성공을 데이터 정확성·사용자 효과와 구별하기 |
| Agile principles | 동작하는 소프트웨어를 자주 전달하고 변화와 정기적 성찰을 수용한다. [M3] | 짧은 기능 단위로 확인 가능한 결과를 남기는 구현 운영 |

**[PLAN] 작업 방식:** 문제 주도 Design Study를 연구의 틀로 참고하고, Nested Model로 검증 계층을 나누며, 짧은 증분 구현을 반복한다. 세 개를 조합하는 것은 프로젝트 판단이며 어떤 논문이 이 조합을 정답으로 지정한 것은 아니다. 정식 Scrum 역할·행사·스프린트를 수행했다고 주장하지 않는다. 전문가 협력·도메인 현장 검증이 부족한 상태를 완결된 design study라고 부르지 않는다.

## 2. 한 번의 개발 반복

1. **질문 고정:** 이번에 다룰 태스크와 관측 가능한 완료 조건을 적는다.
2. **데이터 확인:** grain, source ID, 피고인 정렬, 근거, 권리, 검토 상태를 확인한다. 미확인 항목은 보류한다.
3. **사용자 설계 검토:** 축·도형·색·공간 의미·상호작용은 [Tutor 노트](../research/DESIGN_TUTOR.md)의 힌트를 참고해 사용자가 기록한다. 에이전트가 선택 이유를 대신 채우지 않는다.
4. **작은 기능 구현:** 로더·선택 상태·화면·원문 연결을 작은 종단 기능으로 묶는다. 단순 mock 화면을 완료 기능으로 계산하지 않는다.
5. **계층별 확인:** 데이터/ID 불변식, 상태 전이, D3 렌더링, 근거 역추적, 키보드·오류·가독성을 구별해 검사한다.
6. **성찰·기록:** 결과, 실패, 스크린샷, 미확인 항목, 변경 명세, 다음 질문을 남긴다.

원자료가 없을 때는 명시적 synthetic fixture로 기술적 경계를 검증할 수 있다. 이를 실제 사건·Case Study finding으로 사용하지 않는다.

## 3. 순서와 진입 조건

| 단계 | 작업 | 다음 단계로 넘어갈 증거 |
|---|---|---|
| F0 기반 | 폴더·의존성 lock·타입 검사·소스 경계·임시 진입; UI 런타임 재검토 | 로컬 check/test/build 결과. 현재 작업 범위 |
| F1 계약 | REVIEW의 문서/선고 grain, 관계 ID, 출처 차원, 검토와 판정, offset 확정 | 명시적 계약·코드북·합성 오류 fixture. 실제 법률 분류는 원문 검토 필요 |
| F2 데이터 | manifest·사건/피고인 대응·검증·권리 검토 | 실제 수량/보류 사유, 대표 경로의 출처 추적. 권리 없는 자료는 공개 안 함 |
| F3 설계 | 사용자 스케치·계산·대안 비교·범례·상호작용 기록 | 사용자의 선택과 재검토 조건; 독립 3개 시각화 조건 확인 |
| F4 기능 | 하나의 피고인 선택에서 근거 역선택까지 D3 기반 연결 | ID 기반 결정적 상태 전이와 브라우저 확인 |
| F5 확장·평가 | 실제 범위, 복잡한 사례, 접근성·성능·실패 복구 | 실제 finding 3개와 캡처, 측정 조건과 한계 |
| F6 제출 | 재현 명령·AI 공개·5쪽 보고서·ZIP 구조 | 과제 PDF 수용 기준과 실제 압축 내용 확인 |

단계는 회귀 가능하다. 예를 들어 F4에서 원문 대응 오류가 발견되면 F1/F2로 돌아간다. 모든 폴더를 채운 뒤에야 연결하는 대형 일괄 구현 방식은 사용하지 않는다. F0는 기능이나 법률 데이터의 검증 완료가 아니다.

## 4. 이번 엔지니어링 구조

Embedding Atlas의 분리된 책임을 참고하되 현재는 **단일 npm 앱 + 내부 모듈**로 시작한다. 세부 조사와 고정 commit은 [ENGINEERING_REFERENCE.md](../research/ENGINEERING_REFERENCE.md)에 있다. 패키지별 배포/API 소비자·다언어 런타임 요구가 생기면 분할 비용을 다시 검토한다.

```text
src/                 앱, 도메인, 데이터, 상태, D3, 기능 모듈
scripts/             비공개 원자료 처리 단계와 개발 검사
tests/              단위 / 통합 / 브라우저 / 합성 fixture
data/               raw / private / processed (비공개)
public/data/        향후 검토된 export 자리 (현재 자동 제공 비활성)
artifacts/          검증 / 설계 / 평가 / 제출 로컬 산출물
docs/               명세, 근거, 사용자 결정
```

현재 실제 폴더별 책임·허용 의존성은 [src/README.md](../../src/README.md)에 있다. D3는 설치하되 아직 차트는 구현하지 않는다. React는 임시 개발 진입만 담당하며 최종 채택은 [UI 런타임 재검토](../research/FRAMEWORK_RUNTIME_REVIEW.md)와 D-011에 따라 미결정이다. Vite `publicDir`은 검토 전 자동 파일 제공/복사를 피하도록 비활성화했다.[M4] 원본 데이터 경로는 개발 서버 deny 규칙에도 추가한다.[M5] 이것은 전체 공개 데이터 심사나 정보 유출 방지 시스템의 구현 완료를 뜻하지 않는다.

## 5. 재현 명령과 완료 기록

README의 명령을 기준으로 `npm ci`, `npm run check`, `npm test`, `npm run build`, `npm run dev`를 사용한다. 의존성은 package-lock으로 고정한다. F0의 실제 결과와 환경은 [FOUNDATION_STATUS.md](../records/FOUNDATION_STATUS.md)에 남긴다. 수업 제출용 `src/`에는 나중에 package/config/재현 문서를 포함한 실행 가능한 소스 패키지를 준비해야 한다. 현재 개발 폴더 `src/`만 복사하는 것은 충분하지 않다.

## 출처와 열람 범위

- **[M1]** Sedlmair, Meyer & Munzner (2012). [Design Study Methodology](https://www.cs.ubc.ca/labs/imager/tr/2012/dsm/). 확인: 저자 페이지 초록·프레임워크 설명. 본문 전체 정독 아님.
- **[M2]** Munzner (2009). [A Nested Model for Visualization Design and Validation](https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/). 확인: 이전 문서 검토에서 열람한 저자 페이지 초록. 이번 재열람은 서버 오류. [기존 조사](../research/RESEARCH_REFERENCES.md)의 F1 참조.
- **[M3]** [Agile Manifesto Principles](https://agilemanifesto.org/principles.html). 확인: 공식 원칙 본문. Scrum/Kanban의 전체 방법론 검증 자료가 아님.
- **[M4]** [Vite publicDir](https://vite.dev/config/shared-options.html#publicdir). 확인: 공식 설정 문서. 기본 public의 제공/빌드 복사 동작과 false 설정.
- **[M5]** [Vite server.fs.deny](https://vite.dev/config/server-options.html#server-fs-deny). 개발 서버 파일 접근 설정; 프로덕션 공개 권리 검토를 대신하지 않는다.

**AI 공개:** Codex가 조사·기술 선택 초안·폴더 및 실행 기반을 작성했다. 시각화 인코딩의 사용자 결정과 실데이터 검증은 수행하지 않았다.
