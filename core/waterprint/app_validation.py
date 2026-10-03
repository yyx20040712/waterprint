"""厂级进水输入合理性校验骨架：project 进水原始声明 × kb input_band 条目求值。

输入:  ProjectFile（design.nodes 进水声明节点原始数据——非计算值）+
       Sequence[KbConstraint]（kb 装载产物——run_full_calc constraints 注入同源）
输出:  validation_summary_of → ValidationReport（PlantWarning 元组——
       app.run_full_calc 第四字段 validation 挂载面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（1A2 校验骨架批 1a2-20261004 §3.2 预裁决；镜像测试
#   tests/app/test_app_validation.py；app_maintenance.py 家族先例同构
#   第十例——根模块聚合投影件，不进 import-linter layers 契约
#   （app_trust/app_carbon 同款 unconstrained）。）
#
# 【公开接口】
#   INPUT_BAND_KIND: Final[str]（="input_band"）：选条判据 kind 符号单源。
#   INPUT_BAND_FIELDS: Final[Mapping[str, str]]：key→字段映射表（memo③
#       ——input_band 七条 key 与冻结字段异名对照：kz_band→kz /
#       cod→CODCR / bod5→BOD5 / ss→SS / nh3n→NH3N / tn→TN / tp→TP；
#       对账测试逐条消费——单源，禁入 kb README〔数据包冻结面〕）：
#         inlet.kz_band          → kz
#         inlet.quality_upper.cod   → CODCR
#         inlet.quality_upper.bod5  → BOD5
#         inlet.quality_upper.ss    → SS
#         inlet.quality_upper.nh3n  → NH3N
#         inlet.quality_upper.tn    → TN
#         inlet.quality_upper.tp    → TP
#   validation_summary_of(project, constraints) -> ValidationReport
#       （命名对齐 maintenance_summary_of）：厂级进水面检查——与单元族
#       无关、与工况无关（进水声明为静态原始面）。
#
# 【行为口径】
#   R1 选条判据=kind=="input_band" 直判（接线红线——见下方逐字引用）。
#   R2 进水单值表=project 进水原始数据直取（design.nodes 中
#      kind=municipal_input 声明节点——非计算值；多声明取插入序首个，
#      app_influent 进水声明识别同款行为注记；矿井线无该节点=空表全
#      跳检）。kz 恒在（municipal_input 必需参+make_flow 守卫）+六指标
#      （WaterQuality 缺项 None 合法→缺项跳检不警：键缺席与值 None 均
#      不入单值表，该指标条目跳检零警告）。
#   R3 求值=solution.apply_constraints 单行 DataFrame 逐条求值
#      （app_maintenance L127 先例形态——DSL 单源禁手写求值；kz_band
#      双子句 and 语义=任一子句假即违规）。
#   R4 违规→PlantWarning：code=kb_warning_code(key)（码规则单源——
#      contracts.validation）、severity=条目 severity、param_key=该条
#      首个子句字段（expression_fields[0]——数据驱动单源）、
#      condition_key="plant"（厂级影响面常量段）、message=条目键+实际值
#      +带域数值（表达式原文承载——数值零抄录）——禁空话禁无出处措辞。
#   R5 纯投影：不重算不阻断（enforcement=flag 仪表灯语义——block 断路
#      器行为归 P1 后续批挂账）；kb 迭代=传入序（warn 序确定性）。
#
# 【接线红线（memo④——README「输入合理性带归属声明」节逐字引用）】
#   「unit_kinds 恒空=通用勾选判据恒不命中（执法面接线归 1A2——接线
#   红线：禁按 boundary_check 空表=全构筑物的 kind 专属语义实现
#   input_band 空表为全适用）」
#
# 【数值纪律】本文件不在魔法数字白名单——零数值字面量（带域数值全部
#   来自 kb 表达式原文，代码零抄录）。
#
# 【测试要求】合法零警告/非法码命中（kz/CODCR/混合）/缺项跳检两态/
#   选条判据 kind 直判/memo①冻结字段集对账/memo③映射表对账/memo②
#   负向锚（A/B/C 三跑）/run_full_calc 接线/双跑确定性。
#
# 【参照】1a2-20261004 任务书 §3.2/§3.4；contracts.validation（码键族）；
#   solution.constraints（DSL 单源）；app_maintenance.py（先例）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.quality import INDICATORS
from waterprint.contracts.validation import (
    PlantWarning,
    ValidationReport,
    kb_warning_code,
)
from waterprint.solution.constraints import (
    KbConstraint,
    apply_constraints,
    expression_fields,
)

INPUT_BAND_KIND: Final[str] = "input_band"
INLET_DECLARATION_KIND: Final[str] = "municipal_input"  # 内置图源市政进水声明
_KZ_FIELD: Final[str] = "kz"
_PLANT_SCOPE: Final[str] = "plant"  # 厂级影响面常量段（condition_key 载荷）
# 单值表准入字段白名单={kz}∪INDICATORS（真源=flow.kz+quality.INDICATORS）
_ADMITTED_FIELDS: Final[frozenset[str]] = frozenset({_KZ_FIELD}) | INDICATORS

# key→字段映射表（memo③——单源；对账测试逐条消费，禁在别处复刻）
INPUT_BAND_FIELDS: Final[Mapping[str, str]] = MappingProxyType({
    "inlet.kz_band": "kz",
    "inlet.quality_upper.cod": "CODCR",
    "inlet.quality_upper.bod5": "BOD5",
    "inlet.quality_upper.ss": "SS",
    "inlet.quality_upper.nh3n": "NH3N",
    "inlet.quality_upper.tn": "TN",
    "inlet.quality_upper.tp": "TP",
})


def _inlet_values(project: ProjectFile) -> dict[str, float]:
    """进水单值表：kz（恒在——make_flow 守卫）+在场六指标（R2 口径）。

    值非数值（None 等——WaterQuality 缺项合法形态）与键缺席同态跳过；
    无市政进水声明节点（矿井线）=空表（全跳检不警）。"""
    for params in project.design.nodes.values():
        if params.get("kind") != INLET_DECLARATION_KIND:
            continue
        return {
            field: float(value)
            for field, value in params.items()
            if field in _ADMITTED_FIELDS
            and isinstance(value, int | float)
            and not isinstance(value, bool)
        }
    return {}


def validation_summary_of(
    project: ProjectFile, constraints: Sequence[KbConstraint]
) -> ValidationReport:
    """厂级进水输入合理性校验（1A2 骨架）：kind 选条→单行表逐条求值→报告。

    纯投影不阻断（R5——仪表灯语义）；kb 迭代=传入序（warn 序确定性）。"""
    values = _inlet_values(project)
    if not values:
        return ValidationReport(warnings=())  # 无进水声明面=全跳检（R2）
    frame = pandas.DataFrame([values])
    warnings: list[PlantWarning] = []
    for kb in constraints:
        if kb.kind != INPUT_BAND_KIND:
            continue  # 选条判据=kind 直判（R1——unit_kinds 不参与选条）
        fields = expression_fields(kb.constraint.expression)
        if not set(fields) <= values.keys():
            continue  # 缺项跳检不警（R2——条目字段不全在场）
        passed = bool(
            apply_constraints(frame, [kb.constraint]).pass_matrix.to_numpy().all())
        if passed:
            continue
        field = fields[0]  # 首个子句字段（param_key 数据驱动单源——R4）
        warnings.append(PlantWarning(
            code=kb_warning_code(kb.constraint.key),
            condition_key=_PLANT_SCOPE,
            param_key=field,
            message=(
                f"进水输入合理性越带：{kb.constraint.key}——{field}="
                f"{values[field]!r} 违反 {kb.constraint.expression}"
            ),
            severity=kb.constraint.severity,
        ))
    return ValidationReport(warnings=tuple(warnings))
