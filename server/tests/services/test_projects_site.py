"""site 批 server 面镜像测试：PUT 全量保存/深度闸/悬空 4xx/digest 镜像（M5 L1）。

输入:  services.projects（save_project/read_project）+ client fixture +
       core design_hash 真源（测试面专用 import，产品码禁直连 D7 不涉）
输出:  design.site 的服务契约断言（core schema 批的 server 侧接线；L4a 批
       format_version 3.0 断言随行+boundary 键入全子键样例）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.projects")
create_project = getattr(_mod, "create_project")
read_project = getattr(_mod, "read_project")
save_project = getattr(_mod, "save_project")
design_digest = getattr(_mod, "design_digest")
InvalidProjectPayloadError = getattr(_mod, "InvalidProjectPayloadError")

_schema = importlib.import_module("waterprint.contracts.project_schema")
DesignState = getattr(_schema, "DesignState")
ViewState = getattr(_schema, "ViewState")
Metadata = getattr(_schema, "Metadata")
ProjectFile = getattr(_schema, "ProjectFile")
SiteDesign = getattr(_schema, "SiteDesign")

_core_hash = importlib.import_module("waterprint.project.content_hash")
design_hash = getattr(_core_hash, "design_hash")

_SITE_FULL: dict[str, object] = {  # 全子键样例（服务面与 core test_site_schema 同构载荷）
    "structures": {"u1": {"x": 1.0, "y": 2.0, "rotation": 90.0, "ground_elevation": 105.5}},
    "roads": [
        {"centerline": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}], "width_m": 6.0}
    ],
    "corridors": [
        {
            "centerline": [{"x": 0.0, "y": 1.0}, {"x": 0.0, "y": 20.0}],
            "width_m": 2.0,
            "kind": "water",
        }
    ],
    "options": {"coord_grid": 10.0, "wind_rose": {"N": 12.5}},
    "boundary": [  # L4a 红线键（≥3 点闭合顶点序——服务面随 core schema v3）
        {"x": -5.0, "y": -5.0},
        {"x": 45.0, "y": -5.0},
        {"x": 45.0, "y": 30.0},
        {"x": -5.0, "y": 30.0},
    ],
}


@pytest.mark.anyio
async def test_put_full_site_persists_and_rereads(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """PUT 全量 site：落盘+独立回读（质量门条款 5——回读面非构造即完）。"""
    outcome = create_project(service_ctx, {})
    project_id = outcome.project_id
    project = read_project(service_ctx, project_id)
    updated = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={
                    "nodes": {"u1": {"pool_length": 10.5}},  # structures 键的 nodes 面
                    "site": SiteDesign.model_validate(_SITE_FULL),
                }
            )
        }
    )
    result = save_project(service_ctx, project_id, updated)
    assert result.design_changed is True  # site 变更计入 design 态（dirty 语义）
    persisted = read_project(service_ctx, project_id)  # 独立回读（盘上文件面）
    assert persisted.design.site == SiteDesign.model_validate(_SITE_FULL)
    assert persisted.design.site.structures["u1"].x == 1.0
    assert persisted.design.site.options.wind_rose == {"N": 12.5}
    assert len(persisted.design.site.boundary) == 4  # L4a 红线键随 PUT 全量落盘
    assert persisted.format_version == "3.0"  # 当前版直通（服务常量与 core 同源）


@pytest.mark.anyio
async def test_put_depth_gate_enumerates_design_site(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """深度闸：design.site 超深子树 → InvalidProjectPayloadError（422 面非 500）。

    按 _check_depth 实现口径构造（Mapping 链）：site 严格类型化后深树
    不可经 parse_project 存在——model_construct 绕过校验钉「site 在
    枚举元组内」的闸接线（防御面——对照修3 view.layout 深炸弹形态）。
    """
    outcome = create_project(service_ctx, {})
    deep: dict[str, object] = {"leaf": 0}
    for _ in range(2 * 10**2):  # 200+ 层 >> max_json_depth
        deep = {"n": deep}
    forged = ProjectFile.model_construct(
        format_version="3.0",
        design=DesignState.model_construct(
            nodes={},
            edges=[],
            influent={},
            site={"structures": {"u1": deep}},  # 经 structures 键长链形态
        ),
        view=ViewState(),
        metadata=Metadata(
            format_version="3.0",
            content_hash="0" * 64,
            engine_version="0",
            data_version="0",
        ),
    )
    with pytest.raises(InvalidProjectPayloadError, match="深度"):
        save_project(service_ctx, outcome.project_id, forged)


@pytest.mark.anyio
async def test_put_dangling_site_key_rejected_4xx(client) -> None:  # type: ignore[no-untyped-def]
    """悬空 site.structures 键 PUT → 4xx（parse_project 拒绝面透传）。

    映射实录：routers 内联 parse_project → pydantic ValidationError →
    main._EXCEPTION_STATUS 422（非 InvalidProjectError→400——按实录断言）。
    """
    created = await client.post("/api/projects", json={})
    project_id = created.json()["project_id"]
    body = (await client.get(f"/api/projects/{project_id}")).json()
    body["design"]["nodes"] = {"u1": {}}
    body["design"]["site"] = {"structures": {"ghost": {"x": 1.0, "y": 1.0}}}
    response = await client.put(f"/api/projects/{project_id}", json=body)
    assert response.status_code == 422  # 实录状态码（4xx——拒绝面非 500）
    assert "悬空" in response.json()["detail"]


def test_design_digest_mirror_v3_with_site() -> None:
    """镜像：v3 形 design（含 site 全子键+boundary）server digest == core design_hash 逐字节。

    沿用 test_design_digest_mirror 形态（值不断言字面——两侧双胞胎随
    site 扩键自动一致即断言面）。
    """
    design = DesignState(
        nodes={"u1": {"pool_length": 10.5}},  # structures 键的 nodes 面
        site=SiteDesign.model_validate(_SITE_FULL),
    )
    assert design_digest(design) == design_hash(design)
    assert design_digest(DesignState()) == design_hash(DesignState())  # 默认空 site 面
