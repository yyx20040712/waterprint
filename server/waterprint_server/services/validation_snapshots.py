"""validation 源 C 伴生件：计算期单元快照警告（unit_api.Warning）聚合投影。

输入:  PlantResult.conditions（condition_key → unit_id → UnitResultSnapshot
       快照 warnings 元组）+序轴（record condition_keys 投影）+聚合分组桶
输出:  merge_snapshot_warnings（源 C 并入分组桶——去重键三元组同族）+
       max_severity/SEVERITY_ASC（severity 分级单源——主件与源 C 共用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（F4 扩源批 2026-11-19——e2e-audit 证实计算期 6 条真警告在
#   聚合面全丢失；镜像测试 server/tests/services/test_validation.py）
#
# 【公开接口】
#   merge_snapshot_warnings(plant, condition_order, grouped) -> None：
#       源 C 并入（就地写分组桶——主件 _aggregated_warnings 第三源）：
#       逐序轴工况×逐单元快照×逐 warning 投影聚合行材料——code=
#       unit_warning_code(unit_id, warning.source)（码派生单源=contracts.
#       validation R1 扩族：source=检查条目出处标识，同检查跨工况恒定，
#       同 unit 同 param_key 多检查模板不吞行）/param_key（None→空串
#       哨兵——无调节方向如实，聚合行 schema param_key:str 必填）/scope=
#       unit_id（影响面=单元级——AUDIT-#5 定案：unit_api.Warning.
#       condition_key=工况键，映射到命中工况清单而非 scope）/命中工况
#       清单=[快照所属工况]（序轴迭代序过滤——源 B 同制）/message=首例
#       （§2 首例语义：序轴首个命中实例，跨工况数值差异不双消息）/
#       severity=max over 命中实例（§3 同制）。
#   SEVERITY_ASC: Final 元组（分级序 INFO<WARN<ERROR——§3 max 判据单源）
#   max_severity(left, right) -> Severity：分级取最严重（主件源 A/B
#       累积与源 C 累积共用——自 validation.py 迁入的单源面）
#
# 【行为规格】
#   R1 前缀域隔离：源 C 码恒 "unit." 前缀，与源 A/B 的 kb 派生码
#      （"kb." 前缀）结构性不撞——同键合并仅合成数据可造，撞上按 §2
#      合并语义处理（message 源 A 优先），无害。
#   R2 序轴口径：conditions.get(ck, {}) 缺工况安全（序轴含 summary-only
#      键时快照面可能缺席——零警告非错误）。
#   R3 v1 边界解除依据：docs/archive/warning-aggregation.md §4「第三
#      警告面显式排除（v1 边界冻结）……=本规格版本升级另批扩源」——
#      本件即该扩源批的实现载体；规格面=主件契约头 R4（同批改写）。
#
# 【数值纪律】本文件不在魔法数字白名单——零数值字面量（分级序由元组
#   index 承载）。
#
# 【测试要求】源 C 跨工况聚合（命中清单序=序轴序）/首例 message/
#   severity 累积 max/param_key None 空串/码=unit_warning_code 派生/
#   同 unit 同 param_key 双模板不吞（test_validation.py 源 C 段）。
#
# 【参照】services/validation.py（主件——消费本件并入分组桶）；
#   contracts/validation.py（unit_warning_code 码派生单源）；
#   contracts/unit_api.py（Warning UF-17 冻结六字段——condition_key=
#   工况键，AUDIT-#5 §3.7 映射定案）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any, Final

from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.unit_api import Severity
from waterprint.contracts.validation import unit_warning_code

__all__ = ["SEVERITY_ASC", "max_severity", "merge_snapshot_warnings"]

# severity max 分级序（§3——ERROR>WARN>INFO；元组 index 承载零数值字面量）
SEVERITY_ASC: Final[tuple[Severity, ...]] = (
    Severity.INFO, Severity.WARN, Severity.ERROR)

# 源 C param_key 缺席哨兵（unit_api.Warning.param_key 可 None——无调节
# 方向如实投影空串；聚合行 schema param_key:str 必填）
_NO_PARAM_KEY: Final[str] = ""


def max_severity(left: Severity, right: Severity) -> Severity:
    """severity 分级取最严重（§3：max over 命中实例——ERROR>WARN>INFO；
    元组 index 分级，零数值字面量）。"""
    if SEVERITY_ASC.index(left) >= SEVERITY_ASC.index(right):
        return left
    return right


def merge_snapshot_warnings(
    plant: PlantResult,
    condition_order: tuple[str, ...],
    grouped: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    """源 C 并入（R1~R3）：快照 warnings → 分组桶（就地写——主件第三源）。

    桶材料：snapshot_message=首例 message（§2）/severity=累积 max（§3）/
    hits=命中工况清单（序轴迭代序）。"""
    for condition_key in condition_order:
        for unit_id, snapshot in plant.conditions.get(condition_key, {}).items():
            for warning in snapshot.warnings:
                code = unit_warning_code(unit_id, warning.source)
                param_key = (
                    warning.param_key if warning.param_key is not None
                    else _NO_PARAM_KEY
                )
                dedup = (code, param_key, unit_id)
                record = grouped.get(dedup)
                if record is None:
                    grouped[dedup] = {
                        "source_a": None, "entry": None, "node": unit_id,
                        "hits": [condition_key], "severity": warning.severity,
                        "snapshot_message": warning.message,
                    }
                else:
                    record["hits"].append(condition_key)
                    record["severity"] = max_severity(
                        record["severity"], warning.severity)
