"""projects 服务镜像测试：保存语义（design_changed）、导入完整性
+约束勾选 PUT 变体（CP2 D6①——constraint_choices 持久/哈希/stale/解勾）。

输入:  waterprint_server.services.projects 公开符号
输出:  服务契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.projects")
save_project = getattr(_mod, "save_project")
import_legacy = getattr(_mod, "import_legacy")
create_project = getattr(_mod, "create_project")
read_project = getattr(_mod, "read_project")
list_projects = getattr(_mod, "list_projects")
result_is_stale = getattr(_mod, "result_is_stale")

pytestmark = [
    pytest.mark.skipif(
        None in (save_project, import_legacy),
        reason="实现未就绪：waterprint_server.services.projects（服务层 M2/M4）",
    ),
    pytest.mark.anyio,
]


async def _created(ctx, payload=None):  # type: ignore[no-untyped-def]
    """创建并返回 (project_id, ProjectFile)。"""
    outcome = create_project(ctx, payload or {})
    return outcome.project_id, read_project(ctx, outcome.project_id)


async def test_view_only_save_reports_no_design_change_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R2 接线断言：仅改 view 态的保存 design_changed=False（§17.1）。"""
    project_id, project = await _created(service_ctx)
    view_only = project.model_copy(
        update={"view": project.view.model_copy(update={"timestamp": "2026-08-26T01:00:00Z"})}
    )
    outcome = save_project(service_ctx, project_id, view_only)
    assert outcome.design_changed is False  # view 态不入哈希（R10 病灶根除）
    design_changed = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"nodes": {**project.design.nodes, "extra_unit": {"x": 1.0}}}
            )
        }
    )
    outcome = save_project(service_ctx, project_id, design_changed)
    assert outcome.design_changed is True  # design 变更区分（R2 dirty 语义）


async def test_legacy_import_lists_unmapped_fields_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R3 接线断言（M4 归属·简报 SERVER D3 未就绪语义实质化）。

    import_legacy 显式未就绪（ImportNotReadyError→501）——不假装功能；
    未映射字段清单（ImportReport.unmapped）的完整性断言归 M4 接线批。
    """
    with pytest.raises(_mod.ImportNotReadyError, match="M4"):
        import_legacy(service_ctx, {"legacy": {"未知字段": 1}})


# ═══ CP2 D6①（约束勾选持久化 2026-09-01）：PUT constraint_choices 变体 ═══

_KEY = "vxinglvchi.v_filter_band"  # kb 真键（vxinglvchi 滤速带——D7 键域宽不校验入 kb）


def _with_choices(project, choices: dict[str, str]):  # type: ignore[no-untyped-def]
    """design 仅换 constraint_choices 的 model_copy（PUT 全量载荷形态）。"""
    return project.model_copy(
        update={"design": project.design.model_copy(update={"constraint_choices": choices})}
    )


async def test_constraint_choices_persist_and_stale_linkage_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """CP2 D6①：PUT 含勾选→design_changed=True+content_hash 变+持久回读
    +旧结果 result_is_stale=True 联动+同 choices 重存 no-op。"""
    outcome0 = create_project(service_ctx, {})
    project_id = outcome0.project_id
    project = read_project(service_ctx, project_id)
    assert project.design.constraint_choices == {}  # 初始空（D1 复用既有字段）
    checked = _with_choices(project, {_KEY: "on"})
    outcome1 = save_project(service_ctx, project_id, checked)
    assert outcome1.design_changed is True  # 勾选变更计入 design 态
    assert outcome1.content_hash != outcome0.content_hash  # design_digest 随勾选变
    persisted = read_project(service_ctx, project_id)
    assert persisted.design.constraint_choices == {_KEY: "on"}  # 落盘持久铁证
    # stale 联动（services/projects.py result_is_stale——三读端点同源口径）：
    # 旧结果锚定旧 digest → 过期；锚定新 digest → 新鲜；缺键 fail-visible
    assert result_is_stale({"design_hash": outcome0.content_hash}, persisted) is True
    assert result_is_stale({"design_hash": outcome1.content_hash}, persisted) is False
    assert result_is_stale({}, persisted) is True
    # 同 choices 重复保存=no-op（design 态等值——不产空变更）
    outcome2 = save_project(service_ctx, project_id, checked)
    assert outcome2.design_changed is False
    assert outcome2.content_hash == outcome1.content_hash


async def test_constraint_choices_uncheck_returns_to_empty_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """CP2 D6①续：解勾删键回空（{}）→design_changed=True+digest 回环
    （确定性序列化——同 design 态哈希字节同）。"""
    outcome0 = create_project(service_ctx, {})
    project_id = outcome0.project_id
    project = read_project(service_ctx, project_id)
    checked = _with_choices(project, {_KEY: "on"})
    save_project(service_ctx, project_id, checked)
    cleared = _with_choices(project, {})
    outcome = save_project(service_ctx, project_id, cleared)
    assert outcome.design_changed is True  # 解勾也是 design 变更
    assert outcome.content_hash == outcome0.content_hash  # 回环=初始空档 digest
    assert read_project(service_ctx, project_id).design.constraint_choices == {}


# ═══ P0-1（建项入口 2026-09-11）：name→view.name 持久/列表回显/导入覆盖 ═══


async def test_create_with_name_persists_and_lists_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """P0-1：空白新建带 name→view.name 持久+列表回显；缺省名=空串回退。"""
    outcome = create_project(service_ctx, {"name": "城市一期"})
    assert read_project(service_ctx, outcome.project_id).view.name == "城市一期"
    by_id = {s.project_id.removesuffix(".wp"): s.name for s in list_projects(service_ctx)}
    assert by_id[outcome.project_id] == "城市一期"
    # 历史项目（不带 name 创建）=空串（FE 回退 id 显示面）
    outcome_blank = create_project(service_ctx, {})
    by_id = {s.project_id.removesuffix(".wp"): s.name for s in list_projects(service_ctx)}
    assert by_id[outcome_blank.project_id] == ""


async def test_create_name_strip_and_length_guard_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """P0-1：name strip 规范（首尾空白剥除——core ViewState 同口径）+超限拒。"""
    outcome = create_project(service_ctx, {"name": "  一期  "})
    assert read_project(service_ctx, outcome.project_id).view.name == "一期"
    with pytest.raises(_mod.InvalidProjectPayloadError, match="100"):
        create_project(service_ctx, {"name": "名" * (100 + 1)})


async def test_import_name_override_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """P0-1：导入时请求 name 非空=覆盖导入文件自带名；缺省=保留导入值。"""
    outcome = create_project(service_ctx, {"name": "原名"})
    raw = read_project(service_ctx, outcome.project_id).model_dump(mode="json")
    overridden = create_project(service_ctx, {"project": raw, "name": "覆盖名"})
    assert read_project(service_ctx, overridden.project_id).view.name == "覆盖名"
    kept = create_project(service_ctx, {"project": raw})
    assert read_project(service_ctx, kept.project_id).view.name == "原名"


# ── P0-3 呈裁④甲：validate_payload 草稿校验+validate_project 结构面 ──

_VALID_DESIGN_NODES: dict[str, dict[str, object]] = {
    "inlet": {"kind": "municipal_input", "q_avg_daily": 0.4, "kz": 1.4},
    "municipal_aao": {},
}
_VALID_EDGE: dict[str, object] = {
    "src": {"unit_id": "inlet", "port_id": "out"},
    "dst": {"unit_id": "municipal_aao", "port_id": "in"},
}


async def _draft_payload(ctx, edges: list[dict[str, object]]) -> dict[str, object]:  # type: ignore[no-untyped-def]
    """合法草稿基座+edges 覆写（基座=已存空白项目 dump——schema 全字段落位）。"""
    outcome = create_project(ctx, {})
    base = read_project(ctx, outcome.project_id).model_dump(mode="json")
    base["design"]["nodes"] = dict(_VALID_DESIGN_NODES)  # type: ignore[assignment]
    base["design"]["edges"] = edges  # type: ignore[assignment]
    return base


async def test_validate_payload_families_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """草稿校验四族：合法/悬空边/端口不在册/方向错（错误清单带定位）。"""
    validate_payload = getattr(_mod, "validate_payload")
    valid_base = await _draft_payload(service_ctx, [_VALID_EDGE])
    assert validate_payload(valid_base).valid is True
    report = validate_payload(await _draft_payload(service_ctx, [
        {"src": {"unit_id": "inlet", "port_id": "out"},
         "dst": {"unit_id": "ghost", "port_id": "in"}}]
    ))
    assert report.valid is False
    assert any("悬空 unit_id：ghost" in item for item in report.errors)
    undeclared = validate_payload(await _draft_payload(service_ctx, [
        {"src": {"unit_id": "inlet", "port_id": "nope"},
         "dst": {"unit_id": "municipal_aao", "port_id": "in"}}]
    ))
    assert any("端口未声明" in item for item in undeclared.errors)
    wrong_dir = validate_payload(await _draft_payload(service_ctx, [
        {"src": {"unit_id": "inlet", "port_id": "out"},
         "dst": {"unit_id": "municipal_aao", "port_id": "out"}}]
    ))
    assert any("边方向非法" in item for item in wrong_dir.errors)


async def test_validate_payload_schema_reject_is_report_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """schema 拒=报告面非抛（422 归 PUT 保存语义——校验端点只呈报⑦甲）。"""
    validate_payload = getattr(_mod, "validate_payload")
    report = validate_payload({"format_version": 3})
    assert report.valid is False
    assert report.errors


async def test_validate_project_saved_structure_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """已存项目校验含结构面：schema 合法但悬空边的存量体 → invalid。"""
    project_id, project = await _created(service_ctx)
    dangling = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={
                    "nodes": _VALID_DESIGN_NODES,  # type: ignore[arg-type]
                    "edges": [{"src": {"unit_id": "inlet", "port_id": "out"},
                               "dst": {"unit_id": "ghost", "port_id": "in"}}],
                }
            )
        }
    )
    save_project(service_ctx, project_id, dangling)  # schema 面放行（边自由 dict）
    report = getattr(_mod, "validate_project")(service_ctx, project_id)
    assert report.valid is False
    assert any("悬空" in item for item in report.errors)


# ── inlet-m3d 批 2026-10-02：注册表旧 v3 项目读时迁移 e2e（简报 §4.5/DoD④）──


def _legacy_v3_registry_project() -> dict[str, object]:
    """注册表存量 v3 形态（市政 inlet m³/s 旧口径——0.4023229167=历史
    round(34760.7/86400,10) 定点；145 件实测同值面普查在批档）。"""
    return {
        "format_version": "3.0",
        "design": {
            "nodes": {
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 0.4023229167,
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "NH3N": 26.0,
                    "TN": 43.0,
                    "TP": 6.5,
                },
                "municipal_cass": {},
            },
            "edges": [
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                }
            ],
        },
        "view": {},
        "metadata": {
            "format_version": "3.0",
            "content_hash": "0" * 64,
            "engine_version": "registry-legacy",
            "data_version": "coefficients@0.0.0",
        },
    }


async def test_registry_v3_project_loads_migrated_read_time(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """注册表旧 v3 项目装载迁移 e2e（DoD④）：盘上 v3 → 读时迁移 v4——

    ①municipal_input q_avg_daily ×86400 round6=34760.700003（机械迁移
    舍入口径定版锚）；②migrated_from="3.0"+版本头 4.0；③存量文件零
    改写（读时迁移不动盘面——幂等键：metadata.content_hash 旧值随读
    保留，哈希失效语义=io R6 版本头设计行为）；④与 v4 直存等值（同
    design 双跑 serialize 字节同——计算面等价闭证）。"""
    import json as _json

    legacy = _legacy_v3_registry_project()
    pid = "f" * 32
    path = service_ctx.settings.projects_dir / f"{pid}.wp.json"
    path.write_text(_json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    on_disk_before = path.read_bytes()

    project = read_project(service_ctx, pid)
    assert project.format_version == "4.0"
    assert project.metadata.migrated_from == "3.0"
    assert project.design.nodes["inlet"]["q_avg_daily"] == 34760.700003
    assert path.read_bytes() == on_disk_before  # 存量文件零改写（读时迁移）

    # ④ v4 直存等值：迁移产物落盘 v4 副本 → 双装载双算 serialize 恒等
    from waterprint.app import load_project, load_run_env, run_full_calc
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.result_schema import serialize

    migrated_dump = project.model_dump(mode="json")
    v4_path = service_ctx.settings.projects_dir / f"{'e' * 32}.wp.json"
    v4_path.write_text(_json.dumps(migrated_dump, ensure_ascii=False), encoding="utf-8")
    blob_a = blob_b = None
    for source in (path, v4_path):
        loaded = load_project(source)
        env = load_run_env(service_ctx.settings.data_dir, loaded, engine_version="e2e-m3d")
        plant = run_full_calc(loaded, build_condition_set([]), env).plant
        blob = serialize(plant)
        if blob_a is None:
            blob_a = blob
        else:
            blob_b = blob
    assert blob_a is not None and blob_b is not None
    assert blob_a == blob_b  # v3 迁移装载计算 == v4 直存装载计算（DoD④ 等值）
