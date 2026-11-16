"""AI-assisted by OpenAI Codex, 2026-11-16. Local priority views; no source moves.
Priority is workflow relevance, never legal verification or redistribution permission.
"""
import json
import os
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
VIEW = DATA / 'priority'


def classify(name):
    n = unicodedata.normalize('NFC', name)
    if n.startswith(('12.', '115.')):
        return '최우선', '개별 판결 원문과 심급 연결 후보; 동일 피고인과 판단 관계는 unverified'
    if n.startswith(('019.', '114.')) or n == '법률 지식베이스':
        return '보통', '판결 보완·조문 조회 자료; 중복과 판본 및 연결 가능성 확인 필요'
    if '양형기준의결' in n or '개정형법' in n:
        return '보통', '법령·양형 맥락; 판결 당시 적용 여부 미확인, 방향 자동 판정 금지'
    return '보충', '연구·통계·뉴스·혼합 묶음; 개별 판결 변경 이유의 직접 증거로 사용 금지, 세부 검토 필요'


def main():
    # Process stores retain their own provenance layout; index them separately.
    stores = {'raw', 'private', 'processed', 'interim', 'originals', 'catalog', 'priority'}
    entries = []
    for source in sorted(DATA.iterdir()):
        if source.name in stores or source.name.startswith('.') or source.name == 'README.md':
            continue
        tier, reason = classify(source.name)
        target = VIEW / tier / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        relative = os.path.relpath(source, target.parent)
        if target.is_symlink():
            if os.readlink(target) != relative:
                raise ValueError(f'Conflicting link: {target}')
        elif target.exists():
            raise ValueError(f'Refusing overwrite: {target}')
        else:
            target.symlink_to(relative, target_is_directory=source.is_dir())
        entries.append({'source_path': str(source.relative_to(ROOT)), 'priority': tier,
                        'reason': reason, 'verification_status': 'unverified',
                        'classification_basis': 'filename_and_existing_local_catalog',
                        'content_review': 'not_performed_by_this_script'})
    VIEW.mkdir(exist_ok=True)
    (VIEW / 'manifest.json').write_text(json.dumps({'entries': entries,
        'process_stores': sorted(stores - {'priority'}), 'source_moved': False}, ensure_ascii=False, indent=2)+'\n')
    (VIEW / 'README.md').write_text('''# 작업 우선순위별 자료 탐색

최우선: 12·115 개별 판결 원문. 보통: 019·114·지식베이스 및 법령·양형기준 맥락.
보충: 통계·연구·뉴스·내용 미검토 혼합 묶음. 파일명과 기존 카탈로그 기반 분류다.
원본은 이동하지 않았고 각 폴더는 상대 심볼릭 링크다. 검증 등급·공개 허가는 아니다.
raw/private/processed/interim/originals/catalog는 처리 단계 저장소로 원래 위치에 유지한다.
세부 사유는 manifest.json, 검토 결과는 docs/records/DATA_PRIORITY_REVIEW.md 참조.
''')
    print(json.dumps({tier: sum(x['priority'] == tier for x in entries) for tier in ('최우선', '보통', '보충')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
