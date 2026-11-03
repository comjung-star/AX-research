"""Apply predeclared uncertainty holds; preserve raw labels and all prior analyses."""
import copy
from collections import Counter
from ax_research.heldout import read,write,jsonl,sha
from scripts.heldout_resume_api import OUT,PRIVATE,PAYLOAD
from scripts.heldout_resume_evaluate import score


def main():
    labels=copy.deepcopy(read(PRIVATE/'qrels_completed_v2.json')['records']);by={(r['query_id'],r['case_id']):r for r in labels};original={(r['query_id'],r['case_id']):r for r in jsonl(PAYLOAD/'qrels.jsonl')};holds={}
    for r in read(OUT/'quality_review.json')['source_cautious_ABSTAIN_pairs']:holds[r['query_id'],r['case_id']]=r['reason']
    # Predeclared blind crosscheck: unresolved binary differences are held,
    # never accepted by majority and never chosen using retrieval performance.
    for r in read(OUT/'evaluation/new_label_crosscheck.json')['records']:
        if r['binary_disagreement'] is True or r['grade'] is None:holds[r['query_id'],r['case_id']]='Unresolved blind first/recheck relevance-boundary disagreement; retain ABSTAIN, do not pick a model score'
    for k,reason in holds.items():
        assert original[k]['status']=='UNJUDGED';by[k].update(status='ABSTAIN',grade=None,rationale=reason)
    for k,r in original.items():
        if r['status']=='JUDGED':assert by[k]==r
    write(PRIVATE/'qrels_final_cautious_v4.json',{'records':labels,'source':'AI-Silver; uncertainty holds; not Human-Gold','raw_version_sha256':sha(PRIVATE/'qrels_completed_v2.json')})
    d=OUT/'quality_final';d.mkdir(exist_ok=False);pred=read(OUT/'predictions/rankings.json');write(d/'metrics.json',score(pred,labels))
    write(d/'label_manifest.json',{'version':'source-cautious-v4','total':1680,'new1635_all_evaluated':True,'counts':dict(Counter(r['status'] for r in labels)),'grade_counts':dict(Counter(str(r['grade']) for r in labels)),'holds':[{'query_id':q,'case_id':c,'reason':reason} for (q,c),reason in holds.items()],'full_question_ids':[q for q in sorted({r['query_id'] for r in labels}) if all(r['status']=='JUDGED' for r in labels if r['query_id']==q)],'original45_preserved':True,'no_primary_or_previous_results_overwritten':True,'selection_uses_performance':False,'rule':'union of source-cautious holds and predeclared blind binary-disagreement holds; not new threshold or model policy','human_verified':False,'private_full_sha256':sha(PRIVATE/'qrels_final_cautious_v4.json')})
    write(d/'complete.json',{'complete':True,'prediction_seal_sha256':sha(OUT/'predictions/complete.json'),'files':{p.name:sha(p) for p in d.iterdir()},'model_tuned':False})


if __name__=='__main__':main()
