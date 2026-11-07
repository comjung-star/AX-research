"""Recover complete, unchanged fenced JSON from saved replies, without rerolls."""
import argparse
from pathlib import Path
from ax_research.heldout import read, write, sha
from scripts import evaluator_abc as run


def recover(provider,output=None,offline_only=True):
    run.configure(provider)
    output=Path(output) if output is not None else run.OUT/provider/'recovery-v2'
    output.mkdir(parents=True,exist_ok=False)
    original_request=run.request
    log=[]
    def saved_request(identifier,prompt,payload,limit,validator):
        original=run.OUT/provider/'results'/(identifier+'.json')
        if original.exists():
            old=read(original)
            assert old['prompt_payload_sha256']==run.transport.digest({'prompt':prompt,'payload':payload}), 'RECOVERY_INPUT_CHANGED'
            # Previously valid responses are retained; never choose an earlier
            # alternative grade merely because the new decoder can read it.
            if old['valid']:
                return old
            parsed_failure=None
            for attempt in old['attempts']:
                name=attempt['id'].removeprefix(provider+'_')
                data,failure=run.read_attempt(provider,name)
                if failure is None:
                    try:failure=validator(data)
                    except (AssertionError,KeyError,TypeError,ValueError):failure='INVALID_SCHEMA'
                log.append({'component':identifier,'attempt':attempt['id'],
                    'original_failure':attempt['failure'],'new_failure':failure,
                    'raw_sha256':sha(run.OUT/provider/'api'/(attempt['id']+'_response.json'))
                    if (run.OUT/provider/'api'/(attempt['id']+'_response.json')).exists() else None,
                    'new_API_call':False,'unchanged_JSON_only':True})
                if failure is None:
                    return {**old,'data':data,'valid':True,'failure':None,
                            'recovered_from':attempt['id'],'original_result_path':str(original.relative_to(run.ROOT)),
                            'local_decode_recovery_only':True}
                if data is not None and parsed_failure is None:
                    # A now-readable complete JSON may still fail its evidence
                    # checks. Report the real remaining failure, not INVALID_JSON.
                    parsed_failure={**old,'data':data,'valid':False,'failure':failure,
                        'decoded_from':attempt['id'],'original_failure':old['failure'],
                        'local_decode_recovery_only':True}
            if parsed_failure is not None:return parsed_failure
            return old
        # Only a previously unexecuted dependent judge may be resumed. A valid
        # unfavorable grade or semantic failure never reaches this branch.
        assert identifier.startswith('judge_'), 'UNEXPECTED_MISSING_CORE'
        c=payload.get('case_core',{})
        if c.get('execution')!='CONFIRMED' or c.get('action') is None:
            log.append({'component':identifier,'new_API_call':False,
                'action':'Deterministic existing case-core gate: ABSTAIN; dependent judge not required.'})
            data={'id':payload['id'],'grade':None,'status':'ABSTAIN',
                'reason':'사례 단독 추출에서 실제 수행 범위를 확인하지 못해 기존 규칙에 따라 보류합니다.',
                'evidence_ids':[],'new_core_functions':[]}
            if identifier.startswith('judge_C_'):
                data['checks']=dict.fromkeys(('actual_work_known','action_match','object_match','output_match',
                    'direct_core','transfer_core','core_sufficient','auxiliary_only','any_useful_link','temporal_conflict'),False)
            return {'valid':True,'failure':None,'data':data,'attempts':[],
                'local_core_gate_without_new_API':True}
        if offline_only:
            log.append({'component':identifier,'new_API_call':False,
                        'action':'Unexecuted dependent judge remains unavailable in offline replay.'})
            return {'valid':False,'failure':'DEPENDENT_JUDGE_NOT_PREVIOUSLY_EXECUTED',
                    'data':None,'attempts':[],'offline_replay':True}
        log.append({'component':identifier,'new_API_call':True,
                    'action':'Resume previously unexecuted dependent judge after local JSON recovery.'})
        return original_request('postparse_'+identifier,prompt,payload,limit,validator)
    run.request=saved_request
    # Reuse the exact same evaluator/rubric, prompts and original valid cores.
    for stage,items in [('benchmark',read(run.OUT/'benchmark.json')['records']),
                        ('pending',read(run.OUT/'pending_items.json')['records'])]:
        rows=[]
        methods='ABC' if stage=='benchmark' else read(run.OUT/'method_selection.json')['method']
        for item in items:
            for method in methods:
                row=run.evaluate_item(item,method);rows.append(row)
        write(output/(stage+'_recovered_results.json'),{'records':rows,
            'human_approved':False,'no_original_files_overwritten':True,'local_decode_recovery':True})
    write(output/'local_recovery_log.json',{'records':log,
        'paid_semantic_rerolls':0,'relevance_prompts_changed':False})
    print(provider,'local recovery records',len(log),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--provider',choices=list(run.CAPS),required=True)
    p.add_argument('--output',type=Path)
    p.add_argument('--resume-unexecuted',action='store_true',help='Explicitly allow a never-executed dependent judge, within original provider budget.')
    args=p.parse_args();recover(args.provider,args.output,not args.resume_unexecuted)
