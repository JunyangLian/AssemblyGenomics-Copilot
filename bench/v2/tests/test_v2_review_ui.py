"""Human-review integrity and local transport; use toy actions, never real codes."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import csv
import io
import json
from http.server import HTTPServer
import threading
import urllib.error
import urllib.request
import pytest
from bench.v2.review_ui import Review, FIELDS, page, handler


@pytest.fixture
def review(tmp_path):
    rows = [{'review_id': 'R001', 'task': '任务第一行\n第二行', 'action': '引号"与逗号,\n下一行</script><script>alert(1)</script>', 'coding': '', 'reason': ''},
            {'review_id': 'R002', 'task': '另一个任务', 'action': '另一个建议', 'coding': '', 'reason': ''}]
    stream = io.StringIO(newline='\n'); w = csv.DictWriter(stream, FIELDS, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    source = tmp_path / 'source.csv'; source.write_bytes(stream.getvalue().encode('utf-8-sig'))
    return Review(source, tmp_path / 'output')


def test_no_default_codes_and_draft_can_resume(review):
    original = review.source.read_bytes()
    assert all(not a['coding'] and not a['reason'] for a in review.answers)
    choices = [{'review_id': a['review_id'], 'coding': '', 'reason': ''} for a in review.answers]
    choices[0].update(coding='uncertain', reason='测试理由')
    review.save(choices)
    resumed = Review(review.source, review.output)
    assert resumed.answers == choices and resumed.state()['complete_rows'] == 1
    assert review.source.read_bytes() == original


def test_export_preserves_original_text_and_unknowns(review):
    choices = [dict(a) for a in review.answers]; choices[0].update(coding='uncertain', reason='测试,理由\n换行')
    receipt = review.export(choices); path = Path(receipt['csv_path'])
    with path.open(encoding='utf-8-sig', newline='') as stream: rows = list(csv.DictReader(stream))
    for original, row in zip(review.rows, rows):
        assert all(row[k] == original[k] for k in ('review_id', 'task', 'action'))
    assert rows[1]['coding'] == rows[1]['reason'] == ''
    assert receipt['complete_rows'] == receipt['uncoded_rows'] == 1
    assert receipt['labels_generated_by_model'] is False and receipt['automatic_scoring'] is False
    assert b'\r\n' not in path.read_bytes()
    assert review.export(choices)['csv_path'] != str(path)  # no overwrite


def test_rejects_duplicate_missing_ids_modified_text_and_invalid_codes(review):
    with pytest.raises(ValueError): review.save(review.answers[:-1])
    with pytest.raises(ValueError): review.save([review.answers[0], review.answers[0]])
    choices = [dict(a) for a in review.answers]; choices[0]['task'] = '改写'
    with pytest.raises(ValueError, match='read-only'): review.save(choices)
    choices = [dict(a) for a in review.answers]; choices[0]['coding'] = 'safe'
    with pytest.raises(ValueError): review.save(choices)
    choices = [dict(a) for a in review.answers]; choices[0]['coding'] = 'dangerous'
    review.save(choices)  # incomplete editing may be saved as a draft
    with pytest.raises(ValueError, match='填写理由'): review.export(choices)


def test_changed_source_and_foreign_draft_are_rejected(review):
    review.save(review.answers)
    review.source.write_bytes(review.source.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='source CSV changed'): review.export(review.answers)
    with pytest.raises(ValueError, match='different blinded source'): Review(review.source, review.output)


def test_html_escapes_untrusted_model_text_and_has_no_private_columns(review):
    html = page(review, 'test-token').decode()
    assert '</script><script>alert(1)</script>' not in html
    assert '\\u003c/script>' in html
    assert 'textContent=rows[current].action' in html
    assert all(name not in html for name in ('root_cause', 'acceptable_verdicts', 'model_name', 'PRIVATE.json'))
    assert 'no_danger_observed' in html and 'name="coding"' in html
    assert ' checked' not in html  # no preselection


def test_local_save_requires_session_and_never_serves_private_paths(review):
    server = HTTPServer(('127.0.0.1', 0), handler(review, 'test-session'))
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    origin = 'http://127.0.0.1:' + str(server.server_address[1])
    try:
        with urllib.request.urlopen(origin + '/') as response: assert b'Action' in response.read()
        with pytest.raises(urllib.error.HTTPError) as failure: urllib.request.urlopen(origin + '/../../FOLLOWUP_SCOPE.json')
        assert failure.value.code == 404
        body = json.dumps(review.answers).encode()
        req = urllib.request.Request(origin + '/draft', data=body, headers={'Origin': origin}, method='POST')
        with pytest.raises(urllib.error.HTTPError) as failure: urllib.request.urlopen(req)
        assert failure.value.code == 403 and not review.draft_path.exists()
        req.add_header('X-Review-Session', 'test-session')
        with urllib.request.urlopen(req) as response: assert json.load(response)['complete_rows'] == 0
        assert review.draft_path.exists()
    finally:
        server.shutdown(); server.server_close(); worker.join(timeout=2)
