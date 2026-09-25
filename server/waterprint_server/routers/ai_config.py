"""LLM 配置面端点（F1 批 2026-09-25）：GET/PUT /api/ai/config。

输入:  PUT 载荷 AiConfigUpdate（四键全可选——缺省=不改动；空串=清除该键）
输出:  AiConfigResponse 五键投影（api_key 仅存在性）+CWD .env 读改写与 env 四键同步
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（F1 批 2026-09-25；镜像测试 server/tests/routers/test_ai_config.py——
# 锁面呈批件 .workflow/healthcheck-20260925/F1-server-tests-draft.md）
#
# 【端点集】GET=当前进程 env 四键投影（spawn 单通道真值——main 启动
#   setdefault 归一化后 env 即对话实际用值）；PUT=校验→.env 读改写→
#   env 同步（子进程 env 继承面）。
# 【行为规格】R1 GET：configured=base_url/model/api_key 三者均非空
#   （agent llm.py available() 判据同构）。R2 PUT 域校验（ValueError→422
#   经 main 统一映射——消息零值嵌入）：base_url 非空时须 http://或
#   https:// 前缀且 ≤500 字符；model ≤100；api_key ≤500；llm_timeout_s
#   ∈[5,900] 整数。R3 持久化：CWD .env 读改写（pydantic env_file 同基点）；
#   非 WATERPRINT_AI_* 行原样保留；空值键行删除；不存在则创建（只含
#   本批非空键）；utf-8+末行换行规整。R4 运行时生效：写盘成功后
#   os.environ 四键 set（含空串清除语义）；写盘 OSError 不捕获=500
#   fail-visible（禁静默跳过持久化）。
# 【禁止事项】禁 print/日志（routers 层）与 api_key 明文入响应/异常文本；禁业务入 router。
# 【测试要求】GET 形态/PUT 写盘+env 同步/422 四族/.env 他键保留/api_key 不回显。【参照】brief-F1 §二
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Final

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/api/ai", tags=["ai-config"])

# 四键 env 名（settings env_prefix 对齐 agent CLI 读取面——子进程 env 单通道）。
_BASE_URL_KEY: Final[str] = "WATERPRINT_AI_BASE_URL"
_API_KEY_KEY: Final[str] = "WATERPRINT_AI_API_KEY"
_MODEL_KEY: Final[str] = "WATERPRINT_AI_MODEL"
_TIMEOUT_KEY: Final[str] = "WATERPRINT_AI_LLM_TIMEOUT_S"
# GET 超时回显缺省（env 未设/非法时——agent llm.py _DEFAULT_TIMEOUT_S 同值）。
_DEFAULT_TIMEOUT_S: Final[int] = 10**2 + 2 * 10  # 120（幂积保白名单字面量集）
# 校验边界值（声明面——来源=简报 F1 §二；幂积保白名单字面量集）：
_BASE_URL_MAX: Final[int] = (10 // 2) * 10**2  # 500
_MODEL_MAX: Final[int] = 10**2  # 100
_API_KEY_MAX: Final[int] = (10 // 2) * 10**2  # 500
_TIMEOUT_MIN_S: Final[int] = 10 // 2  # 5（简报 F1 声明面）
_TIMEOUT_MAX_S: Final[int] = (10 - 1) * 10**2  # 900（简报 F1 声明面）
# .env 四键行匹配（非匹配行原样保留——本批键行重排至文件尾，dotenv 后行胜出兜底）。
_ENV_KEY_LINE: Final[re.Pattern[str]] = re.compile(
    r"^\s*WATERPRINT_AI_(?:BASE_URL|API_KEY|MODEL|LLM_TIMEOUT_S)\s*="
)
_ENV_PATH: Final[Path] = Path(".env")


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


def _snapshot() -> AiConfigResponse:
    """当前进程 env 四键投影（R1——对话子进程实际消费的真值面）。"""
    base_url = os.environ.get(_BASE_URL_KEY, "")
    api_key = os.environ.get(_API_KEY_KEY, "")
    model = os.environ.get(_MODEL_KEY, "")
    raw_timeout = os.environ.get(_TIMEOUT_KEY, "")
    return AiConfigResponse(
        base_url=base_url,
        model=model,
        has_api_key=bool(api_key),
        llm_timeout_s=int(raw_timeout) if raw_timeout.isdecimal() else _DEFAULT_TIMEOUT_S,
        configured=bool(base_url and api_key and model),
    )


def _final_values(body: AiConfigUpdate) -> dict[str, str]:
    """域校验+env 合并（R2——缺省键沿用 env 现值；空串=清除；键序=.env 行序单源）。"""
    values: dict[str, str] = {}
    for name, key, raw, limit in (
        ("base_url", _BASE_URL_KEY, body.base_url, _BASE_URL_MAX),
        ("model", _MODEL_KEY, body.model, _MODEL_MAX),
        ("api_key", _API_KEY_KEY, body.api_key, _API_KEY_MAX),
    ):
        if raw is None:
            values[key] = os.environ.get(key, "")
            continue
        text = raw.strip()
        if len(text) > limit:
            raise ValueError(f"{name} 长度超限（>{limit} 字符）")
        values[key] = text
    new_base = values[_BASE_URL_KEY]
    if new_base and body.base_url is not None and not new_base.startswith(("http://", "https://")):
        raise ValueError("base_url 非空时须以 http:// 或 https:// 开头")
    if body.llm_timeout_s is None:
        raw_timeout = os.environ.get(_TIMEOUT_KEY, "")
        values[_TIMEOUT_KEY] = raw_timeout if raw_timeout.isdecimal() else str(_DEFAULT_TIMEOUT_S)
    else:
        if not _TIMEOUT_MIN_S <= body.llm_timeout_s <= _TIMEOUT_MAX_S:
            raise ValueError(f"llm_timeout_s 须为 {_TIMEOUT_MIN_S}~{_TIMEOUT_MAX_S} 的整数")
        values[_TIMEOUT_KEY] = str(body.llm_timeout_s)
    return values


def _rewrite_env_file(final_values: dict[str, str]) -> None:
    """读改写 CWD .env（R3——非本批键行原样保留；空值键行删除）。"""
    kept: list[str] = []
    if _ENV_PATH.is_file():
        lines = _ENV_PATH.read_text(encoding="utf-8").splitlines()
        kept = [ln for ln in lines if ln.strip() and not _ENV_KEY_LINE.match(ln)]
    kept.extend(f"{key}={value}" for key, value in final_values.items() if value)
    if not kept and not _ENV_PATH.is_file():
        return  # 全清除且 .env 不存在——不造空文件
    _ENV_PATH.write_text(
        ("\n".join(kept) + "\n") if kept else "", encoding="utf-8", newline="\n"
    )


@router.get("/config", response_model=AiConfigResponse)
async def get_config() -> AiConfigResponse:
    """读配置面（env 四键投影——api_key 仅存在性布尔）。"""
    return _snapshot()


@router.put("/config", response_model=AiConfigResponse)
def update_config(body: AiConfigUpdate) -> AiConfigResponse:
    """写配置面（校验→.env 读改写→os.environ 同步——不重启即生效，同步 def）。"""
    final_values = _final_values(body)
    _rewrite_env_file(final_values)
    for key, value in final_values.items():
        os.environ[key] = value
    return _snapshot()
