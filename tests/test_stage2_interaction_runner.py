import numpy as np
import torch

from ax_research.stage2_interaction_runner import (
    Candidate,
    QueryCaseMLP,
    fit_case_pca,
    interaction_features,
    rrf_score,
)


def test_rrf_rewards_both_sources():
    both = Candidate("A", "both", 1, 1)
    dense = Candidate("B", "dense", 1, None)
    assert rrf_score(both, 60) > rrf_score(dense, 60)


def test_interaction_feature_shape():
    q = torch.tensor([1.0, 2.0])
    cases = torch.tensor([[3.0, 4.0], [5.0, 6.0]])
    features = interaction_features(q, cases)
    assert features.shape == (2, 8)
    assert torch.equal(features[0, 4:6], torch.tensor([3.0, 8.0]))
    assert torch.equal(features[0, 6:8], torch.tensor([2.0, 2.0]))


def test_case_pca_shape_and_centering():
    matrix = np.asarray(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float32,
    )
    mean, basis = fit_case_pca(matrix, projection_dim=2)
    assert mean.shape == (3,)
    assert basis.shape == (3, 2)


def test_interaction_mlp_output_shape():
    model = QueryCaseMLP(projection_dim=2, hidden_dim=4, dropout=0.0)
    scores = model(torch.zeros((3, 8)))
    assert scores.shape == (3,)
