"""validation 聚合回炉伴生件：同键多实例/排序对抗/severity 方向/真库推导探针。

输入:  waterprint_server.services.validation 聚合段+推导链（_aggregated_
       warnings/_expression_first_field）+合成桩+真 kb 目录（仓库 data 面）
输出:  门一回炉轮 1 锚（d1-W2 首例保序+severity 累积/d1-W4 排序对抗桩/
       k1-N1·d1-N6c severity 反向与同级并列/k1-W1·d1-U3 真库推导链探针）
       ——500 行预算墙伴生拆分（主件 test_validation.py，1A4 契约伴生件先例）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：2A1 门一双审回炉轮 1（2a1-20261005 g1-dispositions §二
#   1/3/4/6①）——聚合语义结构性防御锚+DSL 镜像解析真库探针。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from waterprint.contracts.result_schema import (
    PlantResult,
    ReproTriple,
    UnitResultSnapshot,
)
from waterprint.contracts.unit_api import Severity
from waterprint.contracts.validation import (
    PlantWarning,
    ValidationReport,
    serialize_validation,
)

from waterprint_server.services import validation as validation_module
from waterprint_server.services.constraints import (
    ConstraintCatalog,
    ConstraintEntry,
    list_constraints,
)
from waterprint_server.services.validation import (
    ValidationObservationResponse,
    build_validation_observation,
)

# 真源 kb 面（仓库 data 目录——test_constraints L30 真库先例同源推导）
_REPO = Path(__file__).resolve().parents[3] / "data"  # server/tests/services/→仓库根


def _entry(key: str, expression: str, severity: str = "WARN") -> ConstraintEntry:
    """合成 kb 目录条目（主件 _entry 同款——伴生件自包含）。"""
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


def _report_of(  # noqa: PLR0913, PLR0917  # 聚合段定点装配（六参=固定桩面——主件 _build 聚焦瘦身；替身签名镜像先例）
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    plant: PlantResult,
    entries: tuple[ConstraintEntry, ...],
    val_bytes: bytes | None,
    condition_keys: list[str],
) -> ValidationObservationResponse:
    """聚合段合成装配（diag/val 降级面归主件——本件聚焦聚合语义）。"""
    result_file = tmp_path / "result.json"
    result_file.write_bytes(b"{}")  # 内容无关——deserialize 已替身
    record: dict[str, object] = {
        "result_file": str(result_file), "condition_keys": condition_keys}
    if val_bytes is not None:
        val_file = tmp_path / "val.json"
        val_file.write_bytes(val_bytes)
        record["val_file"] = str(val_file)
    ctx = SimpleNamespace(settings=SimpleNamespace(data_dir=tmp_path))
    monkeypatch.setattr(validation_module, "read_project", lambda ctx, pid: object())
    monkeypatch.setattr(
        validation_module, "latest_calc_result",
        lambda ctx, pid, not_found: ("t1", record),
    )
    monkeypatch.setattr(validation_module, "deserialize", lambda data: plant)
    monkeypatch.setattr(
        validation_module, "list_constraints",
        lambda data_dir: ConstraintCatalog(entries=entries),
    )
    monkeypatch.setattr(validation_module, "result_is_stale", lambda latest, project: False)
    return build_validation_observation(ctx, "p1")


def _plant_violation() -> PlantResult:
    """单越门最小结果件（B 行载体——node municipal_aao 一工况越门）。"""
    return PlantResult(
        conditions={"design": {}, "design_offline_aao": {"municipal_aao":
            UnitResultSnapshot(
                unit_id="municipal_aao", outflows={}, outqualities={},
                dims={"n": 0.0}, warnings=(), formula_ids=())}},
        summary={"design": {}, "design_offline_aao": {
            "maint.municipal_aao.kb.param.n.positive": 0.0}},
        trace=(), repro=ReproTriple("h1", "e1", "d1"),
    )


def test_rework_w2_same_key_dual_a_instances_first_message_severity_max(
    monkeypatch, tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    """回炉 d1-W2：源 A 同三元组多实例=首例保序（message=首例——§2 首例
    条款前瞻绑定）+severity 累积 max（非末例覆盖）；core 各族单发现状
    不可达——结构性防御锚。"""
    val = serialize_validation(ValidationReport(warnings=(
        PlantWarning(
            code="kb.param.n.positive", condition_key="municipal_aao",
            param_key="n", message="首例消息", severity=Severity.WARN),
        PlantWarning(
            code="kb.param.n.positive", condition_key="municipal_aao",
            param_key="n", message="次例消息", severity=Severity.ERROR),
    )))
    report = _report_of(
        monkeypatch, tmp_path, _plant_violation(),
        (_entry("param.n.positive", "n > 0"),), val, ["design", "design_offline_aao"],
    )
    assert len(report.warnings) == 1  # 同键归一行（去重键三元组）
    row = report.warnings[0]
    assert row.message == "首例消息"  # 首例保序（旧实现 last-wins 缺陷锚）
    assert row.severity is Severity.ERROR  # 实例 severity 累积 max
    assert row.condition_keys == ("design_offline_aao",)  # 源 B 清单随行


def test_rework_w4_rows_sorted_adversarial_explicit_order(
    monkeypatch, tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    """回炉 d1-W4：排序对抗桩——入桶序（A 报告序+工况序）≠终序
    (scope,code,param_key)，显式期望元组序断言（sort 键实现真跑）。"""
    val = serialize_validation(ValidationReport(warnings=(  # A 面：code 逆序入桶
        PlantWarning(
            code="kb.inlet.zz_band", condition_key="plant",
            param_key="kz", message="A-zz", severity=Severity.WARN),
        PlantWarning(
            code="kb.inlet.aa_band", condition_key="plant",
            param_key="kz", message="A-aa", severity=Severity.WARN),
    )))
    report = _report_of(
        monkeypatch, tmp_path, _plant_violation(),
        (_entry("param.n.positive", "n > 0"),), val, ["design", "design_offline_aao"],
    )
    # 入桶序=[plant-zz, plant-aa, municipal_aao-n]≠终序（scope 交叉+code 交叉）
    assert [(row.scope, row.code, row.param_key) for row in report.warnings] == [
        ("municipal_aao", "kb.param.n.positive", "n"),  # B 行 scope 前置
        ("plant", "kb.inlet.aa_band", "kz"),  # A 行 code 字典序重排
        ("plant", "kb.inlet.zz_band", "kz"),
    ]


def test_rework_n1_severity_reverse_and_parallel_first(
    monkeypatch, tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    """回炉 k1-N1/d1-N6c：severity 反向锚（kb 条目 ERROR>A 实例 WARN→聚合
    行 ERROR）+同级并列取序首（A WARN+kb WARN→WARN——§2 分级值同无展示差）。"""
    val = serialize_validation(ValidationReport(warnings=(
        PlantWarning(
            code="kb.param.n.positive", condition_key="municipal_aao",
            param_key="n", message="源A消息", severity=Severity.WARN),
    )))
    reverse = _report_of(
        monkeypatch, tmp_path, _plant_violation(),
        (_entry("param.n.positive", "n > 0", severity="ERROR"),), val,
        ["design", "design_offline_aao"],
    )
    assert reverse.warnings[0].severity is Severity.ERROR  # kb 条目更严重胜出
    parallel = _report_of(
        monkeypatch, tmp_path, _plant_violation(),
        (_entry("param.n.positive", "n > 0", severity="WARN"),), val,
        ["design", "design_offline_aao"],
    )
    assert parallel.warnings[0].severity is Severity.WARN  # 同级并列=序首无展示差


def test_rework_w1_real_kb_catalog_first_field_probe() -> None:
    """回炉 k1-W1/d1-U3：真 kb 目录探针——现库 DSL 域全条目（boundary_
    check 豁免同 _maint_face 适用判据——符号契约面非比较 DSL 域，装载器
    同款豁免镜像）expression 过 _expression_first_field 不抛+首字段非空。"""
    catalog = list_constraints(_REPO)
    probed = 0
    for entry in catalog.entries:
        if entry.kind == "boundary_check":
            continue  # 符号式 containment == inside——非 DSL 域（豁免注记）
        field = validation_module._expression_first_field(entry)  # noqa: SLF001  # 推导链私有直测（test_site _env 先例）
        assert field, f"{entry.key} 首子句字段空"
        probed += 1
    assert probed == len(catalog.entries) - 1  # 全 DSL 域条目覆盖（155−1）


def test_rework_w1_malformed_expression_fail_visible() -> None:
    """回炉 k1-W1：畸形表达式 RuntimeError fail-visible 在场核（镜像解析
    守卫——非静默跳过非伪造值）。"""
    bad = ConstraintEntry(
        key="malformed.probe", kind="param_band", unit_kinds=("municipal_aao",),
        label="畸形桩", expression="== 畸形", source="probe",
        severity="WARN", value_basis="测试合成", enforcement="flag",
    )
    with pytest.raises(RuntimeError, match="首子句形态非法"):
        validation_module._expression_first_field(bad)  # noqa: SLF001  # 同上私有直测
