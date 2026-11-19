"""项目组工具（权威表 #4~#6）：种子/空白建项+outline 摘要+结构校验。

输入:  工具调用参数（name/seed/project_id）
输出:  投影 dict（JSON schema 友好；错误={"error","hint"} 不 raise）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-TRACK-B 2026-09-13）
#   路径：agent/waterprint_agent/tools/projects.py
#   职责：_create_impl（#4 种子白名单+空白新建）/_outline_impl（#5 token
#       友好摘要）/_validate_impl（#6 结构校验直通）/_update_params_impl
#       （#7 清单式改参）——chat toolspec.dispatch 的 impl 真源（MCP
#       wp_* 包装随 main.py 退役批剥除 2026-11-19）。
#   禁区：顶层禁 import core/server（懒加载铁律）；impl 签名
#       冻结；golden 种子只读装载（PathGuard 正式区门——禁写正式区）。
#
# 【行为规格】
#   R1 种子面：seed=blank → services.projects.create_project payload.project
#      =None 空白路径（E3）；seed=municipal_34760 → golden input_project.json
#      经 guard.open_readonly_external 只读装载后整树入 payload（A5）；
#      其余 seed → 错误 dict（白名单铁律）。
#   R2 PathGuard 接线：project_id 一律过 guard.resolve_in（../与注入拒）；
#      建项落沙箱 projects/ 区（Settings 基点=沙箱/projects）。
#   R3 outline 口径：节点={unit_id,kind,type,param_count}（kind=内置声明/
#      "unit"；param_count 不计 kind 键）+边（"a:port→b:port" 压缩）+
#      进水+工况勾选+design_digest。
#   R4 #6 校验：waterprint.app.validate_design_structure（core 直调许可
#      =app 门面再导出）经 read_project 投影——清单式零计算。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖（懒加载铁律）
    from waterprint_agent.context import AgentContext

# 种子白名单（预裁决②）：blank=空白骨架；余四者=golden 四用例种子
# （正式区只读门装载同款 input_project.json）。
_SEEDS: tuple[str, ...] = (
    "blank",
    "municipal_34760",
    "municipal_loop_34760",
    "municipal_recycle_34760",
    "mine_43836",
)

# 种子名 → golden_data 用例目录（命名差异折叠——种子面友好拼写）。
_SEED_CASES: dict[str, str] = {
    "municipal_34760": "municipal_34760",
    "municipal_loop_34760": "municipal_34760_loop",
    "municipal_recycle_34760": "municipal_34760_recycle",
    "mine_43836": "mine_43836",
}


def _golden_seed_path(seed: str) -> Path:
    """golden 种子路径（仓库内固定锚——正式区只读真源）。"""
    from waterprint_agent import sandbox

    return (
        sandbox.repo_root() / "core" / "tests" / "golden" / "golden_data"
        / _SEED_CASES[seed] / "input_project.json"
    )


def _create_impl(ctx: AgentContext, name: str, seed: str) -> dict[str, Any]:
    """#4：种子白名单装配 payload → services.projects.create_project 落沙箱。"""
    from waterprint_server.services import projects as projects_service

    payload: dict[str, Any] = {"name": name}
    if seed in _SEED_CASES:
        golden = ctx.guard.open_readonly_external(_golden_seed_path(seed))  # 只读门
        payload["project"] = json.loads(golden.read_text(encoding="utf-8"))
    elif seed != "blank":
        return {"error": f"未知种子 seed：{seed!r}", "hint": f"有效值：{_SEEDS}"}
    outcome = projects_service.create_project(ctx.service_ctx, payload)
    # 沙箱归位校验（PathGuard 门——projects 区前缀内）。
    ctx.guard.resolve_in(Path(f"{outcome.project_id}.wp.json"), area="projects")
    return {"project_id": outcome.project_id, "name": name, "design_digest": outcome.content_hash}


def _outline_impl(ctx: AgentContext, project_id: str) -> dict[str, Any]:
    """#5：read_project → 节点/边/进水/工况勾选 token 友好投影。"""
    from waterprint.app import discover_units
    from waterprint_server.services import projects as projects_service

    ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")  # R2 守卫
    project = projects_service.read_project(ctx.service_ctx, project_id)
    known = set(discover_units())
    nodes: list[dict[str, Any]] = []
    for node_id, value in project.design.nodes.items():
        kind = value.get("kind") if isinstance(value, dict) else None
        if isinstance(kind, str):
            entry_kind, entry_type = kind, "builtin"
        elif node_id in known:
            entry_kind, entry_type = "unit", "unit"
        else:
            entry_kind, entry_type = "unknown", "unknown"
        param_count = len(value) - (1 if isinstance(kind, str) else 0)  # kind 键不计参
        nodes.append(
            {"unit_id": node_id, "kind": entry_kind, "type": entry_type, "param_count": param_count}
        )
    edges: list[dict[str, str]] = []
    for edge in project.design.edges:
        src = edge.get("src", {}) if isinstance(edge, dict) else {}
        dst = edge.get("dst", {}) if isinstance(edge, dict) else {}
        edges.append(
            {
                "src": f"{src.get('unit_id', '?')}:{src.get('port_id', '?')}",
                "dst": f"{dst.get('unit_id', '?')}:{dst.get('port_id', '?')}",
            }
        )
    return {
        "project_id": project_id,
        "name": project.view.name,
        "design_digest": project.metadata.content_hash,
        "node_count": len(nodes),
        "nodes": nodes,
        "edge_count": len(edges),
        "edges": edges,
        "influent": project.design.influent,
        "checked_units": list(project.design.checked_units),
    }


def _validate_impl(ctx: AgentContext, project_id: str) -> dict[str, Any]:
    """#6：app.validate_design_structure 经 read_project 投影（零计算清单）。"""
    from waterprint.app import validate_design_structure
    from waterprint_server.services import projects as projects_service

    ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")  # R2 守卫
    project = projects_service.read_project(ctx.service_ctx, project_id)
    errors = validate_design_structure(project.design)
    return {
        "project_id": project_id,
        "valid": not errors,
        "error_count": len(errors),
        "errors": list(errors),
    }


def _atomic_write(path: Path, data: bytes) -> Path:
    """GR-38 原子写（uuid 唯一 tmp+os.replace——services._write_meta 同款）。"""
    import os
    import uuid

    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return path


def _update_params_impl(
    ctx: AgentContext, project_id: str, patches: list[dict[str, Any]]
) -> dict[str, Any]:
    """#7：批量 patch 改参——逐条 params_guard 三面守护，清单式不拒整批。

    接受项合并写入（改前 undo 快照落 sessions/ 旁挂 .undo.json）；
    返回恰 {results, accepted_count, design_digest} 三键（冻结面）。
    """
    from waterprint.flows import InvalidFlowError, params_guard
    from waterprint_server.services import projects as projects_service

    project_path = ctx.guard.resolve_in(Path(f"{project_id}.wp.json"), area="projects")
    project = projects_service.read_project(ctx.service_ctx, project_id)
    merged: dict[str, dict[str, Any]] = {
        uid: dict(node) for uid, node in project.design.nodes.items()
    }
    results: list[dict[str, Any]] = []
    accepted_count = 0
    for patch in patches:
        unit_id = patch.get("unit_id") if isinstance(patch, dict) else None
        key = patch.get("key") if isinstance(patch, dict) else None
        value = patch.get("value") if isinstance(patch, dict) else None
        if not isinstance(unit_id, str) or not unit_id or not isinstance(key, str):
            results.append(
                {"unit_id": unit_id if isinstance(unit_id, str) else str(unit_id),
                 "key": key if isinstance(key, str) else str(key),
                 "accepted": False,
                 "reason": "patch 形态非法（须 unit_id: str 与 key: str）"}
            )
            continue
        try:
            verdict = params_guard(project, unit_id, {key: value})[0]
        except InvalidFlowError as exc:  # 未知单元/目录外=该条拒（不拒整批）
            results.append(
                {"unit_id": unit_id, "key": key, "accepted": False, "reason": str(exc)}
            )
            continue
        results.append(
            {"unit_id": unit_id, "key": key,
             "accepted": verdict.accepted, "reason": verdict.reason}
        )
        if verdict.accepted:
            merged[unit_id][key] = value
            accepted_count += 1
    digest = project.metadata.content_hash
    if accepted_count:
        # undo 快照：改前项目字节原样落 sessions/{pid}-{旧 digest10}.undo.json。
        undo = ctx.guard.resolve_in(
            Path(f"{project_id}-{digest[:10]}.undo.json"), area="sessions"
        )
        _atomic_write(undo, project_path.read_bytes())
        updated = project.model_copy(
            update={"design": project.design.model_copy(update={"nodes": merged})}
        )
        try:
            outcome = projects_service.save_project(ctx.service_ctx, project_id, updated)
        except Exception:
            # 门一 FIX-3/C1：保存失败（锁冲突/深度闸族）→undo 快照半写孤儿
            # best-effort 清理后原样重抛（run_tool 兜底转错误 dict）。
            with contextlib.suppress(OSError):
                undo.unlink(missing_ok=True)
            raise
        digest = outcome.content_hash
    return {"results": results, "accepted_count": accepted_count, "design_digest": digest}
