"""Test evidence and staged-secret-pattern checks; never loads credentials."""
import re
import subprocess
from scripts import dense_bm25_candidates as c

def main():
    test=subprocess.run([__import__('sys').executable,'-m','pytest','tests/test_dense_bm25_candidates.py','-q'],cwd=c.ROOT,capture_output=True,text=True)
    c.save('test_results.json',{'command':'python -m pytest tests/test_dense_bm25_candidates.py -q','returncode':test.returncode,'stdout':test.stdout,'stderr':test.stderr,'passed':test.returncode==0})
    assert test.returncode==0,test.stdout+test.stderr
    changed=set(subprocess.check_output(['git','diff',c.CFG['base_commit'],'--name-only','-z'],cwd=c.ROOT).split(b'\0'));blobs=[]
    for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=c.ROOT).split(b'\0'):
        if not entry:continue
        info,path=entry.split(b'\t',1)
        if path in changed:blobs.append((path.decode('utf-8'),info.split()[1].decode()))
    raw=subprocess.check_output(['git','cat-file','--batch'],input=''.join(sha+'\n' for _,sha in blobs).encode(),cwd=c.ROOT)
    patterns=[rb'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}',rb'AIza[0-9A-Za-z_-]{30,}',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    offset=0;total=0;findings=[]
    for name,_ in blobs:
        end=raw.index(b'\n',offset);size=int(raw[offset:end].split()[-1]);data=raw[end+1:end+1+size];offset=end+2+size;total+=size
        if any(re.search(p,data) for p in patterns) or any(p in ('.env','.local','.venv','.git') or p.startswith('.env.') for p in name.split('/')):findings.append(name)
    report={'scope':'All indexed branch changes since base, before this generated report; known credential patterns and prohibited paths. This is a pattern scan, not proof that every possible secret is detectable.','files_scanned':len(blobs),'bytes_scanned':total,'credential_environment_reads':0,'finding_paths':findings,'passed':not findings}
    c.save('security_scan.json',report);assert report['passed']
    print(test.stdout.strip());print({'files_scanned':len(blobs),'security_passed':report['passed']})

if __name__=='__main__':main()
