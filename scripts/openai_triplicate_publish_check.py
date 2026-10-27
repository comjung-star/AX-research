"""Scan staged blobs without reading Gemini/Claude credentials or printing secrets."""
import re
import subprocess
from scripts import openai_triplicate as r

def main():
    changed=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r.ROOT).split(b'\0'))
    entries=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=r.ROOT).split(b'\0');blobs=[]
    for entry in entries:
        if not entry:continue
        info,path=entry.split(b'\t',1)
        if path in changed:blobs.append((path.decode('utf-8'),info.split()[1].decode()))
    raw=subprocess.check_output(['git','cat-file','--batch'],input=''.join(sha+'\n' for _,sha in blobs).encode(),cwd=r.ROOT)
    secret=r.key();key_bytes=secret.encode() if secret else None;offset=0;total=0;findings=[]
    patterns=[rb'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}',rb'AIza[0-9A-Za-z_-]{30,}',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    for name,_ in blobs:
        end=raw.index(b'\n',offset);size=int(raw[offset:end].split()[-1]);data=raw[end+1:end+1+size];offset=end+2+size;total+=size
        bad=(key_bytes and key_bytes in data) or any(re.search(p,data) for p in patterns) or any(p in ('.env','.local','.venv','.git') or p.startswith('.env.') for p in name.split('/'))
        if bad:findings.append(name)
    result={'scope':'All currently staged changed Git blobs before this report; report itself uses secret-blocking save','files_scanned':len(blobs),'bytes_scanned':total,'active_openai_key_checked_without_printing':bool(key_bytes),'other_llm_keys_read':False,'finding_paths':findings,'passed':not findings}
    r.save(r.OUT/'security_scan.json',result);print({k:result[k] for k in ('files_scanned','bytes_scanned','passed')})
    assert result['passed'],'Publication blocked: findings, values not printed'
if __name__=='__main__':main()
