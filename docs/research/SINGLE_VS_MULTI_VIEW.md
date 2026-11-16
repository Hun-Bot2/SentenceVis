# 한 뷰에 모을 것인가, 여러 뷰로 나눌 것인가: 문헌 조사 (2026-11-16)

> 작성: Claude Code (웹 검색). AGENTS.md §7에 따라 결론은 내리지 않는다.
> **확인 범위:** 각 항목에 적었다. 전문을 읽지 않은 논문은 초록·색인·강의 슬라이드 요약 수준이다. "읽었다"고 쓰지 않는다.
> 연구 사실 [RESEARCH]과 프로젝트 적용 질문 [PLAN]을 나눠 적는다.

## 0. 과제 조건 [ASSIGNMENT]

`InfoVis_Term_Project_2026.pdf` p.(How: Vis Idiom Design)에는 "at least three visualization components"라고 적혀 있다. 로컬 PDF 텍스트를 추출해 확인했다. 따라서 "그림 하나"로 줄이더라도 그 안에서 **구분되는 컴포넌트 세 개**를 보고서에 설명할 수 있어야 한다. 합성 뷰 하나를 컴포넌트 3개로 인정할지는 교수자에게 확인해야 한다(미확인).

## 1. 합치는 방법을 분류한 문헌 [RESEARCH]

| 문헌 | 확인 범위 | 내용 |
|---|---|---|
| Javed & Elmqvist, *Exploring the Design Space of Composite Visualization*, PacificVis 2012. [dblp](https://dblp.org/rec/conf/apvis/JavedE12) | 초록, 인용 논문·강의 슬라이드 요약 | 여러 표현을 같은 공간에 결합하는 방식을 "composite visualization view"로 정리했다. 인용 문헌들이 드는 패턴 5개: juxtaposed(나란히), integrated(나란히 + 명시적 연결선), superimposed(겹쳐 그림), overloaded(한 뷰 안에 다른 뷰를 끼워 넣음), nested(마크 안에 뷰를 넣음). 원문 정의 문장은 직접 확인하지 못했다. |
| Gleicher et al., *Visual Comparison for Information Visualization*, Information Visualization 10(4), 2011. DOI 10.1177/1473871611416549 | 초록·2차 요약 | 비교 설계는 juxtaposition, superposition, explicit encoding 세 가지 기본 요소의 조합이다. 2차 요약에 따르면 juxtaposition은 기억에, superposition은 시각 체계에, explicit encoding은 계산에 의존한다. |
| Deng et al., *Revisiting the Design Patterns of Composite Visualizations*, arXiv 2203.10476 (2022). [arXiv](https://arxiv.org/abs/2203.10476) | 초록 | IEEE VIS 논문 속 합성 시각화를 분해해 패턴 8개를 도출했다. 초록에 나오는 이름은 repeated, stacked, accompanied, nested다. 각 패턴의 장단점을 논의한다. |
| Chen et al., *Composition and Configuration Patterns in Multiple-View Visualizations*, TVCG 27(2), 2021. [arXiv](https://arxiv.org/abs/2007.15407) | 초록 | VIS·EuroVis·PacificVis 논문(2011–2019)의 다중 뷰 그림 360장에서 뷰 종류의 조합과 배치 패턴을 셌다. |
| Munzner, *Visualization Analysis and Design* (2014) 12장. [슬라이드](https://www.cs.ubc.ca/~tmm/talks/minicourse14/vad16act.pdf) | 저자 강의 슬라이드 | 복잡도를 다루는 전략은 Manipulate, Facet, Reduce다. Facet은 Juxtapose, Partition, Superimpose로 나뉜다. 정의는 책 본문에서 확인해야 한다. |

## 2. 나눌지 합칠지에 대한 근거 [RESEARCH]

| 문헌 | 확인 범위 | 내용 |
|---|---|---|
| Wang Baldonado, Woodruff, Kuchinsky, *Guidelines for Using Multiple Views in Information Visualization*, AVI 2000. [PDF](https://courses.ischool.berkeley.edu/i247/f05/readings/Baldonado_MultipleViews_AVI00.pdf) | 강의 슬라이드 요약 | 지침 8개를 제시한다. 그중 *rule of parsimony*는 "뷰를 최소한으로 쓰라"이다(뷰마다 학습·화면·계산 비용이 들기 때문). *rule of decomposition*은 복잡한 자료를 의미 있는 덩어리로 나눠 보이라는 것이다. 두 규칙은 서로 반대 방향으로 작용한다. |
| Plumlee & Ware, *Zooming versus Multiple Window Interfaces*, ACM TOCHI 13(2), 2006. DOI 10.1145/1165734.1165736 | 초록 | 시각 작업기억의 용량이 핵심 요인이다. 비교할 패턴이 작업기억에 담을 수 있는 양보다 복잡하면 창을 여러 개 쓰는 편이 오류가 적었다. 한 화면에서 확대·축소로 오가는 방식은 오류가 훨씬 많았다. |
| Ellis & Dix, *A Taxonomy of Clutter Reduction for Information Visualisation*, TVCG 13(6), 2007. DOI 10.1109/TVCG.2007.70535 | 초록 | 화면이 과밀할 때 쓰는 혼잡 감소 기법을 각각의 이득과 손실로 분류했다. 한 뷰에 많이 겹쳐 그리면 이 비용이 생긴다. |
| 강의 09 *Novel Visualization Idioms* (슬라이드 확인) | 슬라이드 | 새 idiom은 기여 자체가 아니다. 정의된 태스크에서 측정된 이점이 있어야 한다. 예로 UpSet(색 절제), DenseLines·Splatterplots(극단적 규모), MosaicSets·TimeCurves(직교 축을 벗어남)를 든다. |

## 3. 법률 자료 시각화 사례 [RESEARCH]

| 문헌 | 확인 범위 | 구성 |
|---|---|---|
| Resck et al., *LegalVis: Exploring and Inferring Precedent Citations in Legal Documents*, TVCG 29(6), 2023. [arXiv](https://arxiv.org/abs/2203.02001), [VIS 페이지](https://content.ieeevis.org/year/2022/paper_v-tvcg-9716779.html) | 초록, VIS 소개 페이지 | 연결된 뷰 3개: 시간 개요, 문단 유사도 뷰, 관련 문단을 강조하는 문서 읽기 뷰. 평가는 사용 시나리오 2개와 전문가 6명의 피드백이다. |
| Chen et al., *JudgmentLens: Human-AI Sensemaking of Complex Legal Judgments*, arXiv 2609.07607 (2026, 동료 심사 전). [arXiv](https://arxiv.org/abs/2609.07607) | 초록 | 사건 표현, 설명, 생성된 해석에서 판결문 문단으로 가는 추적 링크를 둔다. 화면 배치는 초록에 없다. 비전문가 16명 대상 피험자 내 비교에서 PDF 읽기보다 빠르고 부담이 적었다. 채점된 이해도에는 신뢰할 만한 차이가 없었다. |

두 사례 모두 "개요 뷰 + 원문 뷰를 연결하는" 구성이다. SentenScope의 V1/V3와 구조가 비슷하다. 한 뷰로 모든 것을 합친 법률 시각화 논문은 이번 검색에서 찾지 못했다(없다는 증거는 아님).

## 4. SentenScope에 대입할 때 생기는 질문 [PLAN · 사용자 기록용]

Javed & Elmqvist의 패턴 이름으로 지금 구조를 바꾸어 보면 다음과 같다(Claude의 대응 해석이며 검증되지 않음).

| 패턴 | SentenScope에서 가능한 형태 | 걸리는 점 |
|---|---|---|
| juxtaposed (현재) | V1·V2·V3를 나란히 두고 선택으로 연결 | 뷰 사이를 오가는 기억 부담. 화면 분할 |
| integrated | 위와 같되 V1 행 → V2 노드 → V3 문장을 실제 선으로 이음 | 선이 패널 경계를 넘어가 혼잡해짐 |
| superimposed | V1 축 위에 V2 정보(이유·처리)를 겹쳐 그림 | 이미 도형 9종 + 쐐기 + 집행유예 글자가 있음 (Ellis & Dix 혼잡 비용) |
| overloaded / nested | 고른 V1 행만 펼쳐 그 행 안에 V2 경로·원문 단서를 넣음(focus+context) | 다른 행이 밀려남. "컴포넌트 3개"로 설명할 수 있는지 미확인 |

고를 때 사용자가 확인할 것:

1. 페르소나의 핵심 태스크(T1–T3)는 *한 사건을 깊게* 보는 것인가, *사건 사이를 비교*하는 것인가? Plumlee & Ware의 결과는 비교할 대상이 복잡할수록 창을 나누는 쪽에 유리하다는 것이다.
2. 지금 화면에서 실제로 불편한 점은 무엇인가? 시선 이동인가, 정보 과밀인가, 연결이 안 보이는 것인가?
3. 과제의 "세 컴포넌트" 조건을 어떻게 설명할 것인가?
