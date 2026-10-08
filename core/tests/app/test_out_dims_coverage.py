"""B5 out_dims 完备性覆盖测试：全包单元声明面=公式输出全集的对账门。

输入:  units_lib 四线全单元 manifest 模块（UNIT_ID/manifest 实例+公式表
       _FORMULAS 模块级真源——私有直读消费面在册，test_app_assembly
       ._unit_params 先例同款 noqa 注记）
输出:  四断言——①field_id 集==公式输出符号集（D5 完备性口径）②dim 逐条
       镜像 FormulaSpec.output_dim ③label_zh 非空 ④schema 正门装载
       （import 期 load_manifest 全量守卫）+枚举面=discover_units 口径
"""

# ══════════════════════════════════════════════════════════════════
# 规格：B5 任务书 §4（b5-20261009）——30 件 out_dims 补全批的常设门：
#   本件合入后全量跑可见，任一单元缺声明/量纲漂移/label 空=红。
#   完备性口径=D5：out_dims field_id 集与 _FORMULAS 输出符号集相等
#   （同符号多式去重单条）。aao/cass 两先例为 B5 前冻结件（任务书 §1
#   禁改既有项），实测与字面等式存在既知差集（先例含 projection 消费面
#   键、aao 缺 4 个公式输出键）——差集以下方 _FROZEN_* 常量钉面：
#   先例后续任何漂移即红；主控勘误批收口后清空（impl-report-b5.md
#   自裁申报 R-2 追认面）。dim 镜像真源=①公式表 output_dim（D3，
#   与 scripts/check_out_dims_consistency.py 门禁同口径；先例差集键
#   的 ②projection dim_of 兜底面归该门禁辖，本件不重复实现）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Mapping
from types import MappingProxyType, ModuleType

from waterprint.units_lib import discover_units

# 先例基准冻结差集（B5 前实测 2026-10-09）：aao out_dims 含 8 个非公式
# 输出键（均经 drawing_projection dim_of 声明——消费面键）且缺 4 个公式
# 输出键（raw 几何×2+内回流×2）；cass 含 5 个非公式输出键（同 projection
# 声明）、公式输出全量在册。语义详注=impl-report-b5.md 自裁申报 R-2。
_FROZEN_MISSING: Mapping[str, frozenset[str]] = MappingProxyType({
    "municipal_aao": frozenset(
        {"b_pool_raw", "l_pool_raw", "q_internal", "q_return"}
    ),
})
_FROZEN_EXTRA: Mapping[str, frozenset[str]] = MappingProxyType({
    "municipal_aao": frozenset(
        {"b_pool", "delta_n", "l_pool", "n", "n_aerator", "t_total",
         "v_o_series", "v_total"}
    ),
    "municipal_cass": frozenset({"b_pool", "l_pool", "n_aerator",
                                 "n_decant", "x_vss"}),
})


def _unit_manifest_modules() -> dict[str, ModuleType]:
    """四线全单元 manifest 模块枚举（discover_units 同源迭代面，32 包口径）。"""
    root = importlib.import_module("waterprint.units_lib")
    modules: dict[str, ModuleType] = {}
    for line_info in pkgutil.iter_modules(root.__path__):
        if not line_info.ispkg or line_info.name == "_template":
            continue
        line = importlib.import_module(f"waterprint.units_lib.{line_info.name}")
        for pkg_info in pkgutil.iter_modules(line.__path__):
            mod = importlib.import_module(
                f"waterprint.units_lib.{line_info.name}.{pkg_info.name}.manifest"
            )
            modules[str(mod.UNIT_ID)] = mod
    return modules


def _formula_outputs(module: ModuleType) -> dict[str, set[str]]:
    """公式表 → 输出符号→output_dim 集合同符号多式并集（去重单条口径）。"""
    outputs: dict[str, set[str]] = {}
    for spec in module._FORMULAS:  # noqa: SLF001  # 公式表模块级真源直读（头注在册）
        symbol = spec.expression.split("=", 1)[0].strip()
        outputs.setdefault(symbol, set()).add(spec.output_dim.value)
    return outputs


def test_out_dims_cover_formula_outputs() -> None:
    """①完备性（D5）：全包单元 out_dims field_id 集==公式输出符号集；
    先例冻结差集外的任何缺口/无基准键=红。"""
    problems: list[str] = []
    for unit_id, module in sorted(_unit_manifest_modules().items()):
        outputs = _formula_outputs(module)
        declared = {spec.field_id for spec in module.manifest.out_dims}
        missing = set(outputs) - declared - _FROZEN_MISSING.get(unit_id, frozenset())
        extra = declared - set(outputs) - _FROZEN_EXTRA.get(unit_id, frozenset())
        if missing:
            problems.append(f"{unit_id}: 公式输出未声明 out_dims {sorted(missing)}")
        if extra:
            problems.append(f"{unit_id}: out_dims 键无公式输出基准 {sorted(extra)}")
    assert not problems, "\n".join(problems)


def test_out_dims_dim_mirror_and_labels() -> None:
    """②dim 镜像（D3）+③label 非空：声明 dim 逐条=公式表 output_dim
    （真源①；先例差集键的 projection 兜底归 check_out_dims_consistency）。"""
    problems: list[str] = []
    for unit_id, module in sorted(_unit_manifest_modules().items()):
        outputs = _formula_outputs(module)
        for spec in module.manifest.out_dims:
            if spec.field_id in outputs and spec.dim.value not in outputs[spec.field_id]:
                problems.append(
                    f"{unit_id}.{spec.field_id}: dim={spec.dim.value}"
                    f" ≠ 公式 output_dim {sorted(outputs[spec.field_id])}"
                )
            if not spec.label_zh or not spec.label_zh.strip():
                problems.append(f"{unit_id}.{spec.field_id}: label_zh 空")
    assert not problems, "\n".join(problems)


def test_units_enumeration_matches_registry() -> None:
    """④schema/口径：manifest 模块经正门装载（import 期 load_manifest 全量
    守卫=④）且枚举面与 discover_units 注册表一致（/api/units 32 包口径）。"""
    modules = _unit_manifest_modules()
    assert set(modules) == set(discover_units())
