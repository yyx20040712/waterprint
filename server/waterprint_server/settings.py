"""环境配置：env → Settings（pydantic-settings，一切可调参数的唯一住所）。

输入:  环境变量 / .env（前缀 WATERPRINT_）
输出:  Settings（不可变，应用启动注入）+ 路径基点分量校验工具
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/test_settings.py）
#
# 【公开接口】
#   class Settings(BaseSettings)：模型字段——
#       projects_dir（项目文件根，路径安全基点）
#       exports_dir（导出产物根，路径安全基点）
#       data_dir（数据包根：单价/系数/模板）
#       calc_workers（进程池大小，默认 CPU−1）
#       max_upload_mb / max_excel_rows（§18 上传面）
#       cache_entries / cache_mb（LRU 与落盘上限 §17.2）
#       task_queue_priorities（FIFO 优先级 §17.1）
#       log_level / log_file
#   get_settings() -> Settings（lru_cache，测试可覆盖）
#   safe_child(base, name) -> Path：R1 路径基点分量校验工具
#   ensure_directories(settings)：基点目录存在或可创建（fail fast）
#
# 【行为规格】
#   R1 一切路径类配置只作基点：业务路径 = 基点内拼接 + 分量校验
#      （拒绝 ".."/绝对路径/分隔符，§18 路径安全——routers/services
#      全部遵守，测试构造越界路径断言拒绝）。
#   R2 配置校验：目录存在或可创建；calc_workers >= 1；
#      非法值启动即失败（fail fast，不静默默认——锁定断言
#      Settings(calc_workers=0) 构造抛 ValidationError）。
#   R3 密钥/外发零依赖：内网工具无外部服务配置项；不出现任何
#      出站 URL 配置（§18 出站请求面——零外部请求是产品约束）。
#
# 【数值纪律】（ADR-009 附则 d：配置数值属 settings/env/数据包）
#   - max_upload_mb=10（10MB 与 core io._MAX_BYTES 同口径，白名单值）；
#   - max_excel_rows=10**2*10**2（=10000 行，§18 上传面幂积表达式）；
#   - cache_entries=10**2*10（=1000 条）、cache_mb=10**2（=100MB，
#     §17.2 LRU 上限，UF-08 注记"缓存属 incremental 优化层"随行）；
#   - max_json_depth=10**2（=100 层，与 core io._MAX_DEPTH 同源口径，
#     HTTP 上传面深度闸）；
#   - page_size_default=2*10**2（=200/页，§12.2 规格值）；
#   - task_queue_priorities 默认 {calc:10, enumerate:2, export_batch:1}
#     （§17.1 交互计算 > 枚举 > 批量导出——值域取白名单 {0,1,2,10}）。
#
# 【测试要求】默认值合法、非法值拒绝、路径越界防护的消费方行为。
#
# 【参照】重写计划 §18/§17.2；简报 SERVER D3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 分量白名单字符集（R1）：ASCII 字母数字开头，允许 -/_，长度上限 64——
# 拒绝 ".."、绝对路径、盘符与路径分隔符注入（§18 路径安全）。
_COMPONENT_PATTERN: re.Pattern[str] = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
_FAIL_FAST_FIELDS = ("calc_workers", "max_upload_mb", "max_excel_rows", "max_json_depth")
# 服务层引擎版本标识（可复算三元组成员——与 server/pyproject version 同源同步）。
ENGINE_VERSION: Final[str] = "waterprint-server 0.1.0"


class Settings(BaseSettings):
    """一切可调参数的唯一住所（不可变；启动注入，禁代码内联数值）。"""

    model_config = SettingsConfigDict(
        env_prefix="WATERPRINT_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="forbid",
    )

    projects_dir: Path = Path("projects")
    exports_dir: Path = Path("exports")
    data_dir: Path = Path("data")
    calc_workers: int = Field(default_factory=lambda: max(1, (os.cpu_count() or 2) - 1))
    max_upload_mb: int = 10
    max_excel_rows: int = 10**2 * 10**2  # 10000（§18 上传面；幂积保白名单字面量集）
    cache_entries: int = 10**2 * 10  # 1000（§17.2 LRU 条数上限）
    cache_mb: int = 10**2  # 100（§17.2 落盘体积上限 MB）
    task_queue_priorities: dict[str, int] = Field(
        default_factory=lambda: {"calc": 10, "enumerate": 2, "export_batch": 1}
    )
    log_level: str = "INFO"
    log_file: str = "waterprint-server.log"
    max_json_depth: int = 10**2  # 100（HTTP 上传面深度闸，与 core io._MAX_DEPTH 同源）
    page_size_default: int = 2 * 10**2  # 200（§12.2 分页默认页大小）

    @field_validator(*_FAIL_FAST_FIELDS)
    @classmethod
    def _positive_int(cls, value: int) -> int:
        """R2 fail fast：下限类配置 < 1 构造即 ValidationError（不静默默认）。"""
        if value < 1:
            raise ValueError(f"配置非法：{value} 须 >= 1（R2 fail fast——不静默默认）")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """进程级配置缓存（测试可用 get_settings.cache_clear() 覆盖）。"""
    return Settings()


def safe_child(base: Path, name: str) -> Path:
    """路径基点分量拼接（R1）：分量过白名单字符集，越界即拒（ValueError）。

    拒绝面：空串/绝对路径/../ 分隔符与盘符（正则只认单分量字符集，
    天然排除）。services 层捕获 ValueError 翻译为领域异常（4xx 面）。
    """
    if not isinstance(name, str) or not _COMPONENT_PATTERN.fullmatch(name):
        raise ValueError(
            f"路径分量非法：{name!r}（§18 路径安全——仅 ASCII 字母数字与 -/_，"
            "拒绝 ../绝对路径/分隔符注入；基点内拼接是唯一合法构造）"
        )
    return base / name


def ensure_directories(settings: Settings) -> None:
    """基点目录存在或可创建（R2 fail fast：创建失败=启动即败，不静默）。"""
    try:
        settings.projects_dir.mkdir(parents=True, exist_ok=True)
        settings.exports_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValidationError.from_exception_data(
            "Settings",
            [
                {
                    "type": "value_error",
                    "loc": ("projects_dir",),
                    "input": str(settings.projects_dir),
                    "ctx": {"error": ValueError(f"基点目录不可创建：{exc}")},
                }
            ],
        ) from exc
