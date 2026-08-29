"""单元元数据端点：GET /api/units + GET /api/assumptions（静态只读目录）。

输入:  无（静态 catalog——服务层 lru_cache 直投，无请求参数）
输出:  UnitCatalog/AssumptionCatalog（服务层冻结模型——response_model 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（META1 D2 2026-08-29；镜像测试 server/tests/routers/test_units.py）
#
# 【端点集（v1 冻结）】
#   GET /api/units         单元目录（36 条=32 包+4 内置 kind——params 批
#                          manifest 字段渲染与 canvas 流体色/中文名/摘要
#                          数据面前置）
#   GET /api/assumptions   设计假设清单（21 条——registry 代码即数据投影）
#
# 【行为规格】
#   R1 静态只读：无请求参数无 ctx（D6 不分页整发）；服务层 lru_cache
#      单例直投——router 零 if 零业务（≤150 行）。
#   R2 响应模型=服务层冻结 pydantic 模型（SceneGraph 先例：经 services
#      再导出——禁协议层重复声明漂移面）。
#   R3 确定性：双 GET sort_keys 字节同（服务层 R4 继承——端点测试常驻）。
#
# 【测试要求】路由集恰两件、200 形态（36 单元/21 假设/端口表）、双跑字节同。
#
# 【参照】META1 简报 D2/D3/D6；scene.py 同构（FE1 D1）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter

from waterprint_server.services import units as service
from waterprint_server.services.units import AssumptionCatalog, UnitCatalog

# 双端点同路由器（路由集恰两件）：prefix=/api 母面承载 /api/units 与
# /api/assumptions 两冻结路径共用 tags=["units"]（META1 D2 端点范围）。
router = APIRouter(prefix="/api", tags=["units"])


@router.get("/units", response_model=UnitCatalog)
async def list_units() -> UnitCatalog:
    """单元目录（32 包+4 内置 kind；unit_id 序+内置排末——D1/D5/D6）。"""
    return service.list_units()


@router.get("/assumptions", response_model=AssumptionCatalog)
async def list_assumptions() -> AssumptionCatalog:
    """设计假设清单（21 条 registry 声明序——六字段取五，D2/D6）。"""
    return service.list_assumptions()
