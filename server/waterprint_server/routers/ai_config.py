"""LLM 配置面端点（F1 批 2026-09-25；回炉批瘦身——逻辑迁 ai_config_store）。

输入:  PUT 载荷 AiConfigUpdate（四键全可选——缺省=不改动；空串=清除该键）
输出:  AiConfigResponse 五键投影（api_key 仅存在性）——校验/持久化/env 同步
       全在 waterprint_server.ai_config_store（sse_limits 顶层共享件先例）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（F1 批 2026-09-25；回炉批——门一 k1 B-1/W-1/W-7/N-8 处置后
# 路由回归薄壳；镜像测试 server/tests/routers/test_ai_config.py——
# 锁面呈批件 .workflow/healthcheck-20260925/F1-server-tests-draft.md）
#
# 【端点集】GET=当前进程 env 四键投影（spawn 单通道真值）；PUT=校验→
#   .env 原子读改写→env 同步（ai_config_store.update 锁内串行全流程）。
# 【行为规格】R1 GET：configured=base_url/model/api_key 三者均非空
#   （agent llm.py available() 判据同构）。R2 PUT 域校验 ValueError→422
#   经 main 统一映射（消息零值嵌入）：控制字符全拒（防 .env 行注入）/
#   长度/scheme+主机部/超时域——细则=ai_config_store 规格头。R3 持久化：
#   tmp+os.replace 原子写、BOM 容忍读、非本批键行与空行原样保留、空值
#   键行删除、GBK 等非 UTF-8=422 引导转存。R4 运行时生效：写盘成功后
#   env 四键同步（不重启即生效）。
# 【禁止事项】禁 print/日志（routers 层）与 api_key 明文入响应/异常文本；
#   禁业务入 router（本件仅协议薄壳）。
# 【测试要求】GET 形态/PUT 写盘+env 同步/422 族（含控制字符注入拒绝）/
#   .env 他键保留/api_key 不回显。【参照】brief-F1 §二+门一审包 A 回炉条目
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from waterprint_server.ai_config_store import snapshot, update

router = APIRouter(prefix="/api/ai", tags=["ai-config"])


class AiConfigUpdate(BaseModel):
    """PUT 载荷（四键全可选——缺省=不改动；空串=清除该键）。"""

    model_config = ConfigDict(extra="forbid")

    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    llm_timeout_s: int | None = None


class AiConfigResponse(BaseModel):
    """配置面五键投影（api_key 只投影存在性——值零回传零日志）。"""

    base_url: str
    model: str
    has_api_key: bool
    llm_timeout_s: int
    configured: bool


@router.get("/config", response_model=AiConfigResponse)
async def get_config() -> AiConfigResponse:
    """读配置面（env 四键投影——api_key 仅存在性布尔）。"""
    return AiConfigResponse(**snapshot())


@router.put("/config", response_model=AiConfigResponse)
def update_config(body: AiConfigUpdate) -> AiConfigResponse:
    """写配置面（校验→.env 原子读改写→os.environ 同步——不重启即生效，同步 def）。"""
    return AiConfigResponse(
        **update(
            body.base_url, body.model, body.api_key, body.llm_timeout_s
        )
    )
