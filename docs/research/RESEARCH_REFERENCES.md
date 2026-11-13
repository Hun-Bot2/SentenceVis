# 추가 조사: 확인 가능한 사실과 적용 범위

**조사일:** 2026-11-13. `[RESEARCH]`는 아래 원문에서 확인한 일반 사실이다. 이 프로젝트에서 어떤 표현을 선택할지는 사용자 판단이며, 참고문헌은 특정 설계의 정답표가 아니다. 웹 열람은 실데이터 검증·법적 적용 판단·사용자 효과 검증과 구별한다.

## F1. 문제·태스크를 먼저 구별하기

- **Munzner (2009), A Nested Model for Visualization Design and Validation.** [저자 페이지/초록](https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/) · [DOI](https://doi.org/10.1109/TVCG.2009.111). **확인 범위: 초록.** 도메인 문제, 데이터/태스크 추상화, 인코딩/상호작용, 알고리즘의 네 계층과 상위 오류의 전파를 설명한다. 특정 차트나 축을 지정하는 규칙은 아니다. 기존 R1.
- **Brehmer & Munzner (2013), A Multi-Level Typology of Abstract Visualization Tasks.** [저자 페이지](https://www.cs.ubc.ca/labs/imager/tr/2013/MultiLevelTaskTypology/) · [DOI](https://doi.org/10.1109/TVCG.2013.124). **확인 범위: 초록.** 목적(why), 수단(how), 입력/출력(what)을 구별하고 복합 태스크를 연결된 작은 태스크로 기술한다. 프로젝트의 T1–T3 명칭을 논문의 분류와 동일하다고 주장하지 않는다. 기존 R2.

## F2. 수량을 읽는 지각 과제

**Heer & Bostock (2010), Crowdsourcing Graphical Perception: Using Mechanical Turk to Assess Visualization Design.** [저자 기관 페이지](https://hci.stanford.edu/publications/paper.php?id=142) · [공개 원문](https://hci.stanford.edu/publications/2010/crowd-perception/heer-chi2010.pdf).

**확인 범위: 초록·서론.** 공간 인코딩과 명도 대비에 관한 선행 실험을 재현하고, 면적 판단·차트 크기·격자 간격을 조사했다. 지각 정확도는 실험 가능한 대상이다. 여기서 모든 상황의 채널 순위나 법률 dumbbell의 효과가 증명되는 것은 아니다. 기존 R4와 함께 읽되 과제·조건·평가 지표를 구별한다.

## F3. 색 체계와 의미 연상

- **ColorBrewer, Color scheme types.** [공식 설명](https://colorbrewer2.org/learnmore/schemes_full.html). **확인 범위: 설명 본문.** sequential은 순서 있는 값, diverging은 중요한 중간 기준, qualitative는 범주 구분을 위한 체계로 설명된다. 청색/주황 또는 빨강/초록이 이 프로젝트에 적합하다는 결론을 제공하지 않는다. 기존 R5 보충.
- **Lin, Fortuna, Kulkarni, Stone & Heer (2013), Selecting Semantically-Resonant Colors for Data Visualization.** Computer Graphics Forum / EuroVis. [저자 연구실 페이지](https://idl.uw.edu/papers/semantically-resonant-colors) · [공개 원문](https://idl.cs.washington.edu/files/2013-SemanticColor-EuroVis.pdf). **확인 범위: 초록·서론.** 데이터 개념과 연관되는 색의 자동 할당과 차트 읽기를 실험한다. 색의 의미 연상이 탐구 대상이라는 근거다. 모든 문화·사용자에게 동일한 연상이나 ‘감형=좋음’을 입증한 연구가 아니다. 상세 방법·효과 크기는 본문 정독 후 인용한다.

## F4. 그룹·연결·선

- **Wagemans et al. (2012), A Century of Gestalt Psychology in Visual Perception: I. Perceptual Grouping and Figure–Ground Organization.** [공개 원문](https://pmc.ncbi.nlm.nih.gov/articles/PMC3482144/) · [DOI](https://doi.org/10.1037/a0029333). **확인 범위: 초록·그룹화 관련 본문.** 근접성·유사성·연결 등 지각적 그룹화와 전경/배경 조직을 검토한 리뷰다. 특정 관계의 법적 타당성은 지각적으로 묶여 보이는 것과 별개다.
- **Sterzik et al., Perception of Line Attributes for Visualization.** [IEEE VIS 2023 공식 페이지](https://content.ieeevis.org/year/2023/paper_v-full-1655.html) · [DOI](https://doi.org/10.1109/TVCG.2023.3326523). **확인 범위: 공식 페이지의 그림 설명.** 선 패턴 선호를 조사하고 구별 가능성을 후속 실험으로 다룬다. 이 페이지는 ‘점선 세 종류 금지’라는 보편적 상한의 근거가 아니다. 기존 R6의 숫자 제한은 프로젝트 가설이다.

## F5. 상호작용과 정보 공개

- **Yi, Kang, Stasko & Jacko (2007), Toward a Deeper Understanding of the Role of Interaction in Information Visualization.** [공개 원문](https://users.cs.duke.edu/~rodger/jflappapers/Stasko2007.pdf) · [DOI](https://doi.org/10.1109/TVCG.2007.70515). **확인 범위: 초록·서론.** 사용자 의도 중심의 select, explore, reconfigure, encode, abstract/elaborate, filter, connect 일곱 범주를 제시한다. 버튼/클릭 수가 많다는 것 자체는 분석 가치의 증거가 아니다.
- **Shneiderman (1996), The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations.** [저자 공개 원문](https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf). **확인 범위: 초록·도입부.** overview, zoom/filter, details-on-demand를 설계 출발점으로 제시한다. 원문을 반드시 접어야 한다거나 모든 사용자가 한 순서로 탐색해야 한다는 결론으로 확대하지 않는다.

## F6. 접근성: 해석과 검출의 구별

**W3C, WCAG 2.2.** [규범 문서](https://www.w3.org/TR/WCAG22/) · [색상 SC 1.4.1 해설](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) · [텍스트 대비 SC 1.4.3 해설](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) · [비텍스트 대비 SC 1.4.11 해설](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).

**확인 범위: 해당 기준·대비/상대휘도 정의.** 의미 전달을 색에만 의존하지 않는다. 일반 텍스트 AA 대비는 4.5:1, 큰 텍스트는 3:1이며 예외와 큰 텍스트 정의를 함께 확인한다. 이해에 필요한 그래픽·UI 상태는 인접 색과 3:1 기준이 적용되며 예외가 있다. 모든 장식선에 일괄 적용되는 것은 아니다. Understanding 문서는 해설이고 규범 문서와 구별한다. 대비 충족은 사용자가 기호 의미를 이해한다는 증거가 아니다. 기존 R8 보충.

## F7. 좌표와 그래프 레이아웃

- **D3, Linear scales.** [공식 문서](https://d3js.org/d3-scale/linear). **확인 범위: linear mapping, domain/range, unknown.** 선형 스케일은 수치 domain을 range로 선형 변환한다. `null`·`undefined`·NaN 처리와 domain 설정을 확인할 수 있다. 선형변환 자체는 축 방향 선택의 근거가 아니다.
- **D3, Force simulations.** [공식 문서](https://d3js.org/d3-force/simulation). **확인 범위: 도입·tick·nodes.** velocity Verlet 수치 적분을 사용하며 노드 좌표·속도를 갱신한다. 시뮬레이션 좌표는 입력 데이터의 법적 의미를 자동으로 보장하지 않는다.
- **Graphviz, dot.** [공식 알고리즘 설명](https://www.graphviz.org/docs/layouts/dot/) · [개발자 기술 보고서: On-line Hierarchical Graph Drawing](https://graphviz.org/documentation/NW01.pdf). **확인 범위: dot 개요·보고서의 계층 배치 설명.** 계층형 방향 그래프 배치와 교차·길이 등의 목적을 다룬다. **수학적 비교 읽기 자료**이며 과제 핵심 렌더러로 Graphviz 도입을 승인한 것이 아니다. 최종 렌더링은 과제 제약을 따른다.

## F8. AI 출력과 평가

- **Guo, Pleiss, Sun & Weinberger (2017), On Calibration of Modern Neural Networks.** ICML, PMLR 70:1321–1330. [출판 원문 페이지](https://proceedings.mlr.press/v70/guo17a.html). **확인 범위: 초록.** 분류 모델의 확률과 실제 정답 빈도 사이의 calibration을 다룬다. 이 연구를 LLM 자기보고 점수의 정확성 보증이나 법적 진실 확률로 확장하지 않는다.
- **scikit-learn, Precision, recall and F-measures.** [공식 정의](https://scikit-learn.org/stable/modules/model_evaluation.html#precision-recall-f-measure-metrics). **확인 범위: 해당 지표 정의.** 정밀도·재현율·F1과 평균 방식은 평가 단위·라벨·분모에 의존한다. 추출 범위 일치나 관계 일치 기준은 프로젝트에서 따로 정의해야 한다.
- **Onami et al. (2025), LegalViz.** [ACL Anthology](https://aclanthology.org/2025.naacl-long.339/). **확인 범위: 초록·서지.** 법률 텍스트→다이어그램 데이터셋과 그래프 구조·텍스트 유사도·법률 내용 평가를 다룬다. 그래프 구조 점수와 법률 내용 평가는 구별된다. 한국 형사 항소심의 피고인 대응이나 비전문가 사용성을 검증한 자료로 대체할 수 없다. 기존 R10.

## F9. 데이터 출처와 미해결 항목

[AI-Hub 공식 페이지](https://aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=511&dataSetSn=71968)의 **변경이력·메타데이터·통계·스키마 표** 확인: 공개 소개는 v1.1(2026-06-30), 일반판결 15,000건과 심급 자료 6,000건, 총 21,000건을 기술한다. 제안서 수치와 단위/버전 대조가 필요하다. 심판유형 표의 건수와 비율이 불일치하고, 참조 필드 설명도 두 표에서 뒤바뀐다. `생성 방식 LLM` 표기만으로 전체 판결문이 합성이라고 단정할 수 없다. 로컬 문서·사용권은 미확인이다.

[국가법령정보 공동활용 가이드](https://open.law.go.kr/LSO/openApi/guideList.do)의 **API 목록** 확인: 법령 연혁 목록/본문 조회가 열거된다. 실제 호출·인증·응답 스키마·사건별 적용 판본은 확인하지 않았다.

## 확인 기록을 늘리는 방법

각 자료에 `날짜 / 읽은 절·페이지 / 확인한 주장 / 프로젝트에 아직 적용할 수 없는 부분 / 사용자 탐구 ID`를 덧붙인다. 초록만 읽었으면 정독으로 표시하지 않는다. 링크의 존재, 논문의 실험 결과, 우리 UI에서의 효과는 각각 별도의 확인이다.
