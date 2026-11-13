# PAPER — SentenScope 연구 계획 및 5쪽 최종 보고서 설계

> **2026-11-13 검토:** 구체적인 축·도형·색·뷰 배치·인터랙션은 기존 제안 후보이며 사용자 결정 전이다. 아래 선택 문구는 확정/승인 기록이 아니다. 선택 이유를 에이전트가 대신 결론내리지 않는다. [단계별 힌트](../research/DESIGN_TUTOR.md) · [근거와 확인 범위](../research/RESEARCH_REFERENCES.md) · [검토 기록](../records/REVIEW.md).

**상태:** working research plan [PROPOSAL + PLAN]. 결과나 기여의 효과는 아직 검증되지 않았다.
**Proposed title:** *SentenScope: Evidence-Linked Exploration of Reasoning Changes in Korean Criminal Appeals*
**Track:** VIS + X / problem-driven information visualization design study.

## 1. 한 문장 핵심 메시지

> 형량의 증감만 보여주는 대신, 비법률 전문가가 **항소이유·법원의 판단·직권판단을 구별하고 해당 판결문 원문으로 거슬러 올라갈 수 있게 하는** 연결형 시각화 시스템을 설계한다.

실형 60개월 → 42개월이라는 숫자만으로 판결의 법적 논거 변화를 알 수 없다. 특히 당사자 주장에 대한 `배척`이 곧 판결의 `유지`를 뜻하지 않을 수 있다. 법원 직권판단이 중요하게 작동하는 사례를 **본문으로 확인**해야 한다.

## 2. Research Question

**RQ (main):**

> How can an evidence-linked interactive visualization help non-experts distinguish appellate claims from court-initiated reasoning changes and verify those changes against original judgments?

**RQ1 / Find:** 피고인별 형량과 집행유예 상태의 변화를 정확하게 찾을 수 있는가?

**RQ2 / Trace:** 항소이유의 제기 주체, 인용·배척·미판단, 직권판단, 조문 적용을 별개의 개념으로 탐색할 수 있는가?

**RQ3 / Verify:** 시스템이 제시한 경로에서 양쪽 판결문의 해당 문장을 찾아 검증할 수 있는가?

이 질문은 **시스템이 형량 변동의 법적·통계적 원인을 자동 판정한다**는 주장이 아니다.

## 3. Motivation 및 Design Goal

1. **Outcome ≠ reasoning:** 결과 수치만으로 변경 이유를 해석할 수 없다.
2. **Multiple documents:** 1심과 항소심의 관련 문장을 사용자가 수작업으로 대조하기 어렵다.
3. **Provenance is essential:** LLM 요약은 판결문에 없는 연결을 생성할 수 있으므로 원문 추적이 필수다.
4. **Citizen-first, researcher-auditable:** 비전문가는 쉬운 용어와 좁은 경로를, 연구자는 정확한 표현과 근거를 필요로 한다.

**Goal:** 판결 변경에 관련된 *문서화된* 판단 경로를 **탐색·추적·검증**하되 형벌의 공정성을 평가하지 않는다.

## 4. Users / Personas [PROPOSAL, fictional]

### Primary — Minji Kim (김민지, 29, 서울)

- 직업: 회사원, 법률 전공이 아닌 일반 시민.
- 관심: 기사에서 본 감형 결과의 근거가 궁금하다.
- Goal: 형량 변화의 사실/법률/양형 쟁점을 구분하고 판결문 문장을 찾는다.
- Pain points: 법리오해·작량감경 등의 전문 용어, 연결되지 않은 2개 판결문, 추론과 원문 진술의 구별 어려움.

### Secondary — Jisoo Park (박지수, 34, 대전)

- 직업: 형사사법 연구자.
- Goal: 여러 사건/피고인의 변경 경로 비교, 직권판단 패턴 탐색, 추출 관계 감사를 수행한다.
- Pain points: 느린 비교, 조문 메타데이터 부족, AI 요약에서 근거 부족.

**공유 UI 전략:** 별도 전문가 모드 대신 progressive disclosure. 기본 화면에는 쉬운 요약, 선택하면 원문 표현·판결문 위치·검증 상태가 나타남.

## 5. Task abstraction (why / how / what)

| ID | Action + Target | Why? | Expected outcome | Views |
|---|---|---|---|---|
| T1 | **Locate +** 피고인별 징역/집행유예 변화 | 보도된 형량 변화의 대상 찾기 | 정렬된 1심·2심 선고와 미정렬 경고 확인 | V1 |
| T2 | **Compare +** 항소이유별 제기·판단·변화 | 인용/배척과 법원 직권의 차이 파악 | 항소이유별 결과/직권 판단 경로 확인 | V2 |
| T3 | **Trace +** 판단 경로 → 원문/조문 | 시각화의 관계가 원문에 근거하는지 검증 | 링크된 한국어 문장과 근거 상태 확인 | V2+V3 |

작업 순서: **Find a change → Trace reasoning → Verify source**.

## 6. Proposed contributions (실증 검증 전 가설)

- **C1. Defendant-level comparison:** 징역 기간 및 집행유예를 독립 채널로, 대법원 후속 결과는 절차 정보로 분리.
- **C2. Reasoning path exploration:** 제기 주체·판단 결과·판단 변화·직권판단을 혼동하지 않는 경로형 시각화.
- **C3. Source verification:** 시각적 관계 → 원문 문장 → 적용 법령을 되짚는 연결된 비교.

이 세 가지는 **설계상 의도된 기여**이며, 기존 연구 전체에 없는 완전한 최초 기능이라고 단정하지 않는다. 새로움은 `RELATED_WORK.md`에서 문헌별로 정밀 비교해야 한다.

## 7. Method / Research framing

1. [Domain] 원심–항소심 문서 탐색의 고충을 기술한다.
2. [Data] 사건 쌍, 피고인, 판결, 항소이유, 근거를 구조화하고 정확성/검증 상태를 기록한다.
3. [Task] T1–T3을 데이터 유형과 사용자 목표로 추상화한다.
4. [Design] V1–V3, 공통 범례, 채널 비용, 상호작용을 비교 설계한다.
5. [Implementation] D3 기반 단독 실행 웹앱을 구축한다. UI 런타임은 동일 기능 비교 후 사용자 판단으로 기록하며 현재 React scaffold는 임시다.
6. [Evaluation] 실데이터 Case Study의 사실 확인된 finding ≥3과 오해 가능성·데모 안정성 검증.
7. [Limitations] 추출 오류, 과거 법령 적용 시점, 데이터 대표성, 법률 인과 추정의 한계 공개.

**연구 방법의 위치:** Nested Model (Munzner 2009), Task Typology (Brehmer & Munzner 2013), Design Study Methodology (Sedlmair et al. 2012). 각 논문은 `RELATED_WORK.md`에서 별도 정리.

## 8. 보고서 골격 (총 5쪽 이내; 계획치)

| 섹션 | 목표 분량 | 포함할 증거 |
|---|---:|---|
| Abstract + 1. Introduction + Related Work | ~0.75쪽 | 동기·RQ·기존 연구 대비 포인트 |
| 2. Data & Task Abstraction | ~0.75쪽 | 데이터 계층, 규모, attributes, 페르소나, T1–T3 |
| 3. Visual Design & Interaction | ~1.50쪽 | 각 뷰 스크린샷, 인코딩 표, 범례, 디자인 대안/근거 |
| 4. Implementation & Case Study | ~1.25쪽 | 동작 아키텍처, 실제 findings ≥3, 근거 스크린샷 |
| 5. Limitations / Conclusion + references | ~0.75쪽 | 불확실성, 법적 한계, AI·외부 코드 공개 |

분량은 가변적이며 **References와 AI disclosure도 전체 5쪽 안에 들어가야 한다**고 가정하여 레이아웃을 잡는다. 최종 편집 시 과제 공지를 재확인한다.

## 9. Case Study 문장의 검증 수준

- **사용 가능:** “이 사건에서 1심 주문의 징역 5년과 항소심 주문의 3년 6월을 확인했다.” (두 주문 확인 후)
- **조건부:** “항소심은 원심의 법령 적용에 법리오해가 있다고 적었다.” (출처 문장/문서 확인 후)
- **금지:** “이 법률 조문 때문에 형량이 정확히 18개월 줄었다.” (판결문이 그런 정량 인과를 명시하지 않는 한)
- **금지:** “피고인의 주장이 모두 배척됐으므로 항소심은 감형하지 않았다.” (직권 판단 여부 확인 필요)

## 10. Limitations to disclose

- 2002–2011 형사 판결에 편중된 과거 데이터; 현대 전체 양형 관행을 대표하지 않음.
- 사건 번호만으로 공동피고인 개인을 정렬할 수 없음.
- LLM 추출이 만들어 낸 관계와 판결문에 명시된 관계는 분리되어야 함.
- 판결 당시 법령의 단순 시행 여부만으로 실제 적용 가능성을 확정할 수 없음(범행 시점·경과규정 등).
- 법률 자문/판결 예측/형량 공정성 판단 기능이 아님.
- 비전문가 페르소나는 가상이며 실제 사용자 효과는 평가 전까지 주장하지 않음.

## 11. 남은 연구 질문

- [ ] 최소 100 items의 **검증 가능한 분석 단위**는 무엇인가?
- [ ] ‘reasoning_change’ 분류의 신뢰도·판단 불일치를 어떻게 처리할 것인가?
- [ ] V2에서 `판단 결과`와 `판단의 변화`를 동시에 표현할 때의 오독은?
- [ ] 전역 범례를 사용자가 보지 않아도 기호를 이해하는가?
- [ ] 좁은 화면/프로젝터에서도 V3 원문을 충분히 읽을 수 있는가?
