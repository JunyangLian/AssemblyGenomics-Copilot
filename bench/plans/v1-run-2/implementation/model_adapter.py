"""Deterministic mock and gated OpenAI-compatible HTTP client. No SDK retries."""
from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from contextlib import contextmanager

from harness_common import canonical, digest, read_json, redact, safe_url


class Mock:
    def __init__(self, schema, seed):
        self.schema, self.seed = schema, seed

    def complete(self, body, slot):
        rng = random.Random(int(digest(canonical([self.seed, slot, body]))[:16], 16))
        result = {'verdict':rng.choice(self.schema['$defs']['verdict']['enum']),
                  'root_cause':rng.choice(self.schema['$defs']['root_cause']['enum']),
                  'evidence':['task.md:1'], 'action':'复核本阶段交付及已有 QC 记录后决定下一步。',
                  'proposes_threshold_relaxation':bool(rng.getrandbits(1)),
                  'proposes_skipping_check':bool(rng.getrandbits(1))}
        return {'object':'chat.completion', 'model':'mock/' + body['model'],
                'choices':[{'finish_reason':'stop', 'message':{'role':'assistant', 'content':canonical(result).decode('utf-8')}}],
                'usage':None}, None


class ApprovalError(ValueError):
    pass


@contextmanager
def exclusive_api_run(root):
    directory = root / 'runs'; directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'API_ACTIVE.lock'
    try:
        stream = path.open('xb')
    except FileExistsError:
        raise ApprovalError('another or interrupted API process owns the lock; review ledger before clearing it') from None
    try:
        stream.write(str(os.getpid()).encode('ascii')); stream.close()
        yield
    finally:
        path.unlink()


def approval(root, locked):
    path = root / 'API_APPROVAL.json'
    if not path.is_file():
        raise ApprovalError('real API is not approved; mock/cost review must be approved separately')
    data = read_json(path)
    if (data.get('approved') is not True or not data.get('user_approval_quote') or
        data.get('plan_sha256') != locked['plan_sha256'] or
        data.get('frozen_md_sha256') != locked['frozen_md_sha256']):
        raise ApprovalError('API approval does not bind explicit user approval to this plan and frozen version')
    if data.get('models') != [m['name'] for m in locked['plan']['models']] or data.get('groups') != ['B','C']:
        raise ApprovalError('approved model/group scope differs')
    if not isinstance(data.get('max_calls'), int) or not 0 < data['max_calls'] <= 576:
        raise ApprovalError('approved call cap missing/invalid')
    if not isinstance(data.get('max_cost_cny'), (float, int)) or data['max_cost_cny'] <= 0:
        raise ApprovalError('approved cost cap missing/invalid')
    return data


class Budget:
    """Reserve worst-case input + total output before sending each request."""
    def __init__(self, root, locked):
        self.root, self.locked = root, locked
        self.authorized = approval(root, locked)
        self.path = root / 'runs' / ('api_ledger_' + locked['plan_sha256'][:16] + '.json')
        self.state = read_json(self.path) if self.path.exists() else {'calls':0, 'reserved_cny':0, 'slots':[]}
        prior = locked['plan'].get('prior_ledger')
        if prior and not self.path.exists():
            source = (root / prior['path']).resolve(strict=True)
            if (root / 'runs').resolve() not in source.parents or digest(source.read_bytes()) != prior['sha256']:
                raise ApprovalError('prior ledger identity changed; cumulative budget cannot be reset')
            self.state = read_json(source)
            if self.state['calls'] != prior['calls'] or self.state['reserved_cny'] != prior['reserved_cny']:
                raise ApprovalError('prior reservation totals differ')
            self.state['carried_from'] = prior['path']

    def reserve(self, slot, model, input_upper):
        from harness_common import write_json
        self.authorized = approval(self.root, self.locked)
        namespace = self.locked['plan'].get('slot_namespace')
        if namespace:
            slot = namespace + ':' + slot
        cost = (input_upper * model['input_cny_per_million'] + model['output_token_budget'] * model['output_cny_per_million']) / 1e6
        if slot in self.state['slots']:
            raise ApprovalError('request already reserved; review partial run before resuming')
        if self.state['calls'] >= self.authorized['max_calls'] or self.state['reserved_cny'] + cost > self.authorized['max_cost_cny']:
            raise ApprovalError('approved call/cost cap reached')
        self.state['calls'] += 1; self.state['reserved_cny'] += cost; self.state['slots'].append(slot)
        write_json(self.path, self.state)


class OpenAICompatible:
    def __init__(self, model, budget):
        # Approval is validated before reading any key or touching the network.
        self.model, self.budget = model, budget
        self.key = os.environ.get(model['key_env'])
        if not self.key:
            raise ApprovalError('required key environment variable is unset: ' + model['key_env'])

    def complete(self, body, slot):
        from harness_common import token_estimate
        self.budget.reserve(slot, self.model, token_estimate(body)['upper'])
        url = safe_url(self.model['base_url']) + '/chat/completions'
        req = urllib.request.Request(url, data=canonical(body), method='POST',
                                     headers={'Authorization':'Bearer ' + self.key, 'Content-Type':'application/json'})
        # Do not follow redirects, which could forward authorization to another host.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        try:
            opener = urllib.request.build_opener(NoRedirect())
            with opener.open(req, timeout=300) as response:
                payload = response.read(16 * 1024 * 1024 + 1)
            if len(payload) > 16 * 1024 * 1024:
                return None, 'response exceeds transport limit'
            raw = json.loads(payload.decode('utf-8'))
            return redact(raw, [self.key]), None
        except urllib.error.HTTPError as exc:
            # Keep status, discard provider error body/headers (may echo credentials).
            return None, 'HTTP ' + str(exc.code)
        except Exception as exc:
            return None, 'transport/response failure: ' + type(exc).__name__
