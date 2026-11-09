import json
from ax_research.perspective_boundary import corrected_request
from ax_research.perspective_panels import request_body

def test_card_boundaries_actually_cross_request_boundary_without_changing_legacy():
    card={'id':'P01','name':'search','definition':'Retrieve existing knowledge','unknown':['access not confirmed'],
          'include_if':['Actual knowledge retrieval'],'exclude_if':['Not the instruction to find case studies'],
          'links':[{'status':'SUPPORTED_FOR_PILOT','supported_scope':'Document reference'}]}
    c={'cards':[card]};system,p=corrected_request('Find examples of stock forecasting.',c)
    assert p['perspectives'][0]['include_if']==card['include_if']
    assert p['perspectives'][0]['exclude_if']==card['exclude_if']
    assert p['perspectives'][0]['limits']==card['unknown']
    assert 'exclude_if' not in json.loads(request_body('q',c)['messages'][0]['content'])['perspectives'][0]
    assert '사례를 찾고 싶다' in system
