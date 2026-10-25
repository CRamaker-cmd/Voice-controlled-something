from macrovoice.config import Settings


def test_defaults_and_overrides():
    s = Settings.from_env({})
    assert s.timezone == "Europe/Amsterdam" and s.api_token is None and s.worker_jobs == ("off-api",)
    s = Settings.from_env({"MACROVOICE_API_TOKEN": "t", "WORKER_JOBS": "off-api, usda", "OFF_PAGES": "3",
                           "ANTHROPIC_API_KEY": ""})
    assert s.api_token == "t" and s.worker_jobs == ("off-api", "usda") and s.off_pages == 3
    assert s.anthropic_api_key is None
