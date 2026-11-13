# UI 런타임·WebGPU·Wasm: 사실 확인과 비교 과제

**조사일:** 2026-11-13. **상태:** `[RESEARCH + PLAN]`. 공식 자료의 아래 절을 확인했다. 프레임워크별 성능 실험이나 WebGPU/Wasm 실기기 검증은 실시하지 않았다. 연구 논문 정독이나 기술 우열의 실증 결과로 표시하지 않는다.

## 1. 사용자 의견의 사실·정정·미확인 구분

| 검토할 주장 | 확인 결과 | 근거 |
|---|---|---|
| React가 필수인지부터 검토해야 한다 | **맞다. 필수가 아니다.** 과제 PDF p.1은 시각화 외 목적으로 React를 쓸 수 있다고 예시를 든다. 필수는 D3/Vega 계열 시각화이며 plain JS/TS 조합도 검토할 수 있다. | 로컬 과제 PDF p.1, [S1] |
| 익숙하다는 이유만으로 React를 택하면 근거가 부족하다 | **이 프로젝트의 선택 근거로 부족하다.** 상태 동기화·정적 배포·타입은 React에만 있는 능력이 아니다. 기존 ENGINEERING의 설명으로 React의 필요성을 입증하지 못했다. 익숙함은 학습·오류·일정 비용으로 기록할 수 있으나 과제 채점 결과를 단정하지 않는다. | 기존 명세 검토; 프로젝트 판단 |
| React는 다른 프레임워크보다 무겁다 | **대상·지표 없이 일반화 불가.** React는 렌더링/상태 런타임을 추가하지만 다운로드 바이트, 초기 실행, 반복 업데이트, 메모리는 서로 다른 비용이다. Vue·Svelte 등의 구현 방식도 다르며 특정 버전·동일 기능을 비교해야 한다. | [S2, S3, S4] |
| Vanilla JS/TS 조합은 ms 단위의 UX 차이를 만들 수 있다 | **가능한 가설이다. 이 앱의 영향은 미확인.** DOM 규모·입력 빈도·그리기·레이아웃·계산·기기 등의 영향을 분리해야 한다. 프레임워크 이름만으로 지연을 특정할 수 없다. | [S5, S6] |
| React의 불필요한 컴포넌트가 많이 포함될 것이다 | **개념 정정 필요.** React/ReactDOM의 렌더링 기능과 별도 UI 위젯 라이브러리를 구별한다. HTML/SVG 요소 지원은 사용하지 않는 모든 위젯을 생성한다는 뜻이 아니다. 현재 package.json에는 MUI·Ant Design 같은 위젯 모음이 없다. 런타임 비용이 없다는 뜻도 아니다. | [S2, S7], 로컬 package.json |
| TypeScript가 JavaScript보다 메모리상 가볍거나 빠르다 | **타입 표기만으로 그렇지 않다.** 타입 주석은 JS 출력에서 지워진다. 실제 출력·런타임 의존성·알고리즘을 비교해야 한다. TS의 검사 이점은 런타임 JSON 검증을 대신하지 않는다. | [S8] |
| Rust는 HTML 같은 기본 언어와 더 잘 동작한다 | **그 인과는 성립하지 않는다.** HTML은 문서 마크업이며 Rust용 메모리 관리자가 아니다. 브라우저 Rust는 보통 Wasm과 호스트 바인딩을 통해 DOM/API를 사용한다. UI 런타임 선택과 Rust 계산 모듈 사용은 분리해 검토할 수 있다. | [S9, S10, S11] |
| Rust/Wasm이면 메모리와 성능이 자동으로 개선된다 | **자동 보장되지 않는다.** Rust 소유권, Wasm 선형 메모리, JS GC heap, DOM·GPU 자원을 구별한다. 문자열 변환과 경계의 배열 복사·할당도 비용에 포함한다. | [S9–S13] |
| WebGPU·Wasm·Rust는 한 세트다 | **서로 다른 계층이다.** WebGPU는 GPU API이고 Wasm은 실행 형식, Rust는 Wasm으로 컴파일할 수 있는 언어다. WebGPU shader는 WGSL 사양을 따른다. UI 런타임이 어느 것인지가 이 조합의 사용 가능성을 정하지 않는다. | [S9, S14, S15] |

현재 React scaffold는 **실행 가능성만 확인한 임시 구현**이다. React 유지/교체 또는 Vanilla TS 최종 채택은 미결정이다. 이번 요청에서는 앱 코드·의존성·레이아웃을 전환하지 않는다. WebGPU/Rust 도입도 결정하지 않는다. [D-011](../records/DECISIONS.md#d-011--ui-런타임-선택-재검토)을 따른다.

## 2. 비교 후보: 구현 방식과 확인할 비용

아래 표는 후보의 우수성을 순위화하지 않는다. 동일한 D3 출력과 기능을 만드는 조건을 먼저 기록한다.

| 후보 | 확인된 구현 방식 | 비교 때 기록할 책임/비용 |
|---|---|---|
| Vanilla JS/TS + 필요한 D3 모듈 | 브라우저 DOM/API와 D3를 직접 조합할 수 있음 [S1] | 상태 전이·구독 해제·선택 ID 정합성·DOM 갱신·접근성을 어디서 보장하는지 |
| React + D3 | 상태 변경 후 컴포넌트 호출과 DOM commit을 수행 [S2] | 렌더링 범위·빈도·할당·번들; D3와 같은 DOM을 중복 소유하지 않는지 |
| Vue + D3 | virtual DOM과 compiler-informed 최적화를 설명 [S3] | 반응성 경계·업데이트·D3 소유권·번들 |
| Svelte + D3 | 컴포넌트를 JS로 변환하는 컴파일러 방식 [S4] | 생성 코드와 런타임·상태 전이·D3 통합·번들; ‘컴파일하니 런타임 비용 0’으로 보지 않기 |

모든 후보에서 동일 source ID·원문·검증 상태·키보드 동작을 유지한다. 상태관리/컴포넌트 추상화는 Vanilla에서도 만들 수 있고, 그 구현·검증 비용도 비교 대상이다. Atlas의 Svelte/Wasm 사용은 가능한 구성의 사례이며 SentenScope에서의 최적 조합을 입증하지 않는다.

## 3. 메모리와 실행 위치를 나눠 보기

```text
HTML / DOM / CSS           문서·상호작용·레이아웃/페인트
UI 코드(JS 또는 TS 출력)    Vanilla / React / Vue / Svelte 후보
D3                        데이터→좌표·마크·선택 연결 (과제 제약)
Worker (선택)             별도 실행 맥락; 계산과 결과 전달
Wasm (선택)               Rust 등에서 만든 계산 모듈·선형 메모리
WebGPU (선택)             명령/버퍼·GPU 계산/렌더링, WGSL shader
```

이 목록은 필수 파이프라인이나 구현 완료 구조가 아니다. Wasm을 호출한다고 자동으로 Worker에서 실행되는 것은 아니다. Worker는 별도 메시지 경계를 만들며, DOM 직접 갱신과 계산을 나눠 생각해야 한다.[S6, S10]

- Rust의 소유권/Drop은 Rust가 관리하는 자원의 수명을 다룬다. 브라우저 전체 메모리 사용량이나 자원 누수 부재를 보장하는 수치가 아니다.[S11]
- wasm-bindgen의 `&str` 경로에는 JS 문자열과 Wasm 메모리 사이 인코딩·복사가 있다. 한국어 근거 위치는 UTF-16 code unit과 UTF-8 byte offset을 동일한 숫자로 취급하지 않는다. 어떤 텍스트 버전과 위치 단위를 썼는지 별도 계약으로 기록한다.[S12]
- 숫자 slice 전달에도 복사가 있을 수 있다. view를 이용하는 다른 경로의 존재가 모든 바인딩의 zero-copy를 뜻하지 않는다.[S13]
- WebGPU 버퍼 쓰기는 별도 API 작업이다. JS 배열/Wasm 메모리와 GPUBuffer를 같은 메모리라고 가정하지 않는다. 전송·dispatch·동기화·readback을 계산 시간과 구별한다.[S14]
- D3/Vega 외 자체 GPU 렌더러로 핵심 차트를 대체하는 것은 과제 제약과 충돌할 수 있다. GPU를 계산 보조로 검토하는 것과 렌더러를 교체하는 것을 구별하고, 허용 여부가 불명확하면 교수자 확인이 필요하다. 현재 GPU 구현 없음.

## 4. 성능 비교 계획 — 아직 실행 결과 아님

**[PLAN]** 비교 범위는 화면의 예쁨이나 선택된 색/도형이 아니라, 동일 데이터·출력·입력에서 발생하는 시스템 비용이다. 어느 후보를 채택할지와 허용 임계치는 사용자가 기록한다.

| 층 | 측정할 것 | 혼동하면 안 되는 것 |
|---|---|---|
| 로드 | production JS/Wasm의 raw/gzip/Brotli 크기, 실제 네트워크, parse/compile/init | node_modules 크기·개발 번들과 사용자 다운로드 크기 |
| 선택·필터 | 입력→피드백, 근거 갱신 완료, 작업별 시간 분포 | DOM 작업 종료와 실제 다음 paint |
| brush/zoom | frame interval 분포, 긴 프레임·메인스레드 점유 | INP 하나로 연속 드래그/스크롤 전부 평가 |
| 계산 | JS/Worker/Wasm/GPU의 계산·변환·전송·동기화·출력 반영 | compute kernel 시간만으로 종단 지연 주장 |
| 메모리 | JS heap, Wasm memory, DOM 수, GPU buffer와 해제 경로 | 한 API의 heap 수치를 전체 탭 메모리로 부르기 |
| 정확성 | 선택 ID/근거 대응, null/보류 상태, 계산 허용 오차 | 빠르지만 다른 정보를 제공하는 조건 |

측정 전 환경(기기·브라우저·GPU·refresh rate·전원·해상도), 라이브러리 lock, 데이터/코드 hash, cold/warm 구분, 반복·워밍업·순서·제외 규칙을 고정한다. 데이터 규모·문서 길이·관계 밀도는 대표 범위와 스트레스 범위를 나누고 실제/합성 여부를 표시한다. 단일 최솟값 대신 중앙값·상위 지연과 변동을 남긴다. 작은 차이를 사용자 체감 향상으로 자동 해석하지 않는다.

**정의 연습:** 주사율 `f`에서 한 refresh 간격은 `1000/f` ms다. 60Hz이면 약 16.7ms, 120Hz이면 약 8.3ms다. 이 간격 전체가 JS 실행 예산이라는 뜻은 아니다. INP의 200ms ‘good’ 기준은 field의 page-load 75th percentile 평가이며 애니메이션 프레임 예산이나 모든 지연의 허용치가 아니다. INP는 주로 click/tap/key 상호작용을 다룬다.[S5]

Rust/Wasm 비교에는 `초기화 + 입력변환/복사 + 호출 + 계산 + 출력변환/복사 + 화면반영`을 기록한다. 이 항의 합은 측정 범위를 나누는 회계식이며 속도 향상 모델이나 측정 결과가 아니다. Worker/GPU 비동기 파이프라인은 중첩될 수 있어 실제 종단 wall-clock도 따로 측정한다. React Profiler는 React 렌더링 관측 도구이며 자체 overhead가 있고 production에서 기본 비활성이다. 프레임워크 간 유일한 종단 지표로 쓰지 않는다.[S16]

## 5. 답안을 대신 쓰지 않는 기술 선택 힌트

**첫 힌트:** 한 피고인 선택에서 원문을 확인할 때까지 ‘어느 데이터가 바뀌고 어느 DOM이 바뀌는가’를 적어본다. 구현 도구 이름은 아직 쓰지 않는다.

<details><summary>다음 힌트 — 비교 대상 좁히기</summary>

Vanilla TS+D3와 UI 런타임 후보 하나에서 같은 선택/해제/필터/근거 연결을 표현하려면 각각 어떤 코드와 검사가 필요한지 나란히 적어본다. 상태 변경 빈도와 DOM 갱신 빈도가 같은지도 살펴본다. 익숙함을 적는다면 시간을 줄인다는 추측과 실제 오류/개발시간 관찰을 구별한다.
</details>

<details><summary>다음 힌트 — 계산 경계 찾기</summary>

느리다고 가정한 작업이 알고리즘·DOM·텍스트 배치·메모리 복사 중 어디에 있는지 먼저 구분해본다. Rust로 계산한 결과를 다시 문자열과 DOM으로 옮기는 경로, GPU 계산 결과를 화면에 반영하는 경로도 그려본다. 전송이 없는 가정과 있는 경우의 비교가 같은 질문에 답하는지 검토한다.
</details>

**사용자 작성:** 실제 필요한 기능 ___ / 비교 후보 ___ / 측정할 병목 ___ / 관찰 ___ / 선택과 재검토 조건 ___

## 6. References와 실제 확인 범위

공식 사양·저자 문서의 아래 절을 열람했다. 수치 성능을 직접 비교한 학술 연구로 제시하지 않는다. 링크는 최신 문서일 수 있으므로 실험에는 설치 버전과 확인일을 함께 기록한다.

- **S1** [D3 Getting started — D3 in vanilla HTML](https://d3js.org/getting-started#d3-in-vanilla-html). 확인: vanilla DOM/SVG 예제와 React 통합 안내. 프로젝트 차트 선택과 별개.
- **S2** [React Render and Commit](https://react.dev/learn/render-and-commit). 확인: 컴포넌트 호출과 DOM commit 구분. 모든 후보 대비 속도 우열을 주장하지 않음.
- **S3** [Vue Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism.html). 확인: Virtual DOM·compiler-informed 최적화 개요. 실측 비교 아님.
- **S4** [Svelte Overview](https://svelte.dev/docs/svelte/overview). 확인: compiler 설명과 컴포넌트 예제. 모든 런타임 비용 소멸을 뜻하지 않음.
- **S5** [web.dev: Interaction to Next Paint](https://web.dev/articles/inp). 확인: 정의·threshold·포함/제외 상호작용. 현장 지표와 lab 작업 분포를 구별.
- **S6** [web.dev: Use web workers to run JavaScript off the browser’s main thread](https://web.dev/articles/off-main-thread). 확인: main thread·Worker·통신 비용 설명. 별도 스레드의 성능 효과는 이 앱에서 미측정.
- **S7** [React DOM Components](https://react.dev/reference/react-dom/components). 확인: HTML/SVG 요소 지원 목록. 완성형 위젯 제품의 목록이 아님.
- **S8** [TypeScript Handbook — Erased Types](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#erased-types). 확인: 타입 주석 제거. 모든 TS 구문이 아무 코드도 생성하지 않는다는 뜻은 아님.
- **S9** [WebAssembly Core Specification — Overview](https://webassembly.github.io/spec/core/intro/overview.html). 확인: memory·module·host function 개념. 호스트 UI 프레임워크 성능 비교를 포함하지 않음.
- **S10** [wasm-bindgen: web-sys DOM hello world](https://wasm-bindgen.github.io/wasm-bindgen/examples/dom.html). 확인: Rust→web-sys→DOM 예제. HTML 기반 앱의 메모리 우월성 근거가 아님.
- **S11** [The Rust Programming Language — Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html). 확인: 소유권·할당·Drop 설명. 전체 브라우저 메모리 평가와 별개.
- **S12** [wasm-bindgen: str](https://wasm-bindgen.github.io/wasm-bindgen/reference/types/str.html). 확인: 문자열 복사·TextEncoder/Decoder와 UTF-16/UTF-8 변환.
- **S13** [wasm-bindgen: Number Slices](https://wasm-bindgen.github.io/wasm-bindgen/reference/types/number-slices.html). 확인: slice 파라미터와 TypedArray 경로의 복사 주의사항.
- **S14** [W3C WebGPU — Buffer copies](https://www.w3.org/TR/webgpu/#buffer-copies) · [GPUQueue.writeBuffer](https://www.w3.org/TR/webgpu/#dom-gpuqueue-writebuffer). 확인: 버퍼 쓰기·메모리 전달 모델. CPU/GPU 성능 실험 아님.
- **S15** [W3C WGSL](https://www.w3.org/TR/WGSL/). 확인: WebGPU shader language 소개·범위. Rust 소스가 그대로 GPU shader가 된다는 뜻이 아님.
- **S16** [React Profiler](https://react.dev/reference/react/Profiler). 확인: 측정 범위·profiling overhead·production caveat.

**AI 공개:** Codex가 조사·주장 분류·비교 계획·힌트 초안을 작성했다. 사용자 최종 선택, 프레임워크 비교 측정, Rust/WebGPU의 실제 성능 결과는 생성하지 않았다.
