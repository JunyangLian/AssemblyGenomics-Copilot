"""Record protocol identity before opening any new source feature records."""
import datetime
import platform
from pathlib import Path

from bench.newsource_validation import cases, protocol
from bench.inspect_adapter import t3_packets as old

DIRECTORY = cases.DIRECTORY
ROOT = DIRECTORY.parent.parent
FILES = ['bench/newsource_validation/' + n for n in (
    'cases.py', 'intake.py', 'protocol.py', 'system.txt', 'final.txt', 'PROTOCOL_DRAFT.md',
    'schemas/case_meta.schema.json', 'schemas/expected.schema.json', 'schemas/model_output.schema.json',
    'server/prepare_config.json', 'SOURCE_AUDIT.json', 'PROTOCOL_FIXTURE.json')]
FILES += ['bench/inspect_adapter/' + n for n in ('t3_packets.py', 't3_task.py', 'readonly.py',
          't3_test/schemas/model_output.schema.json')]
FILES += ['bench/harness_common.py', 'bench/v2/runtime.py']


def lock():
    target = DIRECTORY / 'PROTOCOL_LOCK.json'
    if target.exists():
        cases.verify_protocol_lock()
        return old.read_json(target)
    if (DIRECTORY / 'selection/SOURCE_SUBSETS.json').exists() or (DIRECTORY / 'cases').exists():
        raise ValueError('construction already exists; cannot claim a preconstruction lock')
    fixture = old.read_json(DIRECTORY / 'PROTOCOL_FIXTURE.json')
    if fixture['status'] != 'pass' or fixture['provider_calls'] != 0 or fixture['new_source_features_read'] != 0:
        raise ValueError('old development fixture absent or out of scope')
    receipt = old.read_json(DIRECTORY / 'SOURCE_RECEIPT.json')
    if receipt['new_gff_or_faa_features_examined']:
        raise ValueError('new features were already examined')
    data = {'version': 'newsource-retrieval-protocol-1', 'status': 'locked_before_feature_extraction',
            'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'python': platform.python_version(), 'files': {n: old.digest((ROOT / n).read_bytes()) for n in FILES},
            'source_receipt_sha256': old.digest((DIRECTORY / 'SOURCE_RECEIPT.json').read_bytes()),
            'assignment': cases.ASSIGNMENT, 'policy': cases.POLICY, 'limits': protocol.LIMITS,
            'source_group_count': 6, 'case_count_proposed': 12, 'development_fixture_cases': fixture['cases'],
            'answers_frozen': False, 'api_call_authorized': False, 'api_calls': 0,
            'paid_http_guard_verified': False,
            'scope': 'protocol, generator, public contracts and label scorer; not gold approval or paid authorization'}
    old.write_json(target, data)
    print('LOCKED: preconstruction protocol; 0 new feature examinations; no gold or API authorization')
    return data


if __name__ == '__main__':
    lock()
