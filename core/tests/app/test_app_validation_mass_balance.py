"""app_validation 泥量量级互校镜像测试（1A3 批——UF-55 闭合）。

输入:  waterprint.app_validation（MASS_BALANCE_KIND/validation_summary_of）+
       kb 真源（仓库 data 面 42 条——mass_balance 1 条）+golden 四案
       （municipal_34760 系：base/conveyance/recycle 有 ds_primary 声明/
       loop 入流直值模式无该键）
输出:  行为断言——族存在锚/荒谬上界码命中五字段值锚（S2-40 复现型）/
       2 量级双向（route 1A3 锚验收）/带内零警告+下界边界邻接触发/
       三态跳检（loop 入流直值/进水缺 SS 或 q_avg_daily/ds_primary 非数值）/
       kind 直判合成条目（unit_kinds 不参与）/双跑确定性/golden 三案例
       带内零警告（validation 面零新警告——serialize 恒等归 A/B 锚）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：1A3 泥量量级互校批（1a3-20261004）§3.1/§3.3/§3.6——对子=
#   sludge_hebing 参数注入模式声明的 ds_primary vs 全厂进水 SS 负荷
#   （SS×q_avg_daily 换算 kg/d），仅此一对；kb 表达式落 primary_ss_ratio
#   派生比值列双侧带 0.2~1.0（DSL 右值不支持字段算术——最小面改形；
#   换算因子经 pint 单源，代码零数值）；跳检=缺任一面不警；severity=
#   WARN/enforcement=flag 仪表灯。独立成件=行数预算墙拆分（1A2 件
#   test_app_validation.py 500 行预算满载——check_file_budgets 无豁免
#   口径「真有理由超标→拆文件」）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from waterprint.app_validation import MASS_BALANCE_KIND, validation_summary_of
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.validation import kb_warning_code
from waterprint.solution.constraints import KbConstraint, load_kb_constraints

_GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "golden_data"
_REPO_DATA = Path(__file__).resolve().parents[3] / "data"
_KB_FILE = _REPO_DATA / "constraint_kb" / "constraints.json"
_MB_CODE = "sludge.primary_load_band"
_MB_EXPRESSION = "primary_ss_ratio >= 0.2 and primary_ss_ratio <= 1.0"
# golden 进水 SS 负荷 kg/d（与实现同序浮点运算——消息面子串对照确定性）
_SS_LOAD = 250.0 * 34760.7 * 0.001


def _municipal_raw() -> dict[str, Any]:
    """golden 市政案原始 JSON（进水声明节点=inlet+泥量声明=sludge_hebing）。"""
    return json.loads(
        (_GOLDEN / "municipal_34760" / "input_project.json").read_text(
            encoding="utf-8"))


def _municipal_project_mb(ds_primary: float) -> ProjectFile:
    """golden 市政案+sludge_hebing.ds_primary 覆盖（泥量声明面原始数据）。"""
    raw = _municipal_raw()
    raw["design"]["nodes"]["sludge_hebing"]["ds_primary"] = ds_primary
    return ProjectFile.model_validate(raw)


@pytest.fixture(scope="module")
def loaded_kb() -> tuple[KbConstraint, ...]:
    """kb 真源装载（42 条全量——单源=data 面）。"""
    return load_kb_constraints(_KB_FILE)


def test_mb_family_exists_single_entry(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """族存在锚：恰 1 条 mass_balance（key/表达式/severity/unit_kinds 恒空
    =kind 直判接线红线同款——1 码稳定集另由 contracts 件锚定）。"""
    family = tuple(kb for kb in loaded_kb if kb.kind == MASS_BALANCE_KIND)
    assert len(family) == 1
    entry = family[0]
    assert entry.constraint.key == _MB_CODE
    assert entry.constraint.expression == _MB_EXPRESSION
    assert entry.constraint.severity.value == "WARN"
    assert entry.unit_kinds == ()


def test_absurd_primary_load_hits_mb_code(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """荒谬上界触发（S2-40 复现型 ×100→ratio≈37.28）→码恰单命中
    kb.sludge.primary_load_band+五字段值锚（param_key/severity/message
    三要素+ratio 与 SS 负荷展示）。"""
    report = validation_summary_of(_municipal_project_mb(324012.0), loaded_kb)
    assert report.codes() == (kb_warning_code(_MB_CODE),)
    (warning,) = report.warnings
    assert warning.condition_key == "plant"
    assert warning.param_key == "ds_primary"
    assert warning.severity.value == "WARN"
    assert "泥量量级互校越带" in warning.message  # 1A3 分支措辞面
    assert "ds_primary=324012.0" in warning.message  # 实际值
    assert f"{324012.0 / _SS_LOAD:.4f}" in warning.message  # ratio（37.2849）
    assert f"{_SS_LOAD:.1f}" in warning.message  # 全厂 SS 负荷 kg/d
    assert "0.2" in warning.message and "1.0" in warning.message  # 带域数值
    assert _MB_CODE in warning.message  # 条目键


@pytest.mark.parametrize(
    ("ds_primary", "lower"), [(972036.0, False), (3.24012, True)])
def test_two_magnitude_violations_hit_mb_code(
    loaded_kb: tuple[KbConstraint, ...], ds_primary: float, lower: bool,
) -> None:
    """2 量级失衡验收（route 1A3 锚）：×300→ratio≈111.85（≥100）与
    ÷1000→ratio≈3.73e-4（≤0.01）均落带外→码命中（双子句双向覆盖）。"""
    report = validation_summary_of(_municipal_project_mb(ds_primary), loaded_kb)
    assert report.codes() == (kb_warning_code(_MB_CODE),)
    ratio = ds_primary / _SS_LOAD
    assert (ratio >= 100.0) or lower  # 验收口径自证（2 量级）
    assert f"{ratio:.4f}" in report.warnings[0].message


@pytest.mark.parametrize(
    ("ds_primary", "fires"), [(6480.24, False), (1620.06, True)])
def test_mb_in_band_and_boundary_faces(
    loaded_kb: tuple[KbConstraint, ...], ds_primary: float, fires: bool,
) -> None:
    """带内/边界两面：×2→ratio≈0.7457 上带内=零警告；÷2→ratio≈0.1864＜
    下界 0.2=触发（边界注记——任务书速览「÷2→0.19 下带内」与 0.2 下界
    数值矛盾，按带数学实现为边界邻接触发，距下界约 7% 非带内）。"""
    report = validation_summary_of(_municipal_project_mb(ds_primary), loaded_kb)
    assert bool(report.codes()) is fires
    if fires:
        assert report.codes() == (kb_warning_code(_MB_CODE),)


def test_mb_skip_faces_silently(loaded_kb: tuple[KbConstraint, ...]) -> None:
    """三态跳检不警：①loop 案入流直值模式（SS/q_avg_daily 在场而全库无
    ds_primary 数值键——泥量系上游计算派生）；②进水缺 SS 或 q_avg_daily
    （互校基准面缺——荒谬 ds 在场不误报）；③ds_primary 非数值 None
    （键在场值缺席态——数值键判据）。"""
    loop = json.loads(
        (_GOLDEN / "municipal_34760_loop" / "input_project.json").read_text(
            encoding="utf-8"))
    assert not validation_summary_of(
        ProjectFile.model_validate(loop), loaded_kb)  # ①
    for missing in ("SS", "q_avg_daily"):  # ②
        raw = _municipal_raw()
        raw["design"]["nodes"]["inlet"].pop(missing)
        raw["design"]["nodes"]["sludge_hebing"]["ds_primary"] = 324012.0
        assert not validation_summary_of(
            ProjectFile.model_validate(raw), loaded_kb)
    raw = _municipal_raw()  # ③
    raw["design"]["nodes"]["sludge_hebing"]["ds_primary"] = None
    assert not validation_summary_of(
        ProjectFile.model_validate(raw), loaded_kb)


def test_mb_selection_criterion_is_kind_direct(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """选条判据=kind 直判（unit_kinds 恒空不参与——接线红线同款）：构造
    unit_kinds=("xxx",) 的合成 mass_balance 条目仍选中触发（形态探针）。"""
    from waterprint.contracts.unit_api import Severity
    from waterprint.solution.constraints import Constraint

    synthetic = KbConstraint(
        constraint=Constraint(
            key="t.mb", expression=_MB_EXPRESSION,
            source="t.mb", severity=Severity.WARN),
        unit_kinds=("xxx",), kind=MASS_BALANCE_KIND)
    assert synthetic not in loaded_kb  # 合成面自证（非 kb 真源混入）
    assert validation_summary_of(
        _municipal_project_mb(324012.0), (synthetic,)
    ).codes() == (kb_warning_code("t.mb"),)


def test_mb_double_run_deterministic(
    loaded_kb: tuple[KbConstraint, ...],
) -> None:
    """纯函数双跑全等（泥量面同进水面——传入序+插入序确定性）。"""
    project = _municipal_project_mb(324012.0)
    assert validation_summary_of(project, loaded_kb) == validation_summary_of(
        project, loaded_kb)


@pytest.mark.parametrize(
    "case", ["municipal_34760", "municipal_34760_conveyance",
             "municipal_34760_recycle"])
def test_golden_three_cases_in_band_zero_mb_warnings(
    loaded_kb: tuple[KbConstraint, ...], case: str,
) -> None:
    """golden 三案例零漂移负向锚：声明 ds_primary=3240.12→ratio≈0.3728
    带内→全量 kb 零警告（serialize 恒等由 1A2 件 A/B 锚承载——本用例锁
    validation 面零新警告）。"""
    project = ProjectFile.model_validate(json.loads(
        (_GOLDEN / case / "input_project.json").read_text(encoding="utf-8")))
    assert not validation_summary_of(project, loaded_kb)
