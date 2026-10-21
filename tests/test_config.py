from ax_research.config import load_rq1_config


def test_frozen_v1_1_config_uses_gpt_6_luna():
    config = load_rq1_config()
    assert config.status == "FROZEN_FOR_IMPLEMENTATION"
    assert config.llm_model == "gpt-6-luna"
    assert config.llm_repeats == 3
    assert config.temperature == 0.5
    assert config.perspective_min == 2
    assert config.perspective_max == 5
