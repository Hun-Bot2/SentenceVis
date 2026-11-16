# 양형기준 대체 공개 자료: 확보 및 한계

2026-11-15 조사. 원문 기준과 실증 연구·통계 자료를 구분한다. 원본은 Git 제외된 `data/raw/sentencing_history/alternatives/`에 있으며 각 URL, 바이트 수, SHA-256, 저장 시각과 분류는 같은 폴더의 `manifest.json`을 따른다. PDF 시그니처 확인은 문서 내용의 법률 검증을 뜻하지 않는다.

| 자료 | 분류 | 확보 상태 |
|---|---|---|
| [2011 양형기준 국회도서관 소장정보](https://dl.nanet.go.kr/detail/MONO1201113794) | catalog_only | 원문 미확보. 2011.7.1 기준, 352쪽 및 15개 범죄군의 서지·목차 확인; 원문보기 표시가 열람·다운로드 권한을 보장하지 않음 |
| [사법정책연구원 살인 연구](https://jpri.scourt.go.kr/post/postView.do?boardSeq=7&lang=ko&menuSeq=11&seq=1839) | empirical_study | 본문·요약 PDF 각 1건 저장. 1998–2023년 1·2심 연구; 프로젝트 사건 정답셋 아님 |
| [2010 춘계 형사정책세미나](https://www.kicj.re.kr/boardDownload.es?bid=0007&list_no=11810&seq=1) | contextual_statistics | PDF 저장; 관련 수치와 범위의 원문 대조는 미완료 |
| [2010 양형합리화정책 평가](https://kicj.re.kr/boardDownload.es?bid=0029&list_no=12543&seq=1) | empirical_study | PDF 저장; 원문 내용 검증 미완료 |
| [2015 양형기준 운영 평가](https://www.kicj.re.kr/board.es?act=view&bid=0001&list_no=10316&mid=a10101000000&tag=) | empirical_study | 사용자 제공 ZIP에 461쪽 PDF 존재; 공식 서버 파일과 바이트 일치 미확인 |
| [2009 연간보고서 부록](https://sc.scourt.go.kr/sc/krsc/board/BoardViewAction.work?gubun=1&searchOption=&searchWord=&seqnum=203) | original_guideline 후보 | 게시물은 성범죄 수정 기준을 포함한다고 설명. 파일은 미확보·원문 확인 미완료 |
| [2010 연간보고서 일부](https://sc.scourt.go.kr/sc/krsc/board/BoardViewAction.work?gubun=1&searchOption=&searchWord=&seqnum=308) | contextual_statistics 후보 | 게시물 확인, 파일 미확보 |

2002–2008은 양형위원회 공식 기준 시행 전 기간으로 구별하며 후대 기준을 소급해 사건을 평가하지 않는다. 2009년 이후에도 특정 사건 적용 여부는 공소제기 시점과 경과규정 및 판결문을 별도로 확인한다. 이 문서는 2002–2011 항소심 판결을 다루는 V1–V3의 범위나 데이터와 별개다. 2009–2011 전체 기준의 완전성·누락률은 미확인이다.

국회도서관 원문 열람/저장 권한과 양형위원회 자료 수집에 대한 운영자 허용 및 에이전트 실행 승인은 각각 미확인 또는 기존 거절 상태다. 자동 수집을 재개하지 않았다. AI 사용: OpenAI Codex가 출처 조사·기록과 다운로드 검증에 참여했다.

## 2026-11-16 사용자 제공 자료 대조

이 작업공간에서는 위 2025년 JPRI 본문·요약을 포함한 PDF 4건이 이전에 실제 저장되어 있다. 전달된 다른 환경의 DNS 실패 기록과 모순되지 않는다. 이번에는 인터넷 PDF 다운로드를 재시도하지 않았다.

- 정숙희(2019), 일반양형인자 연구: `data/KCI_FI002450803.pdf`와 `data/SenteseVis_research_verified_2026-11-16.zip` 내 `article_2019_jung_general_factors.pdf`는 동일 SHA-256 `671576ee46bdaa5080fbd16941d2b91e7649ede70077569d876329cbec9f6910`, 36쪽, PDF 서명 및 첫 페이지 제목을 확인했다.
- 박성훈·최이문(2016), 성범죄와 강도범죄 연구: `data/`의 원본 PDF와 위 ZIP 내 `article_2016_park_choi_before_after.pdf`는 동일 SHA-256 `79744b6ab19053c71a5f040c388b39ead4e5671667918eb7ef806ac5e618836f`, 34쪽, PDF 서명 및 첫 페이지 제목을 확인했다. 중복 복사하지 않았다.
- **2015년 KICJ 평가연구(IX): 위 표의 '첨부 파일 미확보'를 정정한다.** 사용자 제공 `data/`의 해당 제목 ZIP 안에 `형사정책과 사법제도에 관한 평가 연구_189p 수정.pdf`가 있다. PDF 461쪽, 16,955,831바이트, SHA-256 `bfc7dd437e67af897f15741b289c0e061f861b9db454372632fcb353a4e4470c`. 발간사·목차의 양형기준제 평가 및 양형기준 수립 연혁 내용을 확인했다. ZIP의 제목과 본문 맥락은 해당 보고서와 부합하지만, 공식 서버 파일과의 바이트 일치·책 전체 내용 검증은 미확인이다. 원본 ZIP 내부에 유지했으며 추출 복사하지 않았다.

두 논문의 표본 수와 결과는 사용자 전달 사항이며, 이번 작업에서는 해당 본문 표를 독립 대조하지 않았다. 연구 원문 확보와 사건 단위 원시자료 공개 및 개별 판결의 법적 판단 검증은 서로 다른 상태다. 다른 후보 논문과 2007년 화이트칼라 보고서의 원문은 미확보다.
