"""平流沉砂池单元包根：白名单导出（mine_water_chenshachi）。

输入:  manifest.py 的清单实例与 compute.py 的单元工厂
输出:  白名单导出 UNIT_ID/make_unit/manifest 三名（discover 探测面=manifest/make_unit）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【身份】UNIT_ID = "mine_water_chenshachi"；业务线：矿井水处理线；
#   旧系统对应 mod：kw_chenshachi（迁移交叉对照，非依据）。
# 【工艺位置】上游：mine_water_tiaojiechi 调节池；下游：
#   mine_water_ningjiao 混凝反应池（保护下游混凝/分离段免受磨损砂粒）。
# 【实现约定】本包结构由 _template 冻结（AGENTS.md §11）：
#   - 包外只经本 __init__ 白名单访问；禁 import 其他单元包；
#   - 与市政同名包 municipal/chenshachi（旋流型）零 import 零参数
#     复用（§14.3：本包=平流型主线——水平流速 0.15~0.30 m/s × 停留
#     30~60 s 主控、浅池 0.4~1.2 m，键空间 factor.mine_chenshachi.*
#     经 mine_ 限定）；
#   - 公式 KC-F1~F10 与参数数值真源=docs/norms/mine_water_chenshachi.md
#     起草表（2026-08-27，数据策略 v2，待追认）+ data/coefficients
#     0.5.0 数据包（removal.mine_chenshachi.ss 0.15 砂粒组分——COD
#     非混凝沉淀滤池段不建键，BOD5 全线不建键）；
#   - 导出面=manifest + make_unit（AGENTS §11 两名铁律的工厂形态读法，
#     units_lib/__init__ D6 注记）。
# ══════════════════════════════════════════════════════════════════

from waterprint.units_lib.mine_water.chenshachi.compute import make_unit
from waterprint.units_lib.mine_water.chenshachi.manifest import UNIT_ID, manifest

__all__ = ["UNIT_ID", "make_unit", "manifest"]
