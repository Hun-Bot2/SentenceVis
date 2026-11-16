# VALIDATION — 링크·피고인·판단·근거 검증 프로토콜

**상태:** 검증 계획 [PLAN]. **아직 187개 쌍·94개 후보를 직접 재검증하지 않았음.** 시각화는 검증 상태를 드러내야 하며, 검증 전 관계를 확정된 사실로 제시하지 않는다.

## 1. 핵심 위험 4가지

1. **Case-pair error:** 1심과 항소심을 잘못 연결.
2. **Defendant alignment error:** 공동피고인 A의 1심과 B의 항소심을 비교.
3. **Legal annotation error:** 항소이유/제기 주체/처리 결과/직권 쟁점을 잘못 분류.
4. **Provenance error:** 판단 경로는 있지만 인용 문장과 링크가 불일치.

## 2. 파이프라인 단계와 보류 규칙

```text
원본 무결성 검사
  → 사건번호/원심판결 참조 추출
  → 사건쌍 후보 생성 (candidate)
  → 사건/법원/죄명/원문 참조 대조 (verified / rejected / unresolved)
  → 피고인별 정렬 (verified / ambiguous)
  → 1심/2심 주문 및 집행유예 추출
  → 항소이유·제기 주체·판단 결과·직권 쟁점 주석
  → 개별 관계 ↔ 판결문 구절 매칭
  → 역사적 조문/법령 판본 조회 (가능한 경우)
  → 사용 가능·보류·제외 이유별 집계 + 스냅샷
```

`unknown`, `ambiguous`, `unreviewed`를 빈 값이나 ‘유지’로 바꾸지 않는다.

## 3. 사건 쌍 연결 기준

필드: `case_pair_id`, `trial_case_no`, `appeal_case_no`, `trial_court`, `appeal_court`, `offense_name`, `source_judgment_id`, `link_basis`, `link_status`, `reviewer`.

- 1순위: 항소심 원문 `【원심판결】`에 명시된 사건 번호, 해당 법원, 죄명을 원심 문서와 대조.
- 보조: 날짜 순서, 일치하는 문서 본문 정보, 범죄사실·주문 정보.
- 번호/법원만 같더라도 공동피고인·분리 사건·환송 등 확인이 필요하면 `unresolved`.
- 거짓 연결 후보와 제안서상 제외된 16건의 이유를 별도 기록.

**테스트:** 역참조, 중복쌍, 하나의 사건 번호가 서로 다른 레코드로 과도하게 중복되는 경우 자동 경고.

## 4. 피고인별 대응 규칙

- `defendant_id`는 사건쌍 **내부의 별칭**이며 사람의 실제 신원이 아니다.
- 두 판결문에서 피고인 지칭의 일관성이 보이지 않으면 `ambiguous`; 1심·2심 형기를 임의 연결하지 않는다.
- 공동피고인 수가 다른 경우 누락/분리/병합 여부를 확인한다.
- 특정 피고인의 선고형이 아닌 전체 사건의 ‘징역’ 숫자를 그대로 매핑하지 않는다.
- 항소심이 파기·환송했는지, 재판 결과가 확정됐는지는 별도 절차 메타데이터로 기록.

## 5. 항소 이유 및 법률 판단 주석

| 항목 | 규칙 |
|---|---|
| `ground_type` | 원문 표제/내용에 근거해 사실오인·법리오해·양형부당·기타로 분류. 모호하면 기타/보류 |
| `origin` | 피고인 / 검사 / 법원 직권 구별. ‘직권’은 당사자 항소이유와 강제 병합 금지 |
| `disposition` | 인용 / 배척 / 판단하지 않음 / 해당 없음; **직권 쟁점의 `해당 없음`은 실패/기각이 아님** |
| `reasoning_change` | 1심 대비 유지/변경/추가/삭제/불명확; 반드시 비교 대상 2개 문장 기록 |
| `statute_role` | **법령의 적용**에 명시된 것인지, 그저 언급만 한 것인지 구분 |

LLM을 초벌 라벨링에 쓸 수 있으나 **모델 이름·프롬프트 버전·응답·검증자**를 기록한다. 핵심 결과를 뒷받침하는 법률 판단 경로는 사람이 직접 읽고 확인한다.

## 6. 출처·검증 상태 — 독립 축

`source_basis`: `explicit_text` / `llm_extracted` / `contextual`
`verification_status`: `unreviewed` / `reviewed` / `conflicted`

- 원문에 명시된 법률 관계(`explicit_text`)도 문서와 피고인을 잘못 연결했다면 `unreviewed` 또는 `conflicted`일 수 있다.
- LLM 추출 관계라도 수작업 대조가 완료되면 `reviewed`가 될 수 있다.
- 점선이 `LLM 추출`을 뜻하더라도 **확인 완료 여부**를 동일한 점선 하나에 억지로 담지 않는다.

## 7. 평가셋 및 합의 절차 [PLAN]

- 시작: **서로 다른 패턴 20~30 사건**을 층화 표본으로 수동 검토. 이후 대표 3~5 사건은 원문까지 완전히 검증.
- 표본 범주: 형기 감소/증가/동일·집행유예 변경·직권판단·공동피고인·조문 오류·미판단.
- 두 사람 검토가 가능하면 `ground_type`, `origin`, `disposition`에 대해 독립 주석과 불일치 조정 기록; 가능하지 않다면 단독 검증임을 투명하게 적음.
- 자동 추출의 **정답률을 임의로 만들지 않는다**. 표본 수, 기준, 일치율, 불확실성 명시.
- 핵심 Case Study는 `source_quote`, `document_sha256`, `section_path`, `reviewed` 상태가 확인된 것만 사용.

## 8. 테스트 예시

- 같은 형기이지만 집행유예가 바뀐 사건은 `unchanged` 형기 + `suspension_changed`로 표현된다.
- 원문에 `판단하지 아니한다`가 있는데 시스템이 `배척`으로 분류하면 실패.
- 법원이 직권으로 원심을 파기한 사건은 당사자 항소 이유를 `accepted`로 변환하지 않는다.
- 추출된 조문이 판결문 본문에 언급된 것만으로 `applied`가 되지 않는다.
- 모든 선택한 V2 path ID는 V3에서 적어도 한 개 이상의 문서 구절/불명확 경고로 연결된다.
- 문서 해시가 바뀌어 offset이 틀어졌다면 해당 근거를 다시 검증한다.

## 9. Audit report 템플릿

```markdown
# Data Validation Snapshot — YYYY-MM-DD
- 원본 문서 수:
- case-pair 후보 / 검증 / 거부 / 보류:
- 정렬된 피고인 수 / 공동피고인 모호:
- 형기·집행유예 파싱 가능 수:
- 항소이유·판단 레이블 수 / 검증 완료 수:
- 원문 출처 연결 완성 경로 수:
- 보류·오류 사례(유형별):
- 모델/코드 버전 및 추출 설정:
- 검증자와 표본 추출 규칙:
- 공개 가능한 데이터 규모 / 공개 불가 이유:
```

## 10. 계약 동결 전 확인 — 2026-11-13

[REVIEW.md](../records/REVIEW.md)의 grain·관계 ID·상태 전이·출처 차원·offset 문제를 먼저 코드북에 기록한다. `reviewed` 수를 수용된 정답 수로 간주하지 않는다. 공식 웹 소개도 로컬 데이터 구조와 다를 수 있으므로 실제 샘플의 필드·해시·비식별화 전후 위치를 확인한다. AI 추출 지표의 정답 단위와 분모는 [탐구 H7](../research/DESIGN_TUTOR.md#h7-왜-mldl이-필요한가-무엇을-맞혀야-하는가)을 참고해 사용자 판단으로 명시한다. 현재 데이터와 성능은 여전히 `unverified`다.

## 11. 로컬 구조 조사 스냅샷

2026-11-13에 [LOCAL_DATA](LOCAL_DATA.md)의 v4 인덱스를 생성했다. 핵심 데이터 12 JSON 전체 파싱·ZIP hash·원천/라벨 분모·ID 중복·표현 간 후보 대응·관측 결측을 확인했다. 비공개 `verification.json`은 구조적 대조 결과이며 법률 정확성 검사가 아니다. 187개 심급 쌍, 94개 징역 후보, 공동피고인 정렬·추출 정답은 여전히 미재현/미검증이다. `char_count`와 span 단위·시대/역법 표기·분류 충돌은 원문 검토 전 자동 수정하지 않는다. 경로·해시·ambiguous·보류 동작은 합성 ZIP 테스트로 확인한다.

## 12. 자동 추출 파이프라인 스냅샷 (2026-11-16)

**상태:** 규칙 기반 자동 추출, 전부 `unreviewed`. 사람 검증 0건. 아래 수치는 관측치가 아니라 **자동 후보 수**다. 결정 근거는 [D-013](../records/DECISIONS.md#d-013--관계는-원문-명시-경로로-한정하고-정확도는-사용자-라벨로-측정).

```bash
python3 -I scripts/align/build_dataset.py data/private/pipeline/<새 실행 폴더> data/private/pipeline/criminal_cache.jsonl
python3 -I scripts/statistics/context_tables.py data/private/pipeline/<실행 폴더>
python3 -I scripts/annotate/make_sample.py data/private/pipeline/<실행 폴더> data/private/labeling/<새 표본 폴더>
python3 -I scripts/annotate/label_server.py data/private/labeling/<표본 폴더>   # http://127.0.0.1:8765/
python3 -I scripts/annotate/metrics.py data/private/labeling/<표본 폴더>
```

캐시가 없으면 첫 명령의 두 번째 인자를 빼면 된다. 이때는 `catalog.sqlite`를 거쳐 ZIP을 해시 검증하며 다시 읽는다.

| 단위 | 실행 `run-20261116b` |
|---|---:|
| 형사 원천 판결(일반 subset, 원천 `category` 기준) | 2,992 |
| 항소 사건번호 문서 | 998 |
| 연결 후보: `auto_strict` / `auto_alias`(서울지법→서울중앙 개편만) / `auto_partial` | 215 / 4 / 33 |
| 수용 연결의 항소 문서 / 그중 2002–2011 선고 | 215 / 201 |
| 피고인 행: `auto_single` / `needs_review` | 119 / 431 |
| V1 후보(양쪽 단일 징역, 복수 형 없음) | 59 |
| 이유 단서(ground/rejected/accepted/ex_officio/reversal/not_reached) | 1,487 / 679 / 184 / 199 / 151 / 64 |

- 라벨 기준 형사 문서는 2,700건, 원천 `category` 기준은 2,992건이다. 두 분류 기준의 차이는 아직 조사하지 않았다.
- `needs_review` 431행은 문서에 나온 피고인 번호를 합친 수라서 실제 인원수가 아니다.
- 연결 규칙은 법원 정규화 후 **완전일치**만 쓴다. 부분문자열로 맞추지 않는다. 별칭은 서울지방법원과 서울중앙지방법원 1쌍뿐이다. 날짜 일치와 날짜 선후는 따로 검사한다. 축약 사건번호 목록을 펼친 경우는 `abbrev_expanded`로 표시한다. 이번 실행에서 그렇게 수용된 연결은 0건이다.
- 이유 단서는 원문 문구와 위치(span)만 담는다. 단서 사이의 관계는 같은 번호 블록 안에서 가장 가까운 단서를 잇는 `rule_proximity` 제안일 뿐이며, 법원의 판단으로 표시하지 않는다.
- 표본(시드 20261116): 수용 연결 40, 부분 연결 33(전수), V1 30, 단서 유형별 10(총 60), 항소 문서 15(항소이유 유형 집합의 재현율 측정용). 정확도는 프레임별 95% Wilson 구간으로 보고한다. '불확실' 응답은 분모에서 빼고 따로 센다.
- 맥락표: CCJS 표에서 `계` 행은 모든 연도가 0이라 말단 죄명 행만 합산했다. 표가 모든 항소심 법원을 포괄하는지는 미확인이다. CCJS는 인원 단위, AI-Hub는 문서 단위라서 표본추출률은 계산하지 않는다. 양형기준 판정은 1심 선고일이 2009-07-01보다 앞서면 `not_applicable_by_date`로 두는 것뿐이고, 이 날짜 자체가 원문 미확인이다.

### 12.1 통합 코퍼스 재구축 (2026-11-16, 실행 `run-20261116n`)

[AI-Hub 교차 검증](../research/AIHUB_CROSS_VALIDATION.md) 이후 12와 115의 형사 판례를 일련번호로 합쳤다(`scripts/align/merge_corpus.py`). 같은 판결은 **12의 익명화본을 우선**하고, 사본은 모두 `copies`에 남긴다. 115에만 있는 문서는 실명·지번이 남아 있을 수 있어 `display_ok=false`로 둔다. 화면에서는 이런 문서의 원문을 표시하지 않는다.

```bash
python3 -I scripts/align/merge_corpus.py data/private/aihub_scan/<스캔> data/private/pipeline/merged_criminal_cache.jsonl
python3 -I scripts/align/build_dataset.py data/private/pipeline/<새 실행> data/private/pipeline/merged_criminal_cache.jsonl
python3 -I scripts/statistics/context_tables.py data/private/pipeline/<실행>
python3 -I scripts/annotate/make_sample.py data/private/pipeline/<실행> data/private/labeling/<새 표본>
```

| 단위 (자동 후보, 미검증) | 12만 사용 | 통합 |
|---|---:|---:|
| 형사 판례 (12 / 115) | 2,992 | 15,875 (2,992 / 12,883) |
| 1심→항소심 수용 연결 | 219 | 237 |
| 항소심→대법원 수용 연결 (`instance_pair=2-3`) | — | 993 |
| 대법원 판결까지 이어진 사건쌍 | — | 226 / 237 |
| 대법원 결과: 상고기각 / 파기환송 | — | 657 / 330 |
| 피고인 행: auto_single / needs_review | 119 / 431 | 128 / 461 |
| V1 후보 | 59 | 63 |
| 피고인 행 중 `display_ok` | — | 557 / 589 |

- 대법원 결과는 사건쌍 단위로 붙인다. 부분 파기가 어느 피고인에게 해당하는지는 `scope` 문자열로만 남기고 피고인에 자동 배정하지 않는다.
- 표본 `sample-20261116m`(시드 20261116, 212개): 수용 연결 40, 부분 연결 47(전수), 대법원 연결과 결과 20, V1 30, 이유 단서 60, 문서 15. 이전 표본 `sample-20261116`은 12만으로 만든 것이라 쓰지 않는다(라벨 0건).

## 명시 양형 방향 규칙 후속

`유리한 정상`/`불리한 정상`만 방향 후보로 인정한다. 두 표현이 같은 문장에 있으면 미기재로 남긴다. PDF 표제·감경 일반어·죄질 표현으로 방향을 추론하지 않는다. 재실행 후보 수와 한계는 [대조 기록](../records/DATA_PRIORITY_REVIEW.md) 참조.
