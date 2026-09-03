"""IFC 导出包正门：SceneGraph → IfcOpenShell 模型（BIM 互操作纯投影，L5c）。

输入:  waterprint.geometry 场景图 + ifcopenshell（LGPL 独立 pip 依赖，C1）
输出:  build_ifc / write_ifc（builder 正门再导出）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（L5c 原型启动 2026-09-03；镜像测试 tests/ifc_export/test_ifc.py）
#
# 【导出白名单】
#   builder:   build_ifc + write_ifc
# 铁律（§10.2 路线 C / LGPL 评估 C1~C6，2026-09-02）：本包是 geometry
#   场景图的 BIM 互操作投影——纯投影消费 SceneGraph，不持有独立状态；
#   import 白名单=ifcopenshell 本体+waterprint.geometry/contracts（C2
#   ——file-contracts.md 登记+importlinter 四契约机器拦截）；禁引入
#   Bonsai/IfcSverchok 等 GPL 子模块。
# ══════════════════════════════════════════════════════════════════

from waterprint.ifc_export.builder import build_ifc, write_ifc

__all__ = ["build_ifc", "write_ifc"]
