#!/usr/bin/env python3
"""AX v2.3 structural + provenance audit; standard library only."""
import csv, hashlib, json
from pathlib import Path
d=Path(__file__).resolve().parents[1]/"data"/"v2_3"
def rows(name):
    with (d/name).open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))
def read_json(name):
    return json.loads((d/name).read_text(encoding="utf-8"))
m=read_json("release_manifest_v2_3.json")
v=read_json("main_cases_v2_3.json")
a=v["cases"]
keys=[c["case_id"] for c in a]
assert len(keys)==86 and len(set(keys))==86
assert v["dataset_release"]=="2.3.0" and v["status"].endswith("RESEARCHER_APPROVAL_PENDING")
fids={x["factor_id"] for x in rows("root_cause_taxonomy_v2_3.csv")}
sids={x["strategy_id"] for x in rows("strategy_taxonomy_v2_3.csv")}
assert len(fids)==11 and len(sids)==7
assert any(x.startswith("F10_") for x in fids) and any(x.startswith("F11_") for x in fids)
assert {x["strategy_id"][:2] for x in rows("strategy_taxonomy_v2_3.csv")}=={f"S{i}" for i in range(1,8)}
for c in a:
    assert all(c.get(k) for k in ("case_id","problem","task","context","source_url","sampling_group_id"))
    assert c["factor_labels"] and c["strategy_labels"]
    assert set(c["factor_labels"])<=fids and set(c["strategy_labels"])<=sids
    assert c["factor_label"]==c["factor_labels"][0] and c["strategy_label"]==c["strategy_labels"][0]
    assert c["dataset_release"]=="2.3.0" and c["human_ground_truth_approved"] is False
    assert c["v23_source_review"]["status"]=="RESEARCHER_APPROVAL_PENDING"
assert v["counts"]["retained"]==86 and v["counts"]["excluded"]==7
assert v["counts"]["multiple_factor_cases"]==sum(len(c["factor_labels"])>1 for c in a)
assert v["counts"]["multiple_strategy_cases"]==sum(len(c["strategy_labels"])>1 for c in a)
assert v["counts"]["unique_groups"]==len({c["sampling_group_id"] for c in a})
old=rows("case_disposition_v2_3.csv")
assert len(old)==93 and len({x["case_id"] for x in old})==93
assert sum(x["status"]=="EXCLUDE" for x in old)==7
assert {x["case_id"] for x in old if x["status"]=="KEEP"}==set(keys)
assert all(x["decision_reason"] and x["source_url"] for x in old)
flat=rows("main_cases_v2_3.csv")
assert len(flat)==86 and {x["case_id"] for x in flat}==set(keys)
assert all(x["root_cause_factor"] and x["strategy"] for x in flat)
qs=read_json("dev_query_candidates_v2_3.json")["queries"]
qids={q["query_id"] for q in qs}
assert len(qids)==10
pairs={(q["query_id"],p["id"]) for q in qs for p in q["draft_perspectives"]}
assert len(pairs)==30
annotations=rows("dev_relevance_annotation_sheet_v2_3.csv")
assert len(annotations)==2580
tuples={(x["query_id"],x["perspective_id"],x["case_id"]) for x in annotations}
assert len(tuples)==2580
assert all((x["query_id"],x["perspective_id"]) in pairs and x["case_id"] in keys for x in annotations)
assert all(x["status"]=="UNJUDGED" and not x["relevance_0_4"] and not x["annotator_id"] for x in annotations)
strats=rows("dev_strategy_annotation_sheet_v2_3.csv")
assert len(strats)==10 and {x["query_id"] for x in strats}==qids
assert all(x["status"]=="UNJUDGED" and not x["strategy_set"] for x in strats)
for path, expected in m["git_blob_sha"].items():
    b=(d/path.removeprefix("data/v2_3/")).read_bytes()
    actual=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    assert actual==expected,(path,actual,expected)
assert m["counts"]["dev_relevance_slots"]==2580
print("PASS: 86 valid workflows, 7 traced exclusions, F=11/S=7, 2580 UNJUDGED + all file blobs verified")
