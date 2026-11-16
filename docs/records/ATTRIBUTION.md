# AI 및 외부 자료 사용 기록

## 2026-11-13 문서 검토

Codex가 기존 명세 검토·공개 자료 조사·참고자료·Tutor 질문과 계산 연습 초안을 작성했다. 사용자 설계 답안·판결 원문 검증·실험 결과는 생성하지 않았다. 자료별 링크·읽은 범위는 RESEARCH_REFERENCES에 있다.

## 2026-11-13 개발 기반

- **도구:** Codex (이 대화의 코딩 에이전트; 정확한 모델 리비전은 이 기록에서 확인하지 못함).
- **범위:** 개발 방법론/Atlas 구조 조사, 폴더, package/config, React 진입, 소스 경계·문서 검사와 경계 테스트, 관련 명세 동기화.
- **외부 구조 참고:** [Embedding Atlas 조사](../research/ENGINEERING_REFERENCE.md). 소스 복사·포팅 없음. 해당 저장소 전체의 빌드·성능은 검증하지 않았다.
- **의존 라이브러리:** package.json과 package-lock.json에서 실제 설치 버전 확인. 라이브러리 사용과 원자료 공개권은 별개다.
- **검증:** [개발 기반 상태](FOUNDATION_STATUS.md)의 실제 실행 결과만 인정한다.
- **인간 검토:** 사용자 설계 검토 및 실데이터 검토는 완료 전이다. 이 기록을 최종 보고서의 사용자 승인/효과 검증으로 쓰지 않는다.

최종 report.pdf와 구현 코드에도 실제 AI/외부 코드 사용 범위를 표시해야 한다. 이 문서만으로 과제의 모든 공개 의무가 완료되는 것은 아니다.

## 2026-11-13 UI 런타임 조사와 문서 재구성

Codex가 공식 React/D3/Vue/Svelte·TypeScript·Rust/wasm-bindgen·W3C·web.dev 자료를 읽고 주장 교정·동등 비교 계획·단계별 힌트를 작성했다. 성능 실험 결과를 생성하지 않았다. 문서를 specs/research/development/planning/records로 정리하고 링크·명세를 동기화했다. 기존 사용자 작성 MCP_WORKFLOW는 개발 문서로 이동하고 실제 폴더명과 연결을 정리했으며, 그 문서의 모든 외부 서비스 주장을 이번 조사에서 재검증한 것은 아니다.

## 2026-11-13 사용자 로컬 데이터 구조 조사

Codex가 사용자 제공 slides.pdf 7쪽·로컬 ZIP 구조를 읽고 inventory.py·verify_inventory.py·research.sql·합성 ZIP 테스트·문서를 작성했다. data-analytics:analyze-data-quality의 grain/중복/결측/조인 점검을 참고했다. 원본은 로컬에서만 처리했고 외부 업로드·본문 공개·법률 정답 생성·사용자 시각 선택은 하지 않았다. 원본 재배포권은 미확인이다. 관측 수치와 검사 범위는 LOCAL_DATA에 있다.

## 2026-11-16 자동 추출 파이프라인과 라벨링 도구

- **도구:** Claude Code (Anthropic, Claude Opus 5.5).
- **작성:** `scripts/align/corpus.py`·`link_pairs.py`·`build_dataset.py`, `scripts/annotate/parse_order.py`·`extract_paths.py`·`make_sample.py`·`metrics.py`·`label_server.py`·`label_tool.html`, `scripts/statistics/context_tables.py`, `tests/data/test_pipeline_rules.py`, D-013과 VALIDATION §12. 각 파일 머리에 AI 작성 표시가 있다.
- **방법:** 규칙(정규식) 기반 추출. LLM 추출은 사용하지 않았다. 규칙은 로컬 원문 표본을 AI가 읽고 설계했으며, 그 과정에서 확인한 오류(예: `형에 대한 집행을 유예` 누락)를 규칙과 테스트에 반영했다.
- **하지 않은 것:** 사람 라벨·정답·정확도 수치를 생성하지 않았다. 원문을 외부로 보내거나 공개하지 않았다. 사용자의 시각 설계 선택을 정하지 않았다.

## 2026-11-16 AI-Hub 전수 스캔과 교차 검증

- **도구:** Claude Code (Anthropic, Claude Opus 5.5).
- **작성:** `scripts/ingest/aihub_scan.py`, `aihub_crosscheck.py`, `aihub_textdiff.py`, [AIHUB_CROSS_VALIDATION](../research/AIHUB_CROSS_VALIDATION.md). `link_pairs.py`도 수정했다(법원 약칭, 원심 접두어, 연도 안 공백).
- **확인 범위:** 로컬 AI-Hub 12·019·114·115의 모든 ZIP과 모든 파일(351,672개)을 읽기 전용으로 처리했다. 외부 전송은 없다.
- **정정:** 이번 작업에서 이 에이전트의 버그 세 가지(점으로 구분된 날짜 변환, 병합 사건번호 비교, 12 일련번호 키)를 찾아 고쳤다. 보고서의 수치는 수정 후 결과다. 이전 응답에서 "019·114 원천 ZIP이 비어 있다"고 한 판단은 JSON만 센 데서 나온 오류였다.
- **추가(같은 날):** `kb_scan.py`, `kb_crosscheck.py`, `aihub_scan.py`의 로컬 헤더 복구(`recover_local_entries`)와 `참조조문` 기록. 지식베이스 하급심 참조조문 수를 한 번 잘못 집계했다가 정정했다(보고서 §5).
- **재구축(같은 날):** `merge_corpus.py`를 작성하고, `link_pairs.py`에 대법원 연결 옵션, `build_dataset.py`에 `supreme_outcome`을 추가했다. `make_sample.py`·`label_tool.html`·`metrics.py`에는 대법원 항목을 확장했다. 부분 파기 패턴 누락(`유죄 부분`)을 원문 대조로 찾아 고쳤다.
- **결측 상태(같은 날):** `build_dataset.py`에 `STATUSES`, `fields`, `unpaired_appeals.jsonl`을 추가했다. `parse_order.py`에 `그 형의`와 일부 집행유예를 처리하도록 고쳤다(원문 전수 대조로 발견). DATA.md에 상태 표를 추가했다. 시각적 표시 방식은 정하지 않았다.
- **양형 맥락·조문(같은 날):** `scripts/annotate/sentencing_factors.py`, `scripts/annotate/law_application.py`, `scripts/statutes/kb_articles.py`, [인코딩 워크시트](../research/ENCODING_DECISION_WORKSHEET.md), D-014를 작성했다. 표본 대조로 거짓 양성(형법 제51조 상투 문구, `장애` 오탐)과 파서 버그(`각 형법`)를 찾아 고쳤고, PDF 기반 방향 추론은 오판이라 폐기했다. 워크시트의 결정 칸은 비워 두었다.

2026-11-16: OpenAI Codex가 Claude 요약과 로컬 구현을 대조하고 명시 양형 방향 규칙, 우선순위 폴더 링크 생성기, 회귀 검사 및 DATA_PRIORITY_REVIEW를 작성했다. 법률 사람 검증은 수행하지 않았다.
- **V1 인코딩 최종본(같은 날):** [V1_ENCODING.md](../specs/V1_ENCODING.md), [glyph_registry.json](../specs/glyph_registry.json), `scripts/checks/glyphs.py`. 대부분은 사용자 결정을 기록했고, 사용자가 위임한 항목(나머지 도형·선 패턴·범례 문구 초안)만 Claude가 정했으며 표마다 표시했다. 12px 픽셀 유사도 측정은 Claude가 설계·실행했고, 측정 기준값은 프로젝트 기준(문헌 수치 아님)이다.
- **프로토타입(같은 날):** React를 걷어 내고 Vanilla TS + D3 프로토타입을 작성했다. 파일은 `src/main.ts`, `src/app/main.ts`, `src/state/store.ts`, `src/data/load.ts`, `src/domain/types.ts`, `src/vis/v1.ts`·`v2.ts`·`legend.ts`, `src/vis/glyphs.generated.ts`(생성), `src/styles/main.css`, `scripts/publish/export_prototype.py`, vite 로컬 데이터 경로, [PROTOTYPE_STATUS](../development/PROTOTYPE_STATUS.md)다. 시각 인코딩은 사용자 결정(V1_ENCODING, V2_ENCODING)을 따랐다. 결정과 다르게 구현된 부분은 그 문서에 적었다.
