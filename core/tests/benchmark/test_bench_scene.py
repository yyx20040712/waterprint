"""性能基准：全厂场景图生成 <100ms（§18.1；SC1 补 scene.py 规格声称的守卫缺口）。

出处：geometry/scene.py 文件头「场景图 schema 与装配……全厂 <100ms 的
总入口」+ R5 规格「全厂场景图生成 <100ms（§18.1，pytest-benchmark
守卫）」——SC1 前该声称无对应基准文件（E 冻结疑点 4），本文件补齐。
CI benchmarks job 目录级收集零改动（本文件落 tests/benchmark/ 即被收集）。

输入:  golden 市政案例（十二节点主线三件套，与 test_bench_full_calc 同种子）
输出:  pytest-benchmark 计时（超预算由 CI 基准门禁判失败）
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_SEED = Path(__file__).resolve().parents[1] / "golden" / "golden_data" / "municipal_34760" / "input_project.json"
_EXPECTED = _SEED.parent / "expected_summary.json"
_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"

pytestmark = [
    pytest.mark.skipif(
        not _SEED.is_file(),
        reason="基准数据未就绪（M1/M2：golden 案例录入后激活）",
    ),
]

BUDGET_SECONDS = 0.1  # §18.1：全厂场景图生成（scene.py 文件头 R5 声称口径）


def _wiring() -> tuple[object, object, object, str]:
    """golden 接线束：正门载项目 + build_condition_set 勾选 3 单元（5 工况）。

    checked_units/工况档取自 expected_summary.json（单一数据源——与
    e2e 同源勾选）；env 口径=expected.generated 实录（test_bench_full_calc
    同款）。返回 (project, conditions, env, chosen_condition)。
    """
    from waterprint.app import load_project
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    expected = json.loads(_EXPECTED.read_text(encoding="utf-8"))
    lib = load_coefficients(_REPO_DATA)
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    # 工况档取 expected（sorted 首键——services/scene.py R2 缺省同口径）
    chosen = sorted(expected["condition_keys"])[0]
    return load_project(_SEED), build_condition_set(expected["checked_units"]), env, chosen


def test_scene_benchmark(benchmark) -> None:
    """全厂场景图生成在预算内（劣化即 CI 失败——SC1 D8 补规格守卫）。

    build_scene 直接消费 plant+assumptions+condition+site_design（纯投影
    无 RunEnv 通道）；assumptions=DEFAULT_ASSUMPTIONS+design.
    assumption_overrides 合成、site_design=design.site——services/scene.py
    build_scene_for_project R3/R5 同款口径（计算与投影假设面一致）。
    计时前先跑 run_full_calc 产 plant（计算不计时——只守 build_scene）。
    """
    from waterprint.app import run_full_calc
    from waterprint.geometry.scene import build_scene
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    project, conditions, env, chosen = _wiring()
    bundle = run_full_calc(project, conditions, env)
    plant = bundle.plant  # ResultBundle 两字段子集（T7b）——场景消费 plant 面
    assert chosen in plant.conditions  # expected 工况档在结果集（接线防漂）
    assumptions: dict[str, float] = {entry.key: entry.default
                                     for entry in DEFAULT_ASSUMPTIONS}
    assumptions.update(project.design.assumption_overrides)

    def build_scene_wrapper() -> object:
        return build_scene(plant, assumptions, chosen,
                           site_design=project.design.site)

    benchmark.pedantic(build_scene_wrapper, rounds=1, iterations=1)
    assert benchmark.stats.stats.mean < BUDGET_SECONDS  # §18.1 预算守卫
