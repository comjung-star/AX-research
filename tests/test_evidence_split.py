import json
import pytest
from scripts import evidence_split as s

def test_inventory_is_query_blind():
    cs,_=s.r.cases_queries()
    j=s.inventory_job('inventory_probe',0,['AXV2C_0093_01'],cs)
    assert set(j['items']['AXV2C_0093_01'])=={'task','context','sources'}
    assert 'qid' not in j and 'problem' not in j['items']['AXV2C_0093_01']

def test_closure_repair_preserves_values():
    d,repairs=s.decode_json('{"items":[{"id":"a","ops":[["x","T0"]}]}')
    assert d=={'items':[{'id':'a','ops':[['x','T0']]}]} and repairs
    with pytest.raises(ValueError):s.decode_json('{"id":"unfinished')

def test_foreign_source_id_rejected():
    cs,_=s.r.cases_queries();j=s.inventory_job('inventory_probe',0,['AXV2C_0093_01'],cs)
    d={'items':[{'id':'AXV2C_0093_01','ops':[['DIAGNOSE','analyze','defects','causes','FOREIGN']]}]}
    with pytest.raises(AssertionError):s.inventory_validate(json.dumps(d),j)

def test_semantic_hold_prevents_generation():
    assert s.api.read_json(s.OUT/'halt.json')['active']
    assert s.api.read_json(s.OUT/'probe_gate.json')['passed'] is False

def test_three_repeats_remain_planned_not_executed():
    jobs=s.phase_jobs(s.base_plan(),'views','claude')
    assert len(jobs)==30 and {j['repeat'] for j in jobs}=={1,2,3}
    assert not list((s.OUT/'results').rglob('views_*.json'))
