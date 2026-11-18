"""app_assembly 镜像测试：装配域拆分不变量（B3-R11 裁定件）+ 联动参数
声明一致性校核（b26 AUDIT-#6——D6 裁决：共同装配点校核）。

输入:  waterprint.app 再导出面与 waterprint.app_assembly 定义面 +
       erchunchi/aao 双包 manifest（漂移副本经 dataclasses.replace 构造）
输出:  恒等断言（assemble/_unit_params/AssembledGraph 同一对象——再导出
       保消费面 from waterprint.app import 零改动，UF-33 单入口语义）+
       联动参数三态断言（同值过/异值拒/单包独立装载不受扰）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3-R11 恒等钉面原样；b26 增 AUDIT-#6 用例组——四组红绿
#   证据的测试面：①同值过=双包同图装配零异常；②异值拒=erchunchi
#   声明漂移（x_mlss/r_external 参数化）→ InvalidAssemblyError 消息含
#   两包名+两参数名+两值；③单包独立装载不受扰=漂移在场（两方向）装配
#   均过——对方缺席不得致败。漂移注入=monkeypatch make_unit 返回
#   manifest 漂移副本单元（discover_units 装配期取包导出面——源
#   manifest 文件零触碰）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import replace
from typing import ClassVar

import pytest

import waterprint.units_lib.municipal.erchunchi as erchunchi_package
from waterprint import app, app_assembly
from waterprint.contracts.manifest import UnitManifest
from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.unit_api import Unit


def test_reexport_identity() -> None:
    """装配域三符号经 app 再导出=定义面同一对象（B3 笔①拆分不变量钉面）。"""
    assert app.assemble is app_assembly.assemble
    assert app._unit_params is app_assembly._unit_params  # noqa: SLF001  # 私有直 import 消费面在册（test_unit_params_projection 同符号）
    assert app.AssembledGraph is app_assembly.AssembledGraph


class _EmptyCoefficients:
    """空系数视图（协议面——装配期只做前缀投影，零键=零投影）。"""

    data_version: ClassVar[str] = "m1b"

    def get(self, key: str) -> object:
        raise KeyError(key)

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return ()

    def require_keys(self, keys: object) -> None:
        return None


def _assemble(node_ids: tuple[str, ...]) -> None:
    """最小装配驱动：inlet + 指定包单元节点（无边——装配面不查连通）；
    异常上抛即断言面（InvalidAssemblyError 由用例 pytest.raises 收口）。"""
    nodes: dict[str, dict[str, object]] = {
        "inlet": {"kind": "municipal_input", "q_avg_daily": 0.4, "kz": 1.4}
    }
    nodes.update({node_id: {} for node_id in node_ids})
    project = ProjectFile(
        format_version="1.0",
        design=DesignState(nodes=nodes, edges=[]),
        metadata=Metadata(
            format_version="1.0", content_hash="", engine_version="m1b", data_version="m1b"
        ),
    )
    env = RunEnv(
        engine_version="m1b",
        data_version="m1b",
        assumptions={},
        coefficients=_EmptyCoefficients(),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    app.assemble(project, env)


def _drifted(manifest: UnitManifest, field_id: str, value: float) -> UnitManifest:
    """单参数声明默认值漂移副本（dataclasses.replace——源 manifest 零触碰）。"""
    return replace(
        manifest,
        params=tuple(
            replace(spec, default=value) if spec.field_id == field_id else spec
            for spec in manifest.params
        ),
    )


def _drift_erchunchi(monkeypatch: pytest.MonkeyPatch, field_id: str, value: float) -> None:
    """erchunchi 包装配面漂移注入：make_unit 返回 manifest 漂移副本单元
    （discover_units 装配期经包导出面取 make_unit——实例属性遮蔽类属性，
    _CoefficientsUnit.manifest 随之携带漂移声明）。"""

    original_make = erchunchi_package.make_unit

    def _make_drifted() -> Unit:
        unit = original_make()
        unit.manifest = _drifted(unit.manifest, field_id, value)
        return unit

    monkeypatch.setattr(erchunchi_package, "make_unit", _make_drifted)


def test_linked_param_same_defaults_assemble_passes() -> None:
    """AUDIT-#6 同值过：双包同图装配（现行声明默认值同值）→ 成功零异常。"""
    _assemble(("municipal_aao", "municipal_erchunchi"))


@pytest.mark.parametrize(
    ("field_id", "value", "aao_value", "erchunchi_value"),
    [
        ("x_mlss", 3500.0, "4000.0", "3500.0"),
        ("r_external", 0.8, "1.0", "0.8"),
    ],
)
def test_linked_param_drift_rejected(
    monkeypatch: pytest.MonkeyPatch,
    field_id: str,
    value: float,
    aao_value: str,
    erchunchi_value: str,
) -> None:
    """AUDIT-#6 异值拒：erchunchi 声明漂移 → InvalidAssemblyError（消息含
    两包名+两参数名+漂移参数两值——键集 ['x_mlss','r_external'] 全列）。"""
    _drift_erchunchi(monkeypatch, field_id, value)
    with pytest.raises(app.InvalidAssemblyError) as excinfo:
        _assemble(("municipal_aao", "municipal_erchunchi"))
    message = str(excinfo.value)
    assert "municipal_aao" in message  # 两包名
    assert "municipal_erchunchi" in message
    assert "x_mlss" in message and "r_external" in message  # 两参数名（键集全列）
    assert aao_value in message  # 漂移参数 aao 侧值
    assert erchunchi_value in message  # 漂移参数 erchunchi 侧值


@pytest.mark.parametrize(("field_id", "value"), [("x_mlss", 3500.0), ("r_external", 0.8)])
def test_single_package_assembly_skips_linked_check(
    monkeypatch: pytest.MonkeyPatch, field_id: str, value: float
) -> None:
    """AUDIT-#6 单包独立装载不受扰：漂移在场（对方缺席）两方向均过——
    仅 AAO（声明未漂移方独装）与仅二沉池（自身带漂移值独装）不校核。"""
    _drift_erchunchi(monkeypatch, field_id, value)
    _assemble(("municipal_aao",))
    _assemble(("municipal_erchunchi",))
