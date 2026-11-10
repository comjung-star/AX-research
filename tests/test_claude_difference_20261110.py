import json
from scripts import claude_difference_20261110 as audit
from scripts import continue_cross_validation_20261110 as transport


def test_difference_inputs_are_exact_frozen_subsets():
    recommendations = audit.core.read(audit.ORIGINAL/'recommendations.json')
    pairs = set()
    counts = [0, 0]
    for question, row in recommendations.items():
        original = audit.core.read(audit.ORIGINAL/'blind-inputs'/(question+'.json'))
        payload = audit.core.read(audit.OUT/'blind-inputs'/(question+'.json'))
        left, right = set(row['A']), set(row['B'])
        assert payload == {**original, 'cases':[case for case in original['cases'] if case['case_id'] in left ^ right]}
        counts[0] += len(left-right)
        counts[1] += len(right-left)
        for case in payload['cases']:
            key = (question,case['case_id'])
            assert key not in pairs
            pairs.add(key)
    assert counts == [76,76]
    assert len(pairs) == 152


def test_existing_receipt_prevents_all_network_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(transport,'OUT',tmp_path)
    receipt = {'status':'STARTED','delivery_unknown':True}
    audit.core.save(tmp_path/'api/anthropic_q.response.json',receipt)
    def forbidden(*args, **kwargs):
        raise AssertionError('network call on existing receipt')
    monkeypatch.setattr(transport.urllib.request,'urlopen',forbidden)
    assert transport.request('anthropic','q',{},'q',100) == receipt


def test_wrong_quote_is_missing_evidence_not_abstain():
    payload = {'cases':[{'case_id':'case','problem':'original'}]}
    row = {'case_id':'case','grade':'2','reason':'reason','evidence_field':'problem','evidence_quote':'invented'}
    receipt = {'provider':'anthropic','raw':{'stop_reason':'end_turn','content':[{'type':'text','text':json.dumps({'judgments':[row]})}]}}
    good, bad = transport.accepted(receipt,payload)
    assert good == {}
    assert len(bad) == 1
    assert row['grade'] == '2'
