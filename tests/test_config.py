from ax_research.config import load_rq1_config


def test_frozen_v1_2_config():
    config = load_rq1_config()
    assert config.status == "FROZEN_FOR_IMPLEMENTATION"
    assert config.experiment_id == "rq1_retrieval_v1_2"
    assert config.llm_model == "gpt-6-luna"
    assert config.llm_repeats == 3
    assert config.temperature == 0.5
    assert config.perspective_min == 2
    assert config.perspective_max == 5
    assert config.branch_query_mode == "perspective_only"
