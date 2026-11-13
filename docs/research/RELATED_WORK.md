# 선행연구 정독 목록 및 Design Rationale 연결

**근거 등급:** 아래 논문의 서지/초록·공식 원문 페이지는 2026-11-12 기준 확인했다. **이 문서는 논문 전체를 정독했다는 주장이 아니다.** 인용 문장은 실제 논문 본문에서 재확인 후 `PAPER.md`에 옮긴다. `읽기 전 메모`는 우리의 적용 제안이지 논문의 실험 결과가 아니다.

## A. 필수 InfoVis 방법론 — 먼저 정독

### [R1] Munzner (2009), *A Nested Model for Visualization Design and Validation*
- **출처:** IEEE TVCG 15(6), 921–928. DOI: https://doi.org/10.1109/TVCG.2009.111
- **공개 소개:** https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/
- **실제 주장:** 도메인 문제 → 데이터/태스크 추상화 → 시각적 인코딩·상호작용 → 알고리즘의 4중 계층; 상위 설계 오류가 하위 구현으로 전파.
- **적용:** DATA/TASK 오류부터 먼저 검증. 예쁜 그래프를 만든 다음 데이터 정의를 끼워 맞추지 않기.
- **정독 질문:** 4계층별 validity threat는 무엇이며 SentenScope의 위험과 어떻게 대응하는가?

### [R2] Brehmer & Munzner (2013), *A Multi-Level Typology of Abstract Visualization Tasks*
- **출처:** IEEE TVCG 19(12), 2376–2385. DOI: https://doi.org/10.1109/TVCG.2013.124
- **저자 페이지/프리프린트:** https://www.cs.ubc.ca/labs/imager/tr/2013/MultiLevelTaskTypology/
- **실제 주장:** WHY, HOW, WHAT을 구분하고 복합 탐색을 단위 작업의 시퀀스로 표현.
- **적용:** T1(Locate) → T2(Compare) → T3(Trace/Verify)의 Action + Target을 기술.
- **정독 질문:** ‘verify’가 abstract action으로 정확히 어떻게 표현되는가?

### [R3] Sedlmair, Meyer & Munzner (2012), *Design Study Methodology: Reflections from the Trenches and the Stacks*
- **출처:** IEEE TVCG 18(12), 2431–2440. DOI: https://doi.org/10.1109/TVCG.2012.213
- **공개 페이지:** https://www.visdesignlab.net/publications/2012_infovis_dsm/
- **실제 주장:** 실제 도메인 문제를 파악하고 시스템을 설계·평가하며 디자인 교훈을 도출하는 design study 과정.
- **적용:** 법률 전문가 실험을 하지 않은 과제 프로젝트라는 한계를 명시하고 시스템 기반 사례 연구에 집중.
- **정독 질문:** 단기간 독립 프로젝트에서 엄밀성을 확보하려면 어떤 design-study claim을 줄여야 할까?

## B. 시각 채널·범례 — 교수님 피드백의 직접 근거

### [R4] Cleveland & McGill (1984), *Graphical Perception: Theory, Experimentation, and Application to the Development of Graphical Methods*
- **출처:** JASA 79(387), 531–554. DOI: https://doi.org/10.1080/01621459.1984.10478080
- **실제 주장:** 그래픽의 정량 값 해석에 쓰이는 지각 작업의 정확성을 비교·검증.
- **적용:** V1의 징역 개월 수는 공동 척도의 위치로 표시; 색상 면적으로 양을 표시하지 않음.
- **주의:** 논문이 *현재 제안한 모든 dumbbell 표현을 직접 검증했다*고 쓰지 말 것.

### [R5] Harrower & Brewer (2003), *ColorBrewer.org: An Online Tool for Selecting Colour Schemes for Maps*
- **출처:** The Cartographic Journal 40(1), 27–37. DOI: https://doi.org/10.1179/000870403235002042
- **팔레트 도구:** https://colorbrewer2.org/
- **실제 주장:** 범주 수, 데이터 성격(순차·발산·정성), 사용 매체에 따라 색 체계 선택.
- **적용:** 결과 변화의 세 방향, 문서 섹션, 상태 범주를 하나의 무분별한 색 범주에 넣지 않음.

### [R6] Sterzik et al. (2023/2024), *Perception of Line Attributes for Visualization*
- **출처:** IEEE TVCG 30(1), 1041–1051. DOI: https://doi.org/10.1109/TVCG.2023.3326523
- **IEEE VIS 발표:** https://content.ieeevis.org/year/2023/paper_v-full-1655.html
- **실제 주장:** 선의 두께·점선·명도·파형 등 인지 가능한 속성을 실험으로 조사. 결과는 ‘모든 점선 패턴이 똑같이 구별된다’는 주장을 지지하지 않음.
- **적용:** V2 연결선에서 3개 이상의 비슷한 점선 패턴으로 법적 상태를 암기하게 하지 않기.

### [R7] Dykes, Wood & Slingsby (2010), *Rethinking Map Legends with Visualization*
- **출처:** IEEE TVCG 16(6), 890–899. DOI: https://doi.org/10.1109/TVCG.2010.191
- **저자 공개 페이지:** https://openaccess.city.ac.uk/id/eprint/178/
- **실제 주장:** 동적 시각화에서 범례의 배치·기호·선택·동적 속성 등을 재고할 필요.
- **적용:** 전역 범례 + 뷰별 보조 범례 + 선택 하이라이트의 설계 동기. (법률 차트에서의 효과는 따로 검증 필요)

### [R8] W3C WCAG 2.2, *Use of Color* + *Non-text Contrast*
- **공식:** https://www.w3.org/WAI/WCAG22/Understanding/use-of-color
- **공식:** https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast
- **실제 요구:** 색상만으로 정보 구분 금지. 이해에 필요한 그래픽 표시부와 주변색의 대비는 일반적으로 3:1 기준 적용.
- **적용:** 색상 + 레이블/도형, 다크/라이트·프로젝션 가독성 확인.
- **주의:** WCAG는 연구 논문이 아니라 접근성 표준/해설임.

## C. 법률 시각화 — 차별화와 과장 방지

### [R9] Vo & Plachkinova (2023), *ShowCase: A Data-Driven Dashboard for Federal Criminal Sentencing*
- **출처:** Journal of the Association for Information Systems 24(6). DOI: https://doi.org/10.17705/1jais.00796
- **기관 초록:** https://digitalcommons.kennesaw.edu/facpubs/7102/
- **차이:** 양형 관련 데이터 대시보드 vs. 한국 형사 **심급 간 판결 변경 경로와 원문 검증**.

### [R10] Onami et al. (2025), *LegalViz: Legal Text Visualization by Text To Diagram Generation*
- **출처:** NAACL 2025. DOI: https://doi.org/10.18653/v1/2025.naacl-long.339
- **원문/페이지:** https://aclanthology.org/2025.naacl-long.339/
- **차이:** 법률 텍스트→다이어그램 생성/평가 vs. 특정 피고인의 1심–항소심 관계 추적.

### [R11] Fürst et al. (2025), *Challenges and Opportunities for Visual Analytics in Jurisprudence*
- **출처:** Artificial Intelligence and Law. DOI: https://doi.org/10.1007/s10506-025-09494-2
- **실제 주장:** 법률 전문가 인터뷰(9명)를 통해 법률 분석/탐색·복잡한 reasoning·provenance의 시각적 지원 기회 제시.
- **적용:** V2↔V3의 provenance 기반 경로 검증 동기. 비전문가에게 동일한 효과가 검증된 것은 아님.

### [R12] Kim et al. (2026), *CaseSense: Mapping the Legal Case Landscape with Multi-Dimensional Visual Exploration*
- **출처:** UIST 2026. DOI: https://doi.org/10.1145/3830398.3830479
- **연구 페이지:** https://jhbale11.github.io/publications/casesense/
- **차이:** 여러 법률 사건의 다차원 공간 탐색 vs. 연결된 두 심급의 **판단 변화 경로**. AI 산출과 확인 가능한 원문을 분리한다는 문제의식은 일부 겹침.

## D. 읽고 기록할 템플릿

논문마다 아래 메모를 작성하고, 확인하지 않은 논문 내용은 `출처 확인 중`으로 표기한다.

```markdown
### [R#] 논문 제목
- 읽은 날짜/섹션:
- 문제 정의 (1문장):
- 데이터 / 분석 태스크:
- 구체적인 인코딩·상호작용:
- 평가 방법 / 표본 / 관측 결과:
- 한계:
- SentenScope에 직접 적용할 근거:
- 적용하면 안 되는 점 / 실험하지 않은 주장:
- 우리 디자인 결정 번호 (DECISIONS.md):
- 본문에서 인용할 정확한 절/그림/페이지:
```

## E. Design Rationale용 최소 참고문헌 세트

- 인코딩: R4, R5, R6, R8
- 범례: R7, R8
- 문제/태스크: R1, R2, R3
- 법률 도메인 기여: R9, R10, R11, R12

논문 이름만 나열하지 말고 **어떤 시각화 결정이 어떤 근거와 연결되는지** `VISUAL_DESIGN.md`에서 표로 관리한다.

## F. 2026-11-13 추가 조사와 인용 범위

[RESEARCH_REFERENCES.md](RESEARCH_REFERENCES.md)에 지각·의미 색상·Gestalt·상호작용·그래프 계산·ML 평가의 1차 자료와 확인 범위를 추가했다. [DESIGN_TUTOR.md](DESIGN_TUTOR.md)는 해당 사실을 설계 답안으로 바꾸지 않고 단계별 읽기 힌트로 연결한다. 기존 R1–R12 전체를 이번에 정독/재검증한 것은 아니다. R2의 `Locate`는 대상/위치의 사전 지식에 따라 구분되는 용어이므로 T1 전체와 자동으로 같다고 볼 수 없다. `Trace/Verify`는 현재 프로젝트 태스크 명칭이며 논문의 분류 항목을 그대로 인용한 것이 아니다.
