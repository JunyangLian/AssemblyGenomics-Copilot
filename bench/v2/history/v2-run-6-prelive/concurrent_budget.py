"""One shared, synchronized cumulative ledger for concurrent model requests."""
from datetime import datetime, timezone
import os
from pathlib import Path
import threading
import time
from bench.v2.runtime import canonical, read_json, token_estimate
from bench.v2.adapter import ApprovalError, approval

_MUTEXES = {}
_MUTEX_GUARD = threading.Lock()


def atomic_json(path, value):
    """Readers see the complete old or complete new JSON, never a partial ledger."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.tmp')
    with temporary.open('wb') as stream:
        stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())
    for attempt in range(20):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 19: raise
            time.sleep(0.025)  # Windows may briefly hold an open progress-reader handle.


class ConcurrentBudget:
    """Reservations and usage updates share a mutex; no refunds and no new budget."""
    def __init__(self, root, locked):
        self.root, self.locked = root, locked
        self.authorized = approval(root, locked)
        self.path = root / 'runs/API_LEDGER.json'
        with _MUTEX_GUARD:
            self.mutex = _MUTEXES.setdefault(self.path.resolve(), threading.RLock())
        with self.mutex:
            self.state = read_json(self.path) if self.path.exists() else {
                'version': 'v2-cumulative-1', 'calls': 0, 'input_reserved': 0,
                'output_reserved': 0, 'slots': [], 'price': None}

    def reserve(self, slot, body):
        with self.mutex:
            self.authorized = approval(self.root, self.locked)
            if self.path.exists(): self.state = read_json(self.path)
            if self.state.get('provider_usage_exceeded_reservation'):
                raise ApprovalError('provider usage exceeded planning reservation; review required')
            versions = {self.locked['plan']['version']}
            resume = self.locked['plan'].get('resume', {})
            if resume:
                versions.add(resume['parent_version'])
                versions.update(resume.get('protected_versions', []))
            if any(row['slot'] == v + ':' + slot for row in self.state['slots'] for v in versions):
                raise ApprovalError('slot already reserved; never resend without a registered revision')
            input_upper, output_upper = token_estimate(body)['upper'], body['max_tokens']
            proposed = {'calls': self.state['calls'] + 1,
                'input_reserved': self.state['input_reserved'] + input_upper,
                'output_reserved': self.state['output_reserved'] + output_upper}
            if any(proposed[k] > self.authorized[cap] for k, cap in [
                ('calls', 'max_calls'), ('input_reserved', 'max_input_tokens'), ('output_reserved', 'max_output_tokens')]):
                raise ApprovalError('approved cumulative v2 call/token reservation cap reached')
            self.state.update(proposed)
            self.state['slots'].append({'slot': self.locked['plan']['version'] + ':' + slot,
                'plan_sha256': self.locked['plan_sha256'], 'input_reserved': input_upper,
                'output_reserved': output_upper, 'usage': None,
                'reserved_at_utc': datetime.now(timezone.utc).isoformat()})
            atomic_json(self.path, self.state)  # persisted before any network request

    def usage(self, slot, usage):
        with self.mutex:
            self.state = read_json(self.path)
            key = self.locked['plan']['version'] + ':' + slot
            entry = next(r for r in self.state['slots'] if r['slot'] == key)
            entry['usage'] = usage
            exceeded = isinstance(usage, dict) and (
                isinstance(usage.get('prompt_tokens'), (int, float)) and usage['prompt_tokens'] > entry['input_reserved'] or
                isinstance(usage.get('completion_tokens'), (int, float)) and usage['completion_tokens'] > entry['output_reserved'])
            if exceeded: self.state['provider_usage_exceeded_reservation'] = True
            atomic_json(self.path, self.state)
