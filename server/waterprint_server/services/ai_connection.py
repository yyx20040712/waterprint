"""ai_connection 服务用例：MCP 接入状态四项检查+两份工作区配置 merge 原子写（AI2）。

输入:  ServiceContext（settings.data_dir 上溯推导工作区路径）+ 运行环境
      （shutil.which 解析 uv/PathFinder 探测 agent 包）
输出:  AiConnectionStatus/AiConnectionSetupResult（server 侧 pydantic 冻结
      模型——routers 直用）+UvNotFoundError（400 面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（AI2-CONNECT 2026-09-13；镜像测试 server/tests/services/
# test_ai_connection.py）
#
# 【公开接口】
#   connection_status(ctx) -> AiConnectionStatus
#       （四项检查：config_written/agent_importable/uv_path/sandbox_root
#       +ready 聚合——GET /api/ai/connection）
#   setup_connection(ctx) -> AiConnectionSetupResult
#       （一键接入：两份工作区 .zcode/config.json merge 式原子写
#       waterprint server 条目——POST /api/ai/connection/setup）
#   AiConnectionStatus/McpServerEntry/AiConnectionSetupResult
#       （响应模型面——routers response_model 直用，trust 先例：禁协议层
#       重复声明漂移面）
#   UvNotFoundError（400 面——uv 不在 PATH）
#
# 【行为规格】
#   R1 路径动态推导（禁硬编码绝对路径）：仓库根=ctx.settings.data_dir.
#      resolve().parent；父目录=仓库根.parent；写目标=仓库根与父目录各一份
#      .zcode/config.json（战役背景真源：会话开在父目录而配置只在仓库根
#      的作用域坑——两份同写根治）；沙箱根=父目录/ai-sandbox；agent 目录
#      =仓库根/agent。写目标为固定推导路径、无用户输入路径参数（无越权面）。
#   R2 状态四项：config_written=两份配置任一含 mcp.servers.waterprint 条目
#      （附两路径清单——损坏/缺失 JSON 视为未写）；agent_importable=
#      PathFinder 在 agent 目录探测 waterprint_agent 包（零 sys.path 污染）；
#      uv_path=shutil.which("uv")；ready=前三项全真（诚实聚合不虚报）。
#   R3 merge 语义：读现有 JSON（损坏/缺失视为 {}）、mcp.servers.waterprint
#      键写入、保留其他 server 条目与无关顶层键；结构性损坏（mcp/servers
#      非 dict）同归重建不弃写。
#   R4 原子写（GR-38 同款）：确定性 JSON（sort_keys+UTF-8）+同分区 .tmp
#      唯一名+os.replace；.zcode 目录缺失即建（mkdir parents）；write/
#      replace 抛错 finally 清理 .tmp 残留（回炉 FIX-4）。
#   R5 server 条目固定 schema：{command: uv 绝对路径（which 缺=None 抛
#      UvNotFoundError——400）, args: [run, --directory, <仓库根>/agent,
#      waterprint-mcp], env: {WATERPRINT_AI_SANDBOX: <父目录>/ai-sandbox}}
#      ——与 E:\class\智水蓝图\.zcode\config.json 已验证形态逐字同源。
#   R6（回炉 2026-09-13·门一）锚点校验+半写补偿：_workspace 校验
#      <仓库根>/agent/waterprint_agent 锚点（缺=WorkspaceLayoutError 400
#      ——data_dir 偏离部署形态即拒，防越权写非预期目录）；setup 前置
#      agent 可导入检查（缺=拒写零文件）；两份写前快照原始字节，第二份
#      失败恢复第一份原始内容（原不存在则删除）后原异常上抛（FIX-2/3）。
#
# 【测试要求】四项聚合/任一配置即真/merge 保留他 server/原子写零 .tmp
#   残留/损坏件重建/uv 缺失 400 零半成品。
#
# 【参照】AI2 任务书预裁决；services/trust.py（服务先例）；
# jobs/registry.py write_record（GR-38 原子写母本）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
import uuid
from contextlib import suppress
from importlib.machinery import PathFinder
from pathlib import Path
from shutil import which

from pydantic import BaseModel, ConfigDict

from waterprint_server.services import ServiceContext

__all__ = [
    "AiConnectionSetupResult",
    "AiConnectionStatus",
    "McpServerEntry",
    "UvNotFoundError",
    "WorkspaceLayoutError",
    "connection_status",
    "setup_connection",
]

_MCP_SERVER_KEY: str = "waterprint"


class UvNotFoundError(Exception):
    """uv 可执行文件不在 PATH（一键接入前置依赖缺——404/422 皆非，400 面）。"""


class WorkspaceLayoutError(UvNotFoundError):
    """工作区推导锚点校验失败/agent 包不可导入（回炉 FIX-3·CONFIRMED-3——400 面）。

    继承 UvNotFoundError 承接其 400 handler 映射（Starlette 按类 MRO 解析
    handler——一键接入环境前置缺失族同面；error_type 按本类名上报）。
    """


class McpServerEntry(BaseModel):
    """MCP server 条目固定 schema（R5——三键：command/args/env）。"""

    model_config = ConfigDict(frozen=True)

    command: str
    args: tuple[str, ...]
    env: dict[str, str]


class AiConnectionStatus(BaseModel):
    """接入状态响应体（四项检查+ready 聚合——R2）。"""

    model_config = ConfigDict(frozen=True)

    config_written: bool
    config_paths: tuple[str, ...]
    agent_importable: bool
    uv_path: str | None
    sandbox_root: str
    ready: bool


class AiConnectionSetupResult(BaseModel):
    """一键接入结果响应体（写入路径清单+server 条目摘要——R3/R5）。"""

    model_config = ConfigDict(frozen=True)

    written_paths: tuple[str, ...]
    server_entry: McpServerEntry


def _workspace(ctx: ServiceContext) -> tuple[Path, Path]:
    """工作区路径推导（R1+FIX-3 锚点校验）：返回（仓库根，父目录）。

    锚点=<仓库根>/agent/waterprint_agent 目录在场——data_dir 偏离
    <仓库根>/data 部署形态（上溯两级非仓库根）即拒（400 面，防越权
    写非预期目录）。
    """
    repo_root = ctx.settings.data_dir.resolve().parent
    anchor = repo_root / "agent" / "waterprint_agent"
    if not anchor.is_dir():
        raise WorkspaceLayoutError(
            f"工作区推导锚点校验失败：{anchor} 不存在——预期部署形态为"
            " data_dir=<仓库根>/data（仓库根含 agent/waterprint_agent 包；"
            "请校正 WATERPRINT_DATA_DIR 后重试）"
        )
    return repo_root, repo_root.parent


def _config_paths(repo_root: Path, parent_dir: Path) -> tuple[Path, Path]:
    """两份工作区配置路径（仓库根+父目录各一——R1 作用域根治双写面）。"""
    return (
        repo_root / ".zcode" / "config.json",
        parent_dir / ".zcode" / "config.json",
    )


def _read_config(path: Path) -> dict[str, object]:
    """现有配置读取（R3：损坏/缺失视为 {}——不弃写不炸状态面）。"""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return document if isinstance(document, dict) else {}


def _has_waterprint(config: dict[str, object]) -> bool:
    """waterprint server 条目在场判定（结构性损坏链=不在场诚实假）。"""
    mcp = config.get("mcp")
    if not isinstance(mcp, dict):
        return False
    servers = mcp.get("servers")
    if not isinstance(servers, dict):
        return False
    return _MCP_SERVER_KEY in servers


def _agent_importable(agent_dir: Path) -> bool:
    """agent 包可导入探测（R2）：PathFinder 限定 agent 目录——零 sys.path 污染。"""
    if not agent_dir.is_dir():
        return False
    return PathFinder.find_spec("waterprint_agent", [str(agent_dir)]) is not None


def connection_status(ctx: ServiceContext) -> AiConnectionStatus:
    """接入状态正门：四项检查+ready 聚合（R2——只读零落盘）。"""
    repo_root, parent_dir = _workspace(ctx)
    paths = _config_paths(repo_root, parent_dir)
    config_written = any(_has_waterprint(_read_config(path)) for path in paths)
    agent_importable = _agent_importable(repo_root / "agent")
    uv_path = which("uv")
    return AiConnectionStatus(
        config_written=config_written,
        config_paths=tuple(str(path) for path in paths),
        agent_importable=agent_importable,
        uv_path=uv_path,
        sandbox_root=str(parent_dir / "ai-sandbox"),
        ready=config_written and agent_importable and uv_path is not None,
    )


def _write_config_atomic(path: Path, config: dict[str, object]) -> None:
    """GR-38 原子写（R4+FIX-4）：确定性 JSON+同分区 .tmp 唯一名+os.replace。

    write/replace 抛错时 finally 清理 .tmp 残留（suppress OSError——清理
    失败不掩盖原异常）。
    """
    blob = (
        json.dumps(config, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_bytes(blob)
        os.replace(tmp, path)
    finally:
        with suppress(OSError):
            tmp.unlink(missing_ok=True)


def _original_bytes(path: Path) -> bytes | None:
    """写前原始字节快照（FIX-2：不存在记 None——补偿恢复真源）。"""
    try:
        return path.read_bytes()
    except OSError:
        return None


def _restore(path: Path, original: bytes | None) -> None:
    """半写补偿（FIX-2）：恢复原始字节（原不存在则删除）——best-effort
    （suppress OSError——补偿失败不掩盖原异常）。"""
    with suppress(OSError):
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(original)


def setup_connection(ctx: ServiceContext) -> AiConnectionSetupResult:
    """一键接入正门：前置拒写→uv 解析→两份配置 merge 原子写+半写补偿
    （R1~R5+FIX-2/FIX-3）。"""
    repo_root, parent_dir = _workspace(ctx)  # 锚点校验（FIX-3——400 面）
    agent_dir = repo_root / "agent"
    if not _agent_importable(agent_dir):  # 前置拒写（FIX-3：status 同款探测）
        raise WorkspaceLayoutError(
            f"agent 包不可导入：{agent_dir} 下未探得 waterprint_agent"
            "（一键接入零写入拒——请先在 agent 目录完成安装/修复）"
        )
    sandbox_root = parent_dir / "ai-sandbox"
    uv_path = which("uv")
    if uv_path is None:
        raise UvNotFoundError(
            "uv 可执行文件不在 PATH（一键接入前置依赖——安装 uv 后重试："
            "https://docs.astral.sh/uv/getting-started/installation/）"
        )
    entry = McpServerEntry(
        command=uv_path,
        args=("run", "--directory", str(agent_dir), "waterprint-mcp"),
        env={"WATERPRINT_AI_SANDBOX": str(sandbox_root)},
    )
    paths = _config_paths(repo_root, parent_dir)
    # FIX-2 跨文件半写补偿面：写前快照两份原始字节（不存在记 None）。
    originals = [_original_bytes(path) for path in paths]
    written: list[Path] = []
    try:
        for path in paths:
            config = _read_config(path)
            # R3 merge：mcp/servers 结构性损坏同归重建（dict 面 setdefault 链）。
            mcp = config.get("mcp")
            if not isinstance(mcp, dict):
                mcp = {}
                config["mcp"] = mcp
            servers = mcp.get("servers")
            if not isinstance(servers, dict):
                servers = {}
                mcp["servers"] = servers
            servers[_MCP_SERVER_KEY] = entry.model_dump()
            _write_config_atomic(path, config)
            written.append(path)
    except OSError:
        # FIX-2：已写面恢复原始内容后原异常上抛（幂等重试可恢复）。
        for path, original in zip(written, originals, strict=False):
            _restore(path, original)
        raise
    return AiConnectionSetupResult(
        written_paths=tuple(str(path) for path in written),
        server_entry=entry,
    )
