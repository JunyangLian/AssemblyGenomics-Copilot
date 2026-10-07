"""Transport, strict parsing and request construction; never loads answers."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator
import yaml

from visible_input import packet

BENCH = Path(__file__).resolve().parent
SYSTEM = '你是基因组分析 QC 审核员，阅读以下任务与产物，按 JSON schema 输出判定'
REPAIR = '上次输出不是符合 schema 的 JSON 对象。请重新审核相同材料，只返回完整的六字段 JSON 对象；不要使用 Markdown 围栏。'


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def safe_url(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('base_url must be HTTPS without credentials, query or fragment')
    if parts.path.endswith('/apps/anthropic'):
        raise ValueError('Anthropic base_url cannot be used with Chat Completions')
    return url.rstrip('/')


def models(root=BENCH, overrides=None):
    data = yaml.safe_load((root / 'models.yaml').read_text(encoding='utf-8'))
    result = []
    for configured in data['models']:
        row = dict(configured)
        if set(row) - {'name', 'base_url', 'key_env', 'model_env', 'base_url_env', 'documented_version',
                       'parameters', 'output_token_budget', 'input_cny_per_million', 'output_cny_per_million',
                       'price_note', 'sources', 'provided_anthropic_url'}:
            raise ValueError('unsupported model configuration field (credentials forbidden)')
        for field, env in [('name', row['model_env']), ('base_url', row['base_url_env'])]:
            if overrides and overrides.get(env):
                row[field] = overrides[env]
        row['base_url'] = safe_url(row['base_url'])
        if not re.fullmatch(r'[A-Z][A-Z0-9_]+', row['key_env']):
            raise ValueError('key_env must be an environment variable name')
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+', row['name']):
            raise ValueError('invalid model name')
        if set(row['parameters']) - {'temperature', 'thinking', 'enable_thinking', 'max_tokens', 'max_completion_tokens'}:
            raise ValueError('unregistered provider parameter')
        result.append(row)
    if len({m['name'] for m in result}) != len(result):
        raise ValueError('duplicate model names')
    return result


def request(case, group, model, root=BENCH, retry=False):
    if group not in ('B', 'C'):
        raise ValueError('model request must be group B or C')
    schema = read_json(root / 'schemas/model_output.schema.json')
    prompt = SYSTEM + '\nJSON schema:\n' + json.dumps(schema, ensure_ascii=False, sort_keys=True)
    if group == 'C':
        prompt += '\n通用 Skill 知识:\n' + (root / 'context/skill_context.md').read_text(encoding='utf-8')
    messages = [{'role': 'system', 'content': prompt},
                {'role': 'user', 'content': json.dumps(packet(case), ensure_ascii=False, sort_keys=True)}]
    if retry:
        # Fresh request, no previous model answer, reasoning, grading feedback or metadata.
        messages.append({'role': 'user', 'content': REPAIR})
    return {'model': model['name'], 'messages': messages, 'stream': False, **model['parameters']}


def token_estimate(body):
    # No provider tokenizer is available. These are explicitly proxies, not usage.
    byte_count = sum(len(m['content'].encode('utf-8')) for m in body['messages'])
    overhead = 64 + 16 * len(body['messages'])
    return {'method': 'UTF-8 bytes / 3 proxy; byte bound + framing allowance',
            'proxy': math.ceil(byte_count / 3) + overhead,
            'upper': byte_count + overhead}


def summary(case, body, root=BENCH):
    visible = packet(case)
    return {'request_sha256': digest(canonical(body)), 'visible_payload_sha256': digest(canonical(visible)),
            'task_sha256': digest(visible['task'].encode('utf-8')),
            'artifacts': [{'filename': a['filename'], 'encoding': a['encoding'],
                           'visible_text_sha256': digest(a['content'].encode('utf-8'))} for a in visible['artifacts']],
            'schema_sha256': digest((root / 'schemas/model_output.schema.json').read_bytes()),
            'context_sha256': digest((root / 'context/skill_context.md').read_bytes()) if '通用 Skill 知识:' in body['messages'][0]['content'] else None,
            'parameters': {k:v for k,v in body.items() if k != 'messages'}, 'input_estimate': token_estimate(body)}


def strict_object(text):
    def unique(pairs):
        obj = {}
        for k,v in pairs:
            if k in obj:
                raise ValueError('duplicate JSON key')
            obj[k] = v
        return obj
    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))


def parse_response(raw, case, root=BENCH):
    try:
        content = raw['choices'][0]['message']['content']
        if not isinstance(content, str):
            raise ValueError('no text content')
        result = strict_object(content)
        Draft202012Validator(read_json(root / 'schemas/model_output.schema.json')).validate(result)
        # Check the filename whitelist; semantic support/field correctness remains human review.
        visible = packet(case)
        allowed = {'task.md'} | {a['filename'] for a in visible['artifacts']}
        for pointer in result['evidence']:
            filename = pointer.split(':', 1)[0]
            rel = PurePosixPath(filename)
            if rel.is_absolute() or '..' in rel.parts or '\\' in filename or filename not in allowed:
                raise ValueError('evidence filename is outside visible input')
        return result, None
    except Exception:
        # Never echo response content into repair prompts or exception strings.
        return None, 'JSON/schema/evidence filename validation failed'


def redact(value, secrets=()):
    if isinstance(value, dict):
        return {k:redact(v, secrets) for k,v in value.items()
                if str(k).lower() not in {'authorization', 'api_key', 'x-api-key'}}
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, '[REDACTED]')
        return re.sub(r'(?i)sk-[A-Za-z0-9_.-]+', '[REDACTED]', value)
    return value
