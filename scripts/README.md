# 오프라인 처리와 개발 검사

- ingest: AI-Hub 전수 스캔(`aihub_scan.py`)·데이터 간 교차 검증(`aihub_crosscheck.py`, `aihub_textdiff.py`; [보고서](../docs/research/AIHUB_CROSS_VALIDATION.md)), 원본 ZIP manifest·스키마 조사·비공개 SQLite 메타데이터 인덱스·독립 대조·원문 private 조회 구현. 법률 레이블 정규화는 미구현.
- align: 형사 원천 판결 로더(`corpus.py`), 원심판결 기반 사건쌍 연결(`link_pairs.py`), 전체 스냅샷 빌더(`build_dataset.py`). 규칙 기반·`unreviewed`. 피고인 정렬은 양쪽 단독 피고인만 자동이며 나머지는 `needs_review`.
- annotate: 주문 파서(`parse_order.py`), 원문 명시 이유 단서(`extract_paths.py`), 고정 시드 표본(`make_sample.py`), 로컬 라벨링 도구(`label_server.py`, 127.0.0.1 전용), Wilson 구간 지표(`metrics.py`), 법령의 적용 단계(`law_application.py`), 양형 요소 단서(`sentencing_factors.py`).
- statistics: CCJS 수집·정규화와 맥락표(`context_tables.py`).
- statutes: AI-Hub 지식베이스 조문 색인(`kb_articles.py`; 법령당 판본 하나, `contextual`). 판결 당시 판본 조회는 미구현.
- publish: 로컬 프로토타입 내보내기(`export_prototype.py`, data/private 아래, display_ok 아닌 원문 제외). 공개 export는 미구현.
- checks: 소스 경계·Markdown 파일 링크 검사 (구현).

이 폴더의 처리기는 브라우저 번들에서 import하지 않는다. 원본·개인정보·API 인증값을 fixture나 public으로 복사하지 않는다. 정렬·추출은 규칙 기반 초판이 있고(VALIDATION §12), 법령 연혁 조회와 공개 export는 미구현이다. 로컬 구조 조사 명령은 [LOCAL_DATA](../docs/specs/LOCAL_DATA.md)에 있다.
