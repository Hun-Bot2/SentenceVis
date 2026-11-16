# 검증 계층

- unit: 현재 소스 경계 규칙의 위반/허용 예제 테스트.
- integration: 계약 검토 후 ID 참조·상태·근거 조회 검증 예정.
- e2e: 사용자 설계 검토 후 linked-view 및 접근성 동작 검증 예정.
- fixtures/synthetic: 향후 명시적으로 합성한 fixture만 보관.

`data/test_inventory.py`는 합성 ZIP으로 경로·용량·해시·문자 위치 단위·중복 대응·보류 처리를 검사한다. `npm run test:data`로 실행하며 `npm test`에도 포함된다. 현재 테스트에 실제 법률 원문이나 개인정보는 없다. 사용자 평가 결과는 없다. 경계 검사 통과가 법률 정확성·공개 권리·실제 시각화 동작을 증명하지 않는다.
