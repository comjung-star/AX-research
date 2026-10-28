import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=process.argv[2];
if(!root)throw new Error('Pass repository root');
const out=path.join(root,'docs/blind-pilot-five-queries-2026-10-28');
const source=JSON.parse(await fs.readFile(path.join(out,'evaluator/review_rows.json'),'utf8'));
const wb=Workbook.create();const sheet=wb.worksheets.add('평가표');const guide=wb.worksheets.add('채점 안내');
const values=[source.headers,...source.rows.map(r=>source.headers.map(h=>r[h]||null))];
sheet.getRange(`A1:H${values.length}`).values=values;
sheet.showGridLines=false;sheet.freezePanes.freezeRows(1);sheet.freezePanes.freezeColumns(1);
const body=sheet.getRange(`A1:H${values.length}`);body.format.font.name='Arial';body.format.font.size=11;body.format.wrapText=true;body.format.verticalAlignment='top';
const head=sheet.getRange('A1:H1');head.format.fill='#23395B';head.format.font.color='#FFFFFF';head.format.font.bold=true;head.format.rowHeight=32;
const widths=[23,58,66,54,66,60,16,48];
for(let i=0;i<8;i++)sheet.getRangeByIndexes(0,i,values.length,1).format.columnWidth=widths[i];
function lines(text,width){return String(text||'').split('\n').reduce((n,s)=>n+Math.max(1,Math.ceil([...s].reduce((v,ch)=>v+(ch.codePointAt(0)>255?2:1),0)/(width-2))),0);}
for(let r=1;r<values.length;r++)sheet.getRangeByIndexes(r,0,1,8).format.rowHeight=Math.min(409,Math.max(84,...values[r].map((v,c)=>lines(v,widths[c])*15+10)));
sheet.getRange(`G2:H${values.length}`).format.fill='#FFF2CC';
sheet.getRange(`G2:G${values.length}`).dataValidation={rule:{type:'list',values:['0','1','2','3','판단 보류']}};
const instructions=[
 ['사람 관련성 평가','먼저 이 파일만 보고 채점하세요. analyst 폴더와 모델별 추천 결과는 채점 전 열지 마세요.'],
 ['입력 위치','평가표 시트 G열 관련성 점수, H열 평가 의견만 입력합니다. 나머지 설명과 평가 ID는 바꾸지 마세요.'],
 ['3점','동일하거나 직접 적용 가능한 업무 기능'],
 ['2점','업무 기능이 유사해 다른 환경에도 응용 가능'],
 ['1점','일부 관련되지만 실제 적용 차이가 큼'],
 ['0점','관련 없는 업무'],
 ['판단 보류','설명이 부족하거나 판단하기 어려울 때 선택하세요. 공란은 미평가입니다. 둘 다0점으로 취급하지 않습니다.'],
 ['일반 예시','문서 번역 질문에 문서 번역은3점, 다른 형식의 번역 응용은2점, 요약만 하면1점, 상자 운반은0점으로 생각할 수 있습니다. 특정 평가 사례의 정답은 아닙니다.'],
 ['판단 방법','Task의 실제 수행 기능을 보세요. 업종이나 수작업 감소만으로 높은 점수를 주지 마세요. 원문에 없는 성과·보안·기능을 추측하지 마세요.'],
 ['기존 설명의 한계','사례 설명은 기존 연구의 구조화 요약입니다. 출처 URL을 제공하지만 원 출판물을 이번에 재검증하지 않았습니다.'],
 ['점수는 공란','현재 점수와 의견은 전부 공란입니다. AI가 정답을 미리 채우지 않았습니다.'],
 ['완료 후','채점한 파일을 다른 이름으로 저장하고 대화에 첨부하세요. CSV도 같은 평가ID를 사용하므로 둘 중 하나만 채점하면 됩니다.']
];
guide.getRange(`A1:B${instructions.length}`).values=instructions;guide.showGridLines=false;
guide.getRange(`A1:B${instructions.length}`).format.font.name='Arial';guide.getRange(`A1:B${instructions.length}`).format.font.size=11;
guide.getRange(`A1:B${instructions.length}`).format.wrapText=true;guide.getRange(`A1:B${instructions.length}`).format.verticalAlignment='center';
guide.getRange('A1:A12').format.columnWidth=23;guide.getRange('B1:B12').format.columnWidth=108;
guide.getRange('A1:B12').format.rowHeight=66;guide.getRange('A1:B1').format.rowHeight=50;guide.getRange('A8:B8').format.rowHeight=84;
guide.getRange('A1:B1').format.font.bold=true;guide.getRange('A1:B1').format.font.size=14;
guide.getRange('A2:B2').format.fill='#FFF2CC';
wb.recalculate();
const inspect=await wb.inspect({kind:'table',range:'평가표!F1:H4',include:'values,formulas',tableMaxRows:4,tableMaxCols:3,maxChars:1200});
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:20},maxChars:800});
await fs.mkdir(path.join(root,'outputs/blind-pilot-five-20261028'),{recursive:true});
for(const [name,range,file] of [['평가표','A1:H3','review_preview.png'],['채점 안내','A1:B12','guide_preview.png']]){
 const img=await wb.render({sheetName:name,range,scale:1,format:'png'});
 await fs.writeFile(path.join(root,'outputs/blind-pilot-five-20261028',file),new Uint8Array(await img.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);
const target=path.join(root,'outputs/blind-pilot-five-20261028/blind_review.xlsx');await xlsx.save(target);
await fs.copyFile(target,path.join(out,'evaluator/blind_review.xlsx'));
await fs.writeFile(path.join(out,'workbook_build_check.json'),JSON.stringify({inspect:inspect.ndjson,errorScan:errors.ndjson,rows:source.rows.length,sheets:['평가표','채점 안내'],hidden_algorithm_sheets:false,human_scores_prefilled:false},null,2)+'\n');
console.log(JSON.stringify({rows:source.rows.length,output:target}));
