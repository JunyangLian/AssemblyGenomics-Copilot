"""Environment-only key, one cumulative v2 ledger, no network retries or redirects."""
from contextlib import contextmanager
import json
import os
import urllib.error
import urllib.request
from bench.v2.runtime import canonical, digest, read_json, write_json, redact, token_estimate, safe_url
from model_adapter import Mock


class ApprovalError(ValueError):
    pass


def approval(root, locked):
    path = root / 'API_APPROVAL.json'
    if not path.is_file():
        raise ApprovalError('v2 numeric resource budget and protocol review are pending; no API call')
    data = read_json(path)
    for field in ('approved', 'accepts_unknown_price', 'accepts_unknown_provider_defaults', 'parameters_reviewed'):
        if data.get(field) is not True:
            raise ApprovalError('explicit v2 resource/protocol acceptance missing: ' + field)
    if (not data.get('user_approval_quote') or data.get('plan_sha256') != locked['plan_sha256']
        or data.get('frozen_md_sha256') != locked['frozen_md_sha256']
        or data.get('models') != [m['name'] for m in locked['plan']['models']]
        or data.get('groups') != ['B', 'C2']):
        raise ApprovalError('v2 approval does not match the frozen plan/model scope')
    for field in ('max_calls', 'max_input_tokens', 'max_output_tokens'):
        if type(data.get(field)) is not int or data[field] <= 0:
            raise ApprovalError('positive integer resource cap required: ' + field)
    if data['max_calls'] > 1440:
        raise ApprovalError('call cap exceeds the preregistered slots plus format repair')
    mock_path = root / 'MOCK_REPORT.json'
    if (not mock_path.is_file() or digest(mock_path.read_bytes()) != data.get('mock_report_sha256')
        or read_json(mock_path).get('plan_sha256') != locked['plan_sha256']
        or read_json(mock_path).get('status') != 'pass'):
        raise ApprovalError('completed mock report must be reviewed and bound to approval')
    return data


@contextmanager
def exclusive(root):
    directory = root / 'runs'; directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'API_ACTIVE.lock'
    try:
        with path.open('xb') as f:
            f.write(str(os.getpid()).encode('ascii'))
    except FileExistsError:
        raise ApprovalError('existing API lock; review interrupted run before continuing') from None
    try:
        yield
    finally:
        path.unlink()


class Budget:
    """Reservations never refunded: absent usage/hidden thinking cannot be treated as free."""
    def __init__(self, root, locked):
        self.root, self.locked = root, locked
        self.authorized = approval(root, locked)
        self.path = root / 'runs/API_LEDGER.json'
        self.state = read_json(self.path) if self.path.exists() else {
            'version': 'v2-cumulative-1', 'calls': 0, 'input_reserved': 0,
            'output_reserved': 0, 'slots': [], 'price': None}

    def reserve(self, slot, body):
        self.authorized = approval(self.root, self.locked)
        key = self.locked['plan']['version'] + ':' + slot
        input_upper, output_upper = token_estimate(body)['upper'], body['max_tokens']
        protected_versions = {self.locked['plan']['version']}
        if self.locked['plan'].get('resume'):
            protected_versions.add(self.locked['plan']['resume']['parent_version'])
            protected_versions.update(self.locked['plan']['resume'].get('protected_versions', []))
        if any(r['slot'] == version + ':' + slot for r in self.state['slots'] for version in protected_versions):
            raise ApprovalError('slot already reserved; never resend without a registered revision')
        proposed = {'calls': self.state['calls'] + 1,
                    'max_input_tokens': self.state['input_reserved'] + input_upper,
                    'max_output_tokens': self.state['output_reserved'] + output_upper}
        if (proposed['calls'] > self.authorized['max_calls'] or
            proposed['max_input_tokens'] > self.authorized['max_input_tokens'] or
            proposed['max_output_tokens'] > self.authorized['max_output_tokens']):
            raise ApprovalError('approved cumulative v2 call/token reservation cap reached')
        self.state['calls'] = proposed['calls']
        self.state['input_reserved'], self.state['output_reserved'] = proposed['max_input_tokens'], proposed['max_output_tokens']
        self.state['slots'].append({'slot': key, 'plan_sha256': self.locked['plan_sha256'],
                                   'input_reserved': input_upper, 'output_reserved': output_upper, 'usage': None})
        write_json(self.path, self.state)

    def usage(self, slot, usage):
        key = self.locked['plan']['version'] + ':' + slot
        entry = next(r for r in self.state['slots'] if r['slot'] == key)
        entry['usage'] = usage
        # Even reported usage cannot release prior reservations. If provider exceeds our
        # planning limits (e.g. hidden reasoning), pause the entire live run for review.
        exceeded = isinstance(usage, dict) and (
            isinstance(usage.get('prompt_tokens'), (int, float)) and usage['prompt_tokens'] > entry['input_reserved'] or
            isinstance(usage.get('completion_tokens'), (int, float)) and usage['completion_tokens'] > entry['output_reserved'])
        if exceeded:
            self.state['provider_usage_exceeded_reservation'] = True
        write_json(self.path, self.state)


class OpenAICompatible:
    def __init__(self, model, budget):
        self.model, self.budget = model, budget
        approval(budget.root, budget.locked)  # before accessing environment credentials
        self.key = os.environ.get(model['key_env'])
        if not self.key:
            raise ApprovalError('required environment variable is unset: ' + model['key_env'])

    def complete(self, body, slot):
        if self.budget.state.get('provider_usage_exceeded_reservation'):
            raise ApprovalError('provider usage exceeded planning reservation; review required')
        self.budget.reserve(slot, body)
        req = urllib.request.Request(safe_url(self.model['base_url']) + '/chat/completions',
            data=canonical(body), method='POST',
            headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=300) as response:
                payload = response.read(16777217)
            if len(payload) > 16777216:
                return None, 'response exceeds transport limit'
            raw = redact(json.loads(payload.decode('utf-8')), [self.key])
            self.budget.usage(slot, raw.get('usage') if isinstance(raw, dict) else None)
            return raw, None
        except urllib.error.HTTPError as exc:
            return None, 'HTTP ' + str(exc.code)  # discard error body and headers
        except Exception as exc:
            return None, 'transport/response failure: ' + type(exc).__name__
