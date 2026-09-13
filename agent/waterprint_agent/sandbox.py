"""沙箱工作区治理：根解析（env 覆盖）+init_workspace 幂等建树（D4 布局）。

输入:  env WATERPRINT_AI_SANDBOX / 默认根派生
输出:  沙箱根 Path（绝对）+ 五区目录树 + workspace.toml 标识
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-TRACK-B 2026-09-13）
#   路径：agent/waterprint_agent/sandbox.py
#   职责：沙箱根唯一解析面（默认=仓库上一级/ai-sandbox，env 可覆盖）；
#       init_workspace 幂等建五区目录+workspace.toml（记录 data 资产根
#       与创建时间——预裁决条款）。
#   禁区：禁 import core/server/fastmcp（纯 stdlib——main 顶层懒加载链）；
#       禁写沙箱之外的任何位置（data 资产根只读引用）。
#
# 【公开接口】
#   sandbox_root() -> Path：env WATERPRINT_AI_SANDBOX 覆盖 → 绝对化；
#       缺省=repo_root().parent/"ai-sandbox"（默认 E:\\class\\智水蓝图\\ai-sandbox）。
#   repo_root() / data_asset_root() -> Path：仓库根=agent 可编辑安装位上溯；
#       data 资产根=仓库/data（constraint_kb/coefficients 真源）。
#   init_workspace(root=None) -> Path：五区建树+workspace.toml（幂等——
#       已存在不覆写，created_at 保持首建时刻）。
#
# 【行为规格】
#   R1 布局：projects/exports/results/sessions/reports 五区（D4 冻结）；
#       tasks 子树（registry/cancel）归 context 私有 Manager 装配面，不在
#       建树清单（无任务提交即无产物）。
#   R2 幂等：重复 init_workspace 零异常零覆写（测试断言 created_at 不变）。
#   R3 标识：workspace.toml 仅首建写入——data 资产根（str）+创建时间
#      （UTC ISO 8601 零偏移——GR-19 同口径）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

__all__ = ["AREAS", "data_asset_root", "init_workspace", "repo_root", "sandbox_root"]

AREAS: tuple[str, ...] = ("projects", "exports", "results", "sessions", "reports")
_SANDBOX_DIR_NAME = "ai-sandbox"
_WORKSPACE_MARKER = "workspace.toml"


def repo_root() -> Path:
    """WaterPrint 仓库根（agent 面可编辑安装——__file__ 即源码位，上溯两级）。"""
    return Path(__file__).resolve().parents[2]


def data_asset_root() -> Path:
    """data 资产根（正式区只读真源：constraint_kb/coefficients/templates）。"""
    return repo_root() / "data"


def sandbox_root() -> Path:
    """沙箱根解析（env 优先，绝对化返回——Settings 装配只收绝对路径）。"""
    override = os.environ.get("WATERPRINT_AI_SANDBOX")
    if override:
        return Path(override).resolve()
    return (repo_root().parent / _SANDBOX_DIR_NAME).resolve()


def init_workspace(root: Path | None = None) -> Path:
    """建五区目录树+workspace.toml（幂等）——返回绝对沙箱根。"""
    target = Path(root).resolve() if root is not None else sandbox_root()
    for area in AREAS:
        (target / area).mkdir(parents=True, exist_ok=True)
    marker = target / _WORKSPACE_MARKER
    if not marker.exists():  # R2/R3：首建写标识，重复调用不覆写
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
        content = (
            "# WaterPrint AI 沙箱工作区标识（waterprint_agent.sandbox.init_workspace 生成；"
            "幂等不覆写）\n"
            f'created_at = "{created_at}"\n\n'
            "[data_asset]\n"
            f"root = '{data_asset_root()}'\n"  # TOML 字面串——Windows 反斜杠免转义
        )
        marker.write_text(content, encoding="utf-8")
    return target
