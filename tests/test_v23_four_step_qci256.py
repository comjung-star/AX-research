"""Unit checks for 256d learned gated fusion, selective silver labels, zero-positive views."""
import numpy as np
import torch
from scripts.v23_four_step_qci256 import GatedFusionQCI,load,pair_indices

def test_learned_gate_shapes_and_normalized_three_views():
    torch.manual_seed(42)
    model=GatedFusionQCI()
    query=torch.randn(2,1024)
    views=torch.randn(4,3,1024)
    logits,weights=model(query,views)
    assert logits.shape==(2,4)
    assert weights.shape==(2,4,3)
    assert torch.isfinite(logits).all()
    assert torch.allclose(weights.sum(-1),torch.ones(2,4),atol=1e-5)
    # Regression: additive q+c gate cancels query in softmax.
    assert float(torch.max(torch.abs(weights[0]-weights[1])).detach())>1e-5
    logits.sum().backward()
    assert model.projection.weight.grad is not None
    assert model.view_gate[0].weight.grad is not None

def test_real_artifact_dimensions_and_preserved_primary_labels():
    ids,keys,queries,views,primary,supplemental=load()
    assert len(ids)==84 and len(keys)==97 and views.shape==(84,3,1024)
    assert int((primary==1).sum())==311
    assert int((primary==-1).sum())==169
    assert int((supplemental>=0).sum())>=7979
    assert int((supplemental==-1).sum())==152
    assert all("P" in k for k in keys)

def test_pair_sampler_skips_zero_positive_views():
    lab=np.array([[0,0,0],[1,0,0]],dtype=np.int8)
    dense=np.array([[.2,.3,.4],[.5,.3,.2]],dtype=np.float32)
    r1,r2,c1,c2=pair_indices(lab,dense,42)
    assert all(x.item()==1 for x in r1)
    assert not any(x.item()==0 for x in r1)
    assert all(lab[a,b]==1 for a,b in zip(r1.numpy(),c1.numpy()))
    assert all(lab[a,b]==0 for a,b in zip(r2.numpy(),c2.numpy()))
