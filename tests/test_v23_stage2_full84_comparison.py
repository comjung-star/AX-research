"""Stage2 full-84 control study invariants."""
import numpy as np
import pytest

from scripts.v23_stage2_full84_comparison import (
    build_pools, interaction_features, ranking_for_pool,
    precision_recall_and_coverage,
)


def test_full84_candidates_are_not_top10():
    dense=[f"C{i:02}" for i in range(84)]
    sparse=[(cid, 10.0 if i<10 else 0.0) for i,cid in enumerate(reversed(dense))]
    pools=build_pools(dense,sparse)
    assert len(pools["full84"])==84
    assert len(set(pools["full84"]))==84
    assert len(pools["dense20"])==20
    assert len(pools["dense40"])==40
    assert set(dense[:20]).issubset(set(pools["hybrid20_20"]))
    assert len(pools["hybrid20_20"])==len(pools["dense_matched_hybrid_n"])
    assert set(pools["sparse20_positive"])==set(dense[-10:])
    assert len(pools["hybrid20_20"])==30


def test_bm25_zero_is_not_lexical_match():
    dense=[f"C{i:02}" for i in range(84)]
    sparse=[(cid,0.0) for cid in reversed(dense)]
    pools=build_pools(dense,sparse)
    assert pools["sparse20_positive"]==[]
    assert pools["hybrid20_20"]==dense[:20]
    assert pools["dense_matched_hybrid_n"]==dense[:20]


def test_all_full_scorer_then_same_scorer_subset():
    dense=[f"C{i:02}" for i in range(84)]
    sparse=[(cid,1.0 if i<10 else 0.0) for i,cid in enumerate(reversed(dense))]
    pools=build_pools(dense,sparse)
    scores={cid:{"mlp":float(84-i),"dense_score":float(i),"rrf":float(84-i)}
            for i,cid in enumerate(dense)}
    full=ranking_for_pool(pools["full84"],"mlp",scores)
    reduced=ranking_for_pool(pools["hybrid20_20"],"mlp",scores)
    assert len(full)==84
    assert len(reduced)==30
    assert reduced==[cid for cid in full if cid in set(pools["hybrid20_20"])]


def test_query_case_interaction_shapes():
    q=np.ones(48,dtype=np.float32)
    d=np.zeros((84,48),dtype=np.float32)
    f=interaction_features(q,d)
    assert f.shape==(84,192)
    assert np.all(f[:,0:48]==1)
    assert np.all(f[:,48:144]==0)
    assert np.all(f[:,144:192]==1)


def test_reference_coverage_not_runtime_id():
    refs={"S1":{"A","B"},"S2":{"C"},"S3":{"D"}}
    r,p,c,n=precision_recall_and_coverage({"A","D","X"},refs)
    assert r==.5
    assert n==2
    assert abs(p-2/3)<1e-12
    assert abs(c-2/3)<1e-12


def test_invalid_pool_is_rejected():
    dense=[f"C{i:02}" for i in range(84)]
    sparse=[(cid,0.) for cid in dense]
    with pytest.raises(ValueError):
        build_pools(dense[:20],sparse)
    with pytest.raises(ValueError):
        build_pools(dense, sparse[:20])
