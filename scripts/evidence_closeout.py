"""Offline closeout: preserve failed semantic probes and prohibit further calls."""
import json
from collections import Counter
from decimal import Decimal
from scripts import evidence_split as s

def main():
    costs={}
    for p in s.CFG['models']:
        actual=Decimal(0);unknown=Decimal(0);states=Counter();tokens=Counter()
        for root in (s.BASE,s.V12,s.OUT):
            for f in (root/'attempts'/p).glob('*.json'):
                d=s.api.read_json(f);states[d.get('state','unknown')]+=1
                u=d.get('usage') or {}
                if u.get('usage_cost_usd') is not None:actual+=Decimal(u['usage_cost_usd'])
                else:unknown+=Decimal(d.get('reserved_usd','0'))
                for k in ('actual_input_tokens','actual_output_tokens_including_thinking','cached_input_tokens'):
                    tokens[k]+=u.get(k,0) or 0
        costs[p]={'usage_based_usd':s.api.money(actual),'unconfirmed_reserved_usd':s.api.money(unknown),'conservative_usd':s.api.money(s.spent(p)),'tokens':dict(tokens),'attempt_states':dict(states)}
    rows=[]
    for p in s.CFG['models']:
        for f in sorted((s.OUT/'results'/p).glob('match_probe*.json')):
            d=s.api.read_json(f)
            rows.append({'provider':p,'job':f.stem,'valid_structure':d['validation']['valid'],'scores':{k:v['score'] for k,v in d['validation']['derived'].items()},'source':str(f.relative_to(s.r.ROOT)).replace('\\','/')})
    result={'status':'HOLD_SEMANTIC_VALIDITY','human_gold':False,'base_commit':'2449542a6ae3b5488556c848687088fadf466fac','branch':'research/stage123-evidence-rules-20261027','completed':{'inventory_probe_requests':9,'match_probe_requests':len(rows),'match_probe_scores':sum(len(x['scores']) for x in rows),'unique_match_probe_pairs':4,'pilot_case_profiles_per_provider':18},'not_executed':['36-pair pilot matching / 108 results','Stage1 3360 new scores','Stage2 retrieval','Stage3 retrieval and 90 perspective generations','Stage4 sealed'], 'costs':costs,'claude_prior_conservative_usd':'0.787382','claude_balance_conservative_usd':s.api.money(Decimal('5')-Decimal('0.787382')-s.spent('claude')),'safety_buffer_usd':'0.50','probes':rows,'blocking_evidence':{'source':'query-blind-v13/results/openai/match_probe_0001.json','case':'AXV2C_0093_01','incorrect_target':'INTEGRATE_PRODUCTION_DATA','actual_quote':'Analyze production quality defects','model_reason':'Analyzes production quality defects and their root causes.','computed_score':4,'finding':'A genuine diagnosis operation was linked to data integration. Literal source existence and correct numeric IDs do not establish functional equivalence. This is an unsupported functional mapping, not merely inter-model disagreement. The case may still be relevant through diagnosis; its wrong route must not be approved.'},'limitations':['Probe batches overlap: 21 scores are not 21 independent pairs.','9/9 JSON results does not imply semantic validity.','Claude schema error absent in simple JSON probes, not a guarantee for all future requests.','Cost is token-price accounting plus conservative reservations, not a billing-console balance.','No human Gold or validated Silver released.']}
    s.save(s.OUT/'halt.json',{'active':True,'reason':'SEMANTIC_FUNCTION_LINK_FAILURE','no_unknown_replay':True})
    s.save(s.OUT/'probe_gate.json',{'passed':False,'structural_requests_passed':9,'semantic_passed':False,'reason':'Source-grounded diagnosis incorrectly connected to data integration; full pilot and downstream stages prohibited.'})
    s.save(s.BASE/'final_status.json',result)
    print(json.dumps({k:result[k] for k in ('status','completed','costs','claude_balance_conservative_usd')},ensure_ascii=False))

if __name__=='__main__':main()
