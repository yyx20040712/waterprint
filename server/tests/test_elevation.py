"""elevation 路由镜像测试：GET /api/elevation/{project_id}（纵断/提升/错误面/AU-1）。

输入:  waterprint_server.routers.elevation 公开符号
输出:  路由契约断言（FE7 D1 端点形态的路由面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE7 D1~D5/D10 2026-08-29；test_scene 同款路由面模式）
#
# 覆盖用例：
#   - 端点集恰一件（GET /api/elevation/{project_id}）无漂移；
#   - 200 正门：CASS 项目跑一次计算→stations 非空+字段面恰十键+
#     crest_elev=water_level+freeboard 逐站（D5 服务端投影）+工况缺省=
#     design 回显（SPC2 §2.5 家族切换）+conditions=sorted 键集+datum_note 在（D2）+
#     pump_stations/drop_warnings/warnings 面存在（D4；空=合法 R4）；
#   - 显式工况透传（200+condition_key 回显）；
#   - 确定性：双 GET 响应 JSON（sort_keys）字节同；
#   - 错误面：未知项目 404（ProjectNotFoundError）/无结果集 404
#     （ElevationSourceNotFoundError——引导语含 /api/calc/run）/
#     工况非法 422（InvalidElevationRequestError——透传含合法工况集）；
#   - AU-1 路径安全（workflow §4-4 必选项）：../ 浅深构造全 4xx 非 500+
#     projects/exports 目录快照零新增。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import importlib
import json

import pytest
from fastapi import status
from waterprint.contracts.drawing_projection import ElevationProfile, ProfileStation
from waterprint.elevation import evaluate_pumping
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

from waterprint_server.services.elevation import project_pump_stations

_mod = importlib.import_module("waterprint_server.routers.elevation")
router = getattr(_mod, "router")

_EXPECTED = {("get", "/api/elevation/{project_id}")}

_STATION_KEYS = {
    "unit_id", "water_level", "floor_elev", "ground_elev", "bury_depth",
    "freeboard", "water_depth", "loss_in", "design_flow", "crest_elev",
}


def _lifted_station(uid: str, water_level: float, flow: float = 0.456) -> ProfileStation:
    """抬升纵断站位（core tests/elevation/test_pumps.py _station 同款直构）。"""
    return ProfileStation(
        unit_id=uid, water_level=water_level, floor_elev=water_level - 1.0,
        ground_elev=water_level + 1.0, bury_depth=2.0, freeboard=0.3,
        water_depth=1.0, loss_in=0.0, design_flow=flow,
    )


async def _project_with_result(client) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """创建 CASS 项目并跑一次计算（结果集就绪——elevation 消费前提）。"""
    payload = {
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
    }
    created = await client.post("/api/projects", json=payload)
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": []}
    )).json()["task_id"]
    body: dict[str, object] = {}
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id, task_id


def test_router_exposes_elevation_endpoint_wiring() -> None:
    """端点集 == 规格一件（GET /api/elevation/{project_id}）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)  # 恰一件无漂移


@pytest.mark.anyio
async def test_elevation_returns_profile_with_default_condition_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """GET 200：stations 字段面恰十键+crest 投影逐站+缺省工况=design 回显+datum_note。"""
    project_id, task_id = await _project_with_result(client)
    tasks = (await client.get(f"/api/calc/tasks/{task_id}")).json()
    expected_keys = sorted(tasks["result"]["condition_keys"])
    assert "design" in expected_keys  # 真值锚：build_condition_set 恒产 design+avg
    response = await client.get(f"/api/elevation/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["condition_key"] == "design"  # 缺省=design 优先（SPC2 §2.5——sorted 回退仅防降级奇态）
    assert body["conditions"] == expected_keys  # 工况键清单=sorted 键集（D9 索引面）
    assert "±0.00" in body["datum_note"]  # D2 相对标高注记（口径单一真源在服务面）
    assert body["stations"], "纵断站位非空（CASS 单元至少一站）"
    for station in body["stations"]:
        assert set(station) == _STATION_KEYS  # 十字段恰合（crest_elev 派生面在内）
        assert station["crest_elev"] == pytest.approx(
            station["water_level"] + station["freeboard"]
        )  # D5 服务端投影：池顶=水面+超高（前端零标高推算）
        assert station["unit_id"] != "inlet"  # 内置源节点不设站
    # D4 提升判定面：空站位列表=全程自流合法终态（core pumps R4）
    assert isinstance(body["pump_stations"], list)
    assert isinstance(body["drop_warnings"], list)
    assert isinstance(body["warnings"], list)
    # R6（zM-8）：动态尾键（expected_keys 已在手——core 工况命名变更不假红；
    # 单工况项目退化为首键）
    explicit = await client.get(
        f"/api/elevation/{project_id}", params={"condition_key": expected_keys[-1]}
    )
    assert explicit.status_code == status.HTTP_200_OK
    assert explicit.json()["condition_key"] == expected_keys[-1]  # 显式工况透传


@pytest.mark.anyio
async def test_elevation_warning_faces_shape_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """D4 警告序列化形状：drop_warnings/warnings 逐条 UF-17 六键+级别域冻结。"""
    project_id, _task_id = await _project_with_result(client)
    body = (await client.get(f"/api/elevation/{project_id}")).json()
    _warning_keys = {
        "severity", "source", "message", "param_key", "condition_key",
        "affected_unit_ids",
    }
    for face in ("drop_warnings", "warnings"):
        for warning in body[face]:
            assert set(warning) == _warning_keys  # UF-17 冻结结构逐键
            assert warning["severity"] in {"ERROR", "WARN", "INFO"}  # 级别域冻结
            assert isinstance(warning["affected_unit_ids"], list)


def test_elevation_pump_station_projection_five_keys_wiring() -> None:
    """R1（yI-2）：非空 PumpingPlan → PumpStationEntry 五键逐字段保真。

    经端点结构性不可达记档：build_profile 水位沿程单调不增（level -= loss），
    空损失口径下 drop<0 提升分支永不触发——golden/CASS 任何真数据项目
    pump_stations 恒空（二审 §二-3 路径 A），「服务循环体×非空 plan」组合
    须 M5 真损失接线才可达。本用例经服务层投影函数正门直构非空 plan
    （core test_pumps 同款两站抬升 10→11 直构模式——路径 B），覆盖
    PumpStationEntry 投影循环体的字段保真与扬程不变量。
    """
    profile = ElevationProfile(
        stations=(
            _lifted_station("u1", 10.0),
            _lifted_station("u2", 11.0),  # 下游水面高于上游=需提升
        ),
        condition_key="design", trace=(), warnings=(),
    )
    assumptions = {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}
    plan = evaluate_pumping(profile, assumptions)
    assert len(plan.stations) == 1  # 提升分支点亮
    pump = plan.stations[0]
    entries = project_pump_stations(plan)
    assert len(entries) == 1
    dumped = entries[0].model_dump()
    assert set(dumped) == {
        "unit_id", "static_head", "total_head", "design_flow", "condition_key",
    }  # 恰五键
    assert dumped["unit_id"] == pump.unit_id == "u2"
    assert dumped["static_head"] == pytest.approx(pump.static_head)
    assert dumped["total_head"] == pytest.approx(pump.total_head)
    assert dumped["design_flow"] == pytest.approx(pump.design_flow)
    assert dumped["condition_key"] == pump.condition_key == "design"  # R3 工况标注
    assert dumped["total_head"] >= dumped["static_head"]  # EL-F1 管路损失 ≥0 不变量


@pytest.mark.anyio
async def test_elevation_double_fetch_byte_identical_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R5 确定性继承：两次 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _task_id = await _project_with_result(client)
    first = (await client.get(f"/api/elevation/{project_id}")).json()
    second = (await client.get(f"/api/elevation/{project_id}")).json()
    assert json.dumps(first, sort_keys=True, ensure_ascii=False) == json.dumps(
        second, sort_keys=True, ensure_ascii=False
    )


@pytest.mark.anyio
async def test_elevation_error_faces_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/无结果集 404（引导语）/工况非法 422（统一错误体）。"""
    missing = await client.get("/api/elevation/nosuchproject0000")
    assert missing.status_code == status.HTTP_404_NOT_FOUND
    assert missing.json()["error_type"] == "ProjectNotFoundError"
    created = await client.post("/api/projects", json={})
    project_id = created.json()["project_id"]
    no_result = await client.get(f"/api/elevation/{project_id}")
    assert no_result.status_code == status.HTTP_404_NOT_FOUND
    assert no_result.json()["error_type"] == "ElevationSourceNotFoundError"  # 先重算指引
    assert "/api/calc/run" in str(no_result.json()["detail"])
    project_id, _task_id = await _project_with_result(client)
    invalid = await client.get(f"/api/elevation/{project_id}", params={"condition_key": "zzz"})
    assert invalid.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert invalid.json()["error_type"] == "InvalidElevationRequestError"  # 透传工况集
    assert "合法" in str(invalid.json()["detail"])


@pytest.mark.anyio
async def test_elevation_path_traversal_rejected_wiring(client, test_settings) -> None:  # type: ignore[no-untyped-def]
    """AU-1 路径安全（workflow §4-4 必选项）：穿越 id 全 4xx+目录快照零新增。"""

    def _snapshot() -> set[str]:
        found: set[str] = set()
        for base in (test_settings.projects_dir, test_settings.exports_dir):
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    found.add(path.as_posix())
        return found

    before = _snapshot()
    for evil in ("%2e%2e%2fevil", "..%2Fevil", "%2Fabs", "..%2f..%2fdeep%2fevil"):
        response = await client.get(f"/api/elevation/{evil}")
        assert 400 <= response.status_code < 500, (
            f"{evil} 期望 4xx，得到 {response.status_code}"
        )
    assert _snapshot() == before  # 目录零新增（穿越不落任何文件）


@pytest.mark.anyio
async def test_elevation_stale_flag_on_design_edit_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """AUDIT2 C-1/I-1：PUT 改档不重算→响应 stale=True（R4 显式提示非静默）。

    探针实录（2026-08-30）：改 design（含 assumption_overrides——I-1 活档
    混搭面）不重算后 GET 全 200 呈旧快照零标记；对照面 task status
    stale=True✓/exports 409✓ 唯三读端点盲。修复口径：latest.design_hash
    ≠当前 design digest → stale=True（缺 digest 视为过期——fail-visible）。
    """
    project_id, _task_id = await _project_with_result(client)
    fresh = await client.get(f"/api/elevation/{project_id}")
    assert fresh.status_code == status.HTTP_200_OK
    assert fresh.json()["stale"] is False  # 新鲜结果集（calc done 未改档）
    # PUT 改 assumption_overrides（I-1 混搭面：假设属 design → digest 变）
    project_doc = (await client.get(f"/api/projects/{project_id}")).json()
    project_doc["design"]["assumption_overrides"] = {"safety.superheight": 0.6}
    put = await client.put(f"/api/projects/{project_id}", json=project_doc)
    assert put.status_code == status.HTTP_200_OK
    assert put.json()["design_changed"] is True
    stale = await client.get(f"/api/elevation/{project_id}")
    assert stale.status_code == status.HTTP_200_OK
    assert stale.json()["stale"] is True  # 旧快照+显式过期旗标（非静默）


@pytest.mark.anyio
async def test_elevation_empty_condition_set_422_face_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """ENG4 D1（M-6）：结果集空工况集→GET 422 InvalidElevationRequestError（非 IndexError 500）。

    造档口径仿 test_scene:159 先例（路由面经任务状态端点取 result_file）：
    行级回写 conditions={}（deserialize 面合法）→ 缺省工况取首键路径
    必须经统一错误体显式拒绝。
    """
    from pathlib import Path

    project_id, task_id = await _project_with_result(client)
    tasks = (await client.get(f"/api/calc/tasks/{task_id}")).json()
    result_path = Path(str(tasks["result"]["result_file"]))
    doc = json.loads(result_path.read_text(encoding="utf-8"))
    doc["conditions"] = {}  # 空工况集（deserialize 合法面——缺省取键才是缺陷面）
    result_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    response = await client.get(f"/api/elevation/{project_id}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["error_type"] == "InvalidElevationRequestError"
    assert "先重算" in str(response.json()["detail"])
