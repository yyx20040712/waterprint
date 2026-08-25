"""app 镜像测试：用例编排（装配失败清单/双跑 diff=0/三元组传播——golden 承载）。

输入:  waterprint.app 公开符号
输出:  编排契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.app")
run_full_calc = getattr(_mod, "run_full_calc", None)
assemble = getattr(_mod, "assemble", None)

pytestmark = pytest.mark.skipif(
    None in (run_full_calc, assemble),
    reason="实现未就绪：waterprint.app（M1 三单元切片）",
)


def test_entrypoints_frozen() -> None:
    """入口冻结：assemble(project, env) / run_full_calc(project, conditions, env)。"""
    assert callable(assemble)
    assert callable(run_full_calc)


def test_double_run_byte_identical_wiring() -> None:
    """R3 接线断言：同 (project, conditions, env) 双跑序列化字节相同。

    与 golden 端到端互补：golden 给数值对照，本断言给可复算性。
    载体=T7b 裁决的三内置节点线性链（municipal_input→junction→
    quality_edit，最小 ProjectFile：design.nodes 三键各含 kind+params、
    edges 两元素冻结形态、其余字段缺省空）——"三单元"以内置节点充当
    （占位意图=app 全链接线可复算性；golden 未整理故数值对照不在本批；
    M1 真实三单元实装后载体升级属未来批）。
    """
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
    from waterprint.contracts.result_schema import serialize
    from waterprint.contracts.run_env import RunEnv

    class _Coefficients:
        data_version = "t7b"

        def get(self, key: str) -> object:
            raise KeyError(key)

        def keys(self, prefix: str = "") -> tuple[str, ...]:
            return ()

        def require_keys(self, keys: object) -> None:
            return None

    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 0.4,
                    "kz": 1.3,
                    "CODCR": 260.0,
                },
                "hub": {"kind": "junction"},
                "polish": {"kind": "quality_edit", "NH3N": 5.0},
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "hub", "port_id": "in_1"},
                },
                {
                    "src": {"unit_id": "hub", "port_id": "out"},
                    "dst": {"unit_id": "polish", "port_id": "in"},
                },
            ],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="t7b",
            data_version="t7b",
        ),
    )
    env = RunEnv(
        engine_version="t7b",
        data_version="t7b",
        assumptions={},
        coefficients=_Coefficients(),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    conditions = build_condition_set([])
    assembled = assemble(project, env)
    assert set(assembled.units) == {"inlet", "hub", "polish"}
    first = run_full_calc(project, conditions, env)
    second = run_full_calc(project, conditions, env)
    assert serialize(first.plant) == serialize(second.plant)
    assert first.repro == second.repro
    assert first.repro.design_hash
