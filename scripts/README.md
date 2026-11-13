# 오프라인 처리와 개발 검사

- ingest: 비공개 원본 manifest와 정규화 (미구현).
- align: 사건·피고인 대응 후보와 검토 기록 (미구현).
- annotate: 문장·관계 추출 및 사람 검토 (미구현).
- statutes: 법령 연혁 조회·스냅샷 (미구현).
- publish: 권리·검증 상태를 점검한 공개 export (미구현).
- checks: 소스 경계·Markdown 파일 링크 검사 (구현).

이 폴더의 처리기는 브라우저 번들에서 import하지 않는다. 원본·개인정보·API 인증값을 fixture나 public으로 복사하지 않는다. 파이프라인은 아직 실행 가능하지 않다.
