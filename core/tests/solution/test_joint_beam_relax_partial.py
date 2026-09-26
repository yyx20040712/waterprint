"""联合枚举放宽重试部分覆盖回归草案（AUD-B2）——core/tests 转正候选件。

输入:  waterprint.solution.joint_enumeration 公开符号+真实 coefficients 数据包
输出:  部分 grids 覆盖+末段全不可行 → 放宽重试按全量网格重建（不抛
       KeyError，返回放宽语义诊断或可行组合）；全量覆盖重试语义非回归断言
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from waterprint.solution.joint_enumeration import (
    JointEnumerationOptions,
    run_joint_enumerate,
)


def _data() -> Path:
    """coefficients 数据包定位（上溯仓库根——草案位/转正位两栖定位）。"""
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "data" / "coefficients").is_dir():
            return ancestor / "data" / "coefficients"
    raise FileNotFoundError("data/coefficients 未定位（仓库根锚）")


_AAO, _CASS = "municipal_aao", "municipal_cass"
_GRIDS = {
    _AAO: ({"field_id": "n", "values": [2.0, 3.0]},),
    _CASS: ({"field_id": "n_pool", "values": [2.0, 3.0]},),
}


def _project() -> Any:
    """inlet→aao→cass 三节点链（两寻优目标拓扑序载体——test_beam 同款）。"""
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile

    return ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "NH3N": 26.0,
                    "TN": 43.0,
                    "TP": 6.5,
                },
                _AAO: {},
                _CASS: {},
            },
            edges=[
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": _AAO, "port_id": "in"}},
                {"src": {"unit_id": _AAO, "port_id": "out"},
                 "dst": {"unit_id": _CASS, "port_id": "in"}},
            ],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="",
            engine_version="b43", data_version="b43",
        ),
    )


def _env() -> Any:
    """真实数据包 env（coefficients 1.5.0——test_beam 同款装配）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
    from waterprint.registry.coefficients import load_coefficients

    assumptions = {item.key: item.default for item in DEFAULT_ASSUMPTIONS}
    return RunEnv(
        engine_version="b43", data_version="b43", assumptions=assumptions,
        coefficients=load_coefficients(_data()), price_book={},
        trace_sink=None, engine_params={},
    )


def _options(**overrides: Any) -> Any:
    """选项装配（assemble 类注入防环面——经 app_assembly 真源）。"""
    from waterprint.app_assembly import assemble

    return JointEnumerationOptions(assemble=assemble, **overrides)


def _conditions() -> Any:
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set([])


def _strict_standard() -> Any:
    """严出水标准（末段复验全不可行构造面——test_beam 同款限值）。"""
    from waterprint.contracts.quality import EffluentStandard

    return EffluentStandard(
        standard_id="test_strict", name_i18n="严标准",
        limits={"CODCR": 1e-9, "BOD5": 1e-9},
    )


def test_relaxed_retry_partial_coverage_returns_diagnosis_not_keyerror() -> None:
    """AUD-B2：部分 grids 覆盖（仅 AAO 请求覆盖，CASS 走 manifest 档回落）
    +末段全不可行 → 放宽重试按全量目标网格重建，返回放宽语义诊断
    （旧行为：retry grids 仅含放宽单元 → staged() 索引缺口单元裸 KeyError）。"""
    outcome = run_joint_enumerate(
        _project(), [_CASS, _AAO], _conditions(), _env(),
        _options(grids={_AAO: _GRIDS[_AAO]}, standards=(_strict_standard(),)),
    )
    assert not outcome.combos  # 严标准：放宽一轮后仍无可行组合
    assert outcome.diagnosis is not None
    assert outcome.diagnosis["kind"] == "final_infeasible"
    # 批5 口径修订（2026-09-26 落位时按批5 语义校正）：离散档网格=名义放宽
    # 不重试（relaxed_grids 仅收录 range 域扩宽——批5 分叉①），诊断载荷
    # 携事由注记非 KeyError（AUD-B2 原意=诊断在场不断链）。
    assert outcome.diagnosis["relaxed"] is False
    assert "离散档" in outcome.diagnosis["note"]


def test_relaxed_retry_full_coverage_semantics_unchanged() -> None:
    """全量覆盖非回归：两单元均有请求网格+末段全不可行 → 放宽重试语义
    不因网格合并改变（discrete values 档原样放宽=等域重搜）。"""
    outcome = run_joint_enumerate(
        _project(), [_AAO, _CASS], _conditions(), _env(),
        _options(grids=_GRIDS, standards=(_strict_standard(),)),
    )
    assert not outcome.combos
    assert outcome.diagnosis is not None
    assert outcome.diagnosis["kind"] == "final_infeasible"
    # 批5 口径修订（同上）：discrete 档原样=名义放宽不重试（旧行为等域重搜
    # 已被批5 分叉①废除——零意义重跑+误导注记）。
    assert outcome.diagnosis["relaxed"] is False
    assert "名义放宽不重试" in outcome.diagnosis["note"]
