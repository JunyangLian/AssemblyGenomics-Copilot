"""Check actual whitelist pagination and draft evidence availability; no model."""
import json

from bench.inspect_adapter.readonly import PublicFiles
from bench.harness_common import token_estimate
from bench.newsource_validation import cases, protocol


def audit():
    cases.verify_protocol_lock()
    packets = cases.build()
    results = {}
    for cid, packet in packets.items():
        files = PublicFiles(cases.DIRECTORY / 'cases' / cid)
        condition_messages = {c: protocol.messages(files, c) for c in ('inline', 'tools')}
        inline = json.loads(condition_messages['inline'][1]['content'])
        tools = json.loads(condition_messages['tools'][1]['content'])
        if inline['files'] != tools['files'] or inline['task'] != tools['task']:
            raise ValueError('task/manifest not equivalent')
        available, page_counts = {}, {}
        for path, text in inline['artifacts'].items():
            start, recovered, count = 1, [], 0
            while start:
                reply = files.read_lines(path, start_line=start, line_count=200)
                recovered += [r['text'] for r in reply['lines']]
                count += 1
                start = reply['next_line']
            if recovered != text.splitlines():
                raise ValueError('tool pagination loses inline evidence')
            available[path] = recovered
            page_counts[path] = count
        if sum(page_counts.values()) > 4:
            raise ValueError('all artifacts cannot be read within fixed preparation rounds')
        for private in ('expected.json', 'meta.json', '../expected.json'):
            try:
                files.text(private)
            except ValueError:
                pass
            else:
                raise ValueError('private file accessible')
        pointers = [p for e in json.loads(packet['expected.json'])['key_evidence'] for p in e['acceptable_pointers']]
        for pointer in pointers:
            name, loc = pointer.split(':', 1)
            if name != 'task.md' and name not in available:
                raise ValueError('gold key evidence unavailable to retrieval')
        results[cid] = {'same_public_bytes': True, 'private_files_rejected': True,
                        'key_evidence_pointers_accessible': pointers, 'artifact_pages': page_counts,
                        'list_plus_all_reads': 1 + sum(page_counts.values()),
                        'initial_input_proxy': {c: token_estimate({'messages': m})['proxy']
                                                for c, m in condition_messages.items()}}
    data = {'status': 'pass', 'cases': results, 'provider_calls': 0,
            'scope': 'available evidence equality and actual page access; not equal actual model evidence uptake',
            'token_note': 'initial text proxy only; tools/schema/history additional; not provider tokenizer or total paid budget',
            'answer_status': 'draft; no human or independent AI review claimed'}
    cases.old.write_json(cases.DIRECTORY / 'MATERIAL_AUDIT.json', data)
    print('PASS: 12 evidence-equivalent packets; list + all artifact reads <= 5; no private reads or API calls')
    return data


if __name__ == '__main__':
    audit()
