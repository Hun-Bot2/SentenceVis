#!/usr/bin/env python3
"""Two bounded gateway probes; no credentials or URLs printed. AI: OpenAI Codex."""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from ccjs_fetch import DEFAULT, NoRedirect, load_env_key, normalize_key

def load_key(path):
    return normalize_key(load_env_key(path))


def classify(data):
    try:
        parsed = json.loads(data)
        response = parsed.get('response', {}) if isinstance(parsed, dict) else {}
        header = response.get('header', {}) if isinstance(response, dict) else {}
        body = response.get('body', {}) if isinstance(response, dict) else {}
        items = body.get('items', {}) if isinstance(body, dict) else {}
        item = items.get('item', []) if isinstance(items, dict) else []
        return {'format':'json','code':str(header.get('resultCode', 'unknown')),
                'total_count':header.get('totalCount'),'item_count':len(item) if isinstance(item,list) else None,
                'body_type':type(body).__name__}
    except (ValueError, UnicodeDecodeError):
        try:
            xml=ET.fromstring(data)
            safe=lambda name: xml.findtext('.//'+name)
            return {'format':'xml','code':safe('resultCode') or safe('returnReasonCode') or 'unknown'}
        except ET.ParseError: return {'format':'unrecognized','code':'unknown'}


def probe(key, params):
    url=DEFAULT+'?'+urllib.parse.urlencode({'serviceKey':key, **params})
    try:
        with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'SentenScope-CCJS/1.0'}),timeout=20) as res:
            data=res.read(1000001)
            if len(data)>1000000: return {'status':'response_too_large'}
            return {'http':res.status, **classify(data)}
    except urllib.error.HTTPError as exc:
        return {'http':exc.code, 'status':'http_error'}
    except (urllib.error.URLError, TimeoutError):
        return {'status':'network_error'}


def main():
    try: key=load_key(Path(__file__).resolve().parents[2]/'.env')
    except (OSError, ValueError) as e:
        print(str(e)); return 1
    p={'table':'T188063000631730','year':'2024'}
    r=probe(key,{**p,'row':'서울지방검찰청(구)@서울동부지방검찰청@인원@인원','col':'처리@기소명령'})
    print('full_parameters:',json.dumps(r))
    if r.get('code') != '00':
        print('인증 또는 서비스 성공이 확인되지 않아 두 번째 요청을 생략합니다.'); return 1
    time.sleep(2)
    print('table_year_only:',json.dumps(probe(key,p)))
    return 0

if __name__ == '__main__': sys.exit(main())
