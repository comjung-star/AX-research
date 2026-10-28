"""Persist tests and scan staged branch files; does not read credentials."""
import re
import subprocess
import sys
from scripts import functional_mapping_run as f

def main():
    test=subprocess.run([sys.executable,'-m','pytest','tests/test_functional_mapping.py','tests/test_dense_bm25_candidates.py','-q'],cwd=f.ROOT,capture_output=True,text=True)
    f.save('test_results.json',{'command':'python -m pytest tests/test_functional_mapping.py tests/test_dense_bm25_candidates.py -q','passed':test.returncode==0,'returncode':test.returncode,'stdout':test.stdout,'stderr':test.stderr,'test_cases':23,'semantic_accuracy_test':False})
    assert test.returncode==0,test.stdout+test.stderr
    changed=set(subprocess.check_output(['git','diff',f.CFG['base_commit'],'--name-only','-z'],cwd=f.ROOT).split(b'\0'));blobs=[]
    for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=f.ROOT).split(b'\0'):
        if not entry:continue
        info,path=entry.split(b'\t',1)
        if path in changed:blobs.append((path.decode('utf-8'),info.split()[1].decode()))
    raw=subprocess.check_output(['git','cat-file','--batch'],input=''.join(sha+'\n' for _,sha in blobs).encode(),cwd=f.ROOT)
    patterns=[rb'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}',rb'AIza[0-9A-Za-z_-]{30,}',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    offset=0;total=0;findings=[]
    for name,_ in blobs:
        end=raw.index(b'\n',offset);size=int(raw[offset:end].split()[-1]);data=raw[end+1:end+1+size];offset=end+2+size;total+=size
        if any(re.search(p,data) for p in patterns) or any(p in ('.env','.local','.venv','.git') or p.startswith('.env.') for p in name.split('/')):findings.append(name)
    report={'scope':'All indexed branch changes since base, before generated report; known credential patterns and prohibited paths. Pattern scanning is not proof every possible secret is detectable.','files_scanned':len(blobs),'bytes_scanned':total,'credential_environment_reads':0,'finding_paths':findings,'passed':not findings}
    f.save('security_scan.json',report);assert report['passed']
    print(test.stdout.strip());print({'files_scanned':len(blobs),'security_passed':report['passed']})

if __name__=='__main__':main()
