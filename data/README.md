# 로컬 비공개 데이터와 조사 인덱스

사용자가 받은 AI-Hub 019/114/115/12 원본 ZIP 폴더를 현재 위치에 보존한다. 이름 변경·일괄 해제·내용 변경을 하지 않았다. `data/` 아래는 이 README를 제외하고 기본 Git 제외이며 Vite 개발 서버의 제공 대상에서도 차단한다. 원본을 다른 도구에 자동 업로드하지 않는다.

현재 조사 결과는 `private/inventory/2026-11-13-v4/`의 `manifest.json`, `schema_profiles.json`, `catalog.sqlite`, `verification.json`이다. 조사 중간 v1–v3는 폐기했으며 현재 사용 대상은 v4다. 이 출력은 비공개 문서 ID/경로/표제를 포함하므로 공개하지 않는다.

```bash
python3 scripts/ingest/inventory.py scan --output data/private/inventory/new-snapshot
python3 scripts/ingest/verify_inventory.py data/private/inventory/new-snapshot
```

프로젝트 루트에서 실행하며, 새 출력 경로를 사용한다. 조사 범위·실제 수량·필드·SQL·원문 조회 방법은 [LOCAL_DATA](../docs/specs/LOCAL_DATA.md), 소스는 [inventory.py](../scripts/ingest/inventory.py)에 있다. `raw/private/processed/cache`는 향후 입력/파생 경로로 계속 보존한다. 현재 사용자 폴더를 raw로 옮길 필요는 없다.

공개 export·형량 추출·피고인 정렬은 미구현이다. 파일 파싱 성공은 법률 정답·원문 공개권 확인을 뜻하지 않는다. `.gitignore`는 이미 추적된 파일을 숨기지 않으므로 staging 전에도 확인한다.

## 작업 우선순위 탐색

`python3 scripts/catalog/prioritize.py`로 `data/priority/최우선`, `보통`, `보충`에 원본 링크를 만든다. 원본 이동은 없다. [분류·검토 기록](../docs/records/DATA_PRIORITY_REVIEW.md)을 참조한다. 우선순위는 검증 상태와 별개다.
