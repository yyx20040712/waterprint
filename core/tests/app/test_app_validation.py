"""app_validation 镜像测试：厂级进水输入合理性校验骨架（1A2 批）。

输入:  waterprint.app_validation（validation_summary_of/INPUT_BAND_FIELDS/
       INPUT_BAND_KIND/MASS_BALANCE_KIND）+kb 真源（仓库 data 面 151 条——
       1A3 批增 mass_balance 1 条+1A4 批增 param_band 109 条）+golden 双案
       （municipal_34760 市政进水声明/mine_43836 矿井线无市政声明节点）
输出:  行为断言——合法进水零警告/非法进水码命中（kz 双界参数化/CODCR/
       五指标越带参数化〔SS 用例含 mass_balance 交互面在档〕/混合越带+
       混合缺项不掩蔽）/缺项跳检不警（指标两态+kz 键缺席态）/真实节点
       键集外部锚/选条判据=kind 直判（input_band∪mass_balance 双剔除）/
       memo①冻结字段集机器对账/memo③映射表对账/memo②负向锚（A42 vs
       B34 serialize 恒等+B vs C 差异面恰 12 键 maint.* 前缀锚定）/首节点
       插入序取首/run_full_calc 第四字段接线（显式+缺省 constraints 路径）
       /双跑确定性；1A3 泥量互校族行为面=伴生件
       test_app_validation_mass_balance.py（行数预算墙拆分）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：1A2 校验骨架批（1a2-20261004）§3.2/§3.4——选条判据=kind==
#   "input_band"（unit_kinds 恒空不参与选条——接线红线逐字引用见模块
#   头注）；进水单值表=project 进水原始数据直取（design.nodes 市政
#   输入声明节点——非计算值）；求值=solution.apply_constraints 单行
#   DataFrame（app_maintenance L127 先例形态——DSL 单源禁手写求值）。
#   memo②负向锚实现形态=主控修正案（A/B/C 三跑替代「全量 vs 零注入」
#   单比——maint.* 键面已在役，全量 vs 零差异非 input_band 独占面）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from waterprint.app_validation import (
    INPUT_BAND_FIELDS,
    INPUT_BAND_KIND,
    MASS_BALANCE_KIND,
    validation_summary_of,
)
from waterprint.contracts.condition import build_condition_set
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.quality import INDICATORS
from waterprint.contracts.result_schema import serialize
from waterprint.contracts.validation import ValidationReport, kb_warning_code
from waterprint.solution.constraints import (
    KbConstraint,
    expression_fields,
    load_kb_constraints,
)

_GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "golden_data"
_REPO_DATA = Path(__file__).resolve().parents[3] / "data"
_KB_FILE = _REPO_DATA / "constraint_kb" / "constraints.json"
_KZ_CODE = "inlet.kz_band"
_COD_CODE = "inlet.quality_upper.cod"
# 五指标越带参数（d1-W2b：值=各带上界外一点；cod 有专例不入此表——
# 满覆盖锚 test_indicator_cases_cover_non_cod_quality_family 对账 kb 族）
_INDICATOR_CASES: tuple[tuple[str, float, str], ...] = (
    ("BOD5", 500.0, "inlet.quality_upper.bod5"),
    ("SS", 500.0, "inlet.quality_upper.ss"),
    ("NH3N", 60.0, "inlet.quality_upper.nh3n"),
    ("TN", 80.0, "inlet.quality_upper.tn"),
    ("TP", 15.0, "inlet.quality_upper.tp"),
)
# mass_balance 键（SS 越带交互断言用——行为面归伴生件）
_MB_CODE = "sludge.primary_load_band"


def _municipal_raw() -> dict[str, Any]:
    """golden 市政案原始 JSON（进水声明节点=inlet）。"""
    return json.loads(
        (_GOLDEN / "municipal_34760" / "input_project.json").read_text(encoding="utf-8"))


def _municipal_project(**inlet_overrides: Any) -> ProjectFile:
    """golden 市政案+进水声明节点参数覆盖（原始数据面——非计算值）。"""
    raw = _municipal_raw()
    raw["design"]["nodes"]["inlet"].update(inlet_overrides)
    return ProjectFile.model_validate(raw)


@pytest.fixture(scope="module")
def loaded_kb() -> tuple[KbConstraint, ...]:
    """kb 真源装载（151 条全量——单源=data 面；1A3 批 +mass_balance 1
    +1A4 批 +param_band 109〔行为面归伴生件 test_app_validation_param_band.py〕）。"""
    return load_kb_constraints(_KB_FILE)


@pytest.fixture(scope="module")
def input_band_family(loaded_kb: tuple[KbConstraint, ...]) -> tuple[KbConstraint, ...]:
    """input_band 七条族（选条判据同款 kind 直判）。"""
    return tuple(kb for kb in loaded_kb if kb.kind == INPUT_BAND_KIND)


# ── 合法/非法/缺项/选条（骨架执行面直调——零装配开销）──────────────────


def test_legal_influent_zero_warnings(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """合法进水（golden kz=1.4+六指标全带内）零警告：report falsy。"""
    report = validation_summary_of(_municipal_project(), loaded_kb)
    assert not report
    assert report.codes() == ()


@pytest.mark.parametrize("kz_value", [3.0, 1.0])
def test_illegal_kz_hits_band_code(
    loaded_kb: tuple[KbConstraint, ...], kz_value: float
) -> None:
    """非法 kz 越带（上界 3.0/下界 1.0 参数化对称——k1-W3：双子句「任一
    假即违规」双向覆盖）→码命中 kb.inlet.kz_band+五字段值锚（param_key
    =kz/severity=WARN/message 含实际值+带域数值+条目键——禁空话）。"""
    report = validation_summary_of(_municipal_project(kz=kz_value), loaded_kb)
    assert report.codes() == (kb_warning_code(_KZ_CODE),)
    (warning,) = report.warnings
    assert warning.param_key == "kz"
    assert warning.condition_key == "plant"
    assert warning.severity.value == "WARN"
    assert f"{kz_value!r}" in warning.message  # 实际值
    assert "1.3" in warning.message and "2.7" in warning.message  # 带域数值
    assert _KZ_CODE in warning.message  # 条目键（label 面——kb label 不在装载形态）


def test_illegal_cod_hits_quality_code(loaded_kb: tuple[KbConstraint, ...]) -> None:
    """非法 CODCR=1200（上界 1000 外）→码命中 kb.inlet.quality_upper.cod
    （param_key=CODCR——key 后缀 cod 与冻结字段异名对照）。"""
    report = validation_summary_of(_municipal_project(CODCR=1200.0), loaded_kb)
    assert report.codes() == (kb_warning_code(_COD_CODE),)
    (warning,) = report.warnings
    assert warning.param_key == "CODCR"
    assert "1200.0" in warning.message


@pytest.mark.parametrize(("field", "value", "code_key"), _INDICATOR_CASES)
def test_illegal_indicator_hits_quality_code(
    loaded_kb: tuple[KbConstraint, ...], field: str, value: float, code_key: str
) -> None:
    """五指标越带参数化（d1-W2b——与 kz/CODCR 用例同构）：各上界外值→
    各自码恰单命中（param_key=冻结字段名——key 后缀与字段异名对照）。
    SS 用例交互面在档（1A3）：越带 SS=500 同时压低互校 ratio≈0.186＜
    下界 0.2（golden 声明 ds_primary=3240.12 对越带 SS 不一致）→
    mass_balance 码齐发（warn 序=kb 声明序：input_band 在前）。"""
    report = validation_summary_of(
        _municipal_project(**{field: value}), loaded_kb)
    expected = [kb_warning_code(code_key)]
    if field == "SS":
        expected.append(kb_warning_code(_MB_CODE))
    assert report.codes() == tuple(expected)
    warning = next(w for w in report.warnings if w.param_key == field)
    assert warning.param_key == field
    assert f"{value!r}" in warning.message  # 实际值入话


def test_indicator_cases_cover_non_cod_quality_family(
    input_band_family: tuple[KbConstraint, ...],
) -> None:
    """五指标参数表满覆盖锚：_INDICATOR_CASES 键集恰=inlet.quality_upper.*
    族−cod（cod 有专例）——参数表删一员/漂一键即红（kb 族真源对账）。"""
    expected = {
        kb.constraint.key for kb in input_band_family
        if kb.constraint.key.startswith("inlet.quality_upper.")
        and kb.constraint.key != _COD_CODE}
    assert {code_key for _, _, code_key in _INDICATOR_CASES} == expected


def test_mixed_violations_hit_both_codes(loaded_kb: tuple[KbConstraint, ...]) -> None:
    """混合越带（kz=3.0+CODCR=1200）→双码齐发（warn 序=kb 声明序）。"""
    report = validation_summary_of(
        _municipal_project(kz=3.0, CODCR=1200.0), loaded_kb)
    assert report.codes() == (
        kb_warning_code(_KZ_CODE), kb_warning_code(_COD_CODE))


def test_missing_indicator_skips_check_silently(
    input_band_family: tuple[KbConstraint, ...],
) -> None:
    """缺项跳检不警（WaterQuality 缺项 None 合法语义）：值 None 态与键
    缺席态均跳检零警告（CODCR 在场带内照常检）。"""
    absent_fields = ("BOD5", "SS", "NH3N", "TN", "TP")
    raw = _municipal_raw()
    inlet = raw["design"]["nodes"]["inlet"]
    for field in absent_fields:
        inlet[field] = None  # 值 None 态（非数值跳检）
    with_none = ProjectFile.model_validate(raw)
    for field in absent_fields:
        inlet.pop(field)  # 键缺席态（缺项不参与单值表）
    absent = ProjectFile.model_validate(raw)
    for project in (with_none, absent):
        assert not validation_summary_of(project, input_band_family)


def test_missing_fields_do_not_mask_present_violation(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """混合缺项+在场越带（k1-W2）：BOD5/SS 缺席+CODCR=1200 越带→恰单码
    kb.inlet.quality_upper.cod 命中（在场指标照常检、缺项不掩蔽）。"""
    raw = _municipal_raw()
    inlet = raw["design"]["nodes"]["inlet"]
    inlet.pop("BOD5")
    inlet.pop("SS")
    inlet["CODCR"] = 1200.0
    report = validation_summary_of(ProjectFile.model_validate(raw), loaded_kb)
    assert report.codes() == (kb_warning_code(_COD_CODE),)


def test_kz_absent_with_node_present_skips_silently(
    input_band_family: tuple[KbConstraint, ...],
) -> None:
    """kz 缺席态（k1-N4）：声明节点在场+kz 键缺席→跳检不警钉死（「kz
    恒在」背书域=run_full_calc 装配路径 make_flow 守卫〔kz>=1 拒非法〕；
    路径外直调无背书——缺席即跳检语义，模块头注 R2 对照）。"""
    raw = _municipal_raw()
    raw["design"]["nodes"]["inlet"].pop("kz")
    report = validation_summary_of(
        ProjectFile.model_validate(raw), input_band_family)
    assert not report
    assert report.codes() == ()


def test_mine_line_without_municipal_declaration_zero_warnings(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """矿井线案（无 municipal_input 声明节点——mine_water_input 为注册表
    单元非内置图源）→进水单值表空=全跳检零警告（kz 检不适用）。"""
    mine = json.loads(
        (_GOLDEN / "mine_43836" / "input_project.json").read_text(encoding="utf-8"))
    assert "municipal_input" not in {
        params.get("kind") for params in mine["design"]["nodes"].values()}
    assert not validation_summary_of(ProjectFile.model_validate(mine), loaded_kb)


def test_selection_criterion_is_kind_not_unit_kinds(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """选条判据=kind 直判：剔除 input_band∪mass_balance∪param_band 后的
    34 条注入+非法 kz=零警告（unit_kinds 恒空既非「全单元适用」亦不参与
    选条——接线红线；param_band 三族剔除=1A4 勘正〔非 kind 直判族——节点
    ID∈unit_kinds 分立判据，行为面归伴生件〕）。"""
    others = tuple(
        kb for kb in loaded_kb
        if kb.kind not in {INPUT_BAND_KIND, MASS_BALANCE_KIND, "param_band"})
    assert len(others) == 34  # 151−117（input_band 7+mass_balance 1+param_band
    # 109 三族剔除——负向锚 B 面同款口径，1A4 勘正注记）
    assert not validation_summary_of(
        _municipal_project(kz=3.0), others)


def test_double_run_deterministic(loaded_kb: tuple[KbConstraint, ...]) -> None:
    """纯函数双跑全等（kb 迭代=传入序/声明节点=插入序的确定性）。"""
    project = _municipal_project(kz=3.0, CODCR=1200.0)
    assert validation_summary_of(project, loaded_kb) == validation_summary_of(
        project, loaded_kb)


def test_multiple_declarations_take_first_in_insertion_order(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """首节点语义（d1-N3）：双 municipal_input 声明节点→仅取插入序首个
    （非法在前→码命中；合法在前+非法在后→零警告——双向钉死取首口径，
    模块头注 R2 勘正注记对照）。"""
    extra = {**_municipal_raw()["design"]["nodes"]["inlet"], "kz": 3.0}
    raw = _municipal_raw()
    raw["design"]["nodes"] = {"inlet_ahead": extra, **raw["design"]["nodes"]}
    ahead = ProjectFile.model_validate(raw)
    raw = _municipal_raw()
    raw["design"]["nodes"] = {**raw["design"]["nodes"], "inlet_behind": extra}
    behind = ProjectFile.model_validate(raw)
    assert validation_summary_of(ahead, loaded_kb).codes() == (
        kb_warning_code(_KZ_CODE),)
    assert not validation_summary_of(behind, loaded_kb)


# ── memo①冻结字段集机器对账+memo③映射表对账────────────────────────


def test_real_inlet_node_keyset_covers_input_band_fields() -> None:
    """真实 schema 外部锚（d1-W2c）：golden 市政案 inlet 节点 params 键集
    ⊇ set(INPUT_BAND_FIELDS.values())——真实节点面外部真源对照（防注入式
    用例自带键名掩蔽真实节点键名假设）。"""
    inlet_keys = set(_municipal_raw()["design"]["nodes"]["inlet"])
    assert set(INPUT_BAND_FIELDS.values()) <= inlet_keys


def test_input_band_fields_match_frozen_truth(
    input_band_family: tuple[KbConstraint, ...],
) -> None:
    """memo①：七条 expression 左侧字段 ⊆ {kz}∪INDICATORS 且恰等于该集
    （真源=quality.INDICATORS+flow.WaterFlow 字段面导入对照——防回归）。"""
    union: set[str] = set()
    for kb in input_band_family:
        fields = expression_fields(kb.constraint.expression)
        assert len(fields) == 1  # kz_band 双子句同字段去重=单字段；余单上限子句
        union.update(fields)
    assert union <= {"kz"} | set(INDICATORS)  # 子集面（白名单字段）
    assert union == {"kz"} | set(INDICATORS)  # 恰等于（七键全覆盖——7 码稳定集）
    assert "kz" in {f.name for f in dataclasses.fields(WaterFlow)}  # kz 锚=flow 契约


def test_key_field_mapping_table_matches_expressions(
    input_band_family: tuple[KbConstraint, ...],
) -> None:
    """memo③：映射表（模块常量单源）逐条对账 kb 表达式首子句字段——
    key 后缀与冻结字段异名对照（cod→CODCR 等）；错配一字段即红。"""
    assert len(INPUT_BAND_FIELDS) == len(input_band_family)  # 表=族满覆盖
    for kb in input_band_family:
        field = expression_fields(kb.constraint.expression)[0]
        assert INPUT_BAND_FIELDS[kb.constraint.key] == field, kb.constraint.key


# ── memo②负向锚（A/B/C 三跑——主控修正案形态）+run_full_calc 接线 ──────


def _summary_diff_face(
    left: dict[str, dict[str, float]], right: dict[str, dict[str, float]]
) -> set[str]:
    """两 summary 的差异键面（含单侧在场键——值不等或在场差均计）。"""
    face: set[str] = set()
    for condition in set(left) | set(right):
        l_fields, r_fields = left.get(condition, {}), right.get(condition, {})
        for key in set(l_fields) | set(r_fields):
            if l_fields.get(key) != r_fields.get(key):
                face.add(key)
    return face


@pytest.fixture(scope="module")
def golden_run() -> Any:
    """golden 全链跑批载体（A=151 全量/B=143 剔 input_band∪mass_balance/
    C=零注入+闭包）。

    1A4 裁量注记：B 面维持两族剔除（param_band 不剔）——param_band 条目
    经 _maint_face 字段准入（expression_fields⊆offline_dims——n/h2 等
    参数名与 aao 离线 dims 同名）合法选中，A/B 两面同步消费→serialize
    恒等锚保活；param_band 的 plant 面新增标注键恰 4 处全 PASS 的实证
    归伴生件 test_app_validation_param_band.py（任务书 §3.2 实证①「零新
    键」论断勘正——详见批档 impl-report 实现裁量）。"""
    from waterprint.app import load_run_env, run_full_calc

    project = _municipal_project()
    env = load_run_env(_REPO_DATA, project)
    conditions = build_condition_set(["municipal_aao"])
    loaded = load_kb_constraints(_KB_FILE)
    without = tuple(
        kb for kb in loaded
        if kb.kind not in {INPUT_BAND_KIND, MASS_BALANCE_KIND})
    # （B 面=151−8=143——input_band∪mass_balance 双剔除口径；param_band
    # 两面同在=plant 消费面同步，差异锚归 B vs C 面）

    def run(active: tuple[KbConstraint, ...], inflow: ProjectFile | None = None) -> Any:
        return run_full_calc(inflow or project, conditions, env, constraints=active)

    def run_default(inflow: ProjectFile | None = None) -> Any:
        return run_full_calc(inflow or project, conditions, env)  # 不传 constraints——签名缺省 ()

    return {"all": run(loaded), "without": run(without), "zero": run(()),
            "run": run, "run_default": run_default, "loaded": loaded}


def test_negative_anchor_input_band_zero_consumption(golden_run: Any) -> None:
    """memo②负向锚：A(151) vs B(143) plant serialize 逐字节恒等——input_band
    ∪mass_balance 零 plant 消费构造性运行期实证（validation=独立第四字段
    不回流 plant；param_band 两面同在不在此锚差异面——其 plant 面增量实证
    归伴生件）。"""
    assert serialize(golden_run["all"].plant) == serialize(golden_run["without"].plant)


def test_negative_anchor_b_vs_c_diff_face_is_maintenance_only(golden_run: Any) -> None:
    """memo②差异面：B(143) vs C(0) 差异恰 maint.* 键族（前缀锚定——k1-W1）
    且基线恰 14 键（14=12 基线〔10 kb+any_fail+fixgeom〕+1A4 批 param_band
    增 2 键〔kb.param.n/h2.positive——_maint_face 字段准入对 dims 同名参数
    键的合法选中，全 PASS〕——B 场实测基线，漂移即红）；其余零漂——防
    「B 恰好等价零注入」假阳：差异面非空且全部落在检修执法键族（两族各
    非空保留）。"""
    face = _summary_diff_face(
        golden_run["without"].plant.summary, golden_run["zero"].plant.summary)
    assert face  # 差异面非空（B≠C 假阳防线）
    assert len(face) == 14  # 基线锚（漂移即红——键数增减均报警）
    assert all(key.startswith("maint.") for key in face), sorted(face)  # 前缀锚定
    assert any(".kb." in key for key in face)
    assert any(".fixgeom." in key for key in face)
    assert {"maint.municipal_aao.kb.param.n.positive",
            "maint.municipal_aao.kb.param.h2.positive"} <= face  # 1A4 增键锚


def test_run_full_calc_wiring_fourth_field(golden_run: Any) -> None:
    """接线：ResultBundle 第四字段 validation 在场（合法 golden=零警告
    falsy；缺省 () 注入=同零警告——validation 面恒产出不因注入缺席丢档）。"""
    for key in ("all", "zero"):
        bundle = golden_run[key]
        assert isinstance(bundle.validation, ValidationReport), key
        assert not bundle.validation
        assert bundle.validation.codes() == ()


def test_run_full_calc_default_constraints_zero_validation(golden_run: Any) -> None:
    """缺省路径接线（k1-N2）：run_full_calc 不传 constraints 实参（走签名
    缺省 ()）→validation 恒产出零警告（falsy/codes()=()——第四字段不因
    调用形态丢档）。"""
    bundle = golden_run["run_default"]()
    assert isinstance(bundle.validation, ValidationReport)
    assert not bundle.validation
    assert bundle.validation.codes() == ()


def test_run_full_calc_illegal_influent_reported(golden_run: Any) -> None:
    """接线（非法面）：run_full_calc 全链+非法 kz=3.0 →bundle.validation
    码命中 kb.inlet.kz_band（进水原始数据直取——非计算值；仪表灯不阻断）。"""
    illegal = golden_run["run"](
        golden_run["loaded"], inflow=_municipal_project(kz=3.0))
    assert illegal.validation.codes() == (kb_warning_code(_KZ_CODE),)
    assert illegal.plant.conditions  # 全链照常产出（enforcement=flag 仪表灯语义）
