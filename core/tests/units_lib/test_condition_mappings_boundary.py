"""检修降级映射边界执法面测试（cond3 批 2026-10-01 C4 拆分件）。

输入:  condition_mapping_facts（23 单元正典表+classify_boundary 档位
       推导）+golden 双案例（municipal_34760 市政图 19 节点=市政 12+
       全部 7 污泥+inlet；mine_43836 矿井水图 11 节点=7 映射 mine
       单元+input+hebing/nongsuo/tuoshui——cifenli 于 cifenli-20261002
       批移入映射面）
输出:  三组断言——①分类自洽守卫（档位/自由两表恰覆盖 23 单元正典键集
       +计数锚 13/10=grid_bound 8+5 / free 3+7——计数翻转须红面人工
       重审）②grid_bound ×13 静态参数面：target=1 装配期拒
       InvalidAssemblyError「档位」（市政 8 沿 cond2 载体——cass 换图/
       tiaojiechi 浮节点；sludge 2=municipal golden 图直改节点参数；
       conveyance 3=浮节点承载——三线不在任何 golden 图，grid 执法
       先于拓扑面）③free ×10 offline 守卫响亮炸=归零 ×9+守卫下限 ×1：
       设计档 target=1（grid=None 装配过）+checked=[unit] → offline
       映射写 n−1=0 → compute 守卫 InvalidUnitConfig「必须 > 0」经 R5
       隔离层上抛 InvalidExecutionError（市政 3 载体沿旧+mine 7 载体=
       mine_43836 golden 图——假设②mine 守卫键集含 n 的参数化实证；
       cifenli n_units 双段类同入=cifenli-20261002 批新增）；
       守卫下限 ×1=mine vxinglvchi 降档至 1 落「必须 ≥ 2」守卫
       （KV-F5 强制滤速 n/(n−1) 除零守卫——一格冲洗余格承载；a
       fortiori 记档非实证：归零面 0 亦被同守卫覆盖但未直证）。

【范围界】本件只测边界执法面（分类+静态装配拒+归零响亮炸）；
声明面清点在 test_condition_mappings（市政）/test_condition_mappings_
lines（三线）；引擎分化行为在两件各自的 golden 行为段。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_CASES = ("municipal_34760", "mine_43836")


def _load_facts() -> ModuleType:
    """facts 单一事实源装载（importlib 路径加载——n1 电池零跨测试件 import 同款）。"""
    path = Path(__file__).resolve().parent / "condition_mapping_facts.py"
    spec = importlib.util.spec_from_file_location("condition_mapping_facts", path)
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_FACTS = _load_facts()
_ALL_CANONICAL: dict[str, tuple[str, str]] = {
    **_FACTS.CANONICAL,
    **_FACTS.CANONICAL_LINES,
}
_GRID_BOUNDARY_UNITS, _FREE_PARAM_UNITS = _FACTS.classify_boundary(_ALL_CANONICAL)

# 自由参数单元例外档（mine_water_vxinglvchi=KV-F5 除零守卫必须 ≥2——
# 设计档 n=2 → offline n−1=1 落同守卫族；其余 9 单元设计档 n=1 →
# offline 归零 0 落「必须 > 0」守卫族）。
_DEGENERATE_DESIGN_N: dict[str, float] = {"mine_water_vxinglvchi": 2.0}


_golden_ready = all(
    (
        Path(__file__).resolve().parents[1] / "golden" / "golden_data" / case
        / "input_project.json"
    ).is_file()
    for case in _CASES
)


def _golden_project(golden_data_dir: Path, case: str) -> object:
    """golden 案例项目装载正门（双案例参数化——市政图/矿井水图）。"""
    from waterprint.app import load_project

    return load_project(golden_data_dir / case / "input_project.json")


def _run_env(golden_data_dir: Path, case: str) -> object:
    """RunEnv（口径=各 golden expected.generated 实录：版本串+数据版本）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    generated = json.loads(
        (golden_data_dir / case / "expected_summary.json").read_text(
            encoding="utf-8"
        )
    )["generated"]
    return RunEnv(
        engine_version=generated["engine_version"],
        data_version=generated["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(_REPO_DATA),
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def _with_checked(project: object, *unit_ids: str) -> object:
    """design.checked_units 承载改写（D4 资格校验路径的输入面）。"""
    return project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"checked_units": list(unit_ids)}
            )
        }
    )


def _with_node_param(project: object, unit_id: str, key: str, value: float) -> object:
    """节点参数覆盖注入（节点不在 golden 图=增浮节点——装配期 grid 执法
    先于任何拓扑面，浮节点仍受检；cond2 T3 tiaojiechi/conveyance 同款）。"""
    nodes = dict(project.design.nodes)
    nodes[unit_id] = {**nodes.get(unit_id, {}), key: value}
    return project.model_copy(
        update={"design": project.design.model_copy(update={"nodes": nodes})}
    )


def _cass_swapped_project(golden_data_dir: Path) -> object:
    """golden 图 aao→cass 换图（model_copy 内存态零落盘——cond2 T2 同款）。

    节点替换（删 municipal_aao 增 municipal_cass={}）+边重接（chuchenchi→
    cass→erchunchi：两端 unit_id 直迁；aao 多 sludge_out 但 golden 图未
    连线=换图零悬边，拓扑等价）。
    """
    project = _golden_project(golden_data_dir, "municipal_34760")
    nodes = dict(project.design.nodes)
    del nodes["municipal_aao"]
    nodes["municipal_cass"] = {}
    edges: list[dict[str, object]] = []
    for edge in project.design.edges:
        rewritten = dict(edge)
        for side in ("src", "dst"):
            endpoint = dict(edge[side])
            if endpoint["unit_id"] == "municipal_aao":
                endpoint["unit_id"] = "municipal_cass"
            rewritten[side] = endpoint
        edges.append(rewritten)
    return project.model_copy(
        update={
            "design": project.design.model_copy(update={"nodes": nodes, "edges": edges})
        }
    )


# ══ ① 分类自洽守卫 ══════════════════════════════════════════════════


def test_boundary_classification_covers_all_canonical() -> None:
    """分类自洽守卫：档位/自由两表恰覆盖 23 单元正典键集+计数锚（防静默漏测）。

    grid 声明含 1.0 的单元落两表之外（n=1 合法档——边界语义不存在）；
    该单元出现时本测试红=分类须人工重审，而非静默退出断言面。计数锚
    13/10（grid_bound=市政 8+sludge 2+conveyance 3；free=市政 3+
    mine 7——cifenli n_units 台数键 cifenli-20261002 批入 free）
    =声明面回归探测器：档位声明任何翻转（grid 增删档/
    grid↔None 迁移/新单元入正典表）须红面人工重审参数化覆盖面——
    意图非脆性名单，而是「翻转须走人」的响红闸；两表非空同锚
    （空表=整类边界执法面静默失守）。
    """
    assert _GRID_BOUNDARY_UNITS, "档位边界表空=整类装配执法面失守"
    assert _FREE_PARAM_UNITS, "自由参数表空=整类响亮炸面失守"
    assert len(_GRID_BOUNDARY_UNITS) == 13  # 市政 8+他线 5（cond3 实测声明面）
    assert len(_FREE_PARAM_UNITS) == 10  # 市政 3+他线 7（cifenli 入 free=cifenli-20261002）
    covered = {unit for unit, _ in _GRID_BOUNDARY_UNITS + _FREE_PARAM_UNITS}
    missing = set(_ALL_CANONICAL) - covered
    assert not missing, f"分类外单元（grid 含 1.0 档？须重审分类）：{sorted(missing)}"
    grid_ids = {unit for unit, _ in _GRID_BOUNDARY_UNITS}
    assert not (grid_ids & {unit for unit, _ in _FREE_PARAM_UNITS}), "两表交叠=分类非互斥"


# ══ ② 档位下限≥2：静态参数面装配期拒 ×13 ═══════════════════════════


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（双案例在册才跑）")
@pytest.mark.parametrize(("unit_id", "target"), _GRID_BOUNDARY_UNITS)
def test_boundary_grid_unit_rejects_single(
    golden_data_dir: Path, unit_id: str, target: str
) -> None:
    """档位下限≥2 单元 target=1 装配期拒：InvalidAssemblyError 含「档位」。

    grid 声明不含 1（下限≥2）→ _check_grid_hits 装配执法（Ruling ④
    档位归 grid 层）。锚定静态参数面装配执法（声明面 grid 拒 n=1 设计
    输入）；运行期映射写值面由各线行为测试锚定；归零面由 grid=None
    单元经 compute 守卫承接。三线载体：sludge 2（nongsuo/xiaohua）在
    municipal golden 图=直改节点参数；conveyance 3 不在任何 golden 图
    =增浮节点（grid 执法先于拓扑面——cond2 T3 tiaojiechi 浮节点先例）；
    cass 用换图项目（golden 无 cass 节点）。
    """
    from waterprint.app import InvalidAssemblyError, assemble

    base = (
        _cass_swapped_project(golden_data_dir)
        if unit_id == "municipal_cass"
        else _golden_project(golden_data_dir, "municipal_34760")
    )
    with pytest.raises(InvalidAssemblyError, match="档位"):
        assemble(
            _with_node_param(base, unit_id, target, 1),
            _run_env(golden_data_dir, "municipal_34760"),
        )


# ══ ③ grid=None 自由参数：offline 归零 ×8+守卫下限 ×1 ═══════════════


def _free_carrier(unit_id: str) -> str:
    """自由参数单元的 golden 载体（市政 3=市政图；mine 7=mine 图——两图均含该单元节点；cifenli 同图新增=cifenli-20261002 批）。"""
    return "municipal_34760" if unit_id.startswith("municipal_") else "mine_43836"


def _free_guard_text(unit_id: str) -> str:
    """归零守卫文案（守卫族双形态：>0 通用族+vxinglvchi ≥2 除零守卫族）。"""
    if unit_id == "mine_water_vxinglvchi":
        return "必须 ≥ 2"  # KV-F5 强制滤速 n/(n−1) 除零守卫（一格冲洗余格承载）
    return "必须 > 0"  # compute _PARAMS_POSITIVE 通用正数守卫族


def _free_match(unit_id: str, target: str) -> str:
    """三段锚正则（d1-W3 回炉轮1）：单元 id+参数 'n'+守卫文案。

    8/10 单元消息实证含「参数 'n'」（guard-messages.txt 在档）；非 n
    双段类两单元——municipal_ziwai target=n_channel/mine_water_cifenli
    target=n_units，其实名消息含「参数 'n_channel'」/「参数 'n_units'」
    非「参数 'n'」（cifenli=probe 实录 §2 ⑤）——按回炉裁定保持双段
    match 记档差异，勿造假锚（参数段参数化挂账）。
    """
    guard = _free_guard_text(unit_id)
    if target == "n":
        return f"单元 '{unit_id}'.*参数 'n'.*{guard}"
    return f"单元 '{unit_id}'.*{guard}"


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（双案例在册才跑）")
@pytest.mark.parametrize(("unit_id", "target"), _FREE_PARAM_UNITS)
def test_boundary_free_unit_offline_zero_fail_loud(
    golden_data_dir: Path, unit_id: str, target: str
) -> None:
    """grid=None 自由参数单元 offline 守卫响亮炸（归零 ×9+守卫下限 ×1）。

    参数 target=设计档（grid=None 装配过；vxinglvchi 例外取 2——n=1
    设计档本身即拒，降档至 1 落 ≥2 守卫=归零面 a fortiori 记档非实证）
    +checked=[unit] → offline 工况映射写 n−1 → compute 守卫
    InvalidUnitConfig 经 R5 异常隔离层上抛 InvalidExecutionError
    ——pytest.raises 即断言无静默通过（零池静默算出假结果=最劣分支）。
    match=三段锚（d1-W3 回炉轮1）：「单元 '<id>'」前缀（工况键亦含
    unit_id，前缀锚防他单元同文案消息顶替通过）+「参数 'n'」（锁定
    致错参数=映射 target 本尊——municipal_ziwai target=n_channel 实名
    差异记档保持双段）+守卫族文案。mine 7 单元=假设②（compute 守卫
    键集含 n）的参数化实证面（cifenli n_units 双段类同入——
    cifenli-20261002 批，mine_43836 图载体）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set
    from waterprint.graph.executor import InvalidExecutionError

    case = _free_carrier(unit_id)
    design_n = _DEGENERATE_DESIGN_N.get(unit_id, 1.0)
    project = _with_checked(_golden_project(golden_data_dir, case), unit_id)
    project = _with_node_param(project, unit_id, target, design_n)
    with pytest.raises(InvalidExecutionError, match=_free_match(unit_id, target)):
        run_full_calc(
            project, build_condition_set([unit_id]), _run_env(golden_data_dir, case)
        )
