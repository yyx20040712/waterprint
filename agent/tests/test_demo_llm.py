"""test_demo_llm——演示版 LLM 解析面：成功解析/回退四态（monkeypatch 零真调用）。

输入:  _llm_call monkeypatch（返回预置 content 或抛异常族）
输出:  parse_intent 回退链断言（LLM 优先→失败规则兜底+note 溯源——B4-4a P2）
"""

from __future__ import annotations

import json

import pytest

from waterprint_agent import demo


def _settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WATERPRINT_DEMO_LLM_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("WATERPRINT_DEMO_LLM_API_KEY", "test-key-placeholder")
    monkeypatch.setenv("WATERPRINT_DEMO_LLM_MODEL", "test-model-placeholder")


def test_llm_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM 正常返回合法 JSON→parse_source=llm（含 note 溯源）。"""
    _settings_env(monkeypatch)
    content = json.dumps(
        {"seed": "mine_43836", "scale_m3_d": 12000, "note": "矿井水 1.2 万吨"}
    )

    def fake_call(utterance: str) -> str:
        return content

    monkeypatch.setattr(demo, "_llm_call", fake_call)
    intent = demo.parse_intent("矿井水处理厂 1.2 万吨")
    assert intent.parse_source == "llm"
    assert intent.seed == "mine_43836"
    assert intent.scale_m3_d == 12000.0
    assert "矿井" in intent.parse_note


def test_llm_json_in_prose(monkeypatch: pytest.MonkeyPatch) -> None:
    """content 夹带说明文字→首段 JSON 对象宽容提取。"""
    _settings_env(monkeypatch)
    content = '解析结果如下：\n{"seed": "municipal_34760", "scale_m3_d": 40000, "note": "市政 4 万吨"}\n请查收。'
    monkeypatch.setattr(demo, "_llm_call", lambda u: content)
    intent = demo.parse_intent("市政污水 4 万吨")
    assert intent.parse_source == "llm"
    assert intent.scale_m3_d == 40000.0


@pytest.mark.parametrize(
    ("content_or_error",),
    [
        ("这不是 JSON",),  # 非 JSON 文本
        ('{"seed": "unknown_seed", "scale_m3_d": 1}',),  # seed 违例
        ('{"seed": "municipal_34760", "scale_m3_d": -5}',),  # 规模违例（非正数）
        ("raise:URLError",),  # 网络/超时异常族
    ],
)
def test_llm_fallback_to_rules(
    monkeypatch: pytest.MonkeyPatch, content_or_error: str
) -> None:
    """LLM 四种失败态→规则回退（parse_source=rules+note 记回退原因）。"""
    _settings_env(monkeypatch)

    def fake_call(utterance: str) -> str:
        if content_or_error.startswith("raise:"):
            raise OSError("模拟网络不可达")
        return content_or_error

    monkeypatch.setattr(demo, "_llm_call", fake_call)
    intent = demo.parse_intent("市政污水处理厂 3 万吨")
    assert intent.parse_source == "rules"  # 回退面诚实标注，不冒充 LLM 解析
    assert "回退" in intent.parse_note
    assert intent.seed == "municipal_34760"
    assert intent.scale_m3_d == 30000.0


def test_llm_missing_env_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """环境变量三元组缺一→不发起调用直接规则回退。"""
    monkeypatch.delenv("WATERPRINT_DEMO_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("WATERPRINT_DEMO_LLM_API_KEY", raising=False)
    called = False

    def spy_call(utterance: str) -> str:
        nonlocal called
        called = True
        return "{}"

    monkeypatch.setattr(demo, "_llm_call", spy_call)
    intent = demo.parse_intent("市政污水 2 万吨")
    assert called is False
    assert intent.parse_source == "rules"


def test_offline_flag_skips_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """--offline 显式开关：LLM 可用也不调用（断网演示预案）。"""
    _settings_env(monkeypatch)
    called = False

    def spy_call(utterance: str) -> str:
        nonlocal called
        called = True
        return "{}"

    monkeypatch.setattr(demo, "_llm_call", spy_call)
    intent = demo.parse_intent("市政污水 2 万吨", offline=True)
    assert called is False
    assert intent.parse_source == "rules"
