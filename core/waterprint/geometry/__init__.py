"""L3 三维几何投影包根：设计结果 → 场景图（纯投影，CPU <10ms/厂）。

输入:  PlantResult（结果契约）+ assumptions
输出:  场景图 JSON（scene 正门，单位 m，前端只做类型化渲染）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【导出白名单】
#   scene:     build_scene
#   pools:     pool_primitives
#   internals: internal_instances
# 铁律（§10.5/§16 A7）：三维是结果 schema 的**纯投影**——只消费字段 ID，
# 不持有独立状态；前端 R3F 组件禁止自行推导业务几何（双源漂移根除）。
# ══════════════════════════════════════════════════════════════════

from waterprint.geometry.internals import internal_instances
from waterprint.geometry.pools import pool_primitives
from waterprint.geometry.scene import build_scene

__all__ = ["build_scene", "internal_instances", "pool_primitives"]
