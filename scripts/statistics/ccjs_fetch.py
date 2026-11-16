#!/usr/bin/env python3
"""Interactive, single-query CCJS statistics snapshot. AI assistance: OpenAI Codex."""
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2] / 'data/raw/ccjs_statistics'
DEFAULT = 'https://apis.data.go.kr/B554626/ccjs/getstatistics'

def load_env_key(path):
    matches = []
    for line in path.read_text(encoding='utf-8').splitlines():
        match = re.match(r'^\s*(?:export\s+)?KICJ_SERVICE_KEY\s*=\s*(.*?)\s*$', line)
        if match:
            value = match.group(1)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            matches.append(value)
    if len(matches) != 1 or not matches[0]:
        raise ValueError('KICJ_SERVICE_KEY 값이 없거나 중복됩니다')
    return matches[0]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'redirect refused', headers, fp)

def normalize_key(key):
    # The portal offers encoded and decoded forms; unquote once, then urlencode once.
    return urllib.parse.unquote(key.strip())

def endpoint_url(raw):
    p = urllib.parse.urlsplit(raw.strip())
    if p.scheme != 'https' or p.hostname != 'apis.data.go.kr' or p.port not in (None, 443) or p.username or p.password or p.query or p.fragment:
        raise ValueError('공공데이터포털 HTTPS 주소만 허용하며 주소에 쿼리를 넣을 수 없습니다.')
    if p.path.rstrip('/') not in ('/B554626/ccjs', '/B554626/ccjs/getstatistics'):
        raise ValueError('형사사법통계 통합조회 경로가 아닙니다.')
    return 'https://apis.data.go.kr/B554626/ccjs/getstatistics'

def build_url(endpoint, key, params):
    if set(params) != {'table', 'year', 'row', 'col'} or not all(params.values()):
        raise ValueError('table, year, row, col 모두 필요합니다.')
    if not params['year'].isdigit() or len(params['year']) != 4:
        raise ValueError('year는 4자리 숫자여야 합니다.')
    if not key: raise ValueError('인증키가 비어 있습니다.')
    return endpoint_url(endpoint) + '?' + urllib.parse.urlencode({'serviceKey': normalize_key(key), **params})

def write_snapshot(data, endpoint, params, root=ROOT):
    obj = json.loads(data)
    if not isinstance(obj, (dict, list)): raise ValueError('JSON 객체 또는 배열이 아닙니다.')
    digest = hashlib.sha256(data).hexdigest()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / (digest + '.json')
    if not path.exists():
        fd, temp = tempfile.mkstemp(dir=root, prefix='.response-')
        try:
            with os.fdopen(fd, 'wb') as f: f.write(data)
            os.replace(temp, path)
        finally:
            if os.path.exists(temp): os.unlink(temp)
    record = {'endpoint': endpoint_url(endpoint), 'parameters': params, 'retrieved_at_utc': now,
              'sha256': digest, 'bytes': len(data), 'raw_file': path.name,
              'source': '한국형사법무정책연구원 형사사법통계 통합조회',
              'verification_status': 'unverified', 'grain': 'unknown', 'interpretation': 'contextual_statistics'}
    manifest = root / 'requests.jsonl'
    fd = os.open(manifest, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, 'a', encoding='utf-8') as f: f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return path, digest

def run_request(endpoint, key, params):
    url = build_url(endpoint, key, params)
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(urllib.request.Request(url, headers={'Accept':'application/json', 'User-Agent':'SentenScope-CCJS/1.0'}), timeout=30) as resp:
            data = resp.read(10_000_001)
            if len(data) > 10_000_000: raise ValueError('응답이 10MB를 초과했습니다.')
    except urllib.error.HTTPError as exc:
        # Never print exception URL, headers, or response body: they can contain the key.
        raise RuntimeError(f'HTTP {exc.code}; 응답 본문과 URL은 보안상 표시하지 않습니다.') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('네트워크 연결에 실패했습니다. DNS·접속 환경을 확인하세요.') from None
    key_raw = normalize_key(key)
    if key_raw and (key_raw.encode() in data or urllib.parse.quote(key_raw, safe='').encode() in data):
        raise ValueError('응답에 인증키가 포함되어 저장을 중단했습니다.')
    try:
        result = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError('JSON이 아닌 응답입니다. 오류 응답일 수 있어 저장하지 않았습니다.') from None
    # Error formats are service-dependent: preserve no success assertion.
    path, digest = write_snapshot(data, endpoint, params)
    print(f'응답 저장: {path}\nSHA-256: {digest}\n바이트: {len(data)}')
    if isinstance(result, dict): print('최상위 필드:', ', '.join(map(str, result.keys())))
    print('응답의 성공 여부·표 의미·기간과 완전성은 직접 확인해야 합니다.')

def main():
    print('CCJS 통계표 1회 조회. 인증키는 루트 .env에서 읽습니다.')
    try:
        endpoint = input(f'Endpoint [기본: {DEFAULT}]: ').strip() or DEFAULT
        endpoint_url(endpoint)
        params = {k:input(f'{label}: ').strip() for k,label in [('table','통계표 ID (table)'),('year','연도 (year)'),('row','행 코드/이름 (row)'),('col','열 코드/이름 (col)')]}
        key = load_env_key(Path(__file__).resolve().parents[2] / '.env')
        run_request(endpoint, key, params)
    except (OSError, ValueError, RuntimeError, EOFError, KeyboardInterrupt) as exc:
        print('조회 중단:', str(exc) or '입력 취소')
        return 1
    return 0

if __name__ == '__main__': raise SystemExit(main())
