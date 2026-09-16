"""计算组工具（权威表 #8~#10）：全厂计算+单单元枚举+可行域图。

输入:  MCP 工具调用参数（project_id/conditions/unit_id/top_n）
输出:  投影 dict（摘要≤1.5k token+artifact_path；错误={"error","hint"}）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-INTEG-2026-09-13）
#   路径：agent/waterprint_agent/tools/calc.py
#   职责：wp_run_calc（#8 flows 全链+结果/诊断落沙箱 results/——digest
#       命名）/wp_run_enumeration（#9 Top-N 摘要+全量行落盘）/
#       wp_run_design_map（#10 可行比例+边界摘要+payload 落盘）。
#       本模块兼结果簿记真源（digest10 命名/最近结果集/stale 门）——
#       结果组与导出组经此共享（单一真源禁双胞胎）。
#   禁区：顶层禁 import core/server/fastmcp（懒加载铁律）；工具签名
#       冻结（v2 D3 权威表）；数值永不出自编排层（ADR-019——只编排 flows）。
#
# 【行为规格】
#   R1 #8 装配链=flows.build_env_flow/build_condition_flow/
#      build_standards_flow（data_dir=Settings.data_dir 仓库数据包）；
#      计算=app.run_full_calc（bundle 含 plant+repro+diagnostics——
#      flows.run_calc_flow 冻结签名不透出诊断，故工具层组合同三件：
#      run_full_calc+flows.result_persist_flow（run_calc_flow 内部同径
#      ——零逻辑复制）+serialize_diag 原子落盘）。
#   R2 落盘命名：{pid}-{design_digest 前 10}.result.json／.diag.json
#      （stale 衔接：消费侧比对项目 content_hash——不符即提示重算）。
#   R3 缺省 conditions=None→project.design.checked_units（server worker
#      payload 同语义——2+k 工况，ADR-007）；显式清单覆盖。
#   R4 #9/#10 全量落盘 results/（确定性 JSON——双跑字节同）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import math
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from fastmcp import FastMCP
    from waterprint.contracts.project_schema import ProjectFile
    from waterprint.contracts.result_schema import PlantResult

    from waterprint_agent.context import AgentContext

__all__ = [
    "DIAG_SUFFIX",
    "RESULT_SUFFIX",
    "atomic_write_bytes",
    "diag_path_of",
    "find_latest_result",
    "fresh_gate",
    "read_project",
    "register",
    "wp_run_calc",
    "wp_run_design_map",
    "wp_run_enumeration",
]

RESULT_SUFFIX = ".result.json"
DIAG_SUFFIX = ".diag.json"
_DIGEST10 = 10  # 文件名摘要长度（exports_support._DIGEST_PREFIX 同源口径）
_DESIGN_KEY = "design"
_WATER_FLUID = "WATER"
_MAX_AXES = 2  # 可行域轴上限（FD 契约 _MAX_AXES 同源——1D 区间条/2D 热力图）

_HINT_CALC = (
    "先 wp_create_project 建项；conditions 缺省=项目 checked_units（2+k 工况），"
    "显式清单=受检单元 unit_id 列表。计算完成后再读结果/诊断/导出。"
)
_HINT_ENUM = "unit_id 须为项目内在册单元（wp_get_project_outline 查）；top_n 为摘要行数上限。"
_HINT_DMAP = "unit_id 须为项目内在册单元；可行域图覆盖其 grid 参数轴（无 grid 轴=错误面）。"


def atomic_write_bytes(path: Path, data: bytes) -> Path:
    """GR-38 原子写（uuid 唯一 tmp+os.replace——services._write_meta 同款）。"""
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return path


def results_dir(ctx: AgentContext) -> Path:
    """沙箱 results/ 区（PathGuard 归位解析）。"""
    return ctx.guard.resolve_in(Path("."), area="results")


def find_latest_result(ctx: AgentContext, project_id: str) -> Path | None:
    """项目最近结果文件（mtime 最新的 {pid}-*.result.json；无=None）。

    project_id 先经 projects 区 resolve_in 守卫（../与注入拒）再入
    glob 模式——模式串本身不过守卫（不落盘），守卫面在分量校验。"""
    ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")
    candidates = sorted(
        results_dir(ctx).glob(f"{project_id}-*{RESULT_SUFFIX}"),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def diag_path_of(result_path: Path) -> Path:
    """诊断件姊妹路径（{pid}-{digest10}.diag.json——同 stem 派生）。"""
    return result_path.with_name(
        result_path.name[: -len(RESULT_SUFFIX)] + DIAG_SUFFIX
    )


def fresh_gate(project: ProjectFile, plant: PlantResult) -> str | None:
    """stale 门：结果三元组 design_hash≠当前项目 content_hash → 提示重算。

    返回 None=新鲜；否则=错误消息（消费侧组 {"error","hint"} dict——
    result_schema R4「过期必须显式提示」的 agent 面实现）。"""
    if plant.repro.design_hash == project.metadata.content_hash:
        return None
    return (
        f"最近结果已过期：结果 design {plant.repro.design_hash[:_DIGEST10]}… ≠ "
        f"当前项目 design {project.metadata.content_hash[:_DIGEST10]}…"
        "（改参后未重算——禁静默消费旧结果）"
    )


def read_project(ctx: AgentContext, project_id: str) -> ProjectFile:
    """读项目（services.read_project——project_id 已过 guard 守卫）。"""
    from waterprint_server.services import projects as projects_service

    return projects_service.read_project(ctx.service_ctx, project_id)


def _jsonable(value: Any) -> Any:
    """DataFrame 行值 → JSON 可序列化形（NaN/Inf→None——确定性落盘面）。"""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _run_calc_impl(
    ctx: AgentContext, project_id: str, conditions: list[str] | None
) -> dict[str, Any]:
    """#8：flows 装配→run_full_calc→结果/诊断 digest 命名落盘→压缩摘要。"""
    from waterprint import flows
    from waterprint.app import run_full_calc
    from waterprint.contracts.trust import serialize_diag

    ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")
    project = read_project(ctx, project_id)
    keys = conditions if conditions is not None else list(project.design.checked_units)
    pack = ctx.service_ctx.settings.data_dir
    env = flows.build_env_flow(pack, project)
    cond = flows.build_condition_flow(project, keys)
    standards = flows.build_standards_flow(pack)
    bundle = run_full_calc(project, cond, env, standards=standards)
    digest = bundle.repro.design_hash
    stem = f"{project_id}-{digest[:_DIGEST10]}"
    result_out = ctx.guard.resolve_in(Path(stem + RESULT_SUFFIX), area="results")
    flows.result_persist_flow(bundle.plant, result_out)  # serialize 原子落盘
    diag_out = diag_path_of(result_out)
    atomic_write_bytes(diag_out, serialize_diag(bundle.diagnostics))
    plant = bundle.plant
    summary = dict(plant.summary.get(_DESIGN_KEY, {}))
    summary["warnings_total"] = sum(
        len(unit.warnings)
        for snapshot in plant.conditions.values()
        for unit in snapshot.values()
    )
    summary["mass_closure_design"] = _water_closure(bundle)
    return {
        "project_id": project_id,
        "design_digest": digest,
        "condition_keys": list(plant.conditions),
        "summary": summary,
        "result_path": str(result_out),
        "artifact_path": str(result_out),  # 门一 FIX-4：D3 schema 统一名别名并存
    }


def _water_closure(bundle: Any) -> float | None:
    """design 工况水线相对闭合（诊断 mass_balance 投影；无= None）。"""
    for closure in bundle.diagnostics.mass_balance:
        if closure.condition_key != _DESIGN_KEY:
            continue
        for line in closure.lines:
            if line.fluid == _WATER_FLUID:
                return line.closure_rel
    return None


def _run_enumeration_impl(
    ctx: AgentContext, project_id: str, unit_id: str, top_n: int
) -> dict[str, Any]:
    """#9：flows.enumeration_flow→Top-N 行摘要+全量行确定性 JSON 落盘。"""
    from waterprint import flows

    ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")
    project = read_project(ctx, project_id)
    pack = ctx.service_ctx.settings.data_dir
    env = flows.build_env_flow(pack, project)
    cond = flows.build_condition_flow(project, list(project.design.checked_units))
    outcome = flows.enumeration_flow(project, unit_id, cond, env)
    records = [
        {str(key): _jsonable(value) for key, value in row.items()}
        for row in outcome.rows.to_dict("records")
    ]
    digest = project.metadata.content_hash
    out = ctx.guard.resolve_in(
        Path(f"{project_id}-enum-{unit_id}-{digest[:_DIGEST10]}.json"),
        area="results",
    )
    atomic_write_bytes(
        out,
        (json.dumps(
            {"project_id": project_id, "unit_id": unit_id, "row_count": len(records),
             "total_feasible": int(outcome.total_feasible),
             "truncated": bool(outcome.truncated), "rows": records},
            ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return {
        "project_id": project_id,
        "unit_id": unit_id,
        "total_feasible": int(outcome.total_feasible),
        "truncated": bool(outcome.truncated),
        "top_rows": records[: max(top_n, 0)],
        "artifact_path": str(out),
    }


def _run_design_map_impl(ctx: AgentContext, project_id: str, unit_id: str) -> dict[str, Any]:
    """#10：flows.design_map_flow→可行比例+边界摘要+payload 全量落盘。

    轴自装配（签名冻结无 axes 参）：单元 manifest 声明 range 的参数按
    声明序取前 _MAX_AXES 轴（server 面由客户端显式声明——agent 面以
    「首两连续参数」策略补位；fixed_params/约束装配=services.design_map
    同款口径镜像）。"""
    from waterprint import flows
    from waterprint.app import Constraint, DesignMapOptions, discover_units
    from waterprint_server.services import constraints as constraints_service

    ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")
    project = read_project(ctx, project_id)
    pack = ctx.service_ctx.settings.data_dir
    env = flows.build_env_flow(pack, project)
    cond = flows.build_condition_flow(project, list(project.design.checked_units))
    catalog_key = (
        project.design.nodes[unit_id].get("kind")
        if isinstance(project.design.nodes.get(unit_id), dict)
        else None
    )
    discovered = discover_units()
    manifest = discovered[catalog_key if isinstance(catalog_key, str) and
                          catalog_key in discovered else unit_id][0]
    axes = [
        {"field_id": spec.field_id}
        for spec in manifest.params
        if spec.range is not None
    ][:_MAX_AXES]
    if not axes:
        return {
            "error": f"单元 {unit_id!r} 无 range 声明参数（可行域轴无定义——FD 轴须连续区间参数）",
            "hint": _HINT_DMAP,
        }
    fixed: dict[str, float] = {spec.field_id: spec.default for spec in manifest.params}
    node = project.design.nodes.get(unit_id)
    if isinstance(node, dict):
        for key, value in node.items():
            if key != "kind" and isinstance(value, int | float) and not isinstance(value, bool):
                fixed[key] = float(value)
    chosen = project.design.constraint_choices
    constraints = tuple(
        Constraint(key=entry.key, expression=entry.expression, source=entry.source)
        for entry in constraints_service.list_constraints(pack).entries
        if unit_id in entry.unit_kinds and chosen.get(entry.key) == "on"
    )
    outcome = flows.design_map_flow(
        project, unit_id, cond, env,
        options=DesignMapOptions(axes=tuple(axes), fixed_params=fixed,
                                 constraints=constraints),
    )
    payload = outcome.payload()
    digest = project.metadata.content_hash
    out = ctx.guard.resolve_in(
        Path(f"{project_id}-map-{unit_id}-{digest[:_DIGEST10]}.json"),
        area="results",
    )
    atomic_write_bytes(
        out, (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    return {
        "project_id": project_id,
        "unit_id": unit_id,
        "stats": dict(outcome.stats),
        "segments": (
            None if outcome.segments is None
            else [dict(seg) for seg in outcome.segments]
        ),
        "constraint_coverage": outcome.constraint_coverage,
        "artifact_path": str(out),
    }


def register(mcp: FastMCP) -> None:
    """工具注册面（main.get_mcp 装配调用）。"""
    mcp.tool(wp_run_calc)
    mcp.tool(wp_run_enumeration)
    mcp.tool(wp_run_design_map)


async def wp_run_calc(
    project_id: str, conditions: list[str] | None = None
) -> dict[str, Any]:
    """全厂计算（同步 <5s）：design_digest+摘要（六指标+warnings+质量闭合）+结果路径。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_run_calc", {"project_id": project_id, "conditions": conditions},
        lambda: _run_calc_impl(ctx, project_id, conditions), hint=_HINT_CALC,
    )


async def wp_run_enumeration(
    project_id: str, unit_id: str, top_n: int = 10
) -> dict[str, Any]:
    """单单元枚举：Top-N 行摘要+全量行落 results/（可行方案空间）。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_run_enumeration",
        {"project_id": project_id, "unit_id": unit_id, "top_n": top_n},
        lambda: _run_enumeration_impl(ctx, project_id, unit_id, top_n),
        hint=_HINT_ENUM,
    )


async def wp_run_design_map(project_id: str, unit_id: str) -> dict[str, Any]:
    """可行域图：可行比例+边界摘要+全量 payload 落 results/。"""
    from waterprint_agent import context as agent_context

    ctx = agent_context.get_context()
    return agent_context.run_tool(
        ctx, "wp_run_design_map", {"project_id": project_id, "unit_id": unit_id},
        lambda: _run_design_map_impl(ctx, project_id, unit_id), hint=_HINT_DMAP,
    )
