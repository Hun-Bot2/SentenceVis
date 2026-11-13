# 과제 명세: Information Visualization Term Project 2026

> **상태: 원본 대조 완료 [ASSIGNMENT; 2026-11-13]**
> 근거: 성균관대학교 정보시각화 기말 과제 PDF `InfoVis_Term_Project_2026.pdf` (2026-10-04, 총 5쪽). 2026-11-13 검토 중 루트에 추가된 `InfoVis_Term_Project_2026.pdf` (로컬 참고 원본; Git 제외) 5쪽 전체를 텍스트 추출해 아래 조건을 대조했다. 이후 수업 공지는 별도 확인 전이다. 사용자가 전달한 교수님 *구두 피드백*과 별도 제안은 구분하여 표시한다.

## 1. 필수 기술·평가 기준

- **개인 프로젝트**: 독립 실행 가능한 **Web 인터랙티브 시각화 앱**.
- 시각화 라이브러리: **D3.js 또는 Vega/Vega-Lite**만 허용. Chart.js, Tableau, Matplotlib 등 기타 시각화 시스템 불허. React 등은 시각화 외 목적에 사용 가능. (p.1, p.3)
- **VIS + X (Application Study)** 선택. 해당 영역의 특수한 데이터를 사용하며 **범용·널리 공개된 데이터셋(공공데이터포털, Kaggle, UCI 등)은 사용하지 말라는 조건**이 있다. AI-Hub 선택의 해당 여부는 데이터/태스크의 특수성과 교수자 판단을 별도로 확인한다. (p.1)
- 평가 관점: **Effectiveness, Novelty, Usability**. 국제 시각화 학회 논문 제출 수준의 논리와 디자인 근거를 요구하지만 실제 학회에 제출해야 한다는 뜻은 아님. (p.1)
- 기존 도구(Tableau/Excel)로 쉽게 재현 가능한 범용 대시보드에는 높은 페널티 가능. (p.4)

## 2. 평가 항목 및 명시적 최소 조건

| 항목 | 점수 | 필수 사항 | 해당 문서 |
|---|---:|---|---|
| What: Data Abstraction | 2 | **100 items 이상, 6 attributes 이상**, dataset/data type, 속성 key/value 구분, nominal/ordinal 수준·의미·순서 방향, quantitative interval/ratio·범위 | DATA.md |
| Who: Personas | 2 | **2명**(Primary, Secondary), 가상 이름+사진, 직업/나이/장소, 목표·니즈·고충·차이 | PAPER.md |
| Why: Task Abstraction | 2 | **최소 3개 task**, action + target, 수행 이유, 기대 결과 | PAPER.md |
| How: Vis Idiom Design | 3 | **최소 3개 인터랙티브 시각화 컴포넌트**, idiom 선택 근거·속성 유형·확장성·상호작용 | VISUAL_DESIGN.md |
| Sketch | 2 | 인터페이스 스케치; fidelity보다 상호작용의 구체성이 중요 | VISUAL_DESIGN.md |
| Implementation | 20 | **웹 구현**, D3 또는 Vega 계열만 사용, 외부 코드/AI 기여 공개, 라이브 데모 준비 | ENGINEERING.md |
| Case Study | 3 | Primary Persona가 T1–T3을 탐색하는 **실제 findings 3개 이상 + 스크린샷** | EVALUATION.md |
| Final Presentation | 5 | **10분 발표 및 라이브 데모**, 발표 언어 한/영 자유, 슬라이드 있으면 영어 | PRESENTATION.md |

총점: **39점** (각 섹션의 2+2+2+3+2+20+3+5).

## 3. 마감 및 제출물

- **Proposal:** 2026-10-28 23:55 KST. English `slides.pdf` (최대 7페이지). 제안 발표 10/29, 발표 5분. *(이미 지난 단계)*
- **Implementation 제출:** **2026-12-02 23:55 KST**, iCampus에 단일 ZIP 제출, 늦으면 0점.
- **Final presentation:** **2026-12-03**, 발표 **10분**, 라이브 데모 포함.
- **최종 ZIP 루트에 반드시:**
  - `report.pdf` — 최대 **5쪽**, 한/영 자유. 시스템 이름·테마·라이브 데모 링크·스크린샷·AI 사용 공개 포함.
  - `src/` — 소스 코드.
  - `image.png` — 인터페이스 이미지.
- 슬라이드를 따로 만들면 **영어**로 작성한다.

## 4. 교수님의 개별 피드백 [USER-REPORTED]

> 주제·데이터셋·뷰 디자인은 흥미롭다. 아이콘/도형·색상·텍스처를 잘 선택하고 채널이 많으면 적절히 제한할 것. **선택 이유를 보고서에서 문헌 근거로 설명**할 것. **전체 인코딩의 범례를 화면 어딘가에 표시**할 것. InfoVis 논문 형태와 동작하는 사이트를 통한 발표를 기대.

위 피드백은 과제 PDF의 공식 조문이 아니라 사용자 전달의 추가 요구다. 다음을 **프로젝트 수용 기준**으로 반영한다:

- `VISUAL_DESIGN.md`에 각 시각적 채널의 attribute, cardinality, 태스크, 근거 논문, 인지적 비용을 기록.
- V1–V3 공통 의미의 **전역 범례** + 필요 시 뷰별 보조 범례를 제공.
- 텍스처/도형/색의 중복과 과밀도를 제한하고, 기본 화면과 세부 화면으로 정보량을 분리.
- 최종 보고서의 Design Rationale에 대안과 선택 이유를 명시.

## 5. 제출 전 수용 체크리스트

- [ ] 데이터 아이템 수 ≥ 100 (무슨 단위인지 명시: 사건 쌍/피고인/판결/근거)
- [ ] 속성 수 ≥ 6, keys/values 및 nominal/ordinal/quantitative 구분
- [ ] 페르소나 2명(가상 이미지 포함), 니즈·차이
- [ ] T1–T3 action + target, why, expected outcome
- [ ] 세 시각화 뷰 모두 **실제 데이터·클릭·연동** 작동
- [ ] 모든 도형/색/선 의미를 전역 또는 문맥 범례에서 해석 가능
- [ ] 디자인 근거를 학술문헌과 속성 유형으로 논증
- [ ] 데이터 검증 여부와 한계 명시, 오인 가능한 인과 표현 제거
- [ ] Primary Persona 중심의 실제 finding 3개 + 스크린샷
- [ ] AI/외부 코드 출처를 **보고서와 코드에 공개**
- [ ] report.pdf ≤ 5쪽, 실행/배포 가능한 `src/`, `image.png`
- [ ] 라이브 데모와 별도 로컬 실행 경로 확인
- [ ] ZIP 루트 구조 확인 후 마감 전에 제출

## 6. 추가 확인이 필요한 사항

- 실제 최종 제출 `src/`의 범위(빌드 결과 포함 여부), 라이브 데모 URL 제출 방식은 추후 수업 공지에 따라 업데이트.
- 공식 PDF는 **대규모 정량 사용자 실험을 요구하지 않음**. 파일럿 사용자 평가가 있으면 유익하나 필수 항목과 구분.

원문 우선순위: 과제 PDF > 이후 교수자/수업 공지 > 본 저장소의 추론·계획.
