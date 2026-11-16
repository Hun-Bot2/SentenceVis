#!/usr/bin/env python3
"""SentenScope V4: conservative official HTML collector; no access-control bypass.
AI assistance: OpenAI Codex. All parsed observations require human verification.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

HOST = 'sc.scourt.go.kr'
ROOT = pathlib.Path(__file__).resolve().parents[2]
UA = 'SentenScopeResearchBot/1.0'
PRODUCT_TOKEN = 'SentenScopeResearchBot'

def robots_parser(text):
    # Older Python robotparser versions use first-match rules rather than the
    # longest match required by RFC 9309. Fail closed if semantics are missing.
    probe = urllib.robotparser.RobotFileParser()
    probe.parse(['User-agent: *', 'Disallow: /', 'Allow: /ok/',
                 'Disallow: /ok/private', 'Allow: /ok/private'])
    if not probe.can_fetch(PRODUCT_TOKEN, '/ok/private'):
        raise RuntimeError('robotparser lacks RFC 9309 longest-match/tie behavior; use Python 3.15 or newer')
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(text.splitlines())
    return parser

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.tables = []; self.text = []; self.table = None; self.row = None; self.cell = None; self.href = None; self.anchor = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a': self.href = a.get('href'); self.anchor = []
        if tag == 'table' and self.table is None: self.table = []
        elif tag == 'tr' and self.table is not None: self.row = []
        elif tag in ('td', 'th') and self.row is not None: self.cell = []
        elif tag in ('br', 'li') and self.cell is not None: self.cell.append(' | ')
    def handle_data(self, data):
        self.text.append(data)
        if self.cell is not None: self.cell.append(data)
        if self.href is not None: self.anchor.append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((self.href, ' '.join(''.join(self.anchor).split()))); self.href = None
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row); self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table); self.table = None

def official(url):
    p = urllib.parse.urlsplit(url)
    return p.scheme == 'https' and p.hostname == HOST and p.port in (None, 443) and not p.username and not p.password

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'redirect refused', headers, fp)

class Fetcher:
    def __init__(self, delay):
        self.delay = max(3., delay); self.last = 0; self.opener = urllib.request.build_opener(NoRedirect)
    def get(self, url):
        if not official(url): raise ValueError('URL outside official host')
        for attempt in range(2):
            time.sleep(max(0, self.delay - (time.monotonic() - self.last)))
            try:
                self.last = time.monotonic()
                with self.opener.open(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=20) as response:
                    data = response.read(10_000_001)
                    if len(data) > 10_000_000: raise ValueError('response exceeds 10 MB')
                    return data, response.headers.get_content_type(), response.headers.get_content_charset()
            except urllib.error.HTTPError as e:
                if e.code not in (500, 502, 503, 504) or attempt: raise
            except (TimeoutError, urllib.error.URLError):
                if attempt: raise
        raise RuntimeError('request failed')

def decode(data, charset):
    for encoding in (charset, 'utf-8', 'euc-kr'):
        if encoding:
            try: return data.decode(encoding)
            except (UnicodeDecodeError, LookupError): pass
    raise ValueError('unknown HTML encoding')

def parse(data, charset=None):
    p = Page(); p.feed(decode(data, charset)); return p

def main():
    ap = argparse.ArgumentParser(description='공식 HTML 수집: robots 및 이용 조건 확인 후 제한적으로 실행')
    ap.add_argument('--terms-url', required=True, help='직접 확인한 공식 이용 조건 URL')
    ap.add_argument('--terms-reviewed', action='store_true', help='이용 조건을 직접 검토하고 수집 허용을 확인')
    ap.add_argument('--delay', type=float, default=3)
    ap.add_argument('--max-pages', type=int, default=100)
    ap.add_argument('--seed', action='append', default=[])
    args = ap.parse_args()
    if not args.terms_reviewed or not official(args.terms_url): ap.error('공식 이용 조건 URL과 검토 확인이 필요합니다')
    if not 1 <= args.max_pages <= 1000: ap.error('max-pages must be 1..1000')
    fetch = Fetcher(args.delay)
    try:
        robots, ct, charset = fetch.get('https://' + HOST + '/robots.txt')
        rawrobots = decode(robots, charset)
        if ct != 'text/plain' or not re.search(r'(?im)^\s*user-agent\s*:', rawrobots): raise ValueError('robots.txt is not a valid plain-text policy')
        rp = robots_parser(rawrobots)
        if not rp.can_fetch(PRODUCT_TOKEN, args.terms_url): raise ValueError('terms URL disallowed by robots.txt')
        terms, tct, _ = fetch.get(args.terms_url)
        if tct not in ('text/html', 'text/plain'): raise ValueError('unexpected terms content type')
    except Exception as e:
        print('정책 확인 실패; 수집 중단:', e, file=sys.stderr); return 2
    raw = ROOT/'data/raw/sentencing_history'; out = ROOT/'data/processed/sentencing_history'
    raw.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    (raw/'robots.txt').write_bytes(robots); (raw/'terms.snapshot').write_bytes(terms)
    queue = args.seed or ['https://sc.scourt.go.kr/sc/krsc/criterion/past/sex_2011/sex_2011_01.jsp']
    seen = set(); records = []; tables = []; errors = []
    while queue and len(seen) < args.max_pages:
        url = urllib.parse.urldefrag(queue.pop(0))[0]
        if url in seen or not official(url): continue
        seen.add(url)
        if not rp.can_fetch(PRODUCT_TOKEN, url): errors.append({'url': url, 'error': 'robots_disallowed'}); continue
        try:
            data, content_type, encoding = fetch.get(url)
            if content_type != 'text/html': raise ValueError('not HTML: '+content_type)
            digest = hashlib.sha256(data).hexdigest(); (raw/(digest+'.html')).write_bytes(data)
            page = parse(data, encoding)
            records.append({'url':url,'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(),'sha256':digest,'verification_status':'unverified','terms_url':args.terms_url,'terms_sha256':hashlib.sha256(terms).hexdigest()})
            for index, table in enumerate(page.tables):
                tables.append({'source_url':url,'source_sha256':digest,'table_index':index,'rows':table,'verification_status':'unverified','comparability':'unknown'})
            for href, label in page.links:
                target = urllib.parse.urljoin(url, href)
                if official(target) and re.search(r'/sc/krsc/criterion/(past|criterion_[^/]+)/', urllib.parse.urlsplit(target).path) and target not in seen:
                    queue.append(target)
        except Exception as e:
            errors.append({'url':url,'error':str(e)})
            if isinstance(e, urllib.error.HTTPError) and e.code in (401,403,429): break
    for name, obj in [('documents.json',records),('tables.json',tables),('errors.json',errors),('quality.json',{'documents':len(records),'tables':len(tables),'errors':len(errors),'pending_urls':len(queue),'coverage':'unknown','normalized_recommendations':'not_implemented','comparability':'unknown'})]:
        (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'documents':len(records),'tables':len(tables),'errors':len(errors),'pending':len(queue)},ensure_ascii=False))
    return 1 if errors or queue else 0

if __name__ == '__main__': sys.exit(main())
