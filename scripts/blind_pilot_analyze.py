"""Human-only pooled evaluation. Missing/held labels are never zero."""
import argparse
import csv
import math
import posixpath
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from scripts import blind_pilot_five as p

NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def read_xlsx(path):
    with zipfile.ZipFile(path) as z:
        wb=ET.fromstring(z.read('xl/workbook.xml'));sheet=next(s for s in wb.findall('x:sheets/x:sheet',NS) if s.attrib['name']=='평가표')
        rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));target=next(r.attrib['Target'] for r in rels if r.attrib['Id']==rid)
        target=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():shared=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('x:si',NS)]
        rows=[]
        for row in ET.fromstring(z.read(target)).findall('x:sheetData/x:row',NS):
            cells={}
            for cell in row.findall('x:c',NS):
                if cell.find('x:f',NS) is not None:raise ValueError('평가표에는 수식 대신 직접 입력한 점수를 사용하세요.')
                col=''.join(c for c in cell.attrib['r'] if c.isalpha());i=0
                for letter in col:i=i*26+ord(letter)-64
                typ=cell.attrib.get('t');val=cell.find('x:v',NS)
                if typ=='s':text=shared[int(val.text)] if val is not None else ''
                elif typ=='inlineStr':text=''.join(t.text or '' for t in cell.findall('.//x:t',NS))
                else:text=val.text if val is not None else ''
                cells[i-1]=text
            if any(cells.values()):rows.append([cells.get(i,'') for i in range(max(8,max(cells,default=7)+1))])
    if not rows or rows[0]!=p.CFG['blind_fields']:raise ValueError('평가표 헤더가 원본과 다릅니다.')
    if any(len(r)!=8 for r in rows[1:]):raise ValueError('평가표에는 원본8열만 사용하세요.')
    return [dict(zip(rows[0],r)) for r in rows[1:]]

def read_review(path):
    if path.suffix.lower()=='.xlsx':return read_xlsx(path)
    with path.open(encoding='utf-8-sig',newline='') as s:
        reader=csv.DictReader(s)
        if reader.fieldnames!=p.CFG['blind_fields']:raise ValueError('CSV헤더가 원본과 다릅니다.')
        return list(reader)

def grade(value):
    value='' if value is None else str(value).strip()
    if not value:return None,'UNASSESSED'
    if value in ('판단 보류','판단보류','보류','HOLD'):return None,'HELD'
    try:number=float(value)
    except ValueError:raise ValueError('점수는0/1/2/3 또는 판단 보류로 입력하세요.') from None
    if not math.isfinite(number) or number not in (0,1,2,3):raise ValueError('허용되지 않은 점수: '+value)
    return int(number),'SCORED'

def ndcg(ranking,labels,pool,k):
    if any(labels.get(cid) is None for cid in pool|set(ranking[:k])):return None
    gains=lambda seq:sum((2**v-1)/math.log2(i+2) for i,v in enumerate(seq))
    ideal=gains(sorted((labels[c] for c in pool),reverse=True)[:k])
    if ideal==0:return None
    return gains([labels[c] for c in ranking[:k]])/ideal

def analyze(rows,public,key,predictions):
    originals={r['평가 ID']:r for r in public};index={};labels=defaultdict(dict);states=defaultdict(dict)
    for row in rows:
        eid=row['평가 ID']
        if eid in index or eid not in originals:raise ValueError('중복 또는 알 수 없는 평가 ID입니다.')
        for field in p.CFG['blind_fields'][:6]:
            if (row.get(field) or '').replace('\r\n','\n')!=originals[eid][field].replace('\r\n','\n'):raise ValueError('원본 설명/ID는 변경하지 마세요: '+eid)
        index[eid]=row
    if set(index)!=set(originals):raise ValueError('원본 평가 행이 누락됐습니다. 삭제한 행을 복원하세요.')
    judged=[]
    for link in key:
        q=link['qid'];cid=link['case_id'];row=index[link['evaluation_id']];v,status=grade(row['관련성 점수']);labels[q][cid]=v;states[q][cid]=status
        judged.append({'evaluation_id':link['evaluation_id'],'qid':q,'case_id':cid,'human_grade':v,'status':status,'comment':row.get('평가 의견',''),'unknown33':link['unknown33']})
    metrics=[];details=[];ranked_relevant=[]
    for model,qs in predictions.items():
        for row in qs:
            q=row['qid'];ranking=row['ranking'];pool=set(labels[q])
            for k in (5,10):
                selected=ranking[:k];missing=[cid for cid in selected if labels[q].get(cid) is None]
                precision=None if missing else sum(labels[q][c]>=2 for c in selected)/k
                metrics.append({'model':model,'qid':q,'k':k,'precision':precision,'precision_topk_scored':k-len(missing),'nDCG_judged_pool':ndcg(ranking,labels[q],pool,k),'pool_size':len(pool),'pool_scored':sum(v is not None for v in labels[q].values()),'pending_topk_ids':missing})
            ranked_relevant.extend({'model':model,'qid':q,'case_id':cid,'rank':i+1,'human_grade':labels[q][cid]} for i,cid in enumerate(ranking) if labels[q].get(cid) is not None and labels[q][cid]>=2)
    summary=[]
    for model in 'ABC':
        for k in (5,10):
            item={'model':model,'k':k,'question_count':5}
            for metric in ('precision','nDCG_judged_pool'):
                values=[m[metric] for m in metrics if m['model']==model and m['k']==k and m[metric] is not None]
                item[metric+'_available_questions']=len(values)
                item[metric+'_official_macro']=sum(values)/5 if len(values)==5 else None
                item[metric+'_partial_mean']=sum(values)/len(values) if values else None
            summary.append(item)
    by={s:{r['qid']:r['ranking'] for r in rs} for s,rs in predictions.items()}
    for q,lab in labels.items():
        for model in ('B','C'):
            for k in (5,10):
                a=set(by['A'][q][:k]);b=set(by[model][q][:k]);relevant={cid for cid,v in lab.items() if v is not None and v>=2}
                wrong=[c for c in by[model][q][:k] if lab.get(c) is not None and lab[c]<2]
                details.append({'qid':q,'model':model,'reference':'A','k':k,'observed_new_relevant':sorted((b-a)&relevant),'observed_lost_relevant':sorted((a-b)&relevant),'observed_retained_relevant':sorted(a&b&relevant),'observed_nonrelevant_in_topk':wrong,'comparison_complete':all(lab.get(c) is not None for c in a|b)})
    scored=sum(x['status']=='SCORED' for x in judged);held=sum(x['status']=='HELD' for x in judged)
    return {'status':'HUMAN_EVALUATION_COMPLETE' if scored==len(judged) else 'AWAITING_OR_PARTIAL_HUMAN_EVALUATION','human_scored_pairs':scored,'held_pairs':held,'unassessed_pairs':len(judged)-scored-held,'metrics':metrics,'macro':summary,'judged_records':judged,'related_ranks_in_judged_pool':ranked_relevant,'comparisons':details,'recall':'NOT_COMPUTED_FULL112_UNJUDGED','ndcg_scope':'IDCG from full judged question pool (unionTop10+diagnostic extras), not corpus-wide relevance','improvement_conclusion':'PENDING_HUMAN_EVALUATION' if scored==0 else 'Inspect complete per-query human metrics; purposeful pilot, not independent generalization.'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('review',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('기존 분석 파일을 덮어쓰지 않습니다. 새 출력 이름을 지정하세요.')
    public=p.read(p.OUT/'evaluator/review_rows.json')['rows'];key=p.read(p.OUT/'analyst/evaluation_key.json')['records'];pred=p.read(p.OUT/'analyst/predictions.json')['systems']
    result=analyze(read_review(args.review),public,key,pred)
    result['provenance']={'review_file':args.review.name,'review_sha256':p.sha(args.review),'prediction_sha256':p.sha(p.OUT/'analyst/predictions.json'),'evaluation_key_sha256':p.sha(p.OUT/'analyst/evaluation_key.json'),'analyzer_sha256':p.sha(Path(__file__)),'human_relevance_threshold':2,'gain':'2**grade-1','ndcg_normalizer':'complete judged question pool, not full112'}
    result['unknown33_relevant_ranks']=[x for x in result['related_ranks_in_judged_pool'] if any(k['qid']==x['qid'] and k['case_id']==x['case_id'] and k['unknown33'] for k in key)]
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes((__import__('json').dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print({'status':result['status'],'human_scored_pairs':result['human_scored_pairs'],'held_pairs':result['held_pairs'],'unassessed_pairs':result['unassessed_pairs']})

if __name__=='__main__':main()
