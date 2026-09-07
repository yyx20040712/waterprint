"""incremental 性质测试：种子编辑序列下 增量 == 全量重算（字节级）。

输入:  golden_data/m3_incremental_seed.json（方案 B golden 派生种子——Ruling
       2026-09-07 ②；生成脚本 .workflow/b11-probe/generate_m3_seed.py，
       用户/领域专家审定后锁面登记）
输出:  等价性断言（违反 = CI 失败——§17.2 语义铁律）：逐步应用 edits，
       recompute_scope 判定范围 vs execute_graph 全量重算——①scope 形态
       与种子期望一致（规则①②③触发面）②未受影响单元前后快照逐字段
       恒等（scope 守护的重用装配=增量语义的安全性质）③每步全量 serialize
       字节锚（sha256 头+长度——跨版本回归）

说明：字节级比较是硬约束，禁删除或放宽。接线=批 11（占位 raise
AssertionError 证红→本接线转绿——红绿实录入批报告）；Q4 降级路径
（Ruling 2026-09-07 ②）：总控接线+领域专家事后追认（追认点入批报告
与 pending-domain-expert.md）。oracle 跑=cache-cold（default_cache()
.clear() 每步——cache.py 规格头预记纪律）。
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

_mod = importlib.import_module("waterprint.graph.incremental")
recompute_scope = getattr(_mod, "recompute_scope", None)

_SEED = (
    Path(__file__).resolve().parent.parent
    / "golden"
    / "golden_data"
    / "m3_incremental_seed.json"
)

pytestmark = [
    pytest.mark.skipif(
        recompute_scope is None or not _SEED.is_file(),
        reason="实现未就绪或种子数据未整理（M1/M3：waterprint.graph.incremental）",
    ),
]


def _apply_edit(design: dict[str, Any], edit: dict[str, Any]) -> dict[str, Any]:
    """种子编辑词汇表（生成器同式独立实现——锁定件不引生成脚本）。"""
    nxt = copy.deepcopy(design)
    kind = edit["kind"]
    if kind == "param":
        nxt["nodes"][edit["target"]["unit_id"]][edit["target"]["field"]] = edit[
            "payload"
        ]["value"]
    elif kind == "remove_unit":
        unit_id = edit["target"]["unit_id"]
        nxt["nodes"].pop(unit_id)
        touching = [
            edge
            for edge in nxt["edges"]
            if edge["src"]["unit_id"] == unit_id or edge["dst"]["unit_id"] == unit_id
        ]
        assert len(touching) == edit["payload"]["edges_removed"], (
            f"remove_unit 关连边数 {len(touching)} != 预期 "
            f"{edit['payload']['edges_removed']}"
        )
        nxt["edges"] = [
            edge
            for edge in nxt["edges"]
            if edge["src"]["unit_id"] != unit_id
            and edge["dst"]["unit_id"] != unit_id
        ]
    elif kind == "restore_unit":
        nxt["nodes"][edit["payload"]["unit_id"]] = copy.deepcopy(
            edit["payload"]["node"]
        )
        nxt["edges"].extend(copy.deepcopy(edit["payload"]["edges"]))
    elif kind == "assumption":
        nxt["assumption_overrides"][edit["target"]["key"]] = edit["payload"]["value"]
    elif kind == "site_boundary":
        nxt["site"]["boundary"] = copy.deepcopy(edit["payload"]["points"])
    else:
        raise ValueError(f"未知编辑种类: {kind}")
    return nxt


def _snapshot_key(snapshot: Any) -> str:
    """单元快照确定性字串（重用安全断言比较基准——手工组装防
    MappingProxyType pickle 面，warnings 经 repr 定形）。"""
    return json.dumps(
        {
            "unit_id": snapshot.unit_id,
            "outflows": dict(snapshot.outflows),
            "outqualities": dict(snapshot.outqualities),
            "dims": dict(snapshot.dims),
            "warnings": [repr(item) for item in snapshot.warnings],
            "formula_ids": list(snapshot.formula_ids),
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def _seed_context(seed: dict[str, Any]) -> tuple[Any, Any, Any]:
    """种子运行上下文三件：基线项目（源文件装载+design 替换）+RunEnv+工况集。"""
    from waterprint.app import load_project
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.project_schema import DesignState
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    meta = seed["meta"]
    repo = Path(__file__).resolve().parents[3]
    base_project = load_project(repo / meta["source"]).model_copy(
        update={"design": DesignState.model_validate(seed["base_design"])}
    )
    env = RunEnv(
        engine_version=meta["engine_version"],
        data_version=meta["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(repo / "data" / "coefficients"),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    return base_project, env, build_condition_set(base_project.design.checked_units)


def test_incremental_equals_full_recompute_on_seed_sequence() -> None:
    """种子编辑序列：每步增量结果与全量重算字节级一致。"""
    from waterprint.app import run_full_calc
    from waterprint.contracts.project_schema import DesignState
    from waterprint.contracts.result_schema import serialize
    from waterprint.graph.cache import default_cache

    seed = json.loads(_SEED.read_text(encoding="utf-8"))
    assert {"base_design", "edits"} <= set(seed)
    base_project, env, conditions = _seed_context(seed)

    prev_design = copy.deepcopy(seed["base_design"])
    prev_project = base_project
    default_cache().clear()
    prev_plant = run_full_calc(prev_project, conditions, env).plant
    base_blob = serialize(prev_plant)
    assert hashlib.sha256(base_blob).hexdigest()[:16] == (
        seed["meta"]["base_serialize_sha256_head"]
    ), "基线 serialize 锚（种子 meta）"

    for step, edit in enumerate(seed["edits"], 1):
        expect = edit["expect"]
        cur_design = _apply_edit(prev_design, edit)
        cur_project = prev_project.model_copy(
            update={"design": DesignState.model_validate(cur_design)}
        )
        scope = recompute_scope(prev_project.design, cur_project.design)
        assert scope.full_graph == expect["full_graph"], f"step{step} 规则触发面"
        assert sorted(scope.changed_units) == expect["changed_units"], (
            f"step{step} changed_units"
        )
        assert len(scope.loop_groups) == expect["loop_group_count"], (
            f"step{step} 回路组命中数"
        )

        default_cache().clear()  # oracle 跑=cache-cold（cache.py 规格头纪律）
        cur_plant = run_full_calc(cur_project, conditions, env).plant
        blob = serialize(cur_plant)
        assert hashlib.sha256(blob).hexdigest()[:16] == (
            expect["serialize_sha256_head"]
        ), f"step{step} serialize sha256 头（全量重算字节锚）"
        assert len(blob) == expect["serialize_bytes"], f"step{step} serialize 长度"

        # 增量语义安全性质：scope 未受影响单元——重用上一步结果合法
        # （前后快照逐字段恒等；违例=recompute_scope 漏标真实变更面）。
        # full_graph 步 affected=全集→本断言组零迭代（全量重算无重用面，
        # 性质咬合住在部分重算步——本图 21 单元 16 大 SCC 下 A 族步
        # 未受影响面=inlet，为该图拓扑上限）。
        affected = scope.affected_units
        assert len(affected) == expect["affected_count"], f"step{step} affected 数"
        for cond_key, snapshots in cur_plant.conditions.items():
            for unit_id, snapshot in snapshots.items():
                if unit_id in affected:
                    continue
                reused = prev_plant.conditions[cond_key].get(unit_id)
                assert reused is not None, f"step{step} {cond_key}/{unit_id} 无前值"
                assert _snapshot_key(reused) == _snapshot_key(snapshot), (
                    f"step{step} {cond_key}/{unit_id} 未受影响单元结果漂移"
                    "（recompute_scope 漏标——增量重用不安全）"
                )
        if expect.get("results_identical_to_prev"):
            # 负控机器锚：全工况全部单元（含受影响重算面）快照与上一步
            # 恒等——无关字段不进结果面（serialize 差异唯一来源=
            # repro.design_hash 随设计字节变化，非结果漂移）。
            for cond_key, snapshots in cur_plant.conditions.items():
                assert set(snapshots) == set(prev_plant.conditions[cond_key]), (
                    f"step{step} {cond_key} 单元键集漂移（负控步应恒等）"
                )
                for unit_id, snapshot in snapshots.items():
                    assert _snapshot_key(
                        prev_plant.conditions[cond_key][unit_id]
                    ) == _snapshot_key(snapshot), (
                        f"step{step} {cond_key}/{unit_id} 负控步结果漂移"
                        "（无关字段泄漏进结果面）"
                    )
        prev_design, prev_project, prev_plant = cur_design, cur_project, cur_plant
