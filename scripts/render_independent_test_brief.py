"""Render existing-Dev-only chart and two-page meeting brief. No experiment."""
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/independent-test-readiness-2026-10-28'

def chart():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=json.loads((OUT/'dev_chart_data.json').read_text(encoding='utf-8'))['rows']
    fig,(ax,notice)=plt.subplots(1,2,figsize=(10.5,4.3),gridspec_kw={'width_ratios':[3.5,1.8]})
    for off,scope,color,label in [(-.18,'O','#365A86','Original query'),(.18,'D','#BC6C32','Original + perspectives')]:
        vals=[next(r['f1_at5']*100 for r in rows if r['scope']==scope and r['method']==m) for m in 'ABC']
        bars=ax.bar([i+off for i in range(3)],vals,width=.34,color=color,label=label)
        ax.bar_label(bars,labels=[f'{v:.2f}' for v in vals],padding=3,fontsize=9)
    ax.set_xticks(range(3),['A: Rules','B: BGE-M3','C: Combined']);ax.set_ylim(0,60);ax.set_ylabel('Macro F1@5 (%)');ax.set_title('Existing DEV results only',fontweight='bold',pad=15);ax.legend(frameon=False,loc='upper left',fontsize=9)
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    notice.axis('off');notice.text(.04,.8,'INDEPENDENT TEST',fontsize=12,weight='bold');notice.text(.04,.64,'NOT RUN',fontsize=18,color='#A33C37',weight='bold');notice.text(.04,.43,'Verified question/qrel\nbundle not identified.\nNo Test score exists.',fontsize=11,linespacing=1.6);notice.text(.04,.12,'No zero-score bar\nor invented results.',fontsize=10,color='#555555')
    fig.text(.06,.02,'Dev: 10 queries, 18 positive pairs; F1 averaged over 6 positive queries. Same-model AI-Silver, not human Gold.',fontsize=8,color='#555555')
    fig.tight_layout(rect=[0,.06,1,1]);fig.savefig(OUT/'dev_only_performance.png',dpi=170);fig.savefig(OUT/'dev_only_performance.svg');plt.close(fig)
    path=OUT/'dev_only_performance.svg';path.write_text('\n'.join(l.rstrip() for l in path.read_text().splitlines())+'\n',encoding='utf-8')

def pdf():
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader
    pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'));pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
    body=ParagraphStyle('body',fontName='Malgun',fontSize=10,leading=16,spaceAfter=8,wordWrap='CJK',alignment=TA_LEFT)
    heading=ParagraphStyle('heading',parent=body,fontName='MalgunBold',fontSize=12,leading=19,spaceBefore=12,spaceAfter=7)
    title=ParagraphStyle('title',parent=body,fontName='MalgunBold',fontSize=19,leading=27,spaceAfter=8)
    note=ParagraphStyle('note',parent=body,fontSize=8.4,leading=13,textColor=colors.HexColor('#526171'))
    styles={'body':body,'heading':heading,'title':title,'note':note}
    story=[];md=['# 교수님 면담용 핵심 요약','','2026-10-28 / 1차 독립 검증 요청 사전 점검','']
    def add(s,kind='body'):
        story.append(Paragraph(escape(s),styles[kind]));md.extend([('## ' if kind=='heading' else '')+s,''])
    add('AX 사례 추천 연구: 현재 성과와 검증 과제','title')
    add('2026-10-28 | 문장 임베딩 기반 기업 AX 전환 사례 추천 모델 연구','note')
    add('독립 Test는 실행하지 못했습니다. 미사용 질문·정답 묶음을 확인하지 못해 사전 조건에서 중단했습니다. 아래 숫자는 모두 기존 Dev 결과입니다.','heading')
    add('1. 연구 목적과 구현','heading')
    add('사용자의 업무 문제를 보고 실제로 적용할 만한 기업 AX 사례를 찾는 연구입니다. 같은 업종이나 비슷한 단어보다, 실제 수행한 행동과 대상을 확인하려 합니다.')
    add('112개 사례의 Problem·Task·Context와 검색 경로를 보존했습니다. 관점별 후보를 확보한 뒤 A(18개 기능 규칙), B(BGE-M3 필드 임베딩), C(두 방식의 50:50 결합)를 비교했습니다. 현재는 비학습 검증용 구현이며, 교수님이 제안한 학습형 Interaction 신경망의 완성판은 아닙니다.')
    add('2. 실제 확인한 개발 자료 결과','heading')
    cells=[['방식','원질문 F1@5','원질문+관점 F1@5','독립 Test'],['Single Dense','31.47%','별도 조건','미실행'],['A: 규칙','45.36%','46.10%','미실행'],['B: 임베딩','37.02%','38.76%','미실행'],['C: 결합','47.58%','47.58%','미실행']]
    t=Table([[Paragraph(escape(c),note if i else ParagraphStyle('th',parent=note,fontName='MalgunBold',textColor=colors.white)) for c in row] for i,row in enumerate(cells)],colWidths=[94,105,137,93])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#304A68')),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#CCD4DB'))]));story.extend([t,Spacer(1,9)])
    md.extend(['|방식|원질문 F1@5|원질문+관점 F1@5|독립 Test|','|---|---:|---:|---|']+['|'+'|'.join(row)+'|' for row in cells[1:]]+[''])
    add('C는 관점 조건에서 A보다 약 1.48%p 높았지만 개선은 고객 문의 Q1에 집중됐습니다. C의 원질문 결과도 47.58%여서 이 개선 전체를 다중관점의 기여로 설명할 수는 없습니다. B 단독은 A보다 전반적으로 좋지 않았습니다.')
    add('정답은 같은 OpenAI 모델의 3회 중앙값 AI-Silver입니다. 사람 Gold가 아닙니다. 10개 질문 중 양성은 6개 질문·18쌍뿐입니다. Precision은 10개, Recall/F1은 양성이 있는 6개 질문 평균입니다. 서로 다른 처리 조건의 기준선과 관점 효과도 구분해야 합니다.','note')
    add('3. 독립 Test를 실행하지 못한 이유','heading')
    add('준비 기록에는 독립 Test 질문 0개·준비 false가 남아 있고, 지정한 세 최신 브랜치와 관련 경로에서도 질문·정답 묶음을 확인하지 못했습니다. 미래 Test 예약 자료나 과거 학습 holdout 감사 파일은 독립 Test가 아닙니다. Q11~Q15는 이미 추천을 확인한 목적 파일럿이며 사람 평가 103쌍도 아직 0건입니다.')
    story.append(PageBreak())
    add('남은 검증과 교수님께 여쭐 점','title')
    add('4. 성과와 실패를 구분한 현재 판단','heading')
    add('검증한 성과: 검색·관점·후보 결합·기능 매핑을 분리 비교하고, 나쁜 결과도 보존했습니다. 규칙이 인식하지 못한 33개 사례도 임베딩 비교 대상으로 처리했습니다. 새 질문의 블라인드 평가표도 준비했습니다.')
    add('남은 한계: 비교 가능해진 것과 정확히 추천한 것은 다릅니다. 33개 미인식 사례는 기존 Dev에서 양성이 0쌍이라 실제 회복률을 입증하지 못했습니다. Output을 양쪽에서 명시 비교한 쌍도 0개입니다. B는 내부 지식 검색과 수요 예측에서 손실을 보였지만, 원인을 Test에서 새로 검증한 것은 아닙니다.')
    add('고정 Dense+BM25도 대응하는 Dense보다 성능이 낮았습니다. 후보를 충분히 남기는 것만으로 최종 추천 정확도가 보장되지 않았습니다. 문장 임베딩 유사도는 업무 기능의 정확한 일치나 실제 도입 효과의 보증이 아닙니다.')
    add('5. 앞으로의 우선순위 - 아직 수행하지 않은 일','heading')
    add('첫째, 현재 파일럿 103쌍을 사람이 채점해 기능 판단의 오류를 진단합니다. 이 파일럿을 독립 Test로 바꾸지 않습니다. 둘째, 교수님과 다중관점의 필요성 및 문장 임베딩 매핑의 기여를 입증할 비교를 정합니다. 셋째, 모델·평가 규칙 고정 후 미사용 질문·정답을 별도로 준비하고, 미노출·출처 중복을 점검한 뒤 한 번의 정식 비교를 합니다.')
    add('교수님 의견에 따라 모델을 수정한다면, 최종 논문 성능은 새로운 미사용 독립 Test에서 확인해야 합니다. 이번에 새 알고리즘·프로토타입·학습·추론·유료 API 호출은 하지 않았습니다.')
    add('6. 교수님께 의견을 구할 핵심 질문','heading')
    questions=[
      '1) 원질문 결합 방식만으로도 성능이 같은 조건에서, 다중관점의 필요성을 어떤 신규 발견·누락·기능 범위 지표로 검증하면 좋겠습니까?',
      '2) 문장 임베딩 기반 정밀 매핑의 연구적 차별성을 보여주려면 어떤 기능 불일치 대조와 구성요소 제거 실험이 필요합니까?',
      '3) 독립 Test 질문·정답은 누가 어떤 업무·출처 그룹으로 설계하고 검증하는 것이 적절합니까?',
      '4) 논문 범위를 현재 검색·기능 매핑 비교로 유지할지, 충분한 독립 라벨을 확보한 뒤 교수님 Interaction 신경망까지 확장할지 의견을 부탁드립니다.'
    ]
    for q in questions:add(q)
    add('근거: 기존 semantic mapping 결과보고서(2026-10-28), 연구 readiness 메타데이터, 신규 5질문 파일럿 상태. 파일 경로·원격 SHA·원본 해시는 함께 저장한 보고서 A/B와 source manifest에서 확인할 수 있습니다. 이번 기록은 “1차 독립 검증 시도 중 준비 부족으로 중단”이며 검증 완료 기록이 아닙니다.','note')
    output=ROOT/'output/pdf/professor-summary-independent-test-status.pdf';output.parent.mkdir(parents=True,exist_ok=True)
    def footer(canvas,doc):
        canvas.setFont('Malgun',8);canvas.setFillColor(colors.HexColor('#657386'));canvas.drawString(42,26,'AX 연구 면담 자료 | Dev 결과와 미검증 범위 구분');canvas.drawRightString(A4[0]-42,26,f'{doc.page} / 2')
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=34,bottomMargin=44,title='AX 연구 교수님 면담 요약 - 독립 Test 준비 점검',author='AX Research')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(output);assert len(reader.pages)==2,'Meeting summary must be exactly2 pages'
    assert all('독립' in (page.extract_text() or '') for page in reader.pages)
    shutil.copyfile(output,OUT/'professor-meeting-summary.pdf')
    (OUT/'report-C-professor-summary.md').write_bytes(('\n'.join(md).rstrip()+'\n').encode('utf-8'))
    (OUT/'pdf_validation.json').write_bytes((json.dumps({'pages':2,'text_extraction_checked':True,'font':'embedded Malgun/MalgunBold','test_scores_created':False,'graph_scope':'existing Dev only, no Test bars'},ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print('Created two-page professor brief and explicitly Dev-only chart.')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('target',choices=['chart','pdf']);args=parser.parse_args()
    {'chart':chart,'pdf':pdf}[args.target]()
