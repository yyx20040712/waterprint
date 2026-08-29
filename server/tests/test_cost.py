"""cost 路由镜像测试：GET /api/cost/{project_id}（概算装配/指标/错误面/AU-1）。

输入:  waterprint_server.routers.cost 公开符号+core cost 四模块直调对拍
输出:  路由契约断言（FE8 D1 端点形态的路由面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE8 D1~D4/D9 2026-08-29；test_elevation 同款路由面模式）
#
# 覆盖用例：
#   - 端点集恰一件（GET /api/cost/{project_id}）无漂移；
#   - 200 正门：CASS 项目跑一次计算→缺省工况="design"（D2——非排序
#     首键）+conditions 索引回显+price_data_version+design_scale≈
#     34760.7（D3 服务面注入）+sheet 全字段+grand_total=core 三正门
#     直调同 fixture 对拍（禁锚 golden 真值——fe3-probe design 含
#     aao n=3 覆盖≠golden 基线）+自洽分级；
#   - name_zh 中文下发（D4——PriceBook.get(price_key).name 直投）；
#   - 指标面：WARN 语义（CASS 单元量级 324.62 < 带下限 3000——诚实
#     读数 D3）+checked True+读数五键（band 嵌套 {min,max}）；
#   - 显式工况透传（avg→200 回显——值与 design 同构为事实记档，
#     不强制差异断言）；
#   - 确定性：双 GET 响应 JSON（sort_keys）字节同；
#   - 错误面：未知项目 404（ProjectNotFoundError）/无结果集 404
#     （CostSourceNotFoundError——引导语含 /api/calc/run）/工况非法
#     422（InvalidCostRequestError——透传工况集）；
#   - AU-1 路径安全（workflow §4-4 必选项）：../ 浅深构造全 4xx 非 500+
#     projects/exports 目录快照零新增。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import importlib
import json
import shutil
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi import status
from waterprint.contracts.result_schema import deserialize
from waterprint.cost.estimate import build_estimate, load_fee_rules
from waterprint.cost.indicators import check_indicators, load_indicator_bands
from waterprint.cost.prices import load_prices
from waterprint.cost.takeoff import load_field_mapping, takeoff_quantities

from waterprint_server.main import create_app
from waterprint_server.settings import Settings

_mod = importlib.import_module("waterprint_server.routers.cost")
router = getattr(_mod, "router")

_EXPECTED = {("get", "/api/cost/{project_id}")}

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPO_DATA = _REPO_ROOT / "data"

_ROW_KEYS = {
    "price_key", "name_zh", "unit", "quantity", "unit_price", "amount",
    "source_field_ids", "source",
}  # 九字段=core EstimateRow 八字段+name_zh（D4）
_FEE_LINE_KEYS = {"fee_key", "rate", "base", "base_amount", "amount", "source"}
_READING_KEYS = {"indicator_key", "value", "band", "status", "reason"}


@pytest.fixture
def cost_settings(tmp_path: Path) -> Settings:
    """cost 消费面 Settings（conftest.test_settings 同款+unit_prices 拷贝）。

    conftest 只拷 coefficients（elevation 前批口径——unit_prices 归 FE8
    消费面）；本 fixture 在 tests/test_cost.py 内自备（conftest 零触碰）。
    """
    data_dir = tmp_path / "data"
    (data_dir / "templates").mkdir(parents=True)
    shutil.copytree(_REPO_DATA / "coefficients", data_dir / "coefficients")
    shutil.copytree(_REPO_DATA / "unit_prices", data_dir / "unit_prices")
    return Settings(
        projects_dir=tmp_path / "projects",
        exports_dir=tmp_path / "exports",
        data_dir=data_dir,
        calc_workers=1,
        log_file=str(tmp_path / "test-cost-server.log"),
    )


@pytest.fixture
async def cost_client(cost_settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """cost 面 AsyncClient（conftest.client 同款装配+unit_prices 数据包）。"""
    executor = ThreadPoolExecutor(max_workers=cost_settings.calc_workers)
    application = create_app(cost_settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            yield async_client
    executor.shutdown(wait=True)


async def _project_with_result(client: httpx.AsyncClient) -> tuple[str, str]:
    """创建 CASS 项目并跑一次计算（结果集就绪——cost 消费前提）。"""
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


def _direct_core_faces(
    cost_settings: Settings, task_body: dict[str, object], condition_key: str):  # type: ignore[no-untyped-def]
    """core 三正门直调（golden test_municipal_e2e 同款装配——对拍真源）。

    grand_total 断言=本函数产物（禁直接锚 golden 真值 11908574.59：
    fe3-probe 项目 design 已含 aao n=3 覆盖≠golden 基线——同 fixture
    对拍是服务面与 core 单点一致性的充分证据）。
    """
    result = task_body["result"]
    assert isinstance(result, dict)
    plant = deserialize(Path(str(result["result_file"])).read_bytes())
    unit_prices = cost_settings.data_dir / "unit_prices"
    book = load_prices(unit_prices)
    fees = load_fee_rules(unit_prices / "field_mapping.yaml", book)
    mapping = load_field_mapping(unit_prices / "field_mapping.yaml")
    items = takeoff_quantities(
        plant, condition_key, price_book=book, field_mapping=mapping
    )
    sheet = build_estimate(
        items, book, fees, repro=plant.repro, condition_key=condition_key
    )
    report = check_indicators(
        sheet, load_indicator_bands(book), design_scale=34760.7
    )
    return sheet, report


def test_router_exposes_cost_endpoint_wiring() -> None:
    """端点集 == 规格一件（GET /api/cost/{project_id}）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)  # 恰一件无漂移


@pytest.mark.anyio
async def test_cost_returns_estimate_default_design_wiring(
    cost_client, cost_settings
) -> None:  # type: ignore[no-untyped-def]
    """GET 200：缺省工况="design"（D2）+直调对拍+design_scale+conditions 回显。"""
    project_id, task_id = await _project_with_result(cost_client)
    tasks = (await cost_client.get(f"/api/calc/tasks/{task_id}")).json()
    response = await cost_client.get(f"/api/cost/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["condition_key"] == "design"  # D2 缺省=design（≠elevation 排序首键 avg）
    assert body["conditions"] == sorted(tasks["result"]["condition_keys"])
    assert body["price_data_version"]  # D4 三元组组件（PriceBook.data_version）
    assert body["design_scale"] == pytest.approx(34760.7, rel=1e-9)  # D3 服务面注入（项目存档 10 位定点→×86400 微差内）
    sheet, report = _direct_core_faces(cost_settings, tasks, "design")
    assert body["sheet"]["grand_total"] == sheet.grand_total  # 直调对拍（精确相等）
    assert body["indicators"]["checked"] is report.checked is True
    reading = body["indicators"]["readings"][0]
    assert reading["value"] == pytest.approx(report.readings[0].value)


@pytest.mark.anyio
async def test_cost_sheet_faces_and_self_consistency_wiring(cost_client) -> None:  # type: ignore[no-untyped-def]
    """D4/D5 sheet 全字段+分级自洽（grand=subtotal+reserve+Σtax 三级链）。"""
    project_id, _task_id = await _project_with_result(cost_client)
    sheet_body = (await cost_client.get(f"/api/cost/{project_id}")).json()["sheet"]
    rows = sheet_body["detail_rows"]
    assert rows, "分部分项明细非空（CASS 单元至少一笔）"
    for row in rows:
        assert set(row) == _ROW_KEYS  # 九字段恰合（name_zh 中文列名在内）
        assert any("\u4e00" <= ch <= "\u9fff" for ch in row["name_zh"]), (
            "name_zh 服务端中文直投（PriceBook.name 单一真源）"
        )
        assert isinstance(row["source_field_ids"], list) and row["source_field_ids"]
    for bucket in ("measure", "indirect", "reserve", "tax"):
        assert sheet_body[bucket], f"四费桶 {bucket} 非空（field_mapping DSL 驱动）"
        for line in sheet_body[bucket]:
            assert set(line) == _FEE_LINE_KEYS  # 六字段恰合
    assert set(sheet_body["repro"]) == {"design_hash", "engine_version", "data_version"}
    assert sheet_body["condition_key"] == "design"
    # 自洽三级链（core estimate 分级汇总不变量——golden _m3_real_values 同款）
    assert sheet_body["grand_total"] == pytest.approx(
        sheet_body["subtotal"] + sheet_body["reserve_subtotal"]
        + sum(line["amount"] for line in sheet_body["tax"])
    )
    assert sheet_body["subtotal"] == pytest.approx(
        sheet_body["construction_subtotal"]
        + sum(line["amount"] for line in sheet_body["indirect"])
    )
    assert sheet_body["construction_subtotal"] == pytest.approx(
        sheet_body["detail_subtotal"] + sum(line["amount"] for line in sheet_body["measure"])
    )


@pytest.mark.anyio
async def test_cost_indicators_warn_semantics_wiring(cost_client) -> None:  # type: ignore[no-untyped-def]
    """D3/D6 指标面：WARN 诚实读数（324.62 量级<3000 带下限）+checked True。"""
    project_id, _task_id = await _project_with_result(cost_client)
    body = (await cost_client.get(f"/api/cost/{project_id}")).json()
    indicators = body["indicators"]
    assert indicators["checked"] is True  # bands 非空=已校核（空带才 False）
    assert indicators["readings"]
    for reading in indicators["readings"]:
        assert set(reading) == _READING_KEYS  # 五键恰合
        assert set(reading["band"]) == {"min", "max"}  # band 嵌套形状（D4）
        assert reading["band"]["min"] < reading["band"]["max"]
        assert reading["status"] in {"OK", "WARN"}
        assert reading["reason"]
    first = indicators["readings"][0]
    assert first["status"] == "WARN"  # CASS 单元量级 324.62 低于带下限 3000
    assert first["value"] < first["band"]["min"]


@pytest.mark.anyio
async def test_cost_explicit_condition_passthrough_wiring(cost_client) -> None:  # type: ignore[no-untyped-def]
    """显式工况透传：avg→200+回显（值同构记档——不强制差异断言）。"""
    project_id, _task_id = await _project_with_result(cost_client)
    response = await cost_client.get(
        f"/api/cost/{project_id}", params={"condition_key": "avg"}
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["condition_key"] == "avg"
    assert body["sheet"]["condition_key"] == "avg"  # sheet 内外工况标注一致（R4）
    assert body["conditions"] == ["avg", "design"]


@pytest.mark.anyio
async def test_cost_double_fetch_byte_identical_wiring(cost_client) -> None:  # type: ignore[no-untyped-def]
    """确定性继承：两次 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _task_id = await _project_with_result(cost_client)
    first = (await cost_client.get(f"/api/cost/{project_id}")).json()
    second = (await cost_client.get(f"/api/cost/{project_id}")).json()
    assert json.dumps(first, sort_keys=True, ensure_ascii=False) == json.dumps(
        second, sort_keys=True, ensure_ascii=False
    )


@pytest.mark.anyio
async def test_cost_error_faces_wiring(cost_client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/无结果集 404（引导语）/工况非法 422（统一错误体）。"""
    missing = await cost_client.get("/api/cost/nosuchproject0000")
    assert missing.status_code == status.HTTP_404_NOT_FOUND
    assert missing.json()["error_type"] == "ProjectNotFoundError"
    created = await cost_client.post("/api/projects", json={})
    project_id = created.json()["project_id"]
    no_result = await cost_client.get(f"/api/cost/{project_id}")
    assert no_result.status_code == status.HTTP_404_NOT_FOUND
    assert no_result.json()["error_type"] == "CostSourceNotFoundError"  # 先重算指引
    assert "/api/calc/run" in str(no_result.json()["detail"])
    project_id, _task_id = await _project_with_result(cost_client)
    invalid = await cost_client.get(f"/api/cost/{project_id}", params={"condition_key": "zzz"})
    assert invalid.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert invalid.json()["error_type"] == "InvalidCostRequestError"  # 透传工况集
    assert "zzz" in str(invalid.json()["detail"])


@pytest.mark.anyio
async def test_cost_path_traversal_rejected_wiring(
    cost_client, cost_settings
) -> None:  # type: ignore[no-untyped-def]
    """AU-1 路径安全（workflow §4-4 必选项）：穿越 id 全 4xx+目录快照零新增。"""

    def _snapshot() -> set[str]:
        found: set[str] = set()
        for base in (cost_settings.projects_dir, cost_settings.exports_dir):
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    found.add(path.as_posix())
        return found

    before = _snapshot()
    for evil in ("%2e%2e%2fevil", "..%2Fevil", "%2Fabs", "..%2f..%2fdeep%2fevil"):
        response = await cost_client.get(f"/api/cost/{evil}")
        assert 400 <= response.status_code < 500, (
            f"{evil} 期望 4xx，得到 {response.status_code}"
        )
    assert _snapshot() == before  # 目录零新增（穿越不落任何文件）
