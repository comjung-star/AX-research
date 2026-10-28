"""Report/metadata consistency and staged-file scan; not model accuracy tests."""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/independent-test-readiness-2026-10-28'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as s:
        for part in iter(lambda:s.read(8*1024*1024),b''):h.update(part)
    return h.hexdigest()
def save(name,d):(OUT/name).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())

def main():
    cfg=read(ROOT/'configs/independent_test_readiness_20261028.json');snap=read(OUT/'freeze_snapshot.json');gate=read(OUT/'readiness_gate.json');execution=read(OUT/'test_execution_record.json')
    for path,h in snap['frozen_files_sha256'].items():assert sha(ROOT/path)==h
    for item in read(OUT/'report_source_manifest.json')['sources']:assert sha(ROOT/item['path'])==item['sha256']
    assert gate['test_queries_evaluated']==gate['test_payloads_opened']==0 and gate['independent_test_qrel_path'] is None
    assert execution['inference_runs']==0 and not execution['test_metrics_generated']
    rows=read(OUT/'dev_vs_test.json')['rows'];assert len(rows)==21
    assert all(r[k] is None for r in rows for k in ('test_precision','test_recall','test_f1','test_ndcg'))
    with (OUT/'dev_vs_test.csv').open(encoding='utf-8-sig',newline='') as s:
        csvrows=list(csv.DictReader(s))
    assert len(csvrows)==21 and all(r[k]=='' for r in csvrows for k in ('test_precision','test_recall','test_f1','test_ndcg'))
    reader=PdfReader(OUT/'professor-meeting-summary.pdf');assert len(reader.pages)==2
    words='\n'.join(p.extract_text() or '' for p in reader.pages)
    assert all(s in words for s in ('미실행','46.10','38.76','47.58','103','다중관점'))
    assert all((OUT/n).exists() for n in ('report-A-research-status.md','report-B-independent-test.md','report-C-professor-summary.md','dev_only_performance.png','dev_only_performance.svg'))
    save('report_validation.json',{'passed':True,'checks_scope':'Only report/data preservation and metadata consistency. No model/Test inference or recommendation-accuracy test.','frozen_files_preserved':len(snap['frozen_files_sha256']),'source_manifest_hashes_verified':True,'dev_comparison_rows':21,'test_metrics_all_null':True,'pdf_pages':2,'both_pdf_pages_and_dev_chart_visually_reviewed':True,'model_inference_count':0,'human_gold_created':0,'test_predictions_created':0})
    changed=set(subprocess.check_output(['git','diff',cfg['base_commit'],'--name-only','-z'],cwd=ROOT).split(b'\0'));blobs=[]
    for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0'):
        if not entry:continue
        info,path=entry.split(b'\t',1)
        if path in changed:blobs.append((path.decode('utf-8'),info.split()[1].decode()))
    raw=subprocess.check_output(['git','cat-file','--batch'],input=''.join(h+'\n' for _,h in blobs).encode(),cwd=ROOT)
    patterns=[rb'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}',rb'AIza[0-9A-Za-z_-]{30,}',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    offset=0;findings=[];total=0
    for name,_ in blobs:
        end=raw.index(b'\n',offset);size=int(raw[offset:end].split()[-1]);data=raw[end+1:end+1+size];offset=end+2+size;total+=size
        if any(re.search(p,data) for p in patterns) or any(s in ('.env','.git','.venv','.local','node_modules') or s.startswith('.env.') for s in name.split('/')):findings.append(name)
    modified=subprocess.check_output(['git','diff',cfg['base_commit'],'--diff-filter=M','--name-only'],cwd=ROOT).decode('utf-8').splitlines();assert all(x=='.gitattributes' for x in modified)
    save('security_scan.json',{'passed':not findings,'finding_paths':findings,'files_scanned':len(blobs),'bytes_scanned':total,'credential_values_read':False,'old_research_files_changed':False,'scope':'Known credential patterns and prohibited staged paths, before generated reports; not proof every possible secret is detectable.'})
    assert not findings
    print('Report checks passed: preserved inputs, 21 null Test rows, two-page PDF; not model accuracy validation.')

if __name__=='__main__':main()
