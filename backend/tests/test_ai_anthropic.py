import httpx
import pytest

from macrovoice.ai import AIError, AnthropicEstimator


def make(handler):
    return AnthropicEstimator("k", client=httpx.Client(transport=httpx.MockTransport(handler)))


def tool_reply(**inp):
    return httpx.Response(200, json={"content": [{"type": "tool_use", "name": "log_item", "input": inp}]})


def test_parses_tool_use_and_sends_forced_tool_call():
    seen = {}

    def handler(req: httpx.Request):
        seen["headers"], seen["body"] = req.headers, __import__("json").loads(req.content)
        return tool_reply(identified=True, grams=100, kcal=200, protein_g=10, carbs_g=20, fat_g=5, note="n")

    est = make(handler).estimate("a croissant")
    assert (est.identified, est.grams, est.kcal, est.protein, est.carbs, est.fat) == (True, 100, 200, 10, 20, 5)
    assert seen["headers"]["x-api-key"] == "k" and "anthropic-version" in seen["headers"]
    assert seen["body"]["tool_choice"] == {"type": "tool", "name": "log_item"}
    assert seen["body"]["messages"][0]["content"] == "a croissant"


def test_not_identified_is_passed_through():
    assert make(lambda r: tool_reply(identified=False, note="?")).estimate("zzz").identified is False


def test_unusable_numbers_count_as_not_identified():
    est = make(lambda r: tool_reply(identified=True, grams=0, kcal=1, protein_g=1, carbs_g=1, fat_g=1)).estimate("x")
    assert est.identified is False


@pytest.mark.parametrize("response", [
    httpx.Response(500, text="oops"),
    httpx.Response(200, json={"content": [{"type": "text", "text": "hi"}]}),
    httpx.Response(200, json={"content": [{"type": "tool_use", "input": {"identified": True}}]}),
])
def test_bad_responses_raise_aierror(response):
    with pytest.raises(AIError):
        make(lambda r: response).estimate("x")


def test_network_failure_raises_aierror():
    def boom(req):
        raise httpx.ConnectError("down")
    with pytest.raises(AIError):
        make(boom).estimate("x")
