"""Inspect staged Git blobs without printing credential values or matching text."""
import json
import re
import subprocess
from scripts import query_isolated_revalidation as run


def verify():
    names=[spec["key_env"] for spec in run.api.CONFIG["models"].values()]+["GITHUB_TOKEN","GH_TOKEN"]
    secrets=[value.encode() for name in names if (value:=run.api.read_key(name))]
    entries=subprocess.check_output(["git","ls-files","--stage","-z"],cwd=run.ROOT).split(b"\0")
    changed=set(subprocess.check_output(["git","diff","--cached","--name-only","-z"],cwd=run.ROOT).split(b"\0"))
    blobs=[]
    for entry in entries:
        if not entry:continue
        meta,path=entry.split(b"\t",1)
        if path in changed:
            blobs.append((path.decode("utf-8"),meta.split()[1].decode()))
    payload="".join(sha+"\n" for _,sha in blobs).encode()
    data=subprocess.check_output(["git","cat-file","--batch"],input=payload,cwd=run.ROOT)
    offset=0;actual=[];patterns=[];forbidden=[];total=0
    regexes=[rb"sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}",rb"AIza[0-9A-Za-z_-]{30,}",rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",rb"gh[pousr]_[A-Za-z0-9]{30,}"]
    for path,_ in blobs:
        end=data.index(b"\n",offset);header=data[offset:end].split();size=int(header[-1]);content=data[end+1:end+1+size];offset=end+2+size;total+=size
        if any(secret in content for secret in secrets):actual.append(path)
        if any(re.search(pattern,content) for pattern in regexes):patterns.append(path)
        if any(p in {".env",".local",".venv",".git"} or p.startswith(".env.") for p in path.split("/")):
            forbidden.append(path)
    result={"scope":"All currently staged changed Git blobs; this report is created after scanning and separately protected by safe_write key-value validation.","files_scanned":len(blobs),"bytes_scanned":total,"known_secret_values_loaded_without_printing":len(secrets),"actual_secret_value_match_files":actual,"credential_pattern_match_files":patterns,"forbidden_local_path_files":forbidden,"passed":not(actual or patterns or forbidden)}
    run.save(run.OUTPUT/"security_scan.json",result)
    print(json.dumps({k:result[k] for k in ("files_scanned","bytes_scanned","known_secret_values_loaded_without_printing","passed")},ensure_ascii=False))
    if not result["passed"]:raise SystemExit("Publication blocked: secret scan findings, no matching values printed")
    return result


if __name__=="__main__":verify()
