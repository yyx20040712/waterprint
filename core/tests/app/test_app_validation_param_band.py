"""app_validation param_band 伴生件镜像测试：单元级参数域校验（1A4 批）。

输入:  waterprint.app_validation（validation_summary_of/PARAM_BAND_KIND）+
       kb 真源（仓库 data 面 151 条——1A4 批 +param_band 109）+golden 五案
输出:  行为断言——正性越带（负值/零值/NaN 三态）/带内正值零警告/缺项跳检
       （声明面稀疏）/非数值跳检（str/bool 不入表）/选条判据（节点 ID∈
       unit_kinds——非条目 unit_kinds 单元零警告）/golden 五案 param_band
       面零警告+plant 面增量恰 4 键全 PASS（§3.2 零破坏实证①勘正——
       _maint_face 字段准入对 aao 离线 dims 同名参数键 n/h2 合法选中）/
       双跑确定性
背景:  1A4 批（2026-10-04）——主件 test_app_validation.py 计数锚与 B 面勘正
       已随数据笔落库；本件=core 消费面行为测试（预算墙拆分先例：
       test_app_validation_mass_balance.py 同款）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from waterprint.app_validation import PARAM_BAND_KIND, validation_summary_of
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.validation import kb_warning_code
from waterprint.solution.constraints import KbConstraint, load_kb_constraints

_GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "golden_data"
_REPO_DATA = Path(__file__).resolve().parents[3] / "data"
_KB_FILE = _REPO_DATA / "constraint_kb" / "constraints.json"
_HEBING_NODE = "sludge_hebing"  # golden 市政案泥量声明节点（ds_* 三键在场）
_DS_BIO_CODE = "param.ds_bio.positive"  # hebing 单元唯一键（与 mass_balance
# 互校面无涉——ds_primary 越带会双码齐发〔mass_balance 交互面归主件 SS
# 用例同族在档〕，本件行为面取单码干净面）


def _raw(case: str = "municipal_34760") -> dict[str, Any]:
    return json.loads(
        (_GOLDEN / case / "input_project.json").read_text(encoding="utf-8"))


def _project_with(
    node: str = _HEBING_NODE, case: str = "municipal_34760", **overrides: Any
) -> ProjectFile:
    """golden 案+指定节点 params 覆盖（原始声明面——非计算值）。"""
    raw = _raw(case)
    raw["design"]["nodes"][node].update(overrides)
    return ProjectFile.model_validate(raw)


@pytest.fixture(scope="module")
def loaded_kb() -> tuple[KbConstraint, ...]:
    """kb 真源装载（151 条全量——单源=data 面；1A4 批 +param_band 109）。"""
    return load_kb_constraints(_KB_FILE)


@pytest.fixture(scope="module")
def param_band_family(
    loaded_kb: tuple[KbConstraint, ...],
) -> tuple[KbConstraint, ...]:
    """param_band 109 条族（选条判据=节点 ID∈unit_kinds——分立判据）。"""
    return tuple(kb for kb in loaded_kb if kb.kind == PARAM_BAND_KIND)


# ── 越带三态（负值/零值/NaN）与带内──────────────────────────────────


@pytest.mark.parametrize(("value", "face"), [(-1.0, "负值"), (0.0, "零值")])
def test_nonpositive_param_hits_param_band_code(
    loaded_kb: tuple[KbConstraint, ...], value: float, face: str
) -> None:
    """正性越带（{face}注入）→码命中 kb.param.ds_bio.positive 五字段锚
    （param_key=ds_bio/condition_key=节点 ID/severity=WARN/message 含
    实际值+表达式原文+条目键——三要素禁空话）。"""
    report = validation_summary_of(
        _project_with(ds_bio=value), loaded_kb)
    assert report.codes() == (kb_warning_code(_DS_BIO_CODE),)
    (warning,) = report.warnings
    assert warning.param_key == "ds_bio"
    assert warning.condition_key == _HEBING_NODE  # 单元级影响面（非 plant 常量段）
    assert warning.severity.value == "WARN"
    assert f"{value!r}" in warning.message  # 实际值
    assert "ds_bio > 0" in warning.message  # 表达式原文
    assert _DS_BIO_CODE in warning.message  # 条目键
    assert f"{_HEBING_NODE}.ds_bio" in warning.message  # 节点.字段


def test_nan_param_hits_band_declaration_face(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """NaN 越带（声明期检出）：NaN>0=False→越带→警告——FZ-4 计算期
    InvalidUnitConfig 守卫的前置报告面（validation 不阻断=仪表灯语义）。"""
    report = validation_summary_of(
        _project_with(ds_bio=float("nan")), loaded_kb)
    assert report.codes() == (kb_warning_code(_DS_BIO_CODE),)
    assert "nan" in report.warnings[0].message


def test_in_band_positive_zero_param_band_warnings(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """带内正值（golden 原值 ds_primary=3240.12）→param_band 面零警告
    （金案合法面——其余 42 条族同跑零警告，1A2/1A3 锚不在此重复）。"""
    report = validation_summary_of(_project_with(), loaded_kb)
    assert not [w for w in report.warnings if w.code.startswith("kb.param.")]


# ── 跳检两态（缺项=声明面稀疏/非数值不入表）──────────────────────


def test_missing_param_skips_check_silently(
    param_band_family: tuple[KbConstraint, ...],
) -> None:
    """缺项跳检不警：节点 params 无该键→零警告（声明面稀疏——用户只声明
    改过的参数，default 面域由 manifest 起草表保证不校）。"""
    raw = _raw()
    del raw["design"]["nodes"][_HEBING_NODE]["ds_primary"]
    report = validation_summary_of(
        ProjectFile.model_validate(raw), param_band_family)
    assert not report
    assert report.codes() == ()


@pytest.mark.parametrize("non_numeric", ["3240.12", True])
def test_non_numeric_param_skips_silently(
    param_band_family: tuple[KbConstraint, ...], non_numeric: Any
) -> None:
    """非数值跳检（str/bool 不入表——_inlet_values 同款口径：bool 是 int
    子类须显式排除）：值非数值与缺项同态跳过零警告。"""
    report = validation_summary_of(
        _project_with(ds_primary=non_numeric), param_band_family)
    assert not report


# ── 选条判据（节点 ID∈unit_kinds——分立判据）──────────────────────


def test_selection_criterion_is_node_id_membership(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """选条判据=节点 ID∈unit_kinds：同字段越带值注入非条目 unit_kinds
    节点（municipal_aao∉param.ds_bio.positive.unit_kinds〔该键唯
    hebing〕）→零警告；对照 hebing 节点→码命中（双向钉死判据）。"""
    outside = _project_with(node="municipal_aao", ds_bio=-1.0)
    assert not any(
        w.code.startswith("kb.param.")
        for w in validation_summary_of(outside, loaded_kb).warnings)
    inside = _project_with(ds_bio=-1.0)
    assert validation_summary_of(inside, loaded_kb).codes() == (
        kb_warning_code(_DS_BIO_CODE),)


def test_municipal_inlet_node_never_selected(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """municipal_input 声明节点不在任何 param_band 条目 unit_kinds →自然
    跳过（节点 ID=inlet 非单元 ID——选条判据分立于 kind 直判族）。"""
    report = validation_summary_of(_project_with(node="inlet", n=-1.0), loaded_kb)
    assert not any(
        w.code.startswith("kb.param.") for w in report.warnings)


# ── golden 零漂移（param_band 面）+plant 增量恰 4 键实证──────────


def test_golden_five_cases_zero_param_band_warnings(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """golden 五案例（三系+loop+矿井）param_band 面零警告——快照对照前置
    实证的运行期复证（24 参数次全带内〔矿井案 12 处——回炉 W1 拆门后
    真跑非空转〕，扫描单源=批档 scan_output.txt）。"""
    for case in ("municipal_34760", "municipal_34760_conveyance",
                 "municipal_34760_recycle", "municipal_34760_loop",
                 "mine_43836"):
        report = validation_summary_of(
            ProjectFile.model_validate(_raw(case)), loaded_kb)
        assert not report, case


def test_mine_line_param_band_positive_control(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """回炉 W1 真证（防空转变真证）：矿井线（无 municipal_input 声明节点
    ——进水单值表空）param_band 照常执法——nongsuo 注 n=-1 →恰单码
    kb.param.n.positive 命中（condition_key=sludge_nongsuo 单元级影响面
    /param_key=n/message 含节点.字段与表达式）；对照未注入态零警告
    （同案原值 n=2.0 带内）。原批早退门 `if not values: return` 下本
    用例空转红面（进水面缺席截断整族——双审 k1+d1 同中）。"""
    report = validation_summary_of(
        _project_with(case="mine_43836", node="sludge_nongsuo", n=-1.0),
        loaded_kb)
    assert report.codes() == (kb_warning_code("param.n.positive"),)
    (warning,) = report.warnings
    assert warning.condition_key == "sludge_nongsuo"
    assert warning.param_key == "n"
    assert warning.severity.value == "WARN"
    assert "sludge_nongsuo.n=-1.0" in warning.message
    assert "n > 0" in warning.message  # 表达式原文
    # 对照：未注入态零警告（修复后矿井腿真跑——12 参数次全带内）
    assert not validation_summary_of(
        ProjectFile.model_validate(_raw("mine_43836")), loaded_kb)


def test_golden_plant_face_increment_is_four_pass_keys() -> None:
    """§3.2 零破坏实证①勘正实录：param_band 注入 vs 零注入的 plant 面
    差异恰=design_offline_municipal_aao 嵌套 4 键全 PASS
    （kb.param.n/h2.positive=1.0+any_fail=0.0+fixgeom.min=0.0——
    _maint_face 字段准入对 aao 离线 dims 同名参数键的合法选中；零值变
    零删减=纯标注增量非行为破坏；任务书「零新键」论断不成立的实证
    勘正——详见批档 impl-report 实现裁量 D1）。"""
    from waterprint.app import load_run_env, run_full_calc
    from waterprint.contracts.condition import build_condition_set

    project = ProjectFile.model_validate(_raw())
    env = load_run_env(_REPO_DATA, project)
    conditions = build_condition_set(["municipal_aao"])
    param_band = tuple(
        kb for kb in load_kb_constraints(_KB_FILE) if kb.kind == PARAM_BAND_KIND)
    active = run_full_calc(project, conditions, env, constraints=param_band)
    zero = run_full_calc(project, conditions, env, constraints=())
    added, removed, changed = [], [], []
    for condition_key in set(active.plant.summary) | set(zero.plant.summary):
        face_a = dict(active.plant.summary.get(condition_key, {}))
        face_z = dict(zero.plant.summary.get(condition_key, {}))
        added += [f"{condition_key}:{k}" for k in set(face_a) - set(face_z)]
        removed += [f"{condition_key}:{k}" for k in set(face_z) - set(face_a)]
        changed += [
            f"{condition_key}:{k}" for k in set(face_a) & set(face_z)
            if face_a[k] != face_z[k]]
    assert set(added) == {
        "design_offline_municipal_aao:maint.municipal_aao.fixgeom.min",
        "design_offline_municipal_aao:maint.municipal_aao.kb.any_fail",
        "design_offline_municipal_aao:maint.municipal_aao.kb.param.h2.positive",
        "design_offline_municipal_aao:maint.municipal_aao.kb.param.n.positive",
    }
    assert not removed and not changed  # 零删减零值变（纯标注增量）
    offline = dict(active.plant.summary["design_offline_municipal_aao"])
    assert offline["maint.municipal_aao.kb.param.n.positive"] == 1.0  # PASS
    assert offline["maint.municipal_aao.kb.param.h2.positive"] == 1.0
    assert offline["maint.municipal_aao.kb.any_fail"] == 0.0  # 全过


def test_double_run_deterministic(loaded_kb: tuple[KbConstraint, ...]) -> None:
    """纯函数双跑全等（kb 迭代=传入序/节点迭代=插入序的确定性）。"""
    project = _project_with(ds_primary=-1.0)
    assert validation_summary_of(project, loaded_kb) == validation_summary_of(
        project, loaded_kb)
