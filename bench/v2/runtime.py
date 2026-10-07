"""Shared v2 imports; public request helpers are unchanged from v1."""
from pathlib import Path
import sys

V2 = Path(__file__).resolve().parent
BENCH = V2.parent
REPO = BENCH.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(BENCH))
from harness_common import (SYSTEM, REPAIR, canonical, digest, read_json, write_json,
                            request as original_request, summary, parse_response,
                            token_estimate, redact, safe_url)
from visible_input import packet, visible_files


def request(case, group, model, root=V2, retry=False):
    if group not in ('B', 'C2'):
        raise ValueError('v2 model group must be B or C2')
    return original_request(case, 'C' if group == 'C2' else 'B', model, root, retry)


def rules(repo=REPO):
    paths = [repo / 'scripts' / n for n in ('run_pitfall_checks.py', 'check_baselines.py')]
    paths += list((repo / 'knowledge/pitfalls').glob('*.yaml'))
    paths += list((repo / 'knowledge/baselines').glob('*.yaml'))
    return {p.relative_to(repo).as_posix(): digest(p.read_bytes().replace(b'\r\n', b'\n'))
            for p in sorted(paths)}
