"""全厂进水负荷供数投影：进水声明节点 Q/浓度 + terminal 出水 TN → summary 负荷平键。

输入:  PlantResult.conditions（逐工况单元快照——进水节点 outflows/outqualities）
       + edges（无入边判定）+ summary 六指标面（terminal 出水 TN——IF4 源）
       + RunEnv.coefficients（factor.influent.s_per_d + factor.carbon.conv_mg_l_kg_m3）
输出:  influent_summary_of（app.run_full_calc 经 _with_influent 合并注入 summary——
       开放映射槽位，result_schema 零改）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（B4-2c 终裁定案 .workflow/b4-2c/master-ruling.md D3；镜像测试
#   tests/app/test_app_influent.py；app_energy.py 拆分先例同构第七例
#   ——根模块聚合投影件，不进 import-linter layers 契约（app_trust
#   同款 unconstrained）。
#
# 【公开接口】
#   influent_summary_of(plant, edges, coefficients, effluent_summary)
#       -> dict[工况→dict[平键→float]]
#       纯投影：逐工况从进水声明节点投 Q/负荷平键（sparse）。
#   _with_influent(base, extra) -> dict[...]
#       summary 合并注入（_with_opex 同语义——同工况字典 update、
#       base 键族优先，两族键集无交集由命名域保证）。
#
# 【进水声明节点识别（终裁 D3 路①）】无入边（不在 edges dst 集）且
#   outflows 含 f"{unit_id}.out.q_avg_daily" 键的单元——q_avg_daily 为
#   进水声明标志键（municipal inlet/mine_water_input 双案实证唯一）；
#   快照插入序取首个（多进水声明=不支持场景，行为注记非断言）。
#
# 【公式（IF1~IF4，逐工况 sparse）】
#   IF1 influent_flow_m3_d = q_avg_daily[m3/s] × factor.influent.s_per_d
#   IF2 influent_tn_load_kg_d = TN[mg/L] × Q × factor.carbon.conv_mg_l_kg_m3
#   IF3 influent_bod5_load_kg_d = BOD5[mg/L] × Q × conv（同上键）
#   IF4 effluent_tn_load_kg_d = effluent_summary[工况][TN][mg/L] × Q × conv
#
# 【行为口径】
#   R1 sparse：换算键缺席（factor.influent.*/factor.carbon.conv 未装载
#      的系数包合法）或进水声明节点缺席或对应浓度键缺席→该键跳过；
#      全缺席→无 influent_* 键（矿井线无 BOD5 声明→IF3 跳过即此语义）。
#   R2 纯投影：不重算不造数——声明值×换算常数的乘加；逐工况同值合法
#      （进水声明为静态面——q_avg_daily 与工况无关，终裁 D3 口径）。
#   R3 effluent TN 源=summary 六指标面（terminal 投影先例 _summary_of
#      产物——本件不重复 terminal 判定逻辑，消费现成面）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量无（仅空迭代求和）。
#
# 【测试要求】进水节点识别/sparse 键族（浓度/换算/节点三态缺席）/
#   逐工况同值/纯函数双跑/effluent TN 联动。
#
# 【参照】.workflow/b4-2c/master-ruling.md D3；app.py _with_energy；
#   app_energy.py（先例）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.run_env import CoefficientsView

_KEY_S_PER_D: Final[str] = "factor.influent.s_per_d"
_KEY_CONV: Final[str] = "factor.carbon.conv_mg_l_kg_m3"
_Q_FIELD: Final[str] = "q_avg_daily"
_FLOW_KEY: Final[str] = "influent_flow_m3_d"
# 进水浓度 outqualities 键 → summary 负荷平键（IF2/IF3）
_INFLUENT_LOADS: Final[dict[str, str]] = {
    "TN": "influent_tn_load_kg_d",
    "BOD5": "influent_bod5_load_kg_d",
}
_EFFLUENT_TN_LOAD: Final[str] = "effluent_tn_load_kg_d"


def influent_summary_of(
    plant: PlantResult,
    edges: tuple,
    coefficients: CoefficientsView,
    effluent_summary: Mapping[str, Mapping[str, float]],
) -> dict[str, dict[str, float]]:
    """IF1~IF4 纯投影：进水声明节点 Q/浓度+terminal 出水 TN → 负荷平键（sparse）。"""
    keys = set(coefficients.keys("factor."))
    has_s_per_d = _KEY_S_PER_D in keys
    has_conv = _KEY_CONV in keys
    dst_units = {edge.dst.unit_id for edge in edges}
    summary: dict[str, dict[str, float]] = {}
    for condition_key, snapshot in plant.conditions.items():
        fields: dict[str, float] = {}
        inlet = next(
            (unit for unit_id, unit in snapshot.items()
             if unit_id not in dst_units
             and f"{unit_id}.out.{_Q_FIELD}" in unit.outflows),
            None,
        )
        if inlet is not None and has_s_per_d:
            unit_id = inlet.unit_id
            flow = (
                inlet.outflows[f"{unit_id}.out.{_Q_FIELD}"]
                * coefficients.get(_KEY_S_PER_D).value
            )
            fields[_FLOW_KEY] = flow
            if has_conv:
                conv = coefficients.get(_KEY_CONV).value
                for indicator, target in _INFLUENT_LOADS.items():
                    conc = inlet.outqualities.get(f"{unit_id}.out.{indicator}")
                    if conc is not None:
                        fields[target] = conc * flow * conv
                tn_eff = effluent_summary.get(condition_key, {}).get("TN")
                if tn_eff is not None:
                    fields[_EFFLUENT_TN_LOAD] = tn_eff * flow * conv
        summary[condition_key] = fields
    return summary


def _with_influent(
    base: dict[str, dict[str, float]], extra: dict[str, dict[str, float]]
) -> dict[str, dict[str, float]]:
    """summary 合并注入：既有平键族 + influent_* 负荷键（B4-2c 终裁——同工况
    字典 update；base 键族优先，两族键集无交集由命名域保证）。"""
    for condition_key, fields in extra.items():
        if condition_key in base:
            base[condition_key].update(fields)
    return base
