import torch

from ax_research.stage2_gated_runner import TinyQueryConditionedGate, _branch_loss


def test_gate_starts_as_equal_weights():
    gate = TinyQueryConditionedGate()
    weights = gate(torch.tensor([0.2, 0.4, 0.6]))
    assert torch.allclose(weights, torch.tensor([1 / 3, 1 / 3, 1 / 3]), atol=1e-7)


def test_pairwise_loss_is_lower_when_positive_score_is_higher():
    gate = TinyQueryConditionedGate()
    feature = torch.tensor([0.1, 0.2, 0.3])
    better = torch.tensor([[0.9, 0.9, 0.9], [0.1, 0.1, 0.1]], dtype=torch.float32)
    worse = torch.tensor([[0.1, 0.1, 0.1], [0.9, 0.9, 0.9]], dtype=torch.float32)
    mask = torch.tensor([True, False])
    loss_better = _branch_loss(gate, feature=feature, view_scores=better, positive_mask=mask, pairwise_scale=10.0)
    loss_worse = _branch_loss(gate, feature=feature, view_scores=worse, positive_mask=mask, pairwise_scale=10.0)
    assert float(loss_better) < float(loss_worse)
