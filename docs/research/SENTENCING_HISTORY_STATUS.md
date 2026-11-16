# 양형기준 연혁 조사 상태

2026-11-15 조사. 공식 웹 검색 및 페이지 열람에 근거한 예비 조사이며 수집 완료 보고서가 아니다.

- [양형위원회 소개](https://sc.scourt.go.kr/sc/krsc/intro/greet/purpose.jsp)는 2009년 최초 시행 범죄군으로 살인, 뇌물, 성범죄, 강도, 횡령·배임, 위증, 무고를 설명한다. 정확한 각 판본의 의결일과 시행일은 원문별 확인이 필요하다.
- [2011년 성범죄 2차 수정 기준](https://sc.scourt.go.kr/sc/krsc/criterion/past/sex_2011/sex_2011_01.jsp)은 과거 기준을 HTML로 제공하는 실제 사례다. 전체 범죄군과 판본의 보존 여부는 미확인이다.
- [양형기준 적용 설명](https://sc.scourt.go.kr/sc/krsc/criterion/explan/introduction/introduction_02.jsp)은 시행 후 공소제기 여부 등 적용 조건을 설명한다. 판결 선고 연도만으로 특정 기준의 실제 적용을 판정하지 않는다.
- 최초 시행 전인 2002–2008년은 별도 기간이다. 판결 데이터의 기존 2002–2011년 범위를 바꾸지 않는다. V4 연혁은 V1–V3 판결 데이터와 별도다.
- robots.txt는 조사 도구에서 열리지 않았고, 로컬 `curl -I --max-time 15 https://sc.scourt.go.kr/robots.txt`는 DNS 조회 실패였다. 공식 저작권보호정책 확인, 자동 수집 허용 범위 미확인이다. 따라서 자동 요청 허용 여부, 원본 확보, 문서 해시, 전체성과 결측률은 미확인이다.
- 실제 판본별 유형 정의와 범위·양형인자 대조 전에는 버전 간 직접 비교 가능성을 `unverified`로 유지한다. PDF 필요 여부도 판본별 HTML 조사 후 판단한다.

## 남은 작업

robots.txt와 이용 조건을 공식 사이트에서 확인한 뒤 허용 범위 내에서 속도 제한·재시도 제한을 적용해 원본을 보존한다. 2009–2011 판본을 먼저 수집하고 이후 2026년까지 확장한다. 출처 URL, 수집 시각, 원본 SHA-256, 파싱 오류, 날짜별 의미, 검증 상태 및 비교 가능성 근거를 기록한다. 수집기, 파서, 테스트와 실제 수집 결과 기반 품질 보고서는 아직 작성되지 않았다. 원문 및 파생물의 공개·재배포 권한도 별도 확인한다.

AI 사용: 이 예비 조사는 OpenAI Codex의 웹 검색과 문서 작성을 사용했다. 공식 원문을 사람이 검증한 결과가 아니다.

## 수집기 초안 (2026-11-15)

`scripts/sentencing/collect.py`는 공식 호스트만 허용하고 robots.txt가 유효하지 않으면 중단한다. 이용 조건 URL과 사람이 검토했다는 명시적 입력이 필요하다. 요청은 최소 3초 간격, 일시적 오류에 최대 1회 재시도하며 401/403/429에서는 중단한다. 리다이렉트와 PDF는 자동으로 따라가지 않는다. HTML 원본은 SHA-256 이름으로 `data/raw/sentencing_history/`, 문서 목록·원시 표·오류·품질 요약은 `data/processed/sentencing_history/`에 보관한다. 양쪽 모두 Git 제외다.

이 초안은 판본 목록의 완전한 탐색이나 병합 셀 복원, 범죄군·시행일·권고 범위·양형인자의 의미 정규화를 구현하지 않았다. 특히 표의 행과 열은 원문 구조와 다를 수 있으므로 분석에 사용하기 전 원문 대조가 필수다. 법적 검증과 버전 비교 가능성은 `unverified`/`unknown`이다. 판결 데이터와 연결하지 않는다. 수집된 실제 데이터는 없다. 로컬 실행 시 DNS 오류로 robots 확인에 실패했다. `python3 -m unittest discover -s tests/data -p 'test_sentencing_collector.py'` 기초 테스트 3개가 통과했다.

공식 이용 조건을 독립적으로 확인한 뒤 실행 예시 (`TERMS_URL`은 실제 공식 정책 주소로 교체):

```sh
python3 scripts/sentencing/collect.py --terms-url "$TERMS_URL" --terms-reviewed --max-pages 100
```

기본 시작점은 2011년 성범죄 기준 1개이므로 2009–2011 전체 수집을 보장하지 않는다. 사이트별 robots 접근이 가능하고 이용 조건이 확인되기 전에는 실행하지 않는다.

## 접근 재확인

공식 `https://sc.scourt.go.kr/robots.txt`를 승인된 네트워크 실행으로 2026-11-15에 조회했고 HTTP 200과 `User-agent: *`, `Disallow: /criterion/` 등을 확인했다. 조회한 원문 후보의 경로는 `/sc/krsc/criterion/past/...`이다. 그 HTML 요청은 자동 승인 심사가 `/criterion/` 제한 위반 위험을 이유로 거절했다. 이 거절을 우회하지 않았으며 실제 원문 수집은 수행하지 않았다. robots 경로 해석과 별도로 공식 저작권보호정책은 확인했으나 자동 수집 허용 범위는 미확인이다. 위의 DNS 실패는 샌드박스 내 직접 요청에 대한 결과다.

수집기 정책 검사는 이용 조건 URL 자체에도 robots 규칙을 적용하도록 보강했다. 자동 심사 거절 상태에서는 실행 예시가 수집 허가를 의미하지 않는다.

## 차단 판단 교정 (2026-11-15)

앞서 `/criterion/`이 `/sc/krsc/criterion/past/...`를 차단한다는 자동 승인 심사의 사유를 충분히 검증하지 않고 전달한 것은 잘못이었다. [RFC 9309 §2.2](https://www.rfc-editor.org/rfc/rfc9309)에 따라 경로 시작부터 비교하면 두 경로는 일치하지 않는다. 재조회한 robots 전문의 그룹은 `AhrefsBot: Disallow /`, `SemrushBot: Disallow /`, 그리고 `*: Disallow /Backup/`, `/ICSFiles/`, `/_minwon/`, `/accessibility/`, `/app/`, `/comm/`, `/common/`, `/criterion/`, `/css/`, `/depo/`, `/doc/`, `/editer/`, `/english/`, `/hdc/`, `/image/`, `/images/`, `/img/`, `/inc/`, `/info/`, `/infor/`, `/information/`, `/ka/`, `/main/`, `/move/`, `/movie_suit/`, `/news/`, `/notice/`, `/npopup/`, `/part_in/`, `/pda/`, `/pdainfo/`, `/public/`, `/regi/`, `/ri/`, `/ri_e/`, `/rss/`, `/scourt_en/`, `/script/`, `/search/`, `/sitemap/`, `/style/`, `/suit/`, `/tel/`, `/today/`, `/welfare/`다. Allow 행은 없으며 해당 수집기 토큰에는 `*` 그룹이 적용된다. 최초 요청 경로에 일치하는 Disallow는 없다. 이는 접근 권한이나 이용 조건의 확인이 아니다.

기존 수집기는 부분 문자열 검색이 아니라 Python `urllib.robotparser`를 사용했으나 오래된 버전은 최장 일치 처리가 다를 수 있다. RFC 우선순위 자기검사에 실패하면 중단하도록 변경했다. 동일 길이 Allow 우선, 더 긴 규칙, 실제 경로와 `/criterion/` 경로 및 사용자 에이전트별 테스트를 추가했다. 실제 수집기에는 `NoRedirect`가 있어 리다이렉트를 따라가지 않는다. 원문 요청이 승인 전 거절되어 실제 HTTP 응답과 Location은 확인되지 않았다. 향후 리다이렉트를 지원하려면 각 hop의 호스트와 robots를 별도 확인해야 한다.

- robots: 위 최초 URL은 확인한 정책에 불일치하는 금지 규칙이 없다.
- 공식 저작권보호정책 확인, 자동 수집 허용 범위 미확인. robots 결과만으로 허용 여부를 확정할 수 없다.
- 네트워크: 샌드박스 안의 직접 DNS 요청은 실패했으나 승인된 robots 조회는 HTTP 200이었다.
- 에이전트 승인: 원문 요청은 자동 심사가 `/criterion/`에 명시적으로 금지됐다는 사유로 거절했다. 이 사유의 경로 매칭은 위와 같이 잘못됐으나, 승인 제한 자체는 유효하며 우회하지 않는다.

**수동 수집 절차:** 사이트 이용 조건과 제공 범위를 확인한 사람이 브라우저에서 공식 원문을 직접 저장한 뒤 `data/raw/sentencing_history/manual/`에 둔다. 파일마다 원문 URL, 저장 시각, 판본명, 이용 조건 확인 상태를 별도 기록하고 SHA-256을 계산한다. 출처와 저장 시각이 없으면 `unverified`로 둔다. 수동 수집으로 접근 제한을 우회하지 않으며, 아직 수동 파일도 확보하지 않았다. 온라인 자동 수집은 실제 접근과 이용 조건이 확인될 때까지 재개하지 않는다.

## 저작권 정책 및 별도 승인 상태

[공식 저작권보호정책](https://sc.scourt.go.kr/sc/krsc/popup/pop_copyright.jsp)을 확인했다. 법원이 저작재산권 전부를 보유한 저작물은 출처를 구체적으로 표시하여 자유이용 가능하다는 정책이다. 개별 자료가 그 조건에 해당하는지와 자동 대량 수집의 허용 범위는 미확인이다.

| 확인 항목 | 상태 |
|---|---|
| 공식 저작권보호정책 | 확인, 조건부 자유이용 및 출처 표시 |
| 자동 대량 수집에 대한 운영자 허용 | 미확인 |
| 에이전트 원문 요청 실행 승인 | 거절 상태; 변경 미확인 |
| 원문 직접 접근·리다이렉트 | 미확인 |

온라인 수집은 재개하지 않는다. 이전 실행 예시는 두 승인 상태가 해소되었다는 뜻이 아니다.

## 오프라인 입력과 대상

`scripts/sentencing/targets_2009_2011.json`은 공식 메뉴에서 확인한 우선 대상 일부다. 메뉴 연도는 시행일로 취급하지 않으며 누락 가능성이 있다. URL이 null인 대상은 확인되지 않은 것이다. 2012–2026 대상 목록도 미완성이다.

`scripts/sentencing/parse_offline.py`는 네트워크 호출 없이 수동 확보 파일과 매니페스트를 읽어 원본 해시·출처·수집 시각·표·오류·미검증 상태를 출력한다. 예를 들어 매니페스트는 `[{'file': 'sample.html', 'url': 'https://sc.scourt.go.kr/원문경로', 'collected_at': '2026-11-15T12:00:00+09:00'}]` 형식의 JSON이다 (실제 JSON에는 작은따옴표 대신 큰따옴표 사용). `python3 scripts/sentencing/parse_offline.py --input-dir data/raw/sentencing_history/manual --manifest data/raw/sentencing_history/manual/manifest.json --output-dir data/processed/sentencing_history/manual`로 실행한다. 원본 파일은 아직 없어 실자료 결과는 없다. 표의 병합 셀, 날짜와 범죄 유형, 권고 구간 및 양형인자 의미 추출은 미구현이며 결과는 V4 분석에 바로 쓰지 않는다.
