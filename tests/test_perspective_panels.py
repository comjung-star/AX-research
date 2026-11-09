import copy
import unittest

from ax_research.perspective_panels import normalize,build_panels,from_legacy,request_body
from scripts.pilot_case_recommendation import inputs
from scripts.improvement_cycle import read


def fixture_selection(f,catalog):
    selected={d['id']:d for d in f['selected']}
    decisions=[]
    for card in catalog['cards']:
        p=card['id']
        decisions.append({'id':p,'status':'SELECTED' if p in selected else 'NOT_SELECTED',
            'relation':selected.get(p,{}).get('relation','NONE'),
            'anchor_quote':selected.get(p,{}).get('anchor_quote',''),
            'bridge_reason':selected.get(p,{}).get('bridge_reason','이 동작 예시에서 선택하지 않은 관점입니다.'),
            'assumptions':selected.get(p,{}).get('assumptions',[]),'missing_information':[]})
    return normalize(f['question'],{'decisions':decisions,'constraints':f.get('constraints',[]),
        'unsupported_work':f.get('unsupported_work',[])},catalog,'MANUAL_FUNCTIONAL_FIXTURE_NOT_LLM_OUTPUT')


def stable_scores(p,text,ids):
    return {c:.9 if c=='AXALL_US_OMB_2025_01754' else .1 for c in ids}


class PerspectivePanelsTests(unittest.TestCase):
    def setUp(self):
        self.catalog,self.rules,self.profiles,self.registry=inputs()
        self.fixtures={f['id']:f for f in read('configs/perspective_panels_fixtures_20261109.json')['examples']}

    def panel(self,name):
        selection=fixture_selection(self.fixtures[name],self.catalog)
        return build_panels(selection,self.catalog,self.profiles,self.registry,stable_scores)

    def test_one_problem_can_keep_explicit_and_alternative_view_with_assumption(self):
        r=self.panel('alternative_for_one_problem')
        self.assertEqual({p['id'] for p in r['panels']},{'P01','P04'})
        alt=next(p for p in r['panels'] if p['id']=='P01')
        self.assertEqual(alt['relation'],'PROBLEM_HYPOTHESIS')
        self.assertTrue(alt['assumptions']);self.assertFalse(alt['confirmed_problem_cause'])

    def test_alternative_without_stated_assumption_is_rejected(self):
        f=copy.deepcopy(self.fixtures['alternative_for_one_problem']);f['selected'][1]['assumptions']=[]
        with self.assertRaises(ValueError):fixture_selection(f,self.catalog)

    def test_per_view_five_and_no_global_five(self):
        r=self.panel('four_views_no_global_five')
        self.assertEqual([len(p['cases']) for p in r['panels']],[3,5,5,4])
        self.assertEqual(r['counts']['display_slots'],17)
        self.assertGreater(r['counts']['unique_cases'],5)
        self.assertFalse(r['counts']['global_final_cut'])

    def test_shared_case_preserves_both_memberships_and_one_detail(self):
        r=self.panel('shared_case_two_views');c='AXALL_US_OMB_2025_01754'
        self.assertEqual(len([p for p in r['panels'] if any(v['case_id']==c for v in p['cases'])]),2)
        self.assertEqual(len([k for k in r['case_details'] if k==c]),1)
        self.assertEqual({v['perspective_id'] for v in r['case_details'][c]['links']},{'P02','P03'})
        self.assertEqual(r['counts']['shared_memberships'],1)

    def test_condition_notes_stay_in_the_named_branch_and_do_not_drop_references(self):
        r=self.panel('separate_pdf_and_night');p={v['id']:v for v in r['panels']}
        self.assertEqual(len(p['P02']['cases']),5);self.assertEqual(len(p['P04']['cases']),4)
        for row in p['P04']['cases']:
            self.assertFalse(any('질문 조건의 지원 여부는 별도 확인: 보험 청구서 PDF'==v for v in row['conditions_to_check']))
        for row in p['P02']['cases']:
            self.assertFalse(any('질문 조건의 지원 여부는 별도 확인: 야간 고객 문의'==v for v in row['conditions_to_check']))
        self.assertTrue(all(not d['direct_application_confirmed'] for d in r['case_details'].values()))

    def test_explicit_excluded_view_cannot_be_selected(self):
        f=copy.deepcopy(self.fixtures['excluded_search'])
        f['selected'].append({'id':'P01','relation':'PROBLEM_HYPOTHESIS','anchor_quote':'대기가 깁니다',
            'bridge_reason':'잘못된 선택 검사용','assumptions':['가정']})
        with self.assertRaises(ValueError):fixture_selection(f,self.catalog)

    def test_no_view_does_not_run_scorer_or_fill_slots(self):
        f=self.fixtures['outside_catalog'];selection=fixture_selection(f,self.catalog)
        def forbidden(*args):raise AssertionError('No scoring without selected views')
        r=build_panels(selection,self.catalog,self.profiles,self.registry,forbidden)
        self.assertFalse(r['panels']);self.assertEqual(r['counts']['unique_cases'],0)
        self.assertTrue(r['unsupported_work'])

    def test_query_and_source_quotes_are_literal(self):
        r=self.panel('four_views_no_global_five')
        for p in r['panels']:
            e=p['question_anchor'];self.assertEqual(r['question'][e['start']:e['end']],e['quote'])
        for c,d in r['case_details'].items():
            for l in d['links']:
                for e in l['source_evidence']:
                    self.assertEqual(self.registry[c][e['field']][e['start']:e['end']],e['quote'])

    def test_source_corruption_fails_instead_of_claiming_evidence(self):
        catalog=copy.deepcopy(self.catalog)
        link=next(l for l in catalog['cards'][0]['links'] if l['status']=='SUPPORTED_FOR_PILOT')
        link['evidence'][0]['quote']='원문에 없는 문자열'
        selection=fixture_selection(self.fixtures['four_views_no_global_five'],catalog)
        with self.assertRaises(ValueError):build_panels(selection,catalog,self.profiles,self.registry,stable_scores)

    def test_hold_and_excluded_links_never_become_reference_cases(self):
        r=self.panel('four_views_no_global_five')
        for panel in r['panels']:
            card=next(c for c in self.catalog['cards'] if c['id']==panel['id'])
            approved={l['case_id'] for l in card['links'] if l['status']=='SUPPORTED_FOR_PILOT'}
            self.assertTrue({row['case_id'] for row in panel['cases']}<=approved)

    def test_fair_baseline_count_uses_unique_cases_not_display_memberships(self):
        r=self.panel('shared_case_two_views')
        self.assertEqual(r['future_baseline_comparison']['top_k_unique'],len(r['case_details']))
        self.assertLess(r['future_baseline_comparison']['top_k_unique'],r['counts']['display_slots'])
        self.assertFalse(r['future_baseline_comparison']['performed'])

    def test_legacy_actual_outputs_remain_labeled_as_old_policy(self):
        saved=read('docs/llm-catalog-selector-20261109/normalized-selections.json')['D11']
        r=build_panels(from_legacy(saved,self.catalog),self.catalog,self.profiles,self.registry,stable_scores)
        self.assertEqual(len(r['panels']),3)
        self.assertIn('OLD_WORK_MATCHING_POLICY',r['selection_provenance'])
        self.assertFalse(r['relevance_accuracy_verified'])

    def test_prompt_builder_has_no_case_ids_or_reference_grades(self):
        body=request_body('고객 답변이 늦어요.',self.catalog)
        self.assertIn('PROBLEM_HYPOTHESIS',body['system'])
        self.assertNotIn('AXALL_',body['messages'][0]['content'])
        self.assertNotIn('AXV2',body['messages'][0]['content'])
        self.assertNotIn('fit',body['messages'][0]['content'])

    def test_invalid_budget_or_nonfinite_score_is_rejected(self):
        s=fixture_selection(self.fixtures['shared_case_two_views'],self.catalog)
        with self.assertRaises(ValueError):build_panels(s,self.catalog,self.profiles,self.registry,stable_scores,6)
        with self.assertRaises(ValueError):build_panels(s,self.catalog,self.profiles,self.registry,lambda p,q,ids:{c:float('nan') for c in ids})
