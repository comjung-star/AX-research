import pytest
from scripts import core_preservation_run as run


def test_unknown_core_fields_have_no_evidence():
    data = {'core': {field: {'text': None, 'evidence': []} for field in run.prompts.FIELDS}}
    run.validate('X', 'CPD01', data)
    data['core']['workflow'] = None
    run.validate('X', 'CPD01', data)
    data['core']['input']['evidence'] = ['invented']
    with pytest.raises(AssertionError):
        run.validate('X', 'CPD01', data)


def test_all_conditions_same_generation_parameters():
    bodies = [run.body(kind, 'CPD01') for kind in ('B', 'C', 'X')]
    keys = set(bodies[0])-{'input', 'instructions'}
    assert all({k: b[k] for k in keys} == {k: bodies[0][k] for k in keys} for b in bodies)


def test_missing_view_has_no_fabricated_content():
    views = [{'id': slot, 'status': 'MISSING', 'title': '', 'description': '',
              'keywords': [], 'source_quote': ''} for slot in run.SLOTS]
    run.validate('E', 'CPD01', {'perspectives': views})
    views[0]['description'] = 'invented'
    with pytest.raises(AssertionError):
        run.validate('E', 'CPD01', {'perspectives': views})
