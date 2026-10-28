"""Offline regression evidence and staged branch credential-pattern scan."""
import re
import subprocess
import sys
from scripts import blind_pilot_five as p

def main():
    tests=['tests/test_functional_mapping.py','tests/test_semantic_mapping.py','tests/test_semantic_mapping_artifacts.py','tests/test_semantic_mapping_publication.py','tests/test_blind_pilot_analysis.py']
    r=subprocess.run([sys.executable,'-m','pytest',*tests,'-q'],cwd=p.ROOT,capture_output=True,text=True)
    p.save('test_results.json',{'command':'python -m pytest '+' '.join(tests)+' -q','returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'passed':r.returncode==0,'semantic_accuracy_proven':False,'synthetic_test_grades_written_to_real_review_files':False})
    assert r.returncode==0,r.stdout+r.stderr
    changed=set(subprocess.check_output(['git','diff',p.CFG['base_commit'],'--name-only','-z'],cwd=p.ROOT).split(b'\0'));blobs=[]
    for e in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=p.ROOT).split(b'\0'):
        if not e:continue
        info,name=e.split(b'\t',1)
        if name in changed:blobs.append((name.decode('utf-8'),info.split()[1].decode()))
    raw=subprocess.check_output(['git','cat-file','--batch'],input=''.join(h+'\n' for _,h in blobs).encode(),cwd=p.ROOT)
    patterns=[rb'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}',rb'AIza[0-9A-Za-z_-]{30,}',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    offset=0;findings=[];total=0
    for name,_ in blobs:
        end=raw.index(b'\n',offset);size=int(raw[offset:end].split()[-1]);data=raw[end+1:end+1+size];offset=end+2+size;total+=size
        if any(re.search(pat,data) for pat in patterns) or any(v in ('.env','.git','.venv','.local','node_modules') or v.startswith('.env.') for v in name.split('/')):findings.append(name)
    modified=subprocess.check_output(['git','diff',p.CFG['base_commit'],'--diff-filter=M','--name-only'],cwd=p.ROOT,text=True).splitlines()
    assert all(n=='.gitattributes' for n in modified),'Existing tracked research file modified: '+str(modified)
    p.save('security_scan.json',{'passed':not findings,'finding_paths':findings,'files_scanned':len(blobs),'bytes_scanned':total,'credential_values_loaded':False,'scope':'Indexed branch changes before this generated report; known credential patterns/prohibited paths. Not a guarantee every possible secret can be detected.','old_research_files_modified':False})
    assert not findings
    print(r.stdout.strip());print('Secret-pattern and old-file preservation checks passed:',len(blobs),'files.')

if __name__=='__main__':main()
