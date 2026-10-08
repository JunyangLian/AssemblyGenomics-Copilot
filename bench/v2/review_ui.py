"""Loopback-only human action review; no model, private labels or API access.

Reads only the public blinded CSV. Human choices remain separate from the
immutable source; draft saves do not enter scoring until explicitly exported.
"""
from pathlib import Path
import argparse
import csv
from datetime import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import os
import re
import secrets

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'reports/v2-run-10_four-models_A-admitted/ACTION_REVIEW.csv'
FIELDS = ['review_id', 'task', 'action', 'coding', 'reason']
CODES = {'', 'dangerous', 'no_danger_observed', 'uncertain'}
MAX_REQUEST = 262144


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(json_bytes(value)); temp.replace(path)


class Review:
    def __init__(self, source=SOURCE, output=None):
        self.source = Path(source).resolve(strict=True)
        self.source_sha = sha(self.source.read_bytes())
        with self.source.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != FIELDS:
                raise ValueError('source must contain only the blinded five CSV columns')
            self.rows = list(reader)
        ids = [r['review_id'] for r in self.rows]
        if (not ids or len(set(ids)) != len(ids) or
            any(not re.fullmatch(r'R[0-9]{3}', rid) for rid in ids) or
            any(not r['task'].strip() or not r['action'].strip() for r in self.rows)):
            raise ValueError('invalid blinded review rows')
        self.output = Path(output or ROOT / 'review' / self.source_sha[:12]).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.draft_path = self.output / 'DRAFT.json'
        self.answers = [{'review_id': r['review_id'], 'coding': r['coding'], 'reason': r['reason']} for r in self.rows]
        if self.draft_path.exists():
            draft = json.loads(self.draft_path.read_bytes())
            if draft['source_sha256'] != self.source_sha:
                raise ValueError('draft belongs to a different blinded source')
            self.answers = self.validate(draft['answers'])
        else:
            self.answers = self.validate(self.answers)

    def check_source(self):
        if sha(self.source.read_bytes()) != self.source_sha:
            raise ValueError('immutable source CSV changed; stop and reload the original')

    def validate(self, answers, exporting=False):
        if (not isinstance(answers, list) or len(answers) != len(self.rows) or
            any(not isinstance(a, dict) or set(a) != {'review_id', 'coding', 'reason'} for a in answers)):
            raise ValueError('answer fields/count differ; task/action must remain read-only')
        mapping = {}
        for a in answers:
            if (not isinstance(a['review_id'], str) or a['review_id'] in mapping or
                not isinstance(a['coding'], str) or a['coding'] not in CODES or
                not isinstance(a['reason'], str) or len(a['reason']) > 4096):
                raise ValueError('invalid/duplicate choice or reason')
            if exporting and a['coding'] and not a['reason'].strip():
                raise ValueError(f"{a['review_id']}：已选择分类，请填写理由再导出")
            mapping[a['review_id']] = dict(a)
        if set(mapping) != {r['review_id'] for r in self.rows}:
            raise ValueError('answer IDs differ from the blinded source')
        return [mapping[r['review_id']] for r in self.rows]

    def save(self, answers):
        self.check_source()
        selected = self.validate(answers)
        atomic_json(self.draft_path, {'source_sha256': self.source_sha, 'answers': selected,
                                    'saved_at': datetime.now().astimezone().isoformat()})
        self.answers = selected
        return self.state()

    def export(self, answers):
        selected = self.validate(answers, exporting=True)
        self.save(selected)
        stream = io.StringIO(newline='\n')
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows({**r, 'coding': a['coding'], 'reason': a['reason']} for r, a in zip(self.rows, selected))
        stamp = datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%f')
        target = self.output / ('ACTION_REVIEW_' + stamp + '.csv')
        data = stream.getvalue().encode('utf-8-sig')
        with target.open('xb') as stream: stream.write(data)
        complete = sum(bool(a['coding']) and bool(a['reason'].strip()) for a in selected)
        receipt = {'source_path': str(self.source), 'source_sha256': self.source_sha,
                   'csv_path': str(target), 'csv_sha256': sha(data),
                   'total_rows': len(selected), 'complete_rows': complete,
                   'uncoded_rows': sum(not a['coding'] for a in selected),
                   'coding_source': 'local human review form; human input not independently authenticated',
                   'labels_generated_by_model': False, 'automatic_scoring': False,
                   'exported_at': datetime.now().astimezone().isoformat()}
        atomic_json(target.with_suffix('.receipt.json'), receipt)
        return receipt

    def state(self):
        return {'answers': self.answers, 'complete_rows': sum(bool(a['coding']) and bool(a['reason'].strip()) for a in self.answers),
                'total_rows': len(self.rows), 'source_sha256': self.source_sha}


def page(review, token):
    # Untrusted model text stays JSON-escaped and is rendered with textContent.
    payload = json.dumps({'rows': review.rows, 'answers': review.answers, 'token': token}, ensure_ascii=False).replace('<', '\\u003c')
    template = (ROOT / 'review_page.html').read_text(encoding='utf-8')
    return template.replace('/* REVIEW_DATA */', payload).encode('utf-8')


def handler(review, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass

        def reply(self, code, body, kind='application/json; charset=utf-8'):
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            if self.path == '/': self.reply(200, page(review, token), 'text/html; charset=utf-8')
            else: self.reply(404, json_bytes({'error': 'not found'}))

        def do_POST(self):
            origin = 'http://127.0.0.1:' + str(self.server.server_address[1])
            if (self.headers.get('Origin') != origin or
                self.headers.get('X-Review-Session') != token):
                self.reply(403, json_bytes({'error': 'local review session required'})); return
            if self.path not in ('/draft', '/export'):
                self.reply(404, json_bytes({'error': 'not found'})); return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= MAX_REQUEST: raise ValueError('invalid request size')
                answers = json.loads(self.rfile.read(size))
                result = review.save(answers) if self.path == '/draft' else review.export(answers)
            except (ValueError, KeyError, TypeError, OSError) as exc:
                self.reply(400, json_bytes({'error': str(exc)})); return
            self.reply(200, json_bytes(result))
    return Handler


def serve(source=SOURCE, output=None, port=0):
    review = Review(source, output)
    token = secrets.token_urlsafe(24)
    server = HTTPServer(('127.0.0.1', port), handler(review, token))
    url = 'http://127.0.0.1:' + str(server.server_address[1]) + '/'
    atomic_json(review.output / 'SESSION.json', {'pid': os.getpid(), 'url': url,
                'source_sha256': review.source_sha, 'source_path': str(review.source), 'output_root': str(review.output),
                'started_at': datetime.now().astimezone().isoformat(), 'status': 'serving', 'api_calls': 0})
    print('Review page: ' + url, flush=True)
    print('Output directory: ' + str(review.output), flush=True)
    print(f'{len(review.rows)} blinded actions; choices blank until human input; 0 API calls', flush=True)
    try: server.serve_forever()
    finally: server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    args = parser.parse_args()
    serve(args.source)
