# 개발 기반 상태 — 2026-11-13

**범위:** F0 / D-010. 폴더·앱 진입·검사 도구 기반. 실제 판결 데이터·시각화·파이프라인·평가·배포는 미구현이다.

## 환경과 검사

로컬 Node v26.8.1, npm 12.0.2에서 확인한다. 정확한 의존성은 package-lock.json을 따른다. 최소 지원 선언과 다른 Node 버전에서의 실행 확인은 별개다.

| 확인 | 실제 결과 |
|---|---|
| 의존성 설치 | 설치 및 npm ci 재설치 통과, 정확한 버전과 integrity는 package-lock.json |
| npm run check | 타입 검사·소스 경계(2개 TSX)·Markdown 파일 대상/펜스 검사 통과 |
| npm test | 소스 계층·비공개 경로·동적 import 경계의 5개 테스트 통과 |
| npm run build | Vite 프로덕션 빌드 통과; dist/index.html 및 JS 생성 |
| 개발 서버 HTTP | 임시 loopback 서버의 진입 HTML HTTP 200 확인 |
| 비공개 경로 HTTP | 합성 marker 파일의 일반 경로와 /@fs 경로 모두 403, 응답에 marker 미포함 |
| Git 제외 규칙 | raw/private/processed 및 validation 출력 경로의 제외 확인 |

처음 TypeScript 7.0.2로 설치했을 때 로컬 경계 검사에서 `ts.ScriptTarget.Latest`가 없어 실패했다. parser API를 사용하는 검사 도구와 함께 동작하는 5.9.3으로 고정한 뒤 위 검사를 통과했다. 최신 버전 일반에 대한 결함 주장이나 모든 버전 호환성을 뜻하지 않는다.

로컬 포트 listen은 최초 샌드박스에서 EPERM으로 실패했고, 승인된 제한 밖 실행에서 임시 loopback HTTP 점검을 완료했다. 서버와 합성 marker 파일은 종료/삭제했다. 실제 판결문이나 API는 사용하지 않았다. HTTP 확인은 브라우저의 React 렌더링·시각적 가독성·접근성 검증과 다르며 화면 캡처는 없다.

## 현재 구현된 경계

- 앱 진입: src/main.tsx, src/app/App.tsx. 개발 안내용 기본 HTML이며 최종 UI가 아니다.
- 검사: scripts/checks의 타입 import 경계·Markdown 파일 대상/코드펜스 검사.
- 테스트: TS/TSX import/re-export/dynamic import로 비공개 경로를 참조하는 예와 계층 위반의 검출.
- 데이터: 원자료·법률 fixture·공개 스냅샷 없음. 법률 스키마는 docs/records/REVIEW.md의 미해결 사항을 유지.
- 배포: Vite publicDir 비활성, loopback 개발 서버 및 private 경로 deny. 원격 배포/CI 없음.

소스 경계 검사는 정적 리터럴 import에 한정한다. 임의 fetch·CSS URL·플러그인·심볼릭 링크 등 모든 경로를 검증하지 않는다. 현재 통과 결과는 데이터 권리·법률 정확성·브라우저 UI 품질의 증거가 아니다.

## 산출 파일과 목적

- `package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`, `index.html`: 재현 가능한 웹 도구 기반과 데이터 제공 경계.
- `src/main.tsx`, `src/app/App.tsx`: 개발 진입; 나머지 src 폴더는 예약된 책임.
- `scripts/checks/boundaries.mjs`, `scripts/checks/docs.mjs`, `tests/unit/boundaries.test.mjs`: 구현 계층·문서 일관성 검사 및 회귀 예제.
- src/scripts/tests/data/public/artifacts의 README와 자리 파일: 폴더 책임·현재 미구현 범위.
- `.gitignore`: 비공개 원본·로컬 검증 산출물 제외.
- `docs/development/DEVELOPMENT_METHOD.md`, `docs/research/ENGINEERING_REFERENCE.md`, `docs/records/ATTRIBUTION.md`, 이 파일: 방법·참고 근거·출처·실행 결과.
- `README.md`, `docs/development/ENGINEERING.md`, `docs/records/DECISIONS.md`, `docs/planning/ROADMAP.md`, `docs/records/REVIEW.md`: 실제 기반과 D-010으로 명세 동기화.

다른 기존 문서·과제 PDF·사용자 수정은 보존했다. 커밋·push·원격 배포는 수행하지 않았다.

## 후속 상태 — UI 런타임 재검토

React는 현재 임시 진입에만 사용되며 최종 채택은 D-011의 미결정 항목이다. 이전 빌드/HTTP 확인은 프레임워크 우열의 증거가 아니다. 이번 작업은 문서 경로 정리와 개발 서버의 향후 data/cache 차단을 동기화했다. 실제 브라우저 성능·Rust/Wasm/GPU를 측정하지 않았다.

## UI 런타임 재검토 후 로컬 검사

2026-11-13에 `npm run check`, `npm test`(5개), `npm run build`를 다시 실행해 통과했다. Markdown 검사는 28개 파일과 로컬 파일 링크 109개를 확인했다(외부 URL/anchor 제외). 비공개 HTTP 차단은 이전 단계의 확인 기록이며 data/cache 추가 규칙의 HTTP 검사는 이번에 별도로 실행하지 않았다.

현재 개발 진입의 production JS `index-DjBcpgYm.js`는 219,849 bytes이며 Node v26.8.1의 `gzipSync(buffer)` 기본 설정으로 68,136 bytes를 관측했다. `dist/assets`의 파일을 readFile한 길이와 gzipSync 결과 길이를 읽은 값이다. 실제 HTTP 전송량·React 패키지 단독 크기·사용자 지연/메모리·Vanilla 대비 효과는 아니다. Vite 로그의 압축 추정치와 도구/옵션이 다를 수 있다. D3 차트가 없는 임시 진입의 전체 JS이므로 최종 시스템 크기로 일반화하지 않는다.

## 후속 상태 — 로컬 ZIP 조사 도구

2026-11-13에 사용자 제공 slides.pdf와 4종 AI-Hub ZIP을 조사하고 [LOCAL_DATA](../specs/LOCAL_DATA.md)의 v4 비공개 인덱스를 생성했다. 핵심 JSON 전체 파싱·원본 ZIP 137개 hash 독립 대조·라벨 분류와 DB 참조 대조가 통과했다. 일반 코드/링크 검사·기존 Node 테스트 5개·새 합성 ZIP 테스트 9개·프로덕션 빌드가 통과했다. 루트 data의 합성 파일은 일반 URL과 /@fs URL 모두 HTTP 403이며 본문 marker가 응답에 없음을 확인하고 정리했다. 원자료를 HTTP로 제공한 시험은 아니다.

Vite 설정의 node:url import에 필요한 타입 선언이 없어 최초 typecheck가 실패했고 devDependency @types/node를 고정 설치한 뒤 재검사했다. 개발 서버의 root data 차단과 Git 제외 범위를 동기화했다. 실제 법률 검증·공개 export·차트는 미구현이다. 기존 MCP_WORKFLOW 사용자 변경은 보존하고 깨진 상대 링크 네 곳만 보정했다.
