"""厂级进水输入合理性校验骨架+泥量量级互校：project 原始声明 × kb 求值。

输入:  ProjectFile（design.nodes 进水声明+泥量声明节点原始数据——非计算值）+
       Sequence[KbConstraint]（kb 装载产物——run_full_calc constraints 注入同源）
输出:  validation_summary_of → ValidationReport（PlantWarning 元组——
       app.run_full_calc 第四字段 validation 挂载面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（1A2 校验骨架批 1a2-20261004 §3.2 预裁决+1A3 泥量量级互校批
#   1a3-20261004 §3.3 预裁决；镜像测试 tests/app/test_app_validation.py；
#   app_maintenance.py 家族先例同构第十例——根模块聚合投影件，不进
#   import-linter layers 契约（app_trust/app_carbon 同款 unconstrained）。）
#
# 【公开接口】
#   INPUT_BAND_KIND: Final[str]（="input_band"）：选条判据 kind 符号单源。
#   MASS_BALANCE_KIND: Final[str]（="mass_balance"）：1A3 泥量互校族选条
#       kind 符号单源（plant 级跨节点质量规模互校——对子=ds_primary vs
#       全厂进水 SS 负荷，仅此一对）。
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
#       无关、与工况无关（进水声明为静态原始面）；1A3 起含泥量互校面。
#
# 【行为口径】
#   R1 选条判据=kind 直判（input_band/mass_balance 两族同款——接线红线
#     见下方逐字引用；unit_kinds 恒空不参与选条）。
#   R2 进水单值表=project 进水原始数据直取（design.nodes 中
#      kind=municipal_input 声明节点——非计算值；多声明仅取插入序首个
#      同款；识别判据不同（本件=kind 字面判据 vs app_influent=无入边+
#      outflows 结构判据）——矿井线排除=1A2 裁决语义（无该节点=空表全
#      跳检）。kz 恒在=装配路径 make_flow 守卫背书（路径外直调无背书
#      ——kz 键缺席即跳检）+q_avg_daily（1A3 增准——WaterFlow 契约字段
#      同源）+六指标（None/键缺席均不入表=跳检零警告）。
#   R3 求值=solution.apply_constraints 单行 DataFrame 逐条求值
#      （app_maintenance L127 先例形态——DSL 单源禁手写求值；双子句
#      and 语义=任一子句假即违规）。
#   R4 违规→PlantWarning：code=kb_warning_code(key)（码规则单源——
#      contracts.validation）、severity=条目 severity、param_key=该条
#      首个子句字段（expression_fields[0]——数据驱动单源）/泥量互校面
#      =ds_primary（物理声明参数位——比值列名不作物参数位）、
#      condition_key="plant"（厂级影响面常量段）、message=条目键+实际值
#      +带域数值（表达式原文承载——数值零抄录）——禁空话禁无出处措辞。
#   R5 纯投影：不重算不阻断（enforcement=flag 仪表灯语义——block 断路
#      器行为归 P1 后续批挂账）；kb 迭代=传入序（warn 序确定性）。
#   R6 泥量互校（1A3——UF-55）：泥量声明面=扫 design.nodes 找 params 含
#      数值 ds_primary 键的节点（非节点 ID 字面量判据——入流直值模式
#      无此键自然不中；插入序取首=_inlet_values 同款口径）；互校基准=
#      全厂进水 SS 负荷（SS×q_avg_daily 换算 kg/d）；kb 表达式落
#      primary_ss_ratio 派生比值列（DSL 右值不支持字段算术——起草
#      算术式的最小面落地形态，比值列=ds_primary÷ss_load 本分支注入）；
#      跳检=缺任一面不警（①无进水声明节点〔R2 早退〕②SS 或 q_avg_daily
#      缺席③无 ds_primary 数值键）。
#   R7 泥量互校 message=「泥量量级互校越带：{key}——ds_primary={值!r}
#      （{ratio:.4f}×全厂 SS 负荷 {ss_load:.1f} kg/d）违反 {表达式}」
#      ——三要素（实际值+带域数值+条目键）+ratio/ss_load 消息面展示
#      计算（非校验面——不引入代码阈值，仅格式化呈现）。
#
# 【接线红线（memo④——README「输入合理性带归属声明」节逐字引用）】
#   「unit_kinds 恒空=通用勾选判据恒不命中（执法面接线归 1A2——接线
#   红线：禁按 boundary_check 空表=全构筑物的 kind 专属语义实现
#   input_band 空表为全适用）」——mass_balance 同款（1A3 收录边界
#   同文注记：恒 []=kind 直判选条非全适用）。
#
# 【数值纪律】本文件不在魔法数字白名单——零数值字面量（带域数值全部
#   来自 kb 表达式原文，代码零抄录）；mg/L·m³/d→kg/d 量纲换算当量经
#   pint 因子单源获取（contracts.quantity R2「换算必须经 pint 完成，
#   禁止手写换算系数」——UF-20 冻结白名单 MASS 仅 kg 无前缀对，milli
#   前缀因子取 LENGTH 对 mm→m：因子=无量纲 SI 前缀 10⁻³）。
#
# 【测试要求】合法零警告/非法码命中（kz/CODCR/混合）/缺项跳检两态/
#   选条判据 kind 直判/memo①冻结字段集对账/memo③映射表对账/memo②
#   负向锚（A/B/C 三跑）/run_full_calc 接线/双跑确定性/1A3 泥量族
#   （荒谬上界+2 量级双向+带内+边界邻接+三种跳检+kind 直判+三案例
#   带内零警告）。
#
# 【参照】1a2-20261004 任务书 §3.2/§3.4+1a3-20261004 §3.1/§3.3；
#   contracts.validation（码键族）；solution.constraints（DSL 单源）；
#   app_maintenance.py（先例）；contracts.quantity（pint 因子单源）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.quality import INDICATORS
from waterprint.contracts.quantity import DimKey, parse
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
MASS_BALANCE_KIND: Final[str] = "mass_balance"  # 1A3 泥量互校族（plant 级）
INLET_DECLARATION_KIND: Final[str] = "municipal_input"  # 内置图源市政进水声明
_KZ_FIELD: Final[str] = "kz"
_Q_AVG_DAILY_FIELD: Final[str] = "q_avg_daily"
_SS_FIELD: Final[str] = "SS"
_DS_PRIMARY_FIELD: Final[str] = "ds_primary"  # 泥量声明面字段（hebing params）
# kb mass_balance 表达式字段（派生比值列——R6：本分支注入单行表）
_SS_LOAD_RATIO_FIELD: Final[str] = "primary_ss_ratio"
_PLANT_SCOPE: Final[str] = "plant"  # 厂级影响面常量段（condition_key 载荷）
# 单值表准入字段白名单={kz,q_avg_daily}∪INDICATORS（真源=flow.WaterFlow
# 两字段+quality.INDICATORS——1A3 增准 q_avg_daily：互校基准面）
_ADMITTED_FIELDS: Final[frozenset[str]] = (
    frozenset({_KZ_FIELD, _Q_AVG_DAILY_FIELD}) | INDICATORS)
# mg/L·m³/d→kg/d 量纲换算当量（10⁻³ kg/d 每 1 mg/L·m³/d）：pint 因子
# 单源（R2 禁手写换算系数）；UF-20 冻结白名单 MASS 仅 kg 无前缀对，
# milli 前缀因子取 LENGTH 对 mm→m（因子=无量纲 SI 前缀，跨量纲同值）。
_SS_LOAD_UNIT_KG_D: Final[float] = parse(1.0, "mm", DimKey.LENGTH)

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
    """进水单值表：kz（恒在——make_flow 守卫）+q_avg_daily+在场六指标。

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


def _sludge_ds_primary(project: ProjectFile) -> float | None:
    """泥量声明面（1A3——R6）：插入序首个 params 含数值 ds_primary 键的
    节点（非节点 ID 字面量判据——入流直值模式无此键自然不中）。"""
    for params in project.design.nodes.values():
        value = params.get(_DS_PRIMARY_FIELD)
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
    return None


def _plant_ss_load(values: Mapping[str, float]) -> float | None:
    """全厂进水 SS 负荷 kg/d（R6 互校基准面）：SS×q_avg_daily×换算当量
    （pint 因子单源）。SS 或 q_avg_daily 缺席（未入单值表=缺项/非数值）
    =None——跳检。"""
    ss = values.get(_SS_FIELD)
    q_avg_daily = values.get(_Q_AVG_DAILY_FIELD)
    if ss is None or q_avg_daily is None:
        return None
    return ss * q_avg_daily * _SS_LOAD_UNIT_KG_D


def validation_summary_of(
    project: ProjectFile, constraints: Sequence[KbConstraint]
) -> ValidationReport:
    """厂级进水输入合理性校验+泥量量级互校（1A2/1A3）：kind 选条→单行表
    逐条求值→报告。

    纯投影不阻断（R5——仪表灯语义）；kb 迭代=传入序（warn 序确定性）。"""
    values = _inlet_values(project)
    if not values:
        return ValidationReport(warnings=())  # 无进水声明面=全跳检（R2）
    frame = pandas.DataFrame([values])
    ds_primary = _sludge_ds_primary(project)
    warnings: list[PlantWarning] = []
    for kb in constraints:
        if kb.kind == INPUT_BAND_KIND:
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
        elif kb.kind == MASS_BALANCE_KIND:
            ss_load = _plant_ss_load(values)
            if ds_primary is None or ss_load is None:
                continue  # 缺面跳检不警（R6——③无声明/②基准面缺）
            ratio = ds_primary / ss_load
            row = {**values, _DS_PRIMARY_FIELD: ds_primary,
                   _SS_LOAD_RATIO_FIELD: ratio}
            fields = expression_fields(kb.constraint.expression)
            if not set(fields) <= row.keys():
                continue  # 表达式字段不全在场（DSL 泛化门——缺即跳检）
            passed = bool(apply_constraints(
                pandas.DataFrame([row]), [kb.constraint],
            ).pass_matrix.to_numpy().all())
            if passed:
                continue
            warnings.append(PlantWarning(
                code=kb_warning_code(kb.constraint.key),
                condition_key=_PLANT_SCOPE,
                param_key=_DS_PRIMARY_FIELD,  # 物理声明参数位（R4/R7）
                message=(
                    f"泥量量级互校越带：{kb.constraint.key}——ds_primary="
                    f"{ds_primary!r}（{ratio:.4f}×全厂 SS 负荷 {ss_load:.1f}"
                    f" kg/d）违反 {kb.constraint.expression}"
                ),
                severity=kb.constraint.severity,
            ))
    return ValidationReport(warnings=tuple(warnings))
