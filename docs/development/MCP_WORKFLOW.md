# MCP WORKFLOW — SentenScope × Orven 연구 자료 왕복 전달 및 데이터 운영

> **핵심 결정:** MCP의 목적은 **데이터셋 다운로드나 GitHub 직접 수정이 아니라**, 이 채팅에서 생성한 연구 산출물을 **Orven의 승인 기반 Handoff를 거쳐 로컬 SentenScope 저장소에 전달**하고, 로컬 분석 결과를 **선별해 다시 ChatGPT에서 검토**하는 것이다.
>
> **문서 상태:** `[PLAN]` · 2026-11-13. 기존 데이터 수집·검증 계획은 유지한다. Orven의 구성과 도구는 **기존 설계에서 파악한 내용**으로, 이 문서는 현재 세션에서 실제 MCP 연결이나 E2E 동작을 검증했다는 뜻이 아니다.
>
> **관련 문서:** [ENGINEERING.md](ENGINEERING.md)(개발 구조) · [DATA.md](../specs/DATA.md)(데이터 정의) · [VALIDATION.md](../specs/VALIDATION.md)(데이터 검증) · [TASK.md](../planning/TASK.md)(학회 투고 연구 과업) · [PAPER.md](../specs/PAPER.md)(연구 질문과 주장). 실제 저장소의 경로가 다를 경우 링크를 해당 경로에 맞춰 조정한다.

## 1. 목적과 책임 경계

SentenScope의 재현성은 **원본과 결과를 모두 공개하는 것**이 아니라, **허가된 원본에서 동일한 파생 결과를 재생성하는 절차·버전·검증 근거를 남기는 것**이다. Orven은 이 과정을 보조하는 **연구 자료 전달·승인 계층**이며, 법률 데이터의 원천이나 검증 주체가 아니다.

| 계층 | 맡는 일 | 맡지 않는 일 |
|---|---|---|
| **ChatGPT (Research workspace)** | 논문 조사, 분석 해석, 설계 검토, Markdown/코드 초안, 허용된 자료로 추가 분석 | 허가 없는 원본 수집, 자동 법률 정답 판정, 로컬 파일에 대한 임의 쓰기 |
| **Orven Cloud Handoff** | 등록된 대상 조회, 선택한 텍스트·메타데이터 수신, 임시 Inbox, 상태 추적 | 데이터셋 다운로드, 대용량 ZIP 저장소, Git 실행, 셸/로컬 에이전트 실행 |
| **Orven Desktop + Local Approval** | 대상 프로젝트와 변경 내용을 확인, 승인·거절, 허가된 로컬 저장 | 승인 전 자동 파일 수정, 연구 결과의 사실성 보증 |
| **SentenScope local repo** | 수집·정규화·매칭·검증·분석·시각화 구현, Git 버전 관리 | 무검증 후보를 gold label로 자동 승격 |
| **연구자·주석자** | 데이터 권리 확인, 법률 판단 검증, 실험 윤리·연구 주장 최종 책임 | AI 출력의 무조건 승인 |

**기본 규칙**

- 원본 판결문 ZIP, API 키, 참여자 식별정보 및 비공개 근거는 **허가된 로컬 환경에 보관하고 Git·Orven Cloud에서 제외**한다.
- GitHub 커밋은 **Orven Handoff의 필수 단계가 아니다**. 로컬에 승인·저장한 후 별도 Git 워크플로에서 수행한다.
- ChatGPT가 분석에 사용한 입력, 산출물, 불확실성을 구별한다. `[PLAN]`, `[CANDIDATE]`, `[VERIFIED]`를 혼용하지 않는다.
- LLM 추출은 `candidate`; 법률적 정답은 독립 검증 후에만 `verified`가 된다.
- Orven의 Handoff는 **전송 완료 ≠ 검증 완료 ≠ 저장 완료 ≠ Git 반영 완료**라는 서로 다른 상태를 유지한다.

## 2. 양방향 협업의 실제 의미

```text
[연구 자료 생산: ChatGPT]
  조사·분석·PAPER/TASK/DATA 초안
           │ 선택된 Markdown·메타데이터만
           ▼
[Orven Remote MCP — 제안된 Cloud Handoff]
  list_handoff_targets → submit_handoff → get_handoff_status
           │
           ▼
[Cloudflare Worker + D1 Inbox]  (단기 임시 보관, 기본 목표 1일)
           │ 로컬 Orven이 조회/claim
           ▼
[Orven Desktop]  내용·대상·경로·차이 확인 → 사용자가 승인/거절
           │ 승인된 파일만 원자적 저장
           ▼
[SentenScope 로컬 저장소]  문서/스크립트/검증 보고서 → 개발·Git 관리
           │
           ▼
[로컬 수집·검증·분석]  원본 ZIP/API 응답은 이 경로에만 보관
           │  허용된 통계·스키마·요약·스크린샷을 선별
           ▼
[ChatGPT로 재반입]
  A. 현재 가능한 기본 경로: 사용자가 파일/내용을 이 채팅에 첨부
  B. 향후 선택적 확장: 별도 권한과 서버가 있는 읽기 전용 Remote MCP
           │
           └────────────── 새 연구 검토 및 다음 Handoff ──────────────┘
```

### 2.1 ChatGPT → 로컬: 승인 기반 Handoff

1. ChatGPT에서 전달할 **최종 Markdown 또는 작은 구조화 보고서**를 선택한다.
2. 등록된 `SentenScope` 대상과 허용 경로를 조회한다(`list_handoff_targets`).
3. 전달 내용을 미리 검토하고 `submit_handoff`로 **임시 Inbox**에 제출한다.
4. Orven Desktop이 항목을 확인한다. 사용자는 파일명·대상·내용·변경 차이·출처를 검토한다.
5. **명시적 승인 후** 로컬 Markdown을 원자적으로 저장한다. 거부·만료된 항목은 저장하지 않는다.
6. 필요하면 연구자가 Git diff와 테스트를 확인한 후 직접 커밋한다.

**현재 상태 주의:** 도구 이름과 흐름은 Orven의 기존 설계 기준이다. Remote MCP를 지금 이 채팅에서 호출할 수 있는지, Orven Desktop까지 실제 수신·저장이 동작하는지 **연동 시험이 필요**하다. 연결이 없다면 파일 다운로드 후 로컬에 넣는 방법을 사용한다.

### 2.2 로컬 → ChatGPT: 기존 설계와 새 기능을 구분

- **현재 기본 경로:** 로컬에서 생성한 허용 가능한 `quality_report.md`, 집계 CSV, 스키마 JSON 등을 사용자가 **직접 첨부**하거나 내용을 붙여넣는다. 이 경로가 확실한 역방향 전달 방식이다.
- **향후 확장안:** 연구자가 선택·승인한 산출물만 조회하는 **읽기 전용 MCP**(예: `list_research_artifacts`, `get_research_artifact_summary`)를 Orven에 별도로 설계할 수 있다. 이 이름은 **제안**이며 현재 구현된 도구가 아니다.
- **금지:** Cloud Handoff가 로컬 저장소를 임의 스캔하거나 파일 전체를 외부로 전송한다고 가정하지 않는다. reverse-sync·자동 읽기·무제한 원격 실행은 현재 범위가 아니다.

### 2.3 대용량 데이터와 작은 전달물을 분리

| 자료 | 이동 경로 | Orven Cloud Handoff |
|---|---|---|
| AI-Hub 원본 ZIP·판결문 전문 | 승인된 연구자 로컬 보안 환경 | **전송하지 않음** |
| 법령 API OC·비공개 API 응답 | 로컬 비밀정보/승인된 데이터 경로 | **전송하지 않음** |
| `PAPER.md` 수정안·분석 메모·작업 지시 | ChatGPT → Orven → 사용자 승인 → repo | **적합** (크기·정책 범위 내) |
| 공개 가능한 스키마·품질 요약·통계 | 로컬 → 사용자 검토 → 채팅 첨부 | 선택적 요약 Handoff 가능, 역방향 자동 읽기는 미구현 |
| 수십~수백 MB 분석 ZIP·User Study 원자료 | 허가된 로컬 저장소 또는 적법한 별도 파일 전달 | **전송하지 않음** |
| ZIP의 `SHA-256`, 버전·크기·공개가능 여부 | 보고서·Manifest | **적합** (파일 자체는 별도 경로) |

## 3. Orven 연계 상태와 보안 계약

### 3.1 확인이 필요한 구현 상태

| 구성 | 기존에 파악한 상태 | SentenScope에서의 확인 항목 |
|---|---|---|
| Orven Rust Core/CLI·Tauri Desktop | 기본 기능 구현·테스트 이력 | 로컬 승인/저장 UI가 실제 연결되는지 |
| stdio MCP 감사 도구 | 제한된 로컬 감사 기능 구현 이력 | Cloud Handoff 도구와 **별개**임을 확인 |
| `orven-handoff` Worker / D1 / KV | 기반 자원 생성·로컬 개발 확인 이력 | 인증, 배포, API 처리, 만료·재시도 동작 확인 |
| Cloud MCP `list_handoff_targets`, `submit_handoff`, `get_handoff_status` | 설계된 도구 계약 | ChatGPT에서 접근 가능한지 실제 호출 시험 |
| 로컬 Inbox 수신·사용자 승인·파일 쓰기 | 설계 흐름 | 종단간 연결과 거절/재승인 검증 |
| 로컬 → ChatGPT 원격 조회 | **완성됐다고 확인되지 않음** | 필요 시 독립적으로 보안·권한 설계 |

### 3.2 Handoff 상태 전이 (기존 Orven 설계 기준)

```text
queued ──→ claimed ──→ awaiting_local_approval ──→ written
   │           │                     │
   ├─→ rejected│                     └─→ rejected
   └─→ expired ├─→ queued  (lease 만료/재시도)
               └─→ expired
```

- Cloud Handoff는 **원격 `submit_handoff`만으로 로컬 저장 성공을 표시하지 않는다**.
- 기존 설계의 **기본 보관 목표는 1일**이다. 실제 TTL, 정리 작업, 만료 시점 계산이 구현됐는지 확인한다.
- 제출은 대상별 `idempotency_key`와 `payload_hash/content_hash`로 중복을 검출한다. 반복 요청 시 중복 파일 생성 금지.
- 사용자가 승인하기 전에는 프로젝트 경로가 변경되지 않도록 한다. 승인 이후에도 단일 제어권·동시 쓰기 충돌·경로 이탈·대용량 입력을 검사한다.
- 인증, 권한, 요청 크기, 속도 제한, 로그 비밀정보 마스킹, 보관·파기 정책은 실제 배포 전에 테스트한다.

### 3.3 전달 패킷: 개념적 계약 (실제 MCP 인자 스키마 아님)

```json
{
  "schema_version": "handoff-note.v1",
  "target": "sentenscope",
  "title": "DATA — 연결 후보 검증 계획",
  "destination_hint": "DATA.md",
  "content_kind": "markdown_proposal",
  "body_markdown": "## 검증 계획\n...",
  "provenance": {
    "origin": "chatgpt",
    "source_context": "SentenScope 연구 검토",
    "review_status": "PROPOSAL",
    "based_on": ["DATA.md", "VALIDATION.md"]
  },
  "artifact_manifest": [],
  "idempotency_key": "caller-generated-unique-key"
}
```

**주의:** `destination_hint`는 **쓰기 권한이 아니다**. Orven이 미리 등록한 `target_id`와 허용 경로만 목적지로 삼고, 최종 쓰기 경로는 Desktop에서 사용자가 확인한다. 실제 도구 입력 형식은 Orven 구현 계약을 따른다. 텍스트 전문·해시·메타데이터를 처리하는 서버 측 검증과 같은 구조를 무조건 가정하지 않는다.

**Handoff 1건의 최소 감사 기록:** `handoff_id`, 대상 ID, 콘텐츠 종류, 제출 시각, 출처·근거, 콘텐츠 해시, 승인/거절자 및 시각(적법한 최소정보), 최종 결과, 쓰기 대상 경로, 해당 Git commit(있을 때만). 사용자 대화 전문이나 민감 원문을 자동 포함하지 않는다.

## 4. 데이터 소스 및 접근 경로 (MCP 역할과 분리)

| 데이터 | 획득·처리 경로 | ChatGPT에 공유할 수 있는 범위 | 유의사항 |
|---|---|---|---|
| AI-Hub 판결서 익명처리 | 연구자가 이용 조건에 따라 로컬에서 다운로드·분석 | 허용된 요약/집계/검증 자료. 원본 업로드는 이용 조건 확인 후에만 | MCP가 원본 ZIP을 받아 주는 다운로드 수단이 아님 |
| 국가법령정보 공동활용 | 승인된 OC를 로컬 환경 변수에 넣고 `scripts/statutes/` 실행 | 키를 제외한 요청 명세·스키마·검증 결과 | 역사적 법령 판본과 실제 사건 적용의 구별 필수 |
| 법률 지식기반 관계/법률 텍스트 분석 등 추가 AI-Hub 데이터 | 필요성·주석 품질을 사전 점검 후 허가된 환경에서 확보 | 공개 허용 범위의 스키마·품질 집계 | 다른 데이터셋의 관계를 특정 판결의 근거로 혼동 금지 |
| User Study | 공식 연구윤리 판단과 참가자 동의 범위에 따라 수집 | 적법하게 익명화한 결과와 집계 | 참가자 녹화·식별 자료 Handoff 금지 |
| GitHub 저장소 | 로컬 Git으로 버전 관리; 별도 GitHub 연동은 선택 | 공개 가능한 스크립트·문서·통계 | GitHub MCP는 Orven의 필수 구성 요소가 아님 |

참고 문서: [AI-Hub FAQ](https://aihub.or.kr/aihubnews/faq/list.do) · [국가법령정보 공동활용 가이드](https://open.law.go.kr/LSO/openApi/guideList.do) · [법령 연혁 본문 가이드](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsHstInfoGuide) · [시행일 법령 목록](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsEfYdListGuide).

> 위 링크는 참고용으로 유지한다. 이 개정에서 각 서비스의 현재 기능·응답 형식·약관을 새로 검증하지 않았다.

## 5. 데이터 수집·검증 단계 (로컬 실행, ChatGPT는 분석·문서화 보조)

**각 단계의 산출물은 로컬에 저장한다.** ChatGPT에는 공유 가능한 요약과 제안만 반입하고, 확정된 Markdown은 필요할 때 Orven Handoff로 반영한다.

### P0. 저장소·권한·자료 경계

- [ ] `SentenScope`를 Orven의 허용된 Handoff 대상으로 등록하고 대상 ID·기본 저장 경로를 확인.
- [ ] `data/raw/`, `data/private/`, `data/processed/`, `data/cache/`, 평가 원자료, `.env`와 비밀키를 Git 제외.
- [ ] AI-Hub·법령 API 이용권, 논문 인용/발췌/공개 범위를 출처별로 기록.
- [ ] `.env`/환경 변수 `LAW_API_OC`를 로컬에서만 사용하며 Handoff 전문·Git·브라우저 번들에 삽입하지 않음.
- [ ] `Orven target → allowed path`를 최소 권한으로 설정; 사용자 승인 없는 덮어쓰기 금지.

**Gate:** 데이터 권리·비밀정보·로컬 쓰기 권한이 분리되고, Orven이 원본 데이터 경로에 접근하지 않음.

### P1. 원본 ZIP 수령·무결성 검사

- [ ] 승인된 로컬 환경에서 ZIP 검사(zip-slip, zip bomb, 중복/인코딩) 및 파일별 SHA-256 계산.
- [ ] 파일 수, 크기, JSON 필드, 누락·중복·판결 유형 분포를 재현 가능한 스크립트로 산출.
- [ ] 비공개 manifest와 공개 가능한 `quality_baseline`을 분리.
- [ ] 공유 가능한 파일은 ChatGPT에서 분석할 수 있도록 사용자가 첨부하고, 확인된 제안·요약은 Orven으로 보냄.

**Gate:** 원본의 규모·구조·결측이 실제 데이터와 동일한 코드로 재생성되고 민감 원문은 외부로 보내지지 않음.

### P2. 심급 연결과 공동피고인 정렬

- [ ] 원심/항소심 사건번호·법원·죄명으로 **연결 후보** 생성, 중복·복수 후보 탐지.
- [ ] 공동피고인 인적 대응과 각 주문의 선고형을 독립 검증; 모호하면 `unreviewed`.
- [ ] `case_pairs`, `defendants`, `judgments` 단위와 분모를 구별.
- [ ] 기존 수치 `2,700 / 187 / 94 / 43`의 재현 결과와 차이 설명을 로컬 보고서에 기록.

**Gate:** 사람 검증된 피고인 대응만 실제 형량 비교의 확정 결과로 사용.

### P3. 항소이유·판단·근거 추출

- [ ] `appeal_ground`, `origin`, `disposition`, `reasoning_change` 추출 후보와 codebook 작성.
- [ ] `source_basis`(원문·추출·맥락)와 `verification_status`(미검증·검증)를 분리.
- [ ] 각 관계에 문서 ID, 섹션, 텍스트 오프셋, 문서 해시를 부여.
- [ ] LLM 출력을 법률적 사실이나 인과 판단으로 자동 승격하지 않음.
- [ ] 독립 주석자 검토/불일치 해결·판단 불가 기준을 기록.

**Gate:** 검증된 시각화 경로마다 원문 근거로 돌아갈 수 있음.

### P4. 과거 법령 연결

- [ ] 판결문의 **법령의 적용**에 명시된 조문을 우선 추출.
- [ ] 범행 시점·판결 시점·경과 규정·실제 적용 판단을 구별하여 정확한 법령 판본 확인.
- [ ] 역사적 법령 조회 응답의 형식·파서를 실제 API 응답으로 검증.
- [ ] 법령 ID, 판본, 조회시각, 조문 해시를 로컬에 기록; 단순 언급을 `applied`로 바꾸지 않음.

**Gate:** 조문 출처를 추적할 수 있으며 확인 불가 항목은 `uncertain`으로 남음.

### P5. 연구 분석·재현 ZIP 생성

- [ ] 정의된 분모로 감형/증형, 집행유예 변화, 직권판단 관계 등 탐색 분석.
- [ ] 데이터 품질 보고서에 결측·오연결·표본 편향·검증 커버리지 포함.
- [ ] User Study용 `gold_cases`를 별도로 버전화하고 법률 정답과 검증 불가 항목을 구분.
- [ ] 공개 허용된 데이터만 `public/data/`로 내보냄.
- [ ] 분석 ZIP은 **로컬 산출물**로 생성; 크기가 크거나 재배포 금지 자료라면 Orven으로 옮기지 않고 manifest/요약만 전달.

**Gate:** 코드·출처 버전·해시로 표와 그림을 재생성할 수 있음.

## 5.1. ChatGPT 파일 업로드 및 MCP 전송 제약

### ChatGPT 파일 업로드 제한

OpenAI 공식 문서 기준(2026-11-13):

| 파일 유형 | 최대 용량 및 제한 |
|---|---|
| 일반 파일 및 ZIP | 파일당 최대 512MB |
| 텍스트·문서(JSON, MD, PDF 등) | 파일당 최대 512MB 및 200만 토큰 |
| CSV·Excel | 파일당 약 50MB (행 구조에 따라 변동) |
| 이미지 | 파일당 20MB |
| 업로드 횟수 | 최대 80개/3시간 (서비스 상황에 따라 축소 가능) |

ZIP은 데이터 분석 도구가 제공되는 환경에서 내부 파일을 처리할 수 있지만, 압축 해제 후 크기, 파일 수, 메모리 사용량에 따라 분석이 실패하거나 중단될 수 있다.

**512MB는 업로드 상한이지 실제 분석 가능한 데이터 크기를 보장하는 수치가 아니다.**

### SentenScope 데이터 전달 정책

- **소규모 산출물:** Markdown, JSON, CSV 형태로 ChatGPT에 직접 첨부.
- **중간 규모 산출물:** ZIP으로 묶되 압축 해제 후 용량과 파일 수를 검사.
- **대용량 데이터셋:** 로컬에서 전처리·집계하고 필요한 파생 결과만 전달.
- **원본 판결문:** 라이선스·이용 조건상 허용되지 않는 경우 외부 채팅 및 MCP로 전송하지 않음.
- **User Study 원자료:** 승인된 연구계획과 동의 범위에 따라 비식별·집계한 결과만 전달.

운영상 권장하는 ChatGPT 전달 단위는 **파일당 10~30MB 이하**로 설정한다. 이는 공식 한도가 아니라 처리 실패와 재전송 비용을 줄이기 위한 프로젝트 자체 기준이다.

AI-Hub에서 제공되는 500MB 이상의 데이터셋은 원본 전체를 업로드하지 않고, 로컬에서 분석 후 필요한 산출물로 분할한다.

### Orven MCP 전송 제한

**ChatGPT 파일 업로드 한도와 MCP 도구 호출 한도는 서로 다르다.**

Orven Cloud Handoff의 실제 요청 본문 크기, MCP 응답 크기, Cloudflare Worker 및 저장소별 제한은 별도 확인해야 한다. ChatGPT의 512MB 한도가 Orven에도 적용된다고 가정하지 않는다.

Orven을 통한 전달은 다음 원칙을 따른다.

1. Markdown 연구 문서, 요약 통계, 검증 결과, 파일 참조를 우선 전송한다.
2. 대용량 ZIP과 원본 데이터셋은 로컬 저장소에 유지하고, 필요시 해시·경로·메타데이터만 전달한다.
3. MCP 호출 전에 payload 크기와 목적지별 제한을 검사한다.
4. 전송 실패에 대비해 idempotency key, 콘텐츠 해시, 전달 상태를 기록한다.
5. 로컬 원본 데이터는 사용자 승인 없이 외부로 업로드하지 않는다.

**대용량 데이터 분석과 연구 문서의 양방향 전달을 분리하는 것이 기본 아키텍처 원칙이다.**

- 데이터 처리: 로컬 연구 환경
- 연구 분석 및 검토: ChatGPT
- 문서·결과 전달: Orven Handoff
- 원본 보관과 최종 저장 승인: 로컬 Orven Desktop

공식 참고: https://help.openai.com/en/articles/8555545-uploading-files-and-audio-to-chatgpt

## 6. Handoff로 교환할 산출물과 폴더

개발 소스 경계는 [ENGINEERING.md](ENGINEERING.md)를 우선한다. 이 문서는 Orven 전달물·개인 데이터·Git 추적 범위만 명시한다.

```text
SentenScope/
├── PAPER.md / DATA.md / VALIDATION.md / TASK.md / MCP_WORKFLOW.md
├── ENGINEERING.md / DECISIONS.md / RELATED_WORK.md
├── scripts/
│   ├── ingest/               # 로컬 원본 정규화
│   ├── align/                # 사건쌍·피고인 대응
│   ├── annotate/             # 추출 후보·수동 검증 자료
│   ├── statutes/             # 법령 API 연혁 수집
│   └── publish/              # 공개 가능 export
├── src/domain/ + src/data/   # 시각화·데이터 검증 코드
├── tests/                   # 스키마/알고리즘/브라우저 테스트
├── data/raw/                # PRIVATE · Git/Orven Cloud 제외
├── data/private/            # PRIVATE · Git/Orven Cloud 제외
├── data/processed/          # PRIVATE · 기본 Git/Cloud 제외
├── data/cache/              # PRIVATE · Git/Orven Cloud 제외
├── artifacts/validation/    # 로컬 산출물; 공개 검토 전 Git/Cloud 제외
└── public/data/             # 허가된 export만 포함
```

**작은 Handoff의 예시**

- `DATA.md`: 스키마 추정과 검증 계획을 `[PROPOSAL]`로 전달.
- `PAPER.md`: 기존 연구와의 차이, 주장 근거, 반례 및 한계를 전달.
- `TASK.md`: 검증된 연구 과업 체크리스트 업데이트.
- `DECISIONS.md`: 어떤 설계 결정을 왜 채택·보류했는지와 출처 전달.
- `artifacts/validation/quality_report.md`: 실제 산출물 중 **공개 가능한 요약만** 전달하고 저장 경로는 승인 대상인지 확인.

**로컬 분석 ZIP 예시** (`sentenscope-stage1-inventory.zip`, Orven 전송 대상 아님):

```text
manifest.json                 # 출처·해시·수집시각·코드 버전
raw_inventory.csv            # 익명 문서 식별자·크기·필드 상태 (원문 없음)
quality_report.md            # 결측·중복·파싱 오류·한계
schema_summary.json          # 검증된 필드/유형
errors.csv                   # 오류 코드와 익명 식별자
README.md                    # 생성·재현 방법, 공개 등급
```

**ZIP으로 묶었다고 원본 재배포 허가가 생기지는 않는다.** 압축파일의 공개 등급을 파일별로 확인한다.

## 7. 첫 종단간 시험과 완료 조건

### T0. 연구자료 전달 시험 — **실제 데이터 없이 먼저**

- [ ] Orven에 SentenScope 로컬 대상 등록; 목적지의 허용 범위 기록.
- [ ] Remote MCP가 ChatGPT에서 호출되는지 `list_handoff_targets`로 확인.
- [ ] 비민감 테스트 메모 1개를 `submit_handoff`로 보냄.
- [ ] Orven Desktop에서 경로/본문/해시 확인 → 승인 → 지정한 파일이 생성·수정되는지 확인.
- [ ] 거절, 만료(목표 1일), 중복 제출, 충돌, 잘못된 경로, 네트워크 끊김 시 원본이 훼손되지 않는지 확인.
- [ ] `get_handoff_status`와 실제 로컬 파일 상태가 일치하는지 검증.

**Gate:** `전달 → 수신 → 로컬 승인 → 저장`이 실제 작동하고 실패 시에도 안전하다. **이 단계에서 실제 데이터셋을 보내지 않는다.**

### T1. 역방향 왕복 시험

- [ ] 로컬에서 민감정보를 제거한 `quality_report.md` 샘플 생성.
- [ ] 사용자가 채팅에 직접 첨부 → ChatGPT가 해석·수정안 작성.
- [ ] 수정한 Markdown을 T0 경로로 다시 전달하고 변경 차이 확인.
- [ ] 장기적으로 역방향 Remote MCP가 필요할 때는 별도 보안 설계/승인 후 독립 테스트.

**Gate:** **로컬 → 채팅 → 승인된 로컬 파일**이 한번 왕복되고 각 버전·출처를 확인할 수 있음.

### T2. 실제 데이터 운영 착수

- [ ] 로컬에서 AI-Hub ZIP의 개수·구조를 조사.
- [ ] 제안서의 `2,700 / 187 / 94 / 43` 수치를 계산 규칙과 함께 재현.
- [ ] 공동피고인을 포함한 후보 5건을 원문 근거까지 검토.
- [ ] 검증된 사례의 실제 적용 법령만 역사적 판본 조회.
- [ ] 허용된 **집계·스키마 요약**을 채팅에 올려 품질 분석하고, 확정 문서를 Orven에 전달.

**Gate:** 검증 가능한 로컬 데이터 파이프라인과 분리된 Handoff 체계가 모두 작동한다.

## 8. 연구·보안상 금지 사항

- **Orven MCP가 AI-Hub 데이터셋을 다운로드하거나 ZIP 전체를 중계한다고 기술하지 않는다.**
- 허가되지 않은 판결문·개인정보·API 키·참가자 원자료를 ChatGPT, Orven Cloud, 공개 저장소로 옮기지 않는다.
- 승인 없이 로컬 파일을 덮어쓰거나 Handoff를 Git 커밋·코드 실행의 허가로 간주하지 않는다.
- 수집 완료, 검증 완료, 사람 연구 완료를 문서의 `[PLAN]`을 근거로 주장하지 않는다.
- 미검증 피고인 대응, LLM 판단, 법령의 단순 언급을 gold label 또는 법적 인과관계로 바꾸지 않는다.
- 과거 사건에 현행 법령을 기계적으로 소급하지 않는다.
- 공식 IRB 심의/면제 판단 및 참가자 동의·데이터 보호 요건을 우회하지 않는다.
- 현재 구현되지 않은 역방향 Remote MCP, 자동 동기화, 클라우드 측 셸/저장소 접근을 구현된 기능처럼 표현하지 않는다.

**운영 원칙 요약:** **데이터는 로컬에서 처리하고, ChatGPT에서는 분석·연구 결정을 돕고, Orven은 선택한 연구 결과만 사용자 승인 후 저장소로 전달한다.** 역방향 입력은 우선 사용자가 선별한 파일을 직접 첨부하며, 자동 왕복은 별도 구현·권한 검증 후 확장한다.
