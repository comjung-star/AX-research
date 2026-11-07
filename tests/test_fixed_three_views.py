import pytest

from scripts.fixed_three_views import SLOTS, fixed_only, request, validate


def test_same_generation_settings():
    query = 'NV20261102_01'
    a, b = request('dynamic', query), request('fixed', query)
    for field in set(a) - {'input', 'instructions'}:
        assert a[field] == b[field]


def test_fixed_missing_slot_cannot_contain_search_content():
    views = [dict(id=slot, status='MISSING', title='', description='',
                  source_quote='', keywords=[]) for slot in SLOTS]
    views[0].update(status='PRESENT', title='서비스 장애 대응',
                    description='운영자가 증상을 입력', source_quote='운영자가 증상을 입력')
    validate('fixed', 'NV20261102_01', {'perspectives': views})
    views[1]['description'] = '가정한 작업'
    with pytest.raises(AssertionError):
        validate('fixed', 'NV20261102_01', {'perspectives': views})


def test_d_uses_branch_maxima_without_original_score():
    rows = {
        ('p1', 'case'): {'C1_rule': {'mapping_grade': 4}, 'semantic': {'score': 0.1}, 'hybrid_exact': '1/61'},
        ('p2', 'case'): {'C1_rule': {'mapping_grade': 0}, 'semantic': {'score': 0.6}, 'hybrid_exact': '1/62'},
    }
    assert fixed_only(['p1', 'p2'], rows, ['case'])['scores']['case'] == pytest.approx(0.9)
