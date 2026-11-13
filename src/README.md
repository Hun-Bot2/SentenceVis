# 소스 경계

D-010의 단일 앱 / 모듈 분리 기반이다. UI 설계는 사용자 검토 전이며, 현재 React 진입은 임시다. 최종 UI 런타임은 D-011에 따라 미결정이다.

| 폴더 | 책임 | 허용 내부 의존성 |
|---|---|---|
| app | React 진입·조립 | 전체 src 모듈 |
| domain | 프레임워크 없는 도메인 타입·규칙; 계약 검토 후 구현 | domain |
| data | 스냅샷 검증·로더·조회 | data, domain |
| state | 프레임워크 없는 선택·필터 전이 | state, domain |
| vis | D3 좌표·기하·렌더링 도구 | vis, domain |
| components | 도메인 공용 UI | components, domain |
| features | sentence-comparison / reasoning / evidence 기능 | app 외 내부 모듈 |
| styles | 사용자 검토 후 스타일 | 현재 미구현 |

루트 `main.tsx`는 앱을 마운트한다. domain/state는 외부 패키지를 사용하지 않는다. data/vis는 React를 참조하지 않는다. `npm run check:boundaries`는 TS/TSX의 정적 문자열 import/re-export와 동적 import를 검사한다. 이 검사는 브라우저 보안 샌드박스나 모든 네트워크/문자열 조합의 정보유출 검사가 아니다. 검토되지 않은 alias·computed dynamic import는 허용하지 않는다.

현재 앱은 개발 진입 확인용 기본 HTML만 출력한다. 차트·팔레트·레이아웃·법률 enum을 확정하지 않았다.
