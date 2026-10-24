"""QCI hypothesis test cases: prevent label leakage and false view ID equivalence."""
from collections import defaultdict

import numpy as np

from scripts.v23_qci_improvement_audit import (
    label_audit,
    map_runtime_to_reference,
    pairwise_features,
    view_centroids,
)


def test_perspective_silver_disagreement_is_measurable():
    ref={"Q":{"P1":{"A","B"},"P2":{"B","C"},"P3":{"D"}}}
    r=label_audit(ref)[0]
    assert r["positive_union"]==4
    assert r["positive_only_one_reference_view"]==3
    assert r["positive_two_reference_views"]==1
    assert r["positive_all_three_reference_views"]==0
    assert r["fraction_positive_not_shared_all_views"]==1.


def test_runtime_id_must_map_by_similarity_not_name():
    doc=np.asarray([[1.,0.],[0.,1.]],dtype=np.float32)
    reference={"Q":{"P1":{"A"},"P2":{"B"},"P3":set()}}
    centroids=view_centroids(reference,"Q",doc,{"A":0,"B":1})
    # Runtime 'P1' embedding points to reference P2; we do not align IDs.
    choice,score,margin=map_runtime_to_reference(np.asarray([0,1],dtype=np.float32),centroids)
    assert choice=="P2"
    assert score==1.
    assert margin>0.5


def test_pairwise_features_only_public_search_signal():
    sims=np.asarray([[.1,.2],[.3,.4],[.5,.6]],dtype=np.float32)
    f=pairwise_features(sims,{"A":1,"B":84},{"A":1.2,"B":0.},["A","B"])
    assert f.shape==(2,5)
    assert np.allclose(f[0,:3],[.1,.3,.5])
    assert f[0,3]>0 and f[0,4]==1.
    assert f[1,3]==0 and f[1,4]==0.
