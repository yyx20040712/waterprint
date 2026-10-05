"""validation 路由/服务镜像测试：GET /api/calc/validation/{project_id}（观测面+聚合+降级）。

输入:  waterprint_server.routers.calc validation 端点 + services.validation 公开符号
输出:  路由契约断言（2A1 消费批——聚合规格 warning-aggregation.md §1~§4 十一条款
       逐条绑定+观测投影+三态降级+404 家族+确定性）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：2A1 消费批（2a1-20261005）§3 D3——聚合实现契约=docs/
#   warning-aggregation.md 冻结规格（§1 命名消歧硬约束/§2 去重键三元组/
#   §3 命中=越门+∅ 哨兵+severity max+序轴=迭代序/§4 两源对齐+any_fail
#   排除）；test_sensitivity 同款路由面模式（合成件 monkeypatch 定点+
#   E2E client 真跑）。
#
# 覆盖用例（§3 十语义逐条+路由面）：
#   - 端点集新增恰一件（GET /api/calc/validation/{project_id}）；
#   - ①字段名硬约束：聚合行 scope+condition_keys[]（禁 condition_key 双义）；
#   - ②源 B 仅 0.0 越门计入、1.0 通过不入聚合（入观测面）；
#   - ③源 A 命中清单=∅ 空序列哨兵、不参与 ≥2 计数；
#   - ④≥2 越门工况入聚合视图+单工况直通行同 schema；
#   - ⑤severity=max over 命中实例（源 A 实例与源 B kb 条目取最严重）；
#   - ⑥序轴唯一源=record condition_keys 迭代序（存量旧记录缺键=字典序兜底）；
#   - ⑦同键双源现→message 取源 A 实例+清单=源 B 工况清单；
#   - ⑧去重键=(code,param_key,scope) 三元组、message/severity 不入键；
#   - ⑨any_fail 汇总键不进去重键族（不入聚合）；
#   - ⑩unit_api.Warning 第三警告面不入聚合（plant 快照 warnings 在场不入行）；
#   - ⑪kb 条目缺席（版本漂移）不入聚合行、观测面保留原值；
#   - B-only 行 message 合成（A1：三要素=条目键+表达式原文+首命中工况实际值；
#     字段缺席无值形态）；
#   - 响应行排序=(scope,code,param_key)（A3）；
#   - 观测投影：nodes 逐节点×逐工况三面（kb bool 语义升级 A6/any_fail/
#     ratio/fixgeom_min）；
#   - 三态降级：val 件缺键/缺文件/损坏→validation_available=False；
#     diag 缺席→kb_injected=None（禁伪造 False）；
#   - E2E 200 形态+确定性双跑+404 家族（未知项目/无结果集/损坏件）+
#     AU-1 路径安全。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import status
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    UnitResultSnapshot,
)
from waterprint.contracts.trust import DiagnosticsReport, serialize_diag
from waterprint.contracts.unit_api import Severity, Warning
from waterprint.contracts.validation import (
    PlantWarning,
    ValidationReport,
    serialize_validation,
)

from waterprint_server.routers import calc as calc_router
from waterprint_server.services import validation as validation_module
from waterprint_server.services.constraints import ConstraintCatalog, ConstraintEntry
from waterprint_server.services.validation import (
    ValidationObservationResponse,
    build_validation_observation,
)

_EXPECTED_VALIDATION = {("get", "/api/calc/validation/{project_id}")}


def _entry(key: str, expression: str, severity: str = "WARN") -> ConstraintEntry:
    """合成 kb 目录条目（param_band 族——expression/首字段推导链载体）。"""
    return ConstraintEntry(
        key=key,
        kind="param_band",
        unit_kinds=("municipal_aao",),
        label="合成条目",
        expression=expression,
        source=key,
        severity=severity,
        value_basis="测试合成",
        enforcement="flag",
    )


def _catalog(*entries: ConstraintEntry) -> ConstraintCatalog:
    return ConstraintCatalog(entries=tuple(entries))


def _snapshot(dims: dict[str, float]) -> UnitResultSnapshot:
    """offline 快照桩（dims 值面——B-only message 实际值取数面）。"""
    return UnitResultSnapshot(
        unit_id="municipal_aao",
        outflows={},
        outqualities={},
        dims=dims,
        warnings=(),
        formula_ids=(),
    )


def _plant_two_hits() -> PlantResult:
    """双越门合成结果件：param.n.positive 两工况越门（≥2 聚合载体）+
    param.h2.positive 单工况通过+any_fail 汇总键+ratio/fixgeom 观测面+
    ghost 键（kb 条目缺席——A2 载体）+第三警告面 warnings（快照级）。"""
    return PlantResult(
        conditions={
            "design": {},
            "avg": {},
            "design_offline_aao": {"municipal_aao": _snapshot({"n": 2.0, "h2": 4.5})},
            "design_offline_aao2": {"municipal_aao": _snapshot({"n": 4.0, "h2": 9.0})},
        },
        summary={
            "design": {},
            "avg": {},
            "design_offline_aao": {
                "maint.municipal_aao.kb.param.n.positive": 0.0,  # 越门（第 1 命中）
                "maint.municipal_aao.kb.param.h2.positive": 1.0,  # 通过不入聚合
                "maint.municipal_aao.kb.any_fail": 1.0,  # 汇总键不入聚合
                "maint.municipal_aao.ratio.n": 2.0,  # 观测面分化键
                "maint.municipal_aao.fixgeom.min": -1.0,  # 观测面裕度
            },
            "design_offline_aao2": {
                "maint.municipal_aao.kb.param.n.positive": 0.0,  # 越门（第 2 命中）
                "maint.municipal_aao.kb.param.ghost.positive": 0.0,  # kb 缺席（A2）
                "maint.municipal_aao.kb.any_fail": 1.0,
            },
        },
        trace=(),
        repro=ReproTriple("h1", "e1", "d1"),
    )


def _val_source_a() -> bytes:
    """源 A 合成 val 件：同键双源（param.n.positive——message 优先载体）+
    A-only 行（kz——∅ 哨兵载体）。"""
    return serialize_validation(ValidationReport(warnings=(
        PlantWarning(
            code="kb.param.n.positive",
            condition_key="municipal_aao",
            param_key="n",
            message="源A消息：param.n.positive 越带",
            severity=Severity.ERROR,
        ),
        PlantWarning(
            code="kb.inlet.kz_band",
            condition_key="plant",
            param_key="kz",
            message="源A消息：kz 越带",
            severity=Severity.WARN,
        ),
    )))


def _diag(kb_injected: bool) -> bytes:
    """合成 diag 件（kb_injected 两态——trust serde 正门产出）。"""
    return serialize_diag(DiagnosticsReport(
        convergence=(),
        loop_params={},
        mass_balance=(),
        effluent=(),
        repro=ReproTriple("h1", "e1", "d1"),
        kb_injected=kb_injected,
    ))


_RECORD_CONDITION_KEYS = [
    "design", "avg", "design_offline_aao", "design_offline_aao2",
]


def _build(  # noqa: PLR0913  # 合成件装配（七参=固定桩面——sensitivity 同款 monkeypatch 定点）
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    plant: PlantResult,
    catalog: ConstraintCatalog,
    val_bytes: bytes | None,
    diag_bytes: bytes | None,
    condition_keys: list[str] | None,
) -> ValidationObservationResponse:
    """服务面合成装配：record/两件落盘+取数面替身（E2E 外的定点真源；
    ctx=最小桩（settings.data_dir=list_constraints 替身消费——真 ctx 归 E2E）。"""
    result_file = tmp_path / "result.json"
    result_file.write_bytes(b"{}")  # 内容无关——deserialize 已替身
    record: dict[str, object] = {"result_file": str(result_file)}
    if val_bytes is not None:
        val_file = tmp_path / "val.json"
        val_file.write_bytes(val_bytes)
        record["val_file"] = str(val_file)
    if diag_bytes is not None:
        diag_file = tmp_path / "diag.json"
        diag_file.write_bytes(diag_bytes)
        record["diag_file"] = str(diag_file)
    if condition_keys is not None:
        record["condition_keys"] = condition_keys
    ctx = SimpleNamespace(settings=SimpleNamespace(data_dir=tmp_path))
    monkeypatch.setattr(validation_module, "read_project", lambda ctx, pid: object())
    monkeypatch.setattr(
        validation_module, "latest_calc_result",
        lambda ctx, pid, not_found: ("t1", record),
    )
    monkeypatch.setattr(validation_module, "deserialize", lambda data: plant)
    monkeypatch.setattr(validation_module, "list_constraints", lambda data_dir: catalog)
    monkeypatch.setattr(validation_module, "result_is_stale", lambda latest, project: False)
    return build_validation_observation(ctx, "p1")


def test_router_exposes_validation_endpoint_wiring() -> None:
    """calc 路由端点集含 validation 恰一件（38→39 路径增量无漂移）。"""
    observed = {
        (method.lower(), route.path)
        for route in calc_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed >= _EXPECTED_VALIDATION


def test_validation_two_source_merge_semantics(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """⑦同键双源现：message 取源 A 实例+condition_keys=源 B 工况清单+
    ⑤severity=max（A=ERROR 与 kb 条目 WARN 取 ERROR）——聚合规格 §2/§3。"""
    report = _build(
        monkeypatch, tmp_path, _plant_two_hits(),
        _catalog(_entry("param.n.positive", "n > 0"), _entry("param.h2.positive", "h2 > 0")),
        _val_source_a(), _diag(True), _RECORD_CONDITION_KEYS,
    )
    by_code = {row.code: row for row in report.warnings}
    merged = by_code["kb.param.n.positive"]
    assert merged.message == "源A消息：param.n.positive 越带"  # ⑦源 A 优先
    assert merged.condition_keys == ("design_offline_aao", "design_offline_aao2")  # 源 B 清单
    assert merged.severity is Severity.ERROR  # ⑤max over 命中实例
    assert merged.scope == "municipal_aao" and merged.param_key == "n"  # §4 推导链


def test_validation_source_a_empty_sentinel_not_mixing(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """③源 A 命中清单=∅ 空序列哨兵（声明级一次——不参与 ≥2 计数不混排）；
    ②1.0 通过键不入聚合（入观测面）；④单工况直通行同 schema。"""
    plant = PlantResult(
        conditions={"design": {}, "design_offline_aao": {
            "municipal_aao": _snapshot({"n": 2.0, "h2": 4.5})}},
        summary={"design": {}, "design_offline_aao": {
            "maint.municipal_aao.kb.param.n.positive": 0.0,  # 单工况直通载体
            "maint.municipal_aao.kb.param.h2.positive": 1.0,  # 通过不入
        }},
        trace=(), repro=ReproTriple("h1", "e1", "d1"),
    )
    report = _build(
        monkeypatch, tmp_path, plant,
        _catalog(_entry("param.n.positive", "n > 0"), _entry("param.h2.positive", "h2 > 0")),
        _val_source_a(), None, ["design", "design_offline_aao"],
    )
    rows = {row.code: row for row in report.warnings}
    assert set(rows) == {"kb.param.n.positive", "kb.inlet.kz_band"}  # h2 通过不入
    a_only = rows["kb.inlet.kz_band"]
    assert a_only.condition_keys == ()  # ③∅ 哨兵（非 None 非混排）
    assert a_only.scope == "plant"  # ①字段名=scope（禁 condition_key 双义）
    direct = rows["kb.param.n.positive"]
    assert direct.condition_keys == ("design_offline_aao",)  # ④单工况直通行同 schema


def test_validation_b_only_message_synthesis(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A1 B-only 行 message 合成：三要素=条目键+表达式原文+首命中工况实际值
    （plant.conditions 首命中 dims——序轴首）；字段缺席=无值形态。"""
    plant = PlantResult(
        conditions={
            "design": {},
            "design_offline_aao": {"municipal_aao": _snapshot({"h2": -1.5})},
            "design_offline_aao2": {"municipal_aao": _snapshot({"h2": -2.5})},
        },
        summary={"design": {}, "design_offline_aao": {
            "maint.municipal_aao.kb.param.h2.positive": 0.0},
            "design_offline_aao2": {"maint.municipal_aao.kb.param.h2.positive": 0.0}},
        trace=(), repro=ReproTriple("h1", "e1", "d1"),
    )
    order = ["design", "design_offline_aao2", "design_offline_aao"]  # 迭代序非字典序
    report = _build(
        monkeypatch, tmp_path, plant, _catalog(_entry("param.h2.positive", "h2 > 0")),
        None, None, order,
    )
    row = report.warnings[0]
    assert row.condition_keys == ("design_offline_aao2", "design_offline_aao")  # ⑥序=迭代序
    assert row.message == "kb 越门：param.h2.positive——h2=-2.5 违反 h2 > 0"  # 首命中值
    assert row.severity is Severity.WARN  # kb 条目 severity（B-only 无 A 实例）
    # 字段缺席（快照 dims 无该字段）→ 无值形态
    plant_absent = PlantResult(
        conditions={"design": {}, "design_offline_aao": {
            "municipal_aao": _snapshot({"n": 1.0})}},
        summary={"design": {}, "design_offline_aao": {
            "maint.municipal_aao.kb.param.h2.positive": 0.0}},
        trace=(), repro=ReproTriple("h1", "e1", "d1"),
    )
    report2 = _build(
        monkeypatch, tmp_path, plant_absent,
        _catalog(_entry("param.h2.positive", "h2 > 0")),
        None, None, ["design", "design_offline_aao"],
    )
    assert report2.warnings[0].message == "kb 越门：param.h2.positive——违反 h2 > 0"


def test_validation_pass_any_fail_and_ghost_faces(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """②⑨⑪观测面：通过键/any_fail/ratio/fixgeom 入观测不入聚合；ghost
    （kb 条目缺席）观测面保留原值（fail-visible 非静默）。"""
    report = _build(
        monkeypatch, tmp_path, _plant_two_hits(),
        _catalog(_entry("param.n.positive", "n > 0"), _entry("param.h2.positive", "h2 > 0")),
        None, None, _RECORD_CONDITION_KEYS,
    )
    assert len(report.nodes) == 1
    node = report.nodes[0]
    assert node.node_id == "municipal_aao"
    faces = {face.condition_key: face for face in node.faces}
    first = faces["design_offline_aao"]
    assert first.kb == {"param.h2.positive": True, "param.n.positive": False}  # A6 bool 升级
    assert first.any_fail is True  # 汇总键独立面
    assert first.ratio == {"n": 2.0}  # 分化键原值
    assert first.fixgeom_min == -1.0
    second = faces["design_offline_aao2"]
    assert second.kb == {"param.ghost.positive": False, "param.n.positive": False}  # ⑪保留
    assert second.ratio == {} and second.fixgeom_min is None
    assert report.conditions == tuple(_RECORD_CONDITION_KEYS)  # record 投影（迭代序）
    assert [row.code for row in report.warnings] == ["kb.param.n.positive"]  # ghost 不入聚合


def test_validation_rows_sorted_by_scope_code_param(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A3 响应行排序=(scope,code,param_key) 确定性冻结（视图分区/重排归 FE）。"""
    report = _build(
        monkeypatch, tmp_path, _plant_two_hits(),
        _catalog(_entry("param.n.positive", "n > 0"), _entry("param.h2.positive", "h2 > 0")),
        _val_source_a(), None, _RECORD_CONDITION_KEYS,
    )
    keys = [(row.scope, row.code, row.param_key) for row in report.warnings]
    assert keys == sorted(keys)  # plant 行前置（scope 字典序）+节点行随


def test_validation_val_artifact_three_state_degrade(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """val 件三态降级（trust _load_diagnostics 同款）：缺键/缺文件/损坏 →
    validation_available=False（禁伪造空报告冒充——源 A 面缺席如实）。"""
    plant = _plant_two_hits()
    catalog = _catalog(_entry("param.n.positive", "n > 0"))
    missing_key = _build(
        monkeypatch, tmp_path, plant, catalog, None, None, _RECORD_CONDITION_KEYS)
    assert missing_key.validation_available is False
    assert missing_key.warnings[0].message.startswith("kb 越门")  # 源 B 面仍在
    # 缺文件：val_file 指向不存在路径
    result_file = tmp_path / "result.json"
    result_file.write_bytes(b"{}")
    absent_record: dict[str, object] = {
        "result_file": str(result_file),
        "val_file": str(tmp_path / "absent.json"),
        "condition_keys": _RECORD_CONDITION_KEYS,
    }
    ctx = SimpleNamespace(settings=SimpleNamespace(data_dir=tmp_path))
    monkeypatch.setattr(validation_module, "read_project", lambda ctx, pid: object())
    monkeypatch.setattr(
        validation_module, "latest_calc_result",
        lambda ctx, pid, not_found: ("t1", absent_record),
    )
    monkeypatch.setattr(validation_module, "deserialize", lambda data: plant)
    monkeypatch.setattr(validation_module, "list_constraints", lambda data_dir: catalog)
    monkeypatch.setattr(validation_module, "result_is_stale", lambda latest, project: False)
    absent = build_validation_observation(ctx, "p1")
    assert absent.validation_available is False
    # 损坏：val 件非法 JSON
    corrupt = _build(
        monkeypatch, tmp_path, plant, catalog, b"{not-json", None,
        _RECORD_CONDITION_KEYS)
    assert corrupt.validation_available is False


def test_validation_kb_injected_none_when_diag_missing(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """kb_injected 三态：diag 缺席=None（禁伪造 False——trust 先例）；
    在场=bool 透传。"""
    no_diag = _build(
        monkeypatch, tmp_path, _plant_two_hits(),
        _catalog(_entry("param.n.positive", "n > 0")),
        None, None, _RECORD_CONDITION_KEYS)
    assert no_diag.kb_injected is None
    with_diag = _build(
        monkeypatch, tmp_path, _plant_two_hits(),
        _catalog(_entry("param.n.positive", "n > 0")),
        None, _diag(True), _RECORD_CONDITION_KEYS)
    assert with_diag.kb_injected is True


def test_validation_legacy_record_dict_order_fallback(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A5 存量旧记录缺 condition_keys 键=字典序兜底（plant.summary 键域——
    测试锁定；现役 worker 恒写键，此面=旧档容认）。"""
    report = _build(
        monkeypatch, tmp_path, _plant_two_hits(),
        _catalog(_entry("param.n.positive", "n > 0")),
        None, None, None,  # record 无 condition_keys
    )
    assert report.conditions == (
        "avg", "design", "design_offline_aao", "design_offline_aao2")  # 字典序
    row = report.warnings[0]
    assert row.condition_keys == ("design_offline_aao", "design_offline_aao2")  # 兜底序


def test_validation_third_warning_face_excluded(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """⑩unit_api.Warning 第三警告面不入聚合（v1 两源边界冻结）：快照级
    warnings 在场（合成植入）而聚合行零该码。"""
    snapshot = UnitResultSnapshot(
        unit_id="municipal_aao", outflows={}, outqualities={}, dims={"n": 2.0},
        warnings=(  # 第三警告面（UF-17 冻结六字段——合成最小桩）
            Warning(severity=Severity.WARN, source="test", message="第三警告面桩"),
        ),
        formula_ids=(),
    )
    plant = PlantResult(
        conditions={"design": {}, "design_offline_aao": {"municipal_aao": snapshot}},
        summary={"design": {}, "design_offline_aao": {
            "maint.municipal_aao.kb.param.n.positive": 1.0}},
        trace=(), repro=ReproTriple("h1", "e1", "d1"),
    )
    report = _build(
        monkeypatch, tmp_path, plant, _catalog(_entry("param.n.positive", "n > 0")),
        None, None, ["design", "design_offline_aao"],
    )
    assert report.warnings == ()  # 快照 warnings 不入（全通过 kb 面亦零行）
    assert report.nodes[0].faces[0].kb == {"param.n.positive": True}


def _aao_project_payload() -> dict[str, object]:
    """inlet→AAO 项目载荷（test_sensitivity 同款——E2E 载体）。"""
    return {
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
                    "municipal_aao": {},
                },
                "edges": [
                    {
                        "src": {"unit_id": "inlet", "port_id": "out"},
                        "dst": {"unit_id": "municipal_aao", "port_id": "in"},
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


async def _project_with_result(client) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """创建 AAO 项目并跑一次计算（三并列 artifact 就绪——val/diag 同批落盘）。"""
    created = await client.post("/api/projects", json=_aao_project_payload())
    assert created.status_code == status.HTTP_200_OK
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": ["municipal_aao"]}
    )).json()["task_id"]
    body: dict[str, object] = {}
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id, task_id


@pytest.mark.anyio
async def test_validation_endpoint_shape(client) -> None:  # type: ignore[no-untyped-def]
    """E2E GET 200：新批三件就绪（validation_available/kb_injected 双 True）+
    conditions=record 投影（baseline 两档+offline）+观测节点在场+行 schema 六键。"""
    project_id, task_id = await _project_with_result(client)
    response = await client.get(f"/api/calc/validation/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["task_id"] == task_id
    assert body["stale"] is False
    assert body["validation_available"] is True  # 新批 worker val 件在场
    assert body["kb_injected"] is True  # kbwire 起生产注入
    assert body["conditions"] == ["design", "avg", "design_offline_municipal_aao"]
    assert [node["node_id"] for node in body["nodes"]] == ["municipal_aao"]
    face = body["nodes"][0]["faces"][0]
    assert set(face) == {
        "condition_key", "kb", "any_fail", "ratio", "fixgeom_min"}
    assert face["condition_key"] == "design_offline_municipal_aao"
    assert face["kb"] and all(isinstance(v, bool) for v in face["kb"].values())
    assert face["any_fail"] is False  # golden aao kb 面 8 条全过
    for row in body["warnings"]:
        assert set(row) == {
            "code", "param_key", "scope", "message", "condition_keys", "severity"}


@pytest.mark.anyio
async def test_validation_determinism_double_get(client) -> None:  # type: ignore[no-untyped-def]
    """确定性：同结果集双 GET 响应 JSON（sort_keys）字节同。"""
    project_id, _ = await _project_with_result(client)
    first = (await client.get(f"/api/calc/validation/{project_id}")).json()
    second = (await client.get(f"/api/calc/validation/{project_id}")).json()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


@pytest.mark.anyio
async def test_validation_error_faces(client) -> None:  # type: ignore[no-untyped-def]
    """错误面：未知项目 404/无结果集 404（引导语含 /api/calc/run）+AU-1 路径安全。"""
    response = await client.get("/api/calc/validation/nosuchproject0000")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    created = await client.post("/api/projects", json=_aao_project_payload())
    project_id = created.json()["project_id"]
    response = await client.get(f"/api/calc/validation/{project_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]
    for probe in ("../escape", "..%2fescape", "x/../../escape"):
        response = await client.get(f"/api/calc/validation/{probe}")
        assert response.status_code < 500  # AU-1：浅深构造全 4xx 非 500


def test_validation_corrupt_result_404_face(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """损坏结果件→404 面（trust/compare 同款）：deserialize 失败族与文件
    缺失同归 ValidationSourceNotFoundError（无 500 泄漏）。"""
    from waterprint.contracts.result_schema import InvalidResultError

    result_file = tmp_path / "corrupt.json"
    result_file.write_bytes(b"{not-json")
    monkeypatch.setattr(validation_module, "read_project", lambda ctx, pid: object())
    monkeypatch.setattr(
        validation_module, "latest_calc_result",
        lambda ctx, pid, not_found: ("t1", {"result_file": str(result_file)}),
    )
    with pytest.raises(validation_module.ValidationSourceNotFoundError) as excinfo:
        build_validation_observation(None, "p1")  # type: ignore[arg-type]
    assert "先重算" in str(excinfo.value)
    monkeypatch.setattr(validation_module, "deserialize", lambda data: (_ for _ in ()).throw(
        InvalidResultError("结构非法")))
    with pytest.raises(validation_module.ValidationSourceNotFoundError):
        build_validation_observation(None, "p1")  # type: ignore[arg-type]
