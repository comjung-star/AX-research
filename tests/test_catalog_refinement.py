import unittest

from ax_research.catalog_refinement import fixed_scope, fixed_requirements, repaired_recommend, parse_fit, refined_outputs
from scripts.pilot_case_recommendation import inputs
from scripts.improvement_cycle import read


class CatalogRefinementTests(unittest.TestCase):
    def setUp(self):
        self.catalog,self.rules,self.profiles,self.registry=inputs()

    def test_propose_is_not_a_negative_but_real_prohibition_remains(self):
        clauses=fixed_scope('담당 부서를 제안하고 싶습니다. 자동 등록은 안 합니다. 금액을 수정하지 마세요.')
        self.assertEqual(clauses[0]['role'],'requested')
        self.assertEqual([c['role'] for c in clauses[1:]],['excluded','excluded'])

    def test_transcript_text_does_not_require_audio_but_live_voice_does(self):
        for text,voice in [('통화 녹취 텍스트에서 항목을 추출해주세요.',False),
                           ('음성 통화 녹취 텍스트에서 항목을 추출해주세요.',False),
                           ('음성 파일에서 항목을 추출해주세요.',True),
                           ('통화 녹취 텍스트를 정리하고 음성 문의에 응답해주세요.',True)]:
            r=fixed_requirements(text,{'clauses':fixed_scope(text),'constraints':[]},self.profiles)
            self.assertEqual('voice' in r['inputs'],voice,text)

    def test_known_scope_failure_is_repaired_without_changing_saved_llm_choice(self):
        normalized=read('docs/llm-catalog-retrieval-comparison-20261109/selections.json')['VQ020']
        result=repaired_recommend(normalized['question'],normalized,self.catalog,self.rules,self.profiles,self.registry,
            lambda p,q,ids:{c:.1 for c in ids})
        self.assertIn('P02',result['branches'])
        self.assertFalse(result['perspective_selection']['adapter_review_required'])

    def test_fit_needs_literal_query_and_performed_task_evidence(self):
        ids=['AXV24_98092b8ca357'];q='상품 정보 파일의 항목을 정리해주세요.'
        task=self.registry[ids[0]]['task']
        row={'position':0,'fit':2,'status':'SUPPORTED','reason':'실제 항목 추출','query_quote':'항목을 정리',
             'evidence':[{'field':'task','quote':task}]}
        self.assertEqual(parse_fit({'rows':[row]},q,ids,self.registry)[ids[0]]['fit'],2)
        row['evidence']=[{'field':'problem','quote':self.registry[ids[0]]['problem']}]
        with self.assertRaises(ValueError):parse_fit({'rows':[row]},q,ids,self.registry)

    def test_auxiliary_or_unknown_case_is_not_used_to_fill_five(self):
        ids=list(self.profiles['cases'])
        normalized=read('docs/llm-catalog-selector-20261109/normalized-selections.json')['D05']
        repaired=repaired_recommend(normalized['question'],normalized,self.catalog,self.rules,self.profiles,self.registry,
            lambda p,q,ids:{c:.1 for c in ids})
        fits={c:{'fit':1,'status':'UNSUPPORTED'} for c in ids}
        r=refined_outputs(normalized['question'],normalized,repaired,fits,ids,self.profiles,{c:.1 for c in ids})
        for s in ('F_StrictFit','G_WidenedFit','H_GlobalFit'):self.assertEqual(r[s]['ranking'],[])
        c=next(iter(repaired['branches']['P03']))['case_id']
        fits[c]={'fit':3,'status':'CONDITION_UNKNOWN'}
        r=refined_outputs(normalized['question'],normalized,repaired,fits,ids,self.profiles,{c:.1 for c in ids})
        self.assertFalse(r['G_WidenedFit']['ranking'])

    def test_widened_can_recover_case_outside_view_and_preserves_origin(self):
        ids=list(self.profiles['cases']);q='청구서 금액을 계약과 대조해주세요.'
        normalized=read('docs/llm-catalog-selector-20261109/normalized-selections.json')['D05']
        q=normalized['question']
        repaired=repaired_recommend(q,normalized,self.catalog,self.rules,self.profiles,self.registry,lambda p,q,ids:{c:.1 for c in ids})
        fits={c:{'fit':0,'status':'UNSUPPORTED'} for c in ids}
        outside='AXALL_US_OMB_2025_01589'
        fits[outside]={'fit':2,'status':'SUPPORTED'}
        r=refined_outputs(q,normalized,repaired,fits,ids,self.profiles,{c:.1 for c in ids})
        self.assertFalse(r['F_StrictFit']['ranking'])
        self.assertEqual(r['G_WidenedFit']['ranking'],[outside])
        self.assertEqual(r['G_WidenedFit']['origins'][outside],['GLOBAL'])

    def test_zero_to_twenty_candidate_budget_and_deduplication(self):
        ids=list(self.profiles['cases']);normalized=read('docs/llm-catalog-selector-20261109/normalized-selections.json')['D11']
        q=normalized['question'];repaired=repaired_recommend(q,normalized,self.catalog,self.rules,self.profiles,self.registry,lambda p,q,ids:{c:.1 for c in ids})
        r=refined_outputs(q,normalized,repaired,{c:{'fit':2,'status':'SUPPORTED'} for c in ids},ids,self.profiles,{c:.1 for c in ids})
        self.assertLessEqual(len(r['G_WidenedFit']['ranking']),5)
        self.assertEqual(len(r['G_WidenedFit']['ranking']),len(set(r['G_WidenedFit']['ranking'])))
        self.assertLessEqual(len(r['G_WidenedFit']['candidates']),20)
