# DATA — 데이터셋 구성·추상화·API·공개 범위

**상태:** source inventory + planned schema [PROPOSAL + OFFICIAL + PLAN]. `slides(1).pdf` p.2·p.7의 수치는 **제안 당시 자동 추출 결과**이며 저장소에서 아직 재현/검증하지 않았다.

## 1. 질문에서 데이터로

분석 단위는 여러 수준의 계층과 링크를 갖는다. **문서 건수 ≠ 사건 쌍 ≠ 피고인 비교 건수 ≠ 항소이유 수**다. 최종 보고서에서는 기준 분모를 반드시 표기한다.

```text
CasePair (1심↔항소심 연결 후보)
 ├── Defendant (같은 사건에서 심급간 대응된 피고인)
 │    ├── Judgment [court_level=1] ─┐
 │    └── Judgment [court_level=2] ─┴─ Sentence
 ├── AppealGround (사실오인/법리오해/양형부당/기타; origin별)
 │    └── Disposition (법원의 판단; 독립적인 직권 쟁점도 있음)
 ├── ReasoningRelation (유지/변경/추가/삭제/불명확; 원문 근거 필수)
 └── Evidence (판결문 구절/조문/문서 섹션/출처 상태)
```

## 2. 외부 자료 및 역할

| 데이터셋 | 핵심 역할 | 범위 / 확인 상태 | 원문 |
|---|---|---|---|
| **AI-Hub 판결서 익명처리 데이터** | 형사 판결문 본문·메타데이터/익명화 주석 | [PROPOSAL] 형사 판결 2,700건으로 연결 시도. 공식 공개 페이지는 원본 전체 규모와 업데이트 이력을 제공; 실제 받은 파일 수 확인 필요 | https://aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=511&dataSetSn=71968 |
| **국가법령정보센터 공동활용 API** | 법령·조문·법령 연혁, 조문판본 조회 | [OFFICIAL] 법령 연혁 목록·본문 조회 가이드 존재. 특정 과거 판결에 적용되는 조문 판본은 따로 검증 | https://open.law.go.kr/LSO/openApi/guideList.do |
| **판례 API** (선택) | 수집된 판결문과 별도 판례 메타데이터 대조 | 필수 아님; 커버리지/접근 제약 확인 전 | 위 API 가이드 |
| **법령용어/지능형 법령지식베이스** (선택) | 시민에게 어려운 용어 해설 | [PLAN] 핵심 근거로 쓰지 않음, 별도 출처 레이블 | 위 API 가이드 |
| **대법원 양형위원회 과거 양형기준** (선택) | 특정 시점의 배경 정보 | [PROPOSAL] 2009년 이전 사건에 현재 양형기준을 소급해서 표시하지 않음 | https://sc.scourt.go.kr/ |
| **대한민국 헌법** (선택) | 개념 설명 | 사건 변경의 *원인 연결선*에 사용하지 않음 | https://www.law.go.kr/ |

### 제안서의 후보 현황 — 무조건 `candidate`로 취급

| 값 | 제안서 내용 | 올바른 해석 |
|---:|---|---|
| 2,700 | 형사 판결문 | 처리 대상 문서로 기술된 수치 |
| 187 | linked case pairs | 사건번호·법원·죄명으로 자동 연결한 **후보** |
| 94 | 양쪽 주문에 징역형이 있는 pair candidates | **94개 피고인 비교가 아님** |
| 43 | 94개 후보 중 공동피고인 포함 | 1·2심 인물 정렬이 특히 위험 |
| 8/37 | 형기는 같지만 집행유예 상태가 다른 후보 | 독립 채널 필요성의 발견 단서, 아직 미검증 |
| 18/187 | 참조조문 메타데이터 있는 쌍 | 메타데이터 부재≠본문에 조문 없음 (제안서상 본문 185건) |

**과제 최소 조건:** 100 items 이상, 6 attributes 이상. 검증되지 않은 187개 사건 쌍을 *검증된 피고인 비교 187건*처럼 제시하면 안 된다. 각 분석 수준의 전체·보류·검증 건수를 별도로 보고한다.

### AI-Hub 원본 관련 주의

- 원본 데이터는 판결서 *익명처리* 목적의 데이터이며, 항소이유/판단/인과관계의 정답 라벨을 제공하는 데이터셋은 아니다.
- 제안서 p.2에서는 전체 자료 13,500 일반판결 + 1,800개의 1·2·3심 사건 묶음을 기술한다. 공식 AI-Hub 페이지의 전체 공개량과 형식 단위가 다를 수 있으므로 **실제 로컬 아카이브 manifest**를 생성해 교차 검증할 것.
- 개인정보 마스킹 표현(`#이름#` 등)은 조작하지 않고 유지하되, 공개 웹 배포 가능 여부는 원자료 약관과 라이선스 조건을 직접 확인한다.

## 3. 데이터 유형과 속성 추상화

**Dataset type:** Multi-level table + derived directed/linked network + semi-structured text. 단순한 flat CSV가 아님.

| 계층 | key (identity) | 주요 values |
|---|---|---|
| CasePair | `case_pair_id` | 원심/항소심 사건번호, 연결 상태, 결정일 |
| Defendant | `defendant_id` (사건 쌍 내부 ID) | 공동피고인 정렬 상태 |
| Judgment | `judgment_id` | `court_level`, `prison_months`, `suspended` |
| AppealGround | `appeal_ground_id` | `ground_type`, `origin`, `disposition`, `reasoning_change` |
| Evidence | `evidence_id` | `source_document_id`, `section`, `source_quote`, `statute_role`, `source_basis`, `verification_status` |

| attribute | 유형/순서 | 값 범위 / 의미 | null / 위험 |
|---|---|---|---|
| `court_level` | ordinal; 1 < 2 < 3 (절차 순서) | 1심/항소심/대법원 | 상고심은 V1의 세 번째 형량점이 아님 |
| `prison_months` | quantitative ratio; 높은 값이 긴 형 | 제안서: 징역 2–144개월 (실제 범위 재계산) | 미확인/징역형 외는 `null`, **0개월로 대체 금지** |
| `suspended` | nominal | `true`/`false`/`unknown` | 실형 vs 집행유예를 형기의 단순 숫자로 환원하지 않음 |
| `ground_type` | nominal | 사실오인/법리오해/양형부당/기타 | 하나의 사건에 다수의 항소이유 가능 |
| `origin` | nominal | 피고인/검사/법원 직권 | 직권 쟁점은 당사자 항소이유가 아닐 수 있음 |
| `disposition` | nominal | 인용/배척/판단하지 않음/해당 없음 | 직권판단에 `인용`이라고 억지 매핑 금지 |
| `reasoning_change` | nominal | 유지/변경/추가/삭제/불명확 | 법률적 해석 필요, 자동 추출로 확정 금지 |
| `statute_role` | nominal | `applied` / `mentioned_only` / `uncertain` | 본문 등장과 적용 구별 |
| `decision_date` | temporal | 제안서 항소심 범위 2002–2011 | 포맷/시간대 정상화 |
| `source_basis` | nominal | `explicit_text` / `llm_extracted` / `contextual` | ‘무슨 근거로 만든 링크인가’ |
| `verification_status` | nominal (작업상태) | `unreviewed` / `reviewed` / `conflicted` | **근거 유형과 별도 차원** |

**주의:** 제안서의 단일 `evidence_status` 4단계는 명시성·추출·검증 여부를 혼합한다. 설계안에서는 위 **두 컬럼으로 분리**한다. 단조 순위로 품질 점수처럼 색을 입히지 않는다.

## 4. 권장 JSON 데이터 계약 [PLAN; 파일 미구현]

### `case_pairs.json` (사건 및 V1의 출발점)

```json
{
  "case_pair_id": "PAIR-PSEUDONYM-001",
  "trial_judgment_id": "J1-001",
  "appeal_judgment_id": "J2-001",
  "link_status": "candidate",
  "link_basis": ["prior_case_number", "court", "offense"],
  "defendants": [
    {
      "defendant_id": "P1",
      "alignment_status": "unreviewed",
      "trial": {"prison_months": null, "suspended": "unknown"},
      "appeal": {"prison_months": null, "suspended": "unknown"}
    }
  ]
}
```

위 값은 **schema 예시용 가짜 데이터**다. 실제 판결 및 확정 관측치로 쓰면 안 된다.

### `grounds.json` / `evidence.json`

- `grounds`: `appeal_ground_id`, `case_pair_id`, `defendant_id?`, `ground_type`, `origin`, `disposition`, `reasoning_change`, `evidence_ids[]`, `verification_status`.
- `evidence`: `evidence_id`, `judgment_id`, `section_path`, `source_excerpt`, `start_offset?`, `end_offset?`, `document_sha256`, `source_basis`, `verification_status`.
- `statutes`: `statute_id`, `law_name`, `article`, `law_version_id`, `effective_from/to`, `applied_or_mentioned`, `url`, `retrieved_at`, `source_snapshot_hash`.
- 원문 인용 범위·문서 해시·파싱 버전은 공개 범위 안에서만 제공.

## 5. 국가법령정보센터 API 작업 방침

공식 가이드: https://open.law.go.kr/LSO/openApi/guideList.do

- `법령 연혁 목록 조회`와 `법령 연혁 본문 조회`가 공식 제공됨. **현행법령만 조회하는 경로로 과거 법령을 대신하지 않는다.**
- `2005고합52 → 2006노444` 같은 사건에서 판결문에 적힌 특정 조문을 먼저 수동 확인하고, 1심·항소심 각 시점의 법령 연혁 ID 및 조문 텍스트를 조회한다.
- **실제 적용 법령의 시점:** 판결일 시행 법령을 참고하되, 범행 시점과 경과규정·법원의 적용 판단도 읽어야 한다.
- 실시간 호출보다 사전 수집·스냅샷·캐시를 우선한다. 인증값(`OC`)은 `.env`에 보관, Git에 올리지 않음.
- 법령 목록 및 본문 JSON/XML에서 응답 필드 구조가 API마다 다를 수 있으므로 schema adapter를 두고 공식 샘플로 검증.
- 에러·호출 제한·서비스 변경에 대비하고, 재현 가능한 수집 일시/원문 버전 기록.

## 6. 공개·비공개·재현성

| 구분 | 예 | 저장/공개 기준 |
|---|---|---|
| 원본 | AI-Hub 원본 JSON, API 인증값, 다운로드 파일 | `data/raw/`, `.env*` 등 private; Git 제외 |
| 내부 파생 | 피고인 정렬 증거, 긴 원문, 추출 후보 및 검증 로그 | `data/private/`에 별도 보관 |
| 공개 가능한 파생 | 최소 요약값, 출처 ID, 라이선스 허용 범위의 짧은 인용 | **권리/재식별/출처표기 점검 후** `public/data/` |
| 구현 및 메타 | 스키마, 검증 코드, 집계 로직, 샘플 테스트 fixture | 공개 가능 여부 확인 후 versioned |

**현재 확인되지 않은 사항:** AI-Hub의 개별 데이터 이용허락 범위, 판결 원문 부분 인용 허용 범위, 서비스 배포 조건. 해당 약관·신청 계약 내용을 확보해 확인하기 전까지 전체 원문 공개 금지. 이 문서는 법률 자문이 아니다.

## 7. 데이터 준비 완료의 수용 기준

- [ ] 원본 manifest: 파일 수, 구분, 해시, 취득 일시, 라이선스/출처
- [ ] 실제 `case_pair`/`defendant`/`judgment`/`ground`/`evidence` 수를 단계별로 재계산
- [ ] 1심–항소심 링크 및 동일 피고인 매핑 검증
- [ ] 형기/집행유예가 각각 독립·정확히 파싱되는지 확인
- [ ] 적용 조문과 단순 언급 조문 구분
- [ ] 샘플별 evidence 링크가 출처 텍스트까지 역추적 가능
- [ ] 유효한 ≥100 items, ≥6 attributes의 **정확한 측정 기준** 보고서에 고정

## 8. 2026-11-13 공개 소개 대조와 계약 확인 과제

`[RESEARCH]` [AI-Hub 공식 소개](https://aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=511&dataSetSn=71968)의 현재 규모 표기는 제안서와 다르다. 소개 표의 건수/비율 및 일부 필드 설명에도 내부 불일치가 있다. 자세한 열람 범위는 [추가 참고자료 F9](../research/RESEARCH_REFERENCES.md#f9-데이터-출처와-미해결-항목)를 따른다. 공개 소개값을 로컬 보유량이나 검증된 비교 건수로 바꾸지 않는다. LLM 관련 소개만으로 모든 문서를 합성으로 분류하지 않는다.

문서–피고인별 선고의 grain, 독립 relation 계약, 검토/판정 구별, 출처 명시성과 추출 방법의 차원, offset 기준은 [검토 기록](../records/REVIEW.md)의 미해결 사항이다. 기존 JSON은 확정 계약이 아니며 이번 검토에서 실제 파일을 검증/변환하지 않았다.
