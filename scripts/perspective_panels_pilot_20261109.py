"""Offline panel prototype: saved choices/manual fixtures and prompt builder; no API client."""
import argparse
import json

from ax_research.perspective_panels import build_panels,from_legacy,normalize,request_body
from scripts.improvement_cycle import ROOT,read
from scripts.pilot_case_recommendation import inputs,LocalTaskScorer

FIXTURES='configs/perspective_panels_fixtures_20261109.json'
LEGACY='docs/llm-catalog-selector-20261109/normalized-selections.json'


def fixture_selection(f,catalog):
    chosen={d['id']:d for d in f['selected']}
    rows=[]
    for card in catalog['cards']:
        p=card['id'];v=chosen.get(p,{})
        rows.append({'id':p,'status':'SELECTED' if p in chosen else 'NOT_SELECTED',
            'relation':v.get('relation','NONE'),'anchor_quote':v.get('anchor_quote',''),
            'bridge_reason':v.get('bridge_reason','이 수동 동작 예시에서 선택하지 않은 관점입니다.'),
            'assumptions':v.get('assumptions',[]),'missing_information':[]})
    return normalize(f['question'],{'decisions':rows,'constraints':f.get('constraints',[]),
        'unsupported_work':f.get('unsupported_work',[])},catalog,'MANUAL_FUNCTIONAL_FIXTURE_NOT_LLM_OUTPUT')


def selections(catalog):
    result={'manual_'+f['id']:fixture_selection(f,catalog) for f in read(FIXTURES)['examples']}
    result.update({'legacy_'+k:from_legacy(v,catalog) for k,v in read(LEGACY).items()})
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Local reference panels; never sends a paid model request')
    parser.add_argument('--fixture');parser.add_argument('--legacy')
    parser.add_argument('--selection',help='New selector JSON content with decisions/constraints/unsupported_work')
    parser.add_argument('--question');parser.add_argument('--question-file')
    parser.add_argument('--prompt',action='store_true',help='Print a draft request only; do not send it')
    args=parser.parse_args();catalog,_,profiles,registry=inputs()
    question=(ROOT/args.question_file).read_text(encoding='utf-8') if args.question_file else args.question
    if args.prompt:
        if not question:parser.error('Use --question or --question-file')
        print(json.dumps(request_body(question,catalog),ensure_ascii=False,indent=2));raise SystemExit
    if args.fixture:
        f=next(f for f in read(FIXTURES)['examples'] if f['id']==args.fixture)
        selection=fixture_selection(f,catalog)
    elif args.legacy:selection=from_legacy(read(LEGACY)[args.legacy],catalog)
    elif args.selection:
        if not question:parser.error('The selection content requires its original question')
        selection=normalize(question,read(args.selection),catalog,'PROVIDED_SELECTOR_CONTENT_NOT_EXECUTED_BY_THIS_COMMAND')
    else:parser.error('Use --fixture, --legacy, --selection, or --prompt')
    print(json.dumps(build_panels(selection,catalog,profiles,registry,LocalTaskScorer(registry)),ensure_ascii=False,indent=2))
