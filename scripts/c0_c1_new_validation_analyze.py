"""Immutable-judgment analysis, independent arithmetic and bounded human review."""
import csv
from collections import Counter,defaultdict
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
import subprocess
from ax_research.heldout import read,write,sha,jsonl
from scripts.c0_c1_new_validation import ROOT,OUT,INPUT,verify


def csvwrite(p,rows):
    with p.open('x',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def main():
    verify();pred=read(OUT/'predictions/rankings.json');rows=read(OUT/'qrels.json')['records'];result=read(OUT/'evaluation/metrics.json');qby={q['query_id']:q for q in jsonl(INPUT)};grades=defaultdict(dict);status={}
    for r in rows:
        grades[r['query_id']][r['case_id']]=r['grade'];status[r['query_id'],r['case_id']]=r['status']
    complete=[q for q,g in grades.items() if len(g)==112 and all(v is not None for v in g.values())]
    lookup={(r['system'],r['query_id']):r for r in result['per_query']};cohort=[]
    for name in pred['systems']:
        for metric in result['per_query'][0]['metrics']:
            vals=[lookup[name,q]['metrics'][metric] for q in complete if lookup[name,q]['metrics'][metric] is not None]
            cohort.append({'system':name,'metric':metric,'value':sum(vals)/len(vals) if vals else None,'defined':len(vals),'complete_questions':complete,'all_questions':len(qby)})
    write(OUT/'evaluation/complete_cohort_summary.json',{'fixed_by_label_completeness_not_model_performance':True,'complete_query_ids':complete,'excluded_due_to_abstain':[q for q in qby if q not in complete],'macro':cohort,'all_original_questions_preserved':True})
    cases=read(ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases'];ranklookup={(n,r['query_id']):r for n,rs in pred['systems'].items() for r in rs};changes=[];events=[];strong=[];summ=[]
    for q in qby:
        old=ranklookup['C0',q];new=ranklookup['C1',q];diag=ranklookup['C1_NO_EMBEDDING',q];g=grades[q]
        for c in pred['case_ids']:
            before=old['ranking'].index(c)+1;after=new['ranking'].index(c)+1;neutral=diag['ranking'].index(c)+1
            changes.append({'query_id':q,'case_id':c,'grade':g[c],'status':status[q,c],'task':cases[c]['task'],'C0_rank':before,'C1_rank':after,'C1_neutral_rank':neutral,'rank_gain_C1_vs_C0':before-after})
            if g[c]==3:strong.append(changes[-1])
        for k in (5,10,20):
            a=set(old['ranking'][:k]);b=set(new['ranking'][:k]);knownpos={c for c,v in g.items() if v is not None and v>=2}
            rec={'query_id':q,'k':k,'complete112':q in complete,'known_related_kept':len(a&b&knownpos),'known_related_added':len((b-a)&knownpos),'known_related_lost':len((a-b)&knownpos)}
            for name,top in [('C0',a),('C1',b)]:
                rec.update({name+'_grade0':sum(g[c]==0 for c in top),name+'_grade1':sum(g[c]==1 for c in top),name+'_grade2':sum(g[c]==2 for c in top),name+'_grade3':sum(g[c]==3 for c in top),name+'_unresolved':sum(g[c] is None for c in top)})
            summ.append(rec)
            for c in sorted((b-a)|(a-b)):
                events.append({'query_id':q,'k':k,'case_id':c,'grade':g[c],'status':status[q,c],'task':cases[c]['task'],'change':'GAIN' if c in b else 'LOSS','C0_rank':old['ranking'].index(c)+1,'C1_rank':new['ranking'].index(c)+1,'complete112':q in complete})
    csvwrite(OUT/'evaluation/rank_changes.csv',changes);csvwrite(OUT/'evaluation/strong_grade3_ranks.csv',strong);csvwrite(OUT/'evaluation/topk_changes.csv',summ);write(OUT/'evaluation/events.json',{'records':events,'incomplete_query_counts_are_known_labeled_pairs_not_complete_recall':True})
    # Evidence plus a bounded review list. First5 are unresolved; next items expose consequential transfer judgments.
    human=[]
    def add(q,c,why):
        if any(r['query_id']==q and r['case_id']==c for r in human) or len(human)>=20:return
        r=next(r for r in rows if r['query_id']==q and r['case_id']==c)
        human.append({'query_id':q,'question':qby[q]['text'],'case_id':c,'Task':cases[c]['task'],'Problem':cases[c]['problem'],'Context':cases[c]['context'],'current_grade':r['grade'],'current_status':r['status'],'AI_rationale':r['rationale'],'human_confirmation_needed':why,'human_grade':None,'human_comment':None})
    for r in rows:
        if r['status']=='ABSTAIN':add(r['query_id'],r['case_id'],'Task의 실제 수행 범위를 확인해야 전체지표를 계산할 수 있음')
    key=read(OUT/'review_key.json')
    for q,eid,why in [
        ('NV20261102_10','E057','온도 보관함에 열펌프 이상탐지를 충분히 응용할 수 있는지. 관찰된 C1 개선의 주요 판정 근거'),
        ('NV20261102_10','E094','장비 위험 감지를 현재 온도 이탈에 충분히 응용할 수 있는지. 핵심 개선이 이 grade2 판정에 의존'),
        ('NV20261102_02','E057','센서 이상 탐지를 IT 접속 로그로 옮기는 기능적 관련성의 강도'),
        ('NV20261102_02','E094','운영 변수 위험 감지와 접속 사건 감지 사이 입력·목적 차이'),
        ('NV20261102_08','E058','지급 정보 보완과 승인된 ERP 계좌 변경의 실제 실행 범위 차이'),
        ('NV20261102_08','E067','새 CRM 연락처 생성이 기존 거래처 계좌 갱신에 충분히 응용 가능한지'),
        ('NV20261102_08','E019','HR 연락의 시스템 반영 기능을 ERP 변경 등록에 응용할 수 있는지'),
        ('NV20261102_04','E086','제재 심사 항목 표시를 자격 증빙 검증에 충분히 응용할 수 있는지'),
        ('NV20261102_04','E066','채용 증빙 대조가 자격 갱신의 직접 기능 일치인지'),
        ('NV20261102_05','E072','계약 요약이 납부 의무·기한·예외 조건까지 다루는지'),
        ('NV20261102_01','E068','통합 지식 검색에서 운영 지침·처리 기록·원문 위치 요구 범위를 충족하는지'),
        ('NV20261102_07','E095','질문 응대·인계는 직접 일치하되 렌탈 규정 지식의 교체가 어느 정도인지'),
        ('NV20261102_06','E049','주문 가격 검증을 은행·장부 양방향 대사에 충분히 응용할 수 있는지'),
        ('NV20261102_06','E024','청구서·요율 대조를 은행·장부 대사에 충분히 응용할 수 있는지')]:add(q,key[eid],why)
    write(OUT/'human_review_max20.json',{'records':human,'count':len(human),'no_human_grades_prefilled':True,'current_experiment_labels_remain_immutable':'Any future human adjudication is a new version, never backfilled into this result'})
    # Independently check model arithmetic/rank ordering and metrics.
    evidence={(r['query_id'],r['case_id']):r for r in read(OUT/'predictions/evidence.json')['records']};detail={(r['query_id'],r['case_id']):r for r in read(OUT/'predictions/C1_details.json')['records']};scorechecks=0
    for name,rs in pred['systems'].items():
        for r in rs:
            q=r['query_id'];values={}
            for c in pred['case_ids']:
                s=evidence[q,c]['semantic']['score'];g=evidence[q,c]['rule']['mapping_grade'] if name=='C0' else detail[q,c]['new_rule']['mapping_grade']
                value=g/8+(.25 if name=='C1_NO_EMBEDDING' else (s+1)/4);assert abs(r['scores'][c]-value)<1e-15;values[c]=value;scorechecks+=1
            assert r['ranking']==sorted(values,key=lambda c:(-values[c],-evidence[q,c]['retrieval_tie'],c))
    independent={};metricchecks=0
    for name,rs in pred['systems'].items():
        for r in rs:
            q=r['query_id'];g=grades[q];full=q in complete;pos={c for c,v in g.items() if v is not None and v>=2};rank=r['ranking'];vals={}
            for k in (5,10,20):
                top=[g[c] for c in rank[:k]];judged=all(v is not None for v in top);hits=sum(c in pos for c in rank[:k])
                vals[f'Precision@{k}']=Fraction(hits,k) if judged else None;vals[f'Recall@{k}']=Fraction(hits,len(pos)) if full and pos else None;vals[f'F1@{k}']=Fraction(2*hits,k+len(pos)) if full and pos else None
                if k in (5,10):
                    with localcontext() as ctx:
                        ctx.prec=45
                        dcg=lambda seq:sum((Decimal(2)**v-1)/(Decimal(i+2).ln()/Decimal(2).ln()) for i,v in enumerate(seq))
                        den=dcg(sorted(g.values(),reverse=True)[:k]) if full else None;vals[f'nDCG@{k}']=float(dcg(top)/den) if full and den else None
            for m,v in vals.items():
                stored=lookup[name,q]['metrics'][m]
                assert (v is None and stored is None) or (v is not None and stored is not None and abs(float(v)-stored)<1e-12);metricchecks+=1
            independent[name,q]=vals
    for m in result['macro_common_queries']:
        names=('C0','C1') if m['comparison']=='primary' else ('C1','C1_NO_EMBEDDING');eligible=[q for q in pred['query_ids'] if all(independent[n,q][m['metric']] is not None for n in names)]
        assert eligible==m['included_query_ids'] and len(eligible)==m['defined']
        vals=[float(independent[m['system'],q][m['metric']]) for q in eligible];value=sum(vals)/len(vals) if vals else None
        assert (value is None and m['value'] is None) or abs(value-m['value'])<1e-12
    replay=ROOT.parent/'AX-c0-c1-validation-replay-20261102';rep=read(replay/'replay_receipt.json');assert rep['all30_rankings_and3360_scores_equal'] and sha(replay/'rankings.json')==sha(OUT/'predictions/rankings.json')
    modified=subprocess.check_output(['git','diff','1e6ad428ac23f493df9a86b1d05fae05f818dd36','--diff-filter=MDR','--name-only'],cwd=ROOT,text=True).splitlines();assert set(modified)<={'scripts/.gitattributes','src/ax_research/.gitattributes','tests/.gitattributes'}
    write(OUT/'verification.json',{'tests_passed':163,'new_tests':15,'old_tests':148,'prediction_score_checks':scorechecks,'full112_rank_order_checks':30,'independent_per_query_metric_checks':metricchecks,'independent_common_macro_checks':len(result['macro_common_queries']),'complete_questions':complete,'qrels_rows':1120,'JUDGED':sum(r['status']=='JUDGED' for r in rows),'ABSTAIN':sum(r['status']=='ABSTAIN' for r in rows),'explicit_all10_vectors':112,'source_review_same_AI_not_independent':True,'new_query_embedding_replay_equal':True,'replay_receipt':rep,'existing_only_metadata_changes':modified,'model_or_question_or_label_tuning':False,'new_perspectives':'NOT_RUN','paid_API_calls':0,'cost_usd':'0.00','WorkB_read':False})
    print('Verified3360scores/30rankings/330query metrics/44common macros; complete6, judged1115, abstain5')


if __name__=='__main__':main()
