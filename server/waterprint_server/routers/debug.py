"""debug 观测端点：操作链集中观测面（只读聚合，零任务副作用）。

输入:  项目 id（路径）——任务时间线+最新结果三源聚合请求
输出:  OpsChainResponse（pydantic 冻结模型直用——服务件单源声明）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-1 实现批 2026-09-19；《裁决书》方案五①）
#
# 【端点集】
#   GET /api/debug/ops-chain/{project_id}   操作链观测面（B4-1，端点
#       计数 35→36——裁决书方案五①授权破面）
#
# 【行为规格】
#   R1 只读聚合：零任务副作用（不提交/不取消/不触碰注册表状态）；
#       服务面全部行为规格见 services/ops_debug.py 规格头（R1~R7）。
#   R2 404 面：项目不存在=ProjectNotFoundError（main 类名义表映射）；
#       PL-03 契约枚举——responses 声明使 openapi 与行为一致（trust
#       同制）。无 done calc=200 空块（诊断面语义，非 404——与 trust
#       消费面语义不同源不同判）。
#   R3 鉴权/装配：include 级 verify_token 依赖（main 装配，非事件流
#       面）；路径分量安全经 read_project→safe_child 链（trust 同构）。
#
# 【测试要求】仓外探针承载（任务书 D5——server/tests 锁面约束）。
#
# 【参照】《裁决书》方案五①；routers/calc.py（trust/compare 同制先例）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
from typing import Any, Final

from fastapi import APIRouter, Request, status

from waterprint_server.errors import ErrorResponse
from waterprint_server.services.ops_debug import OpsChainResponse, build_ops_chain

router = APIRouter(prefix="/api/debug", tags=["debug"])

# PL-03 契约枚举（B4-1）：404=项目不存在（无 done calc 是 200 空块非 404）。
_OPS_CHAIN_RESPONSES: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "项目不存在",
    },
}


@router.get(
    "/ops-chain/{project_id}",
    response_model=OpsChainResponse,
    responses=_OPS_CHAIN_RESPONSES,
)
async def get_ops_chain(project_id: str, request: Request) -> OpsChainResponse:
    """操作链观测面（项目任务时间线+最新结果诊断/警告/trace 三源聚合——
    B4-1：注册序时间线，无 done calc=latest_calc 空块降级呈现；to_thread
    承载大结果件反序列化[万级 trace 面——FD PD6 先例]防事件循环阻塞）。"""
    return await asyncio.to_thread(
        build_ops_chain, request.app.state.ctx, project_id
    )
