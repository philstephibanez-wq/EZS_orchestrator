"""R2E PROFILE AI job relay. Runs on MAIN, independent of scientific workers.

XPS calls this relay with an R2E-only shared secret. MAIN is the only peer
allowed to mutate LAB canonical AI jobs and save reviews.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

KIND = 'assistant.profile.review'
PREFIX = '/internal/analysis/desktop'
MAX_JSON = 1024 * 1024


class RelayError(Exception):
    def __init__(self, status: int, code: str):
        self.status, self.code = status, code
        super().__init__(code)


class LabClient:
    def __init__(self, base_url: str, token: str):
        self.base_url, self.token = base_url.rstrip('/'), token

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        raw = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
        request = urllib.request.Request(self.base_url + path, data=raw, method=method, headers={
            'X-EZScore-Analysis-Token': self.token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        try:
            with urllib.request.urlopen(request, timeout=30) as r:
                data = r.read(MAX_JSON + 1)
                if len(data) > MAX_JSON:
                    raise RelayError(502, 'lab_response_oversized')
                return json.loads(data.decode('utf-8')) if data else {}
        except urllib.error.HTTPError as exc:
            raise RelayError(502, 'lab_http_' + str(exc.code)) from exc
        except (OSError, ValueError) as exc:
            raise RelayError(502, 'lab_unavailable') from exc


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as c, c:
            c.execute('CREATE TABLE IF NOT EXISTS receipts (run_id INTEGER PRIMARY KEY, payload_hash TEXT NOT NULL, state TEXT NOT NULL, updated REAL NOT NULL)')

    def connect(self):
        c = sqlite3.connect(self.path, timeout=30)
        c.execute('PRAGMA busy_timeout=30000')
        return c

    def receipt(self, run_id: int) -> tuple | None:
        with closing(self.connect()) as c:
            return c.execute('SELECT payload_hash,state FROM receipts WHERE run_id=?', (run_id,)).fetchone()

    def set_receipt(self, run_id: int, digest: str, state: str):
        with closing(self.connect()) as c, c:
            c.execute('INSERT INTO receipts VALUES(?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET payload_hash=excluded.payload_hash,state=excluded.state,updated=excluded.updated', (run_id, digest, state, time.time()))


class Relay:
    def __init__(self, lab: LabClient, store: Store):
        self.lab, self.store = lab, store
        self.lock = threading.RLock()

    def queue(self, limit: int) -> dict:
        # LAB is the authority for eligibility and claim. Never expose scientific jobs.
        with self.lock:
            requests = self.lab.call('GET', PREFIX + '/profile/ai-requests').get('requests', [])
            if not isinstance(requests, list):
                raise RelayError(502, 'invalid_lab_requests')
            reviews = []
            for job in requests:
                if len(reviews) >= limit:
                    break
                if not isinstance(job, dict) or job.get('status') != 'queued':
                    continue
                run_id = int(job.get('run_id') or 0)
                if run_id <= 0 or self.store.receipt(run_id) is not None:
                    continue
                response = self.lab.call('POST', PREFIX + f'/profile/ai-requests/{run_id}/claim', {})
                if response.get('claimed') is not True:
                    continue
                try:
                    item = self.lab.call('GET', PREFIX + f'/profile/reviews/run/{run_id}').get('item')
                    if not isinstance(item, dict) or int(item.get('run_id') or 0) != run_id:
                        raise RelayError(502, 'invalid_run_context')
                except Exception:
                    # terminal error rather than leave a stuck running claim
                    self.lab.call('POST', PREFIX + f'/profile/ai-requests/{run_id}/finish', {'status':'error','message':'r2e_context_unavailable'})
                    raise
                self.store.set_receipt(run_id, '', 'claimed')
                reviews.append(item)
            return {'schema':'ezs.r2e.profile-queue.v1','reviews':reviews,'count':len(reviews)}

    def submit(self, payload: dict) -> dict:
        run_id = int(payload.get('run_id') or 0)
        if run_id <= 0:
            raise RelayError(422, 'run_id_required')
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        digest = hashlib.sha256(encoded).hexdigest()
        with self.lock:
            receipt = self.store.receipt(run_id)
            if not receipt:
                raise RelayError(409, 'run_not_claimed_by_relay')
            if receipt:
                if receipt[0] and receipt[0] != digest:
                    raise RelayError(409, 'run_already_submitted_different_payload')
                if receipt[1] == 'completed':
                    return {'ok':True,'idempotent':True}
            # Save before marking canonical job completed. Never report success if LAB rejects the revision.
            if receipt[1] == 'claimed':
                result = self.lab.call('POST', PREFIX + '/profile/reviews', payload)
                if result.get('ok') is not True:
                    raise RelayError(502, 'lab_revision_not_saved')
                self.store.set_receipt(run_id, digest, 'saved')
            finish = self.lab.call('POST', PREFIX + f'/profile/ai-requests/{run_id}/finish', {'status':'completed','message':'r2e_revision_saved'})
            if finish.get('ok') is not True:
                raise RelayError(502, 'lab_job_not_finished')
            self.store.set_receipt(run_id, digest, 'completed')
            return {'ok':True,'idempotent':bool(receipt)}


def make_handler(relay: Relay, key: str):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, payload):
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _handle(self, method):
            auth = self.headers.get('X-EZS-R2E-Token', '')
            if not hmac.compare_digest(auth, key):
                self._send(403, {'ok':False,'error':'forbidden'})
                return
            url = urlsplit(self.path)
            try:
                if method == 'GET' and url.path == '/r2e/profile/reviews/queue':
                    limit = min(5, max(1, int(parse_qs(url.query).get('limit',['1'])[0])))
                    self._send(200, relay.queue(limit))
                elif method == 'POST' and url.path == '/r2e/profile/reviews':
                    length = int(self.headers.get('Content-Length','0'))
                    if length < 2 or length > MAX_JSON:
                        raise RelayError(413, 'invalid_request_size')
                    payload = json.loads(self.rfile.read(length).decode('utf-8'))
                    if not isinstance(payload, dict):
                        raise RelayError(422, 'object_required')
                    self._send(200, relay.submit(payload))
                else:
                    self._send(404, {'ok':False,'error':'not_found'})
            except RelayError as exc:
                self._send(exc.status, {'ok':False,'error':exc.code})
            except (ValueError, TypeError, json.JSONDecodeError):
                self._send(422, {'ok':False,'error':'invalid_input'})
            except Exception:
                self._send(500, {'ok':False,'error':'relay_internal_error'})

        def do_GET(self): self._handle('GET')
        def do_POST(self): self._handle('POST')
        def log_message(self, fmt, *args): pass
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8702)
    parser.add_argument('--db', required=True)
    parser.add_argument('--lab-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    lab_token = os.environ.get('EZSTUDIO_ANALYSIS_WORKER_TOKEN','')
    r2e_key = os.environ.get('EZS_R2E_RELAY_TOKEN','')
    if len(lab_token) < 12 or len(r2e_key) < 32:
        raise SystemExit('R2E_TOKENS_REQUIRED')
    server = ThreadingHTTPServer((args.host,args.port), make_handler(Relay(LabClient(args.lab_url, lab_token), Store(args.db)), r2e_key))
    print('EZS_R2E_RELAY_LISTENING', flush=True)
    server.serve_forever()

if __name__ == '__main__': main()
