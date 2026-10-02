"""三线（mine_water/sludge/conveyance）检修降级映射声明面与引擎行为测试（cond3 批 2026-10-01；cifenli-20261002 批扩 cifenli）。

输入:  condition_mapping_facts（三线正典表）+units_lib 三线 19 包
       manifest 声明面+golden 双案例（mine_43836 矿井水图=mine 引擎
       行为载体；municipal_34760 市政图 19 节点含全部 7 污泥单元=
       sludge 行为载体）
输出:  两组断言——①声明面（12 单元恰 1 条正典三元式+target/rule 字面
       恒等+target∈params——facts 表驱动参数化；分线计数恰 7/2/3；
       7 单元空映射锁定=不合格面明示；两表并集分线恰等 registry 分线
       全集=分类防呆锚〔顺手①：表移动漏项即红〕）②引擎行为（探针
       实录事实固化）：mine tiaojiechi checked 3 工况+offline 分化
       键集 ⊇{l,a1,v1}（恰 11 键记档注释——下限锚 ≥3 防脆性，cond2
       cass ≥4 先例同款）+纯缩放键精确比（v1/a1/b_raw——KT-F2/F3/F4
       可证纯缩放，rel=1e-12）+步进键方向锚（l——cond2 l_pool 先例：
       方向不锚比值）+其余 10 单元 dims 全等；mine cifenli（n_units
       台数=并联机队键）checked 分化恰 5 键 {q_1h,a_total_req,
       n_disks_raw,n_disks,e_magnetic}——纯缩放 ×4/3 三键精确比
       （KS-F1/F3/F4）+n_disks ceil 方向锚+e_magnetic ×3/4 精确比且
       方向向下（并联机队装机功率随台数缩减——与结构池类降级升功率
       方向相反，语义记档非缺陷）+其余 10 单元全等；sludge nongsuo
       checked 分化恰 3 键 {a_single,d,d_raw}（NS-F12 v_concrete=
       a_single·h·coef·n 在 n−1 下 n-不变自愈）+a_single/d_raw 纯缩放
       精确比（NS-F4/F5）+其余 18 单元全等；bengzhan（无映射）勾选
       拒检 InvalidAssemblyError「须声明检修降级映射」；mine 基线
       零漂移（无 checked 与 checked=[tiaojiechi] 两跑 design/avg
       summary 逐键相等+全单元 dims 逐键 IEEE 位串恒等与 float 类型
       鉴别〔顺手②升级位串级——市政 cond2 d1-W1/N2 形态对齐，UF-61
       附记不对称小账清偿〕——【假设①】golden 零漂移的 mine 侧实证）。

【范围界】conveyance 3 单元不在任何 golden 图——引擎 offline 行为
不测（声明面+boundary 件静态边界执法面承载，浮节点先例=cond2 T3；
覆盖缺口记档 UF-61）。n 不在他线单元 dims 输出面（申报偏差⑤口径）
——锚用派生几何键，不改产品。纯缩放键锚前从 formulas 源码证纯缩放
性；步进/取整键（b/l/bucket 族）只锚方向+在场。锚策略准则（k2-N3/
d1-N1 回炉轮1）：分化键集闭合小集用恰等锚（回归探测器——本件
nongsuo 3 键/cifenli 5 键两形态）；开放集用下限锚+方向锚（防脆性）。
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_MINE_CASE = "mine_43836"
_MUNI_CASE = "municipal_34760"


def _load_facts() -> ModuleType:
    """facts 单一事实源装载（importlib 路径加载——n1 电池零跨测试件 import 同款）。"""
    path = Path(__file__).resolve().parent / "condition_mapping_facts.py"
    spec = importlib.util.spec_from_file_location("condition_mapping_facts", path)
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_FACTS = _load_facts()
CANONICAL_LINES: dict[str, tuple[str, str]] = _FACTS.CANONICAL_LINES
UNMAPPED: tuple[str, ...] = _FACTS.UNMAPPED
UNMAPPED_LINES: tuple[str, ...] = _FACTS.UNMAPPED_LINES

_golden_ready = all(
    (
        Path(__file__).resolve().parents[1] / "golden" / "golden_data" / case
        / "input_project.json"
    ).is_file()
    for case in (_MINE_CASE, _MUNI_CASE)
)


def _registry() -> Any:
    """单元注册表（discover_units——19 包 manifest 装载即静态校验）。"""
    from waterprint.units_lib import discover_units

    return discover_units()


def _golden_project(golden_data_dir: Path, case: str) -> Any:
    """golden 案例项目装载正门（双案例参数化——mine 图/市政图）。"""
    from waterprint.app import load_project

    return load_project(golden_data_dir / case / "input_project.json")


def _run_env(golden_data_dir: Path, case: str) -> Any:
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


def _with_checked(project: Any, *unit_ids: str) -> Any:
    """design.checked_units 承载改写（D4 资格校验路径的输入面）。"""
    return project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"checked_units": list(unit_ids)}
            )
        }
    )


# ══ ① 声明面清点（三线）════════════════════════════════════════════


@pytest.mark.parametrize(
    ("unit_id", "expected"),
    sorted(CANONICAL_LINES.items()),
)
def test_lines_mapped_units_declare_canonical_triple(
    unit_id: str, expected: tuple[str, str]
) -> None:
    """三线 12 单元各恰 1 条三元式：target/rule 字面与正典表恒等+target 在 params。"""
    manifest = _registry()[unit_id][0]
    mappings = manifest.condition_mappings
    assert len(mappings) == 1, (
        f"{unit_id} condition_mappings 恰 1 条：得到 {len(mappings)}"
    )
    target, rule = expected
    assert mappings[0].target == target
    assert mappings[0].rule == rule
    param_ids = {spec.field_id for spec in manifest.params}
    assert target in param_ids, f"{unit_id} 映射 target {target!r} 不在 params 声明面"


def test_lines_mapped_counts_per_business_line() -> None:
    """分线映射单元总数恰 7/2/3（清点面防静默漏报——恰等正典表分线键集；mine 7=cifenli 入表）。"""
    registry = _registry()
    for prefix, expected in (("mine_water_", 7), ("sludge_", 2), ("conveyance_", 3)):
        mapped = {
            unit_id
            for unit_id in registry
            if unit_id.startswith(prefix)
            and registry[unit_id][0].condition_mappings
        }
        assert mapped == {
            unit_id for unit_id in CANONICAL_LINES if unit_id.startswith(prefix)
        }, f"{prefix} 线映射单元集与正典表漂移"
        assert len(mapped) == expected, f"{prefix} 线映射单元数：{len(mapped)} ≠ {expected}"


@pytest.mark.parametrize("unit_id", UNMAPPED_LINES)
def test_lines_unmapped_units_declare_no_mappings(unit_id: str) -> None:
    """三线 7 单元 condition_mappings 为空（不合格面锁定——D4 拒检语义承载）。"""
    assert _registry()[unit_id][0].condition_mappings == ()


def test_lines_unmapped_table_counts() -> None:
    """不合格面双表计数锚：市政恰 2+三线恰 7（d1-W10 回炉轮1；cifenli 移出=cifenli-20261002）。

    空表=两族参数化测试静默 skip（0 用例假绿面）；漏项=不合格面静默
    失守。恰等计数锚与 boundary 件两表非空锚同哲学——表翻转（增删
    不合格单元）须红面人工重审，非静默退出断言面。
    """
    assert len(UNMAPPED) == 2
    assert len(UNMAPPED_LINES) == 7


def test_lines_classification_covers_registry_per_line() -> None:
    """分线分类恰等锚：CANONICAL_LINES∪UNMAPPED_LINES 分线键集恰等 registry 全集。

    mine_water 8/sludge 7/conveyance 4=19 包（discovered registry 实测
    ）——防静默漏分类/表移动漏改（cifenli-20261002 顺手①：本批恰需
    的防呆面，facts 表 cifenli 移动漏项即红；每单元恰落两表之一由
    mapped/unmapped 两族参数化各司其职，本锚只锁并集分线无漏）。
    """
    registry = _registry()
    table = set(CANONICAL_LINES) | set(UNMAPPED_LINES)
    for prefix, expected in (("mine_water_", 8), ("sludge_", 7), ("conveyance_", 4)):
        line_units = {unit_id for unit_id in registry if unit_id.startswith(prefix)}
        assert len(line_units) == expected, (
            f"{prefix} 线 registry 包数：{len(line_units)} ≠ {expected}"
        )
        assert {
            unit_id for unit_id in table if unit_id.startswith(prefix)
        } == line_units, f"{prefix} 线两表并集与 registry 全集漂移（漏分类/表移动漏改）"
    assert table == {
        unit_id
        for unit_id in registry
        if unit_id.startswith(("mine_water_", "sludge_", "conveyance_"))
    }, "两表并集与 registry 三线全集漂移（表内混入他线键/registry 漂移）"


# ══ ② 引擎行为面（探针实录固化——golden 实跑）═══════════════════════


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（双案例在册才跑）")
def test_mine_tiaojiechi_offline_differentiates(golden_data_dir: Path) -> None:
    """mine tiaojiechi（自由参数 n=16 默认）checked：3 工况+offline 单格几何分化。

    探针实录（cond3 §2 ①）：offline 分化恰 11 键=a1/a_act/b_raw/e_stir/
    l/l_raw/p_stir/t_reg_act/v1/v_act_total/v_concrete——本测试下限锚
    ⊇{l,a1,v1} 且 ≥3（cond2 cass ≥4 下限锚先例：计数记档注释，防脆性）。
    纯缩放键精确比（公式实义可证——v_total/h2/ratio_lb 工况不变）：
    v1=v_total/n（KT-F2，manifest.py:74）→ ×16/15；a1=v1/h2（KT-F3，
    manifest.py:81）→ ×16/15；b_raw=sqrt(a1/ratio_lb)（KT-F4，
    manifest.py:88）→ ×sqrt(16/15)。步进/取整键只锚方向（cond2
    l_pool 先例）：l/l_raw 单格加大（0.5 m 档步进，比值非纯缩放不锚）。
    其余 10 单元 dims 与 design 全等（「该单元 n−1、其余全池」ADR-007）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set

    project = _golden_project(golden_data_dir, _MINE_CASE)
    assert project.design.nodes["mine_water_tiaojiechi"] == {}, (
        "golden 载体节点参数面漂移（n=16 默认档前提失效——比率锚失效）"
    )
    conditions = build_condition_set(["mine_water_tiaojiechi"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == ["design", "avg", "design_offline_mine_water_tiaojiechi"]  # 2+k=3
    plant = run_full_calc(
        _with_checked(project, "mine_water_tiaojiechi"),
        conditions,
        _run_env(golden_data_dir, _MINE_CASE),
    ).plant
    assert set(plant.conditions) == set(keys)  # 全 3 工况各出整图结果
    unit_id = "mine_water_tiaojiechi"
    design = plant.conditions["design"][unit_id].dims
    offline = plant.conditions["design_offline_" + unit_id][unit_id].dims
    assert set(offline) == set(design), "tiaojiechi 自身 design↔offline dims 键集漂移"
    ratio = 16 / 15  # n 16→15（n−1 冻结语义；manifest 默认档）
    assert offline["v1"] == pytest.approx(design["v1"] * ratio, rel=1e-12)
    assert offline["a1"] == pytest.approx(design["a1"] * ratio, rel=1e-12)
    assert offline["b_raw"] == pytest.approx(
        design["b_raw"] * math.sqrt(ratio), rel=1e-12
    )
    differentiated = {key for key in offline if offline[key] != design[key]}
    assert {"l", "a1", "v1"} <= differentiated  # 三锚键在场（探针实录 11 键）
    assert len(differentiated) >= 3  # 实跑 11；下限=三锚键在场的最小面
    assert offline["l"] > design["l"]  # 步进方向=单格加大（防静默不动）
    for other_id, snapshot in plant.conditions["design"].items():
        if other_id == unit_id:
            continue  # 受检单元自身=分化面
        assert (
            plant.conditions["design_offline_" + unit_id][other_id].dims
            == snapshot.dims
        ), f"其余全池面漂移：{other_id}"


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（双案例在册才跑）")
def test_mine_cifenli_offline_differentiates(golden_data_dir: Path) -> None:
    """mine cifenli（自由参数 n_units=4 台默认）checked：3 工况+offline 分化恰 5 键。

    探针实录（cifenli-20261002 §2 ②）：offline 分化恰 5 键={q_1h,
    a_total_req,n_disks_raw,n_disks,e_magnetic}——恰等断言（闭合小集=
    回归探测器；其余 5 键 a_disk/m_seed_net/q_sludge/v_line/w_ss 不变
    =KS-F2/F5~F8 n_units-不消费，公式实义可证）。纯缩放键精确比
    （公式实义可证——q_design/q_surf/a_disk/p_drive 工况不变）：q_1h=
    q_design·3600/n_units（KS-F1 按台均分）→ ×4/3（n_units 4→3 台）；
    a_total_req=q_1h/q_surf（KS-F3）→ ×4/3；n_disks_raw=a_total_req/
    a_disk（KS-F4）→ ×4/3。n_disks=ceil 取整键只锚方向 offline>design
    （ceil 单调——探针实录 23→30 步进；比值非纯缩放不锚比）。e_magnetic
    =n_units·p_drive·24（KS-F9 rated-power 模型按台数）→ ×3/4 精确比
    +方向向下断言：并联机队装机功率随台数缩减（单机功率×台数），与
    结构池类降级升功率方向相反——装机口径语义记档非缺陷。其余 10
    单元 dims 与 design 全等（ADR-007「该单元 n−1、其余全池」镜像）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set

    project = _golden_project(golden_data_dir, _MINE_CASE)
    assert project.design.nodes["mine_water_cifenli"] == {}, (
        "golden 载体节点参数面漂移（n_units=4 默认档前提失效——比率锚失效）"
    )
    conditions = build_condition_set(["mine_water_cifenli"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == ["design", "avg", "design_offline_mine_water_cifenli"]  # 2+k=3
    plant = run_full_calc(
        _with_checked(project, "mine_water_cifenli"),
        conditions,
        _run_env(golden_data_dir, _MINE_CASE),
    ).plant
    assert set(plant.conditions) == set(keys)  # 全 3 工况各出整图结果
    unit_id = "mine_water_cifenli"
    design = plant.conditions["design"][unit_id].dims
    offline = plant.conditions["design_offline_" + unit_id][unit_id].dims
    assert set(offline) == set(design), "cifenli 自身 design↔offline dims 键集漂移"
    ratio = 4 / 3  # n_units 4→3（n−1 冻结语义；manifest 默认档）
    assert offline["q_1h"] == pytest.approx(design["q_1h"] * ratio, rel=1e-12)
    assert offline["a_total_req"] == pytest.approx(
        design["a_total_req"] * ratio, rel=1e-12
    )
    assert offline["n_disks_raw"] == pytest.approx(
        design["n_disks_raw"] * ratio, rel=1e-12
    )
    assert offline["e_magnetic"] == pytest.approx(design["e_magnetic"] * 3 / 4, rel=1e-12)
    assert offline["e_magnetic"] < design["e_magnetic"]  # 装机功率随台数缩减（向下）
    assert offline["n_disks"] > design["n_disks"]  # ceil 步进方向（探针实录 23→30）
    differentiated = {key for key in offline if offline[key] != design[key]}
    assert differentiated == {
        "q_1h",
        "a_total_req",
        "n_disks_raw",
        "n_disks",
        "e_magnetic",
    }, f"分化键集恰 5 键锚失效：{sorted(differentiated)}"
    for other_id, snapshot in plant.conditions["design"].items():
        if other_id == unit_id:
            continue  # 受检单元自身=分化面
        assert (
            plant.conditions["design_offline_" + unit_id][other_id].dims
            == snapshot.dims
        ), f"其余全池面漂移：{other_id}"


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（双案例在册才跑）")
def test_sludge_nongsuo_offline_differentiates(golden_data_dir: Path) -> None:
    """sludge nongsuo（grid [2,3,4] 默认 2）checked：3 工况+offline 分化恰 3 键。

    探针实录（cond3 §2 ②）：offline 分化恰 3 键={a_single,d,d_raw}——
    恰等断言（闭合小集=回归探测器；NS-F12 v_concrete=a_single·h_total·
    wall_coef·n 在 a_single ×2 与 n ×½ 相消下 n-不变自愈，a_req/ds 链
    工况不变）。纯缩放键精确比（a_req/pi 工况不变）：a_single=a_req/n
    （NS-F4，manifest.py:97）→ ×2（n=2→1）；d_raw=sqrt(4·a_single/pi)
    （NS-F5，manifest.py:107）→ ×sqrt(2)。d=ceil(d_raw/0.5)·0.5 取整
    键只锚方向（ceil 单调——探针实录该档 d 上跳）。其余 18 单元 dims
    与 design 全等（含 inlet 空字典恒等）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set

    project = _golden_project(golden_data_dir, _MUNI_CASE)
    assert project.design.nodes["sludge_nongsuo"] == {}, (
        "golden 载体节点参数面漂移（n=2 默认档前提失效——比率锚失效）"
    )
    conditions = build_condition_set(["sludge_nongsuo"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == ["design", "avg", "design_offline_sludge_nongsuo"]  # 2+k=3
    plant = run_full_calc(
        _with_checked(project, "sludge_nongsuo"),
        conditions,
        _run_env(golden_data_dir, _MUNI_CASE),
    ).plant
    assert set(plant.conditions) == set(keys)  # 全 3 工况各出整图结果
    unit_id = "sludge_nongsuo"
    design = plant.conditions["design"][unit_id].dims
    offline = plant.conditions["design_offline_" + unit_id][unit_id].dims
    assert set(offline) == set(design), "nongsuo 自身 design↔offline dims 键集漂移"
    assert offline["a_single"] == pytest.approx(design["a_single"] * 2, rel=1e-12)
    assert offline["d_raw"] == pytest.approx(design["d_raw"] * math.sqrt(2), rel=1e-12)
    assert offline["d"] >= design["d"]  # 取整方向（ceil 单调；探针实录上跳分化）
    differentiated = {key for key in offline if offline[key] != design[key]}
    assert differentiated == {"a_single", "d", "d_raw"}, (
        f"分化键集恰 3 键锚失效：{sorted(differentiated)}"
    )
    for other_id, snapshot in plant.conditions["design"].items():
        if other_id == unit_id:
            continue  # 受检单元自身=分化面
        assert (
            plant.conditions["design_offline_" + unit_id][other_id].dims
            == snapshot.dims
        ), f"其余全池面漂移：{other_id}"


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（双案例在册才跑）")
def test_lines_unmapped_checked_unit_rejected(golden_data_dir: Path) -> None:
    """三线 unmapped 单元（sludge_bengzhan，市政图在册）勾选受检=InvalidAssemblyError。

    D4 拒检=诚实行为（泵台数 ceil 计算值非池数参数——wushui_tisheng
    先例；探针实录 §2 ③：app_assembly.py:113 消息面）。
    """
    from waterprint.app import InvalidAssemblyError, assemble

    with pytest.raises(InvalidAssemblyError, match="须声明检修降级映射"):
        assemble(
            _with_checked(
                _golden_project(golden_data_dir, _MUNI_CASE), "sludge_bengzhan"
            ),
            _run_env(golden_data_dir, _MUNI_CASE),
        )


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（双案例在册才跑）")
def test_mine_baseline_summary_zero_drift_with_checked(
    golden_data_dir: Path,
) -> None:
    """mine 基线零漂移：无 checked 与 checked=[tiaojiechi] 两跑 design/avg 相等。

    映射激活仅经 offline 工况承载（基线档 pool.all_pools=True 真支原值
    浮点透传——构造性零漂移）；【假设①】golden 零漂移的 mine 侧实证
    （探针实录 §2 ① 尾行 True；市政侧=cond 批 ④ 同款在册）。增补
    （cifenli-20261002 顺手②——UF-61 附记不对称小账清偿）：全单元
    dims 逐键 IEEE 位串恒等+float 类型鉴别（struct.pack("<d") 相等
    强于 ==——0.0/−0.0 位面可分），市政 cond2 d1-W1/N2 形态对齐
    （test_condition_mappings.py 基线零漂移同款；键集恒等先于逐键
    比对封死 checked 侧静默新增键；NaN 契约自包含锚——dims 禁 NaN
    GR-02，位串恒等不依赖 NaN 语义）。
    """
    import struct

    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set

    project = _golden_project(golden_data_dir, _MINE_CASE)
    env = _run_env(golden_data_dir, _MINE_CASE)
    baseline = run_full_calc(project, build_condition_set([]), env).plant
    checked = run_full_calc(
        project, build_condition_set(["mine_water_tiaojiechi"]), env
    ).plant
    assert set(baseline.conditions) == {"design", "avg"}
    assert set(checked.conditions) == {
        "design",
        "avg",
        "design_offline_mine_water_tiaojiechi",
    }
    for key in ("design", "avg"):
        assert checked.summary[key] == baseline.summary[key], f"summary.{key} 漂移"
        base_units = baseline.conditions[key]
        checked_units = checked.conditions[key]
        assert set(checked_units) == set(base_units), (
            f"conditions.{key} 单元集漂移"
        )
        for unit_id, snapshot in base_units.items():
            checked_dims = checked_units[unit_id].dims
            assert set(checked_dims) == set(snapshot.dims), (
                f"{key}/{unit_id} dims 键集漂移（checked 侧静默新增/缺失键）"
            )
            for dim_key, value in snapshot.dims.items():
                other = checked_dims[dim_key]
                assert isinstance(value, float) and isinstance(other, float), (
                    f"{key}/{unit_id}.{dim_key} dims 非 float（位串鉴别前提）"
                )
                assert not math.isnan(value) and not math.isnan(other), (
                    f"{key}/{unit_id}.{dim_key} dims NaN 违约（GR-02）"
                )
                assert struct.pack("<d", value) == struct.pack("<d", other), (
                    f"{key}/{unit_id}.{dim_key} dims IEEE 位串漂移"
                )
