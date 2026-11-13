# Embedding Atlas 엔지니어링 조사

**확인일:** 2026-11-13. GitHub 연결 도구로 저장소·개발 문서·일부 실제 소스를 읽었다. 도구를 빌드/실행하거나 전체 소스를 감사한 것은 아니다. Apple이 특정 개발 방법론을 사용한다고 추론하지 않는다.

**기준 commit:** [`152e5c5cfc7810e99953f65a979dbdea0fbf27fa`](https://github.com/apple/embedding-atlas/commit/152e5c5cfc7810e99953f65a979dbdea0fbf27fa). 초기 탐색은 main에서 했고 소스·CI 확인은 이 commit에 고정했다. main은 변경될 수 있다.

| 확인한 실제 구조/소스 | 확인 사실 | SentenScope의 적용 범위 |
|---|---|---|
| [개발 문서](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/packages/docs/develop.md), [루트 package.json](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/package.json) | component/viewer/utils, 예제·문서, Python backend, Rust/WASM을 나눈 workspace | 책임 분리는 참고; 단일 수업 앱에서 동일 monorepo 규모·다언어 toolchain을 요구하지 않음 |
| [viewer src](https://github.com/apple/embedding-atlas/tree/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/packages/viewer/src) | charts/layouts/renderers/stores/highlight 등 분리 | 도메인·데이터·상태·D3·기능의 경계로 작게 대응 |
| [embedding_atlas_store.ts](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/packages/viewer/src/stores/embedding_atlas_store.ts) | coordinator/crossFilter, 앱별 state와 파생 store, chart context를 관리 | 선택 상태의 명시적 소유와 파생 조회 참고. Mosaic/SQL 도입은 하지 않음. 생성자 부분 확인 |
| [history_manager.ts](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/packages/viewer/src/stores/history_manager.ts) | UI에서 분리된 상태 이력·undo/redo와 debounce 관리 | 상태 전이를 UI와 분리하는 참고. 현재 undo/redo 기능 구현은 하지 않음 |
| [schemas.ts](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/packages/viewer/src/schemas.ts) | 타입으로부터 생성하는 chart/layout/style schema를 모아 export | 데이터 계약과 검증을 별도 경계로 둠. 법률 계약은 아직 확정하지 않음 |
| [store.test.ts](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/packages/viewer/test/store.test.ts), [CI](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/.github/workflows/ci.yml) | 상태 알림 동작 테스트, CI의 빌드·타입·테스트·형식 검사 단계 | 로컬 명령을 분리해 재현. Atlas CI가 현재 통과한다고 주장하지 않음; 우리 원격 CI는 미구성 |
| [component lib](https://github.com/apple/embedding-atlas/tree/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/packages/component/src/lib) | geometry 유틸·라벨 배치·WebGPU renderer 등의 경계 | 계산/렌더링 분리의 참고. 라벨 알고리즘 품질·성능은 미측정 |

## 그대로 가져오지 않는 부분

현재 이 프로젝트에 embedding-atlas·Mosaic·WebGPU·UMAP·Svelte·Python backend·Rust/WASM을 설치하지 않는다. 이는 해당 기술의 품질 판단이 아니라 현재 데이터·과제 제약·실측 부재에 따른 범위 관리다. D3 렌더러 제약·법률 provenance 계약을 유지하되 UI 런타임은 D-011에 따라 재검토한다. Atlas의 구조가 React 채택의 근거는 아니다. 임베딩 공간의 거리나 cluster를 법률적 관련성·판결 이유로 도입하지 않는다. 그런 설계가 필요해지면 사용자 탐구와 별도 데이터 검증을 거친다.

## 출처·라이선스

[Atlas README](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/README.md), [MIT LICENSE](https://github.com/apple/embedding-atlas/blob/152e5c5cfc7810e99953f65a979dbdea0fbf27fa/LICENSE)를 확인했다. 이번 작업은 구조적 아이디어를 참고했으며 소스 코드를 복사/번역/수정해 포함하지 않았다. 추후 코드 재사용 시 실제 가져온 범위·파일·commit·저작권 및 라이선스 고지를 따로 기록한다. 앱 의존 라이브러리 목록은 package.json/package-lock.json에 있다.
