"""test_demo_pipeline——演示版全链管线：三话术真跑（B4-4a 验收基准）。

输入:  tmp_path 沙箱（env 覆盖）+ golden 种子（正式区只读装载）+规则解析（零外部依赖）
输出:  run_demo 三话术断言——①③全链绿（达标+双报告落盘）；②矿井案计算/达标/
       摘要绿+双报告 core 既有缺口可解释回显（test_e2e_golden 记档面，挂账呈报）
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from waterprint_agent import context, demo

UTTERANCE_AAO = "设计一座日处理 3 万吨的市政污水处理厂，AAO 工艺"
UTTERANCE_MINE = "矿井水处理厂，日处理量 1 万吨"
UTTERANCE_LEVEL_A = "市政污水厂 5 万吨每天，出水要一级 A"


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    monkeypatch.delenv("WATERPRINT_DEMO_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("WATERPRINT_DEMO_LLM_API_KEY", raising=False)
    context.reset_context()
    yield root
    context.reset_context()


_SIX_INDICATORS = ("CODCR", "BOD5", "SS", "NH3N", "TN", "TP")


def test_pipeline_municipal_aao(sandbox_env: Path) -> None:
    """话术①市政 3 万吨 AAO：全链绿——达标+六指标+双报告落盘+吨水指标在带。"""
    result = demo.run_demo(UTTERANCE_AAO)
    assert result["intent"]["seed"] == "municipal_34760"
    assert result["intent"]["scale_m3_d"] == 30000.0
    assert result["compliant"] is True
    summary = result["summary"]
    for indicator in _SIX_INDICATORS:
        assert indicator in summary, f"六指标缺 {indicator}"
    assert result["flow_m3_d"] == pytest.approx(30000.0, rel=1e-9)
    assert summary["carbon_intensity_kgco2e_m3"] == pytest.approx(0.5876, abs=0.05)
    assert 0.15 < summary["power_total_kwh_d"] / result["flow_m3_d"] < 0.30
    for kind in ("calcbook", "report"):
        assert "path" in result["exports"][kind], f"{kind} 未落盘"
        assert Path(result["exports"][kind]["path"]).is_file()


def test_pipeline_municipal_level_a(sandbox_env: Path) -> None:
    """话术③市政 5 万吨一级 A：全链绿——达标（一级 A 判定面）+双报告落盘。"""
    result = demo.run_demo(UTTERANCE_LEVEL_A)
    assert result["intent"]["scale_m3_d"] == 50000.0
    assert result["compliant"] is True
    assert result["flow_m3_d"] == pytest.approx(50000.0, rel=1e-9)
    assert "path" in result["exports"]["calcbook"]
    assert "path" in result["exports"]["report"]


def test_pipeline_mine_with_known_gaps(sandbox_env: Path) -> None:
    """话术②矿井 1 万吨：计算/摘要绿+达标判定诚实呈现；双报告=core 既有缺口。

    达标判定=False 系标准适用性事实（矿井水高 TN/TP，在库标准族=gb18918
    市政口径——明细负裕度可解释；矿井水适用标准不在 data 包，挂账深化段）。
    既有缺口（agent/tests/test_e2e_golden.py:25-28 记档+B4-4a 新发现）：
    calcbook 模板硬引 summary.design.BOD5（矿井线天然无 BOD5）；
    report HB-F10 锚定值与 trace 输出不等（原规模即红，与改参无关）。
    """
    result = demo.run_demo(UTTERANCE_MINE)
    assert result["intent"]["seed"] == "mine_43836"
    assert result["intent"]["scale_m3_d"] == 10000.0
    assert result["compliant"] is False  # 诚实判定（TN/TP 负裕度——标准适用性）
    by_indicator = {item["indicator"]: item for item in result["effluent_design"]}
    assert by_indicator["TN"]["compliant"] is False  # 60 vs 15（一级 A 限值）
    assert by_indicator["TP"]["compliant"] is False  # 2.0 vs 0.5（一级 A 限值）
    assert result["flow_m3_d"] == pytest.approx(10000.0, rel=1e-9)
    # 矿井线六指标族 sparse：BOD5 缺席合法（e2e 记档口径）
    assert "CODCR" in result["summary"]
    assert "BOD5" not in result["summary"]
    assert result["summary"]["carbon_intensity_kgco2e_m3"] == pytest.approx(
        0.70, abs=0.05
    )
    for kind in ("calcbook", "report"):
        entry = result["exports"][kind]
        assert "error" in entry, f"{kind} 应为缺口回显（core 既有缺口记档面）"


def test_pipeline_result_is_jsonable(sandbox_env: Path) -> None:
    """run_demo 返回体 JSON 可序列化（--json 输出面确定性）。"""
    result = demo.run_demo(UTTERANCE_AAO)
    blob = json.dumps(result, ensure_ascii=False)
    assert "演示" in blob


def test_pipeline_hard_failure_create(
    sandbox_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """硬失败路径（门一 W4 处置）：建项步 error→可解释三键+不裸异常。"""
    from waterprint_agent.tools import projects as projects_tools

    monkeypatch.setattr(
        projects_tools, "_create_impl", lambda ctx, name, seed: {"error": "种子缺失"}
    )
    result = demo.run_demo(UTTERANCE_AAO)
    assert result["error"] == "管线步骤「建项目」失败"
    assert result["detail"]["error"] == "种子缺失"
    assert result["intent"]["seed"] == "municipal_34760"


def test_pipeline_scale_patch_rejected(
    sandbox_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """规模 patch 被拒=硬失败（门一 W3 处置——防静默携模板规模继续算）。"""
    from waterprint_agent.tools import projects as projects_tools

    def fake_update(ctx, project_id, patches):
        return {
            "results": [
                {"unit_id": "inlet", "key": "q_avg_daily", "accepted": False,
                 "reason": "值越出 grid 档位带"}
            ],
            "accepted_count": 0,
            "design_digest": "0" * 64,
        }

    monkeypatch.setattr(projects_tools, "_update_params_impl", fake_update)
    result = demo.run_demo(UTTERANCE_AAO)
    assert "规模改参被拒" in result["error"]
    assert result["detail"]["rejected"][0]["reason"] == "值越出 grid 档位带"
