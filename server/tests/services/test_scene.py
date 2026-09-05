"""scene 服务镜像测试：最近结果集取数、工况缺省/非法、假设合成视图口径。

输入:  waterprint_server.services.scene 公开符号
输出:  服务契约断言（FE1 D1 端点形态的服务面）
"""

from __future__ import annotations

import asyncio
import importlib
import json
from dataclasses import asdict

import pytest
from waterprint.geometry import SCENE_VERSION  # 测试面专用 core 真源引用（test_cost.py 先例）

_mod = importlib.import_module("waterprint_server.services.scene")
build_scene_for_project = getattr(_mod, "build_scene_for_project")

calculation_mod = importlib.import_module("waterprint_server.services.calculation")
projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = pytest.mark.anyio


async def _project_with_result(ctx) -> str:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（最近结果集就绪——scene 消费前提）。"""
    outcome = projects_mod.create_project(
        ctx,
        {
            "project": {
                "format_version": "1.0",
                "design": {
                    "nodes": {
                        "inlet": {
                            "kind": "municipal_input",
                            "q_avg_daily": 34760.7 / 86400,
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
                    "format_version": "1.0",
                    "content_hash": "0",
                    "engine_version": "0",
                    "data_version": "0",
                },
            }
        },
    )
    project_id = outcome.project_id
    handle = await calculation_mod.submit_calculation(ctx, project_id, [])
    for _ in range(200):
        if ctx.manager.status(handle.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert ctx.manager.status(handle.task_id).state == "done"
    return project_id


async def _latest_conditions(ctx, project_id: str) -> list[str]:  # type: ignore[no-untyped-def]
    """最近 done calc 的结果工况键集（缺省工况断言真值——不猜测）。"""
    status = ctx.manager.status(ctx.manager.task_ids_for_project(project_id)[-1])
    return [str(key) for key in status.result["condition_keys"]]  # type: ignore[index]


async def test_scene_defaults_to_design_condition_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """D1：condition_key 缺省=design 优先（SPC2 §2.5 家族切换——构筑物物理
    尺寸/水位=design 工况设计值；sorted 首键回退仅防降级奇态，真算恒产
    design+avg 两档故直断 design，不猜测）。
    """
    project_id = await _project_with_result(service_ctx)
    scene = build_scene_for_project(service_ctx, project_id)
    conditions = sorted(await _latest_conditions(service_ctx, project_id))
    assert "design" in conditions  # 真值锚：build_condition_set 恒产 design+avg
    assert scene.condition_key == "design"
    assert scene.scene_version == SCENE_VERSION  # R4 版本回显（前端唯一读取口；core 真源常量——L5a 步进 -2，禁字面漂移）
    assert scene.nodes  # 场景非空（CASS 池体图元在册）
    assert any(node.instance_count >= 1 for node in scene.nodes)  # 实例数声明面
    explicit = build_scene_for_project(service_ctx, project_id, "design")
    assert explicit.condition_key == "design"  # 显式工况透传


async def test_scene_site_design_wired_into_graph(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """L5R N-2：design.site 装配透传 build_scene 第四参（总装模式真 wire 可达）。

    简报预裁 5「端点零新增」限定=openapi 恒红线；验收矩阵「总装模式三态
    探针」要求 site 摆放经真 wire 可达——service 层装配是唯一接线。
    """
    from math import isclose, pi

    outcome = projects_mod.create_project(
        service_ctx,
        {
            "project": {
                "format_version": "1.0",
                "design": {
                    "nodes": {
                        "inlet": {
                            "kind": "municipal_input",
                            "q_avg_daily": 34760.7 / 86400,
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
                    "site": {
                        "structures": {
                            "municipal_cass": {
                                "x": 12.0, "y": -5.0,
                                "rotation": 90.0, "ground_elevation": 0.5,
                            }
                        },
                        "roads": [],
                        "corridors": [],
                        "boundary": [
                            {"x": 0.0, "y": 0.0},
                            {"x": 40.0, "y": 0.0},
                            {"x": 40.0, "y": -20.0},
                        ],
                    },
                },
                "view": {},
                "metadata": {
                    "format_version": "1.0",
                    "content_hash": "0",
                    "engine_version": "0",
                    "data_version": "0",
                },
            }
        },
    )
    project_id = outcome.project_id
    handle = await calculation_mod.submit_calculation(service_ctx, project_id, [])
    for _ in range(200):
        if service_ctx.manager.status(handle.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert service_ctx.manager.status(handle.task_id).state == "done"
    scene = build_scene_for_project(service_ctx, project_id)
    by_id = {node.node_id: node for node in scene.nodes}
    # 已摆放单元：position=(x, y北, 标高)（core z-up 存储）+度→弧度换算
    pool = by_id["municipal_cass::pool_wall"]
    assert pool.position == (12.0, -5.0, 0.5)
    assert isclose(pool.rotation[2], pi / 2)
    # 水面足迹键=池面同源（A-S1 wire 面）
    surface = by_id["municipal_cass::water_surface"]
    assert surface.primitive.dims["length"] == pool.primitive.dims["length"]
    assert surface.primitive.dims["width"] == pool.primitive.dims["width"]
    # 红线图元进图（压平顶点序）
    assert "site::boundary" in by_id


async def test_scene_double_run_byte_identical_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """R1 确定性继承：同结果集双跑 JSON(sort_keys) 字节同。

    AUDIT2 FIX1 C-1 后置适配：返回面 SceneGraph dataclass→SceneResponse
    pydantic——序列化经 model_dump(mode="json")（asdict 适配旧形态）。
    """
    project_id = await _project_with_result(service_ctx)
    first = build_scene_for_project(service_ctx, project_id)
    second = build_scene_for_project(service_ctx, project_id)
    dump1 = json.dumps(first.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    dump2 = json.dumps(second.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    assert dump1 == dump2


async def test_scene_invalid_condition_raises_422_face_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """工况非法=InvalidSceneRequestError（422 面，消息透传 build_scene KeyError 文本）。"""
    project_id = await _project_with_result(service_ctx)
    with pytest.raises(_mod.InvalidSceneRequestError, match="合法"):
        build_scene_for_project(service_ctx, project_id, "no_such_condition")


async def test_scene_without_result_raises_404_face_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """无完成结果集=SceneSourceNotFoundError（404 面，消息含先重算指引）。"""
    outcome = projects_mod.create_project(
        service_ctx,
        {
            "project": {
                "format_version": "1.0",
                "design": {
                    "nodes": {
                        "inlet": {
                            "kind": "municipal_input",
                            "q_avg_daily": 34760.7 / 86400,
                            "kz": 1.4,
                            "CODCR": 400.0,
                            "BOD5": 200.0,
                            "SS": 250.0,
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
                    "format_version": "1.0",
                    "content_hash": "0",
                    "engine_version": "0",
                    "data_version": "0",
                },
            }
        },
    )
    with pytest.raises(_mod.SceneSourceNotFoundError, match="/api/calc/run"):
        build_scene_for_project(service_ctx, outcome.project_id)


async def test_scene_unknown_project_raises_not_found_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """项目不存在=ProjectNotFoundError（既有 404 面——read_project 先于取数）。"""
    with pytest.raises(projects_mod.ProjectNotFoundError):
        build_scene_for_project(service_ctx, "nosuchproject0000")


async def test_scene_result_file_missing_raises_404_face_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """FE1 M4：结果文件缺失=SceneSourceNotFoundError（404 面——非 FileNotFoundError 裸 500）。"""
    import os

    project_id = await _project_with_result(service_ctx)
    status = service_ctx.manager.status(
        service_ctx.manager.task_ids_for_project(project_id)[-1]
    )
    os.remove(str(status.result["result_file"]))  # type: ignore[index]
    with pytest.raises(_mod.SceneSourceNotFoundError, match="先重算"):
        build_scene_for_project(service_ctx, project_id)


async def test_scene_empty_condition_set_raises_422_face_wiring(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """ENG4 D1（M-6）：结果集空工况集=InvalidSceneRequestError（422 面——非 IndexError 500）。

    造档口径仿 :159 先例：取最近 done calc 的 result_file → 行级回写
    conditions={}（deserialize 面合法——schema 无非空约束）→ 缺省工况
    取首键路径必须显式拒绝。
    """
    from pathlib import Path

    project_id = await _project_with_result(service_ctx)
    status = service_ctx.manager.status(
        service_ctx.manager.task_ids_for_project(project_id)[-1]
    )
    result_path = Path(str(status.result["result_file"]))  # type: ignore[index]
    doc = json.loads(result_path.read_text(encoding="utf-8"))
    doc["conditions"] = {}  # 空工况集（deserialize 合法面——缺省取键才是缺陷面）
    result_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(_mod.InvalidSceneRequestError, match="先重算"):
        build_scene_for_project(service_ctx, project_id)
