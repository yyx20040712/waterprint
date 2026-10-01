"""市政线检修降级映射声明面与引擎行为测试（cond 批 2026-10-01；
cond2 批 2026-10-01 补强——cass 整图换图/边界档位执法/位串鉴别；
cond3 批 2026-10-01 拆分——正典表迁 condition_mapping_facts 单一
事实源+⑤⑥边界段独立件+k2-N7 ceil 巧合行改双档锚）。

输入:  units_lib 声明面（discover_units 注册表 13 市政包 manifest；
       正典表自 condition_mapping_facts 装载）+golden municipal_34760
       案例（19 节点全厂——引擎行为面载体）
输出:  四组断言——①声明面清点（11 有并行槽数参数单元恰 1 条正典三元式
       且 target/rule 字面恒等；bashi_jiliangcao/wushui_tisheng 两单元
       空映射锁定=不合格面明示）②mapped 单元（aao）design.checked_units
       承载路径 → 3 工况+offline dims 逐键分化（n 降一/单系列量翻倍
       ——v_o_series/n_aerator_raw 精确锚+n_aerator=ceil(raw) 双档
       取整锚〔k2-N7 cond3：approx(2×) 在 ceil(2x)=2·ceil(x) 巧合
       成立时过、一般不成立〕）③unmapped 单元（bashi）D4 拒检=
       InvalidAssemblyError（消息含「须声明检修降级映射」——诚实行为）
       ④基线零漂移（同一项目无 checked 与有 checked 两跑 design/avg
       两档 summary 逐键相等+全单元 dims IEEE 位串恒等与 float 类型
       鉴别——基线档 pool.all_pools=True 真支原值透传，ADR-007 冻结
       语义）。

【范围界】⑤cass 整图换图亲验与⑥边界执法面（cond2 增补段）随 cond3
批迁出：换图亲验留本件②段（cass 整图行为面）；边界执法面（分类
守卫+档位装配拒+自由参数归零炸——22 单元全口径）=test_condition_
mappings_boundary.py；三线（mine_water/sludge/conveyance）声明面
与引擎行为=test_condition_mappings_lines.py；正典表单一事实源=
condition_mapping_facts.py（本件与两新件共用，importlib 路径装载）。
tiaojiechi 仅 n（格数）映射——n_pump_duty 泵台数非池数语义不映射
（映射表出处=cond 批简报 §4.1，ADR-007）。l_pool 模数步进、b_pool
取档与 n_aerator ceil 取整非纯缩放——不锚 4/3 精确比（cond2 批简报
§3 记档；l_pool 锚方向不锚比值）。
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
_GOLDEN_CASE = Path("municipal_34760")


def _load_facts() -> ModuleType:
    """facts 单一事实源装载（importlib 路径加载——n1 电池零跨测试件 import 同款）。"""
    path = Path(__file__).resolve().parent / "condition_mapping_facts.py"
    spec = importlib.util.spec_from_file_location("condition_mapping_facts", path)
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 11 单元正典三元式表+两单元不合格面（cond3 批迁 condition_mapping_facts
# 单一事实源——本件与 lines/boundary 件三处共用；内容逐字零变更）。
_FACTS = _load_facts()
CANONICAL: dict[str, tuple[str, str]] = _FACTS.CANONICAL
UNMAPPED: tuple[str, ...] = _FACTS.UNMAPPED


def _registry() -> Any:
    """单元注册表（discover_units——32 包 manifest 装载即静态校验）。"""
    from waterprint.units_lib import discover_units

    return discover_units()


# ══ ① 声明面清点 ══════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("unit_id", "expected"),
    sorted(CANONICAL.items()),
)
def test_mapped_units_declare_canonical_triple(
    unit_id: str, expected: tuple[str, str]
) -> None:
    """11 单元各恰 1 条三元式：target/rule 字面与正典表恒等+target 在 params。"""
    manifest = _registry()[unit_id][0]
    mappings = manifest.condition_mappings
    assert len(mappings) == 1, f"{unit_id} condition_mappings 恰 1 条：得到 {len(mappings)}"
    target, rule = expected
    assert mappings[0].target == target
    assert mappings[0].rule == rule
    param_ids = {spec.field_id for spec in manifest.params}
    assert target in param_ids, f"{unit_id} 映射 target {target!r} 不在 params 声明面"


def test_mapped_unit_count_is_eleven() -> None:
    """市政线映射单元总数=11（清点面防静默漏报——恰等正典表键集）。"""
    registry = _registry()
    municipal = {
        unit_id
        for unit_id in registry
        if unit_id.startswith("municipal_")
    }
    mapped = {
        unit_id
        for unit_id in municipal
        if registry[unit_id][0].condition_mappings
    }
    assert mapped == set(CANONICAL)


@pytest.mark.parametrize("unit_id", UNMAPPED)
def test_unmapped_units_declare_no_mappings(unit_id: str) -> None:
    """两单元 condition_mappings 为空（不合格面锁定——D4 拒检语义承载）。"""
    assert _registry()[unit_id][0].condition_mappings == ()


# ══ ②③④⑤ 引擎行为面（golden municipal_34760 实跑）═════════════════

_golden_ready = (
    Path(__file__).resolve().parents[1] / "golden" / "golden_data" / _GOLDEN_CASE
    / "input_project.json"
).is_file()


def _golden_project(golden_data_dir: Path) -> Any:
    """golden municipal_34760 项目（19 节点全厂装载正门）。"""
    from waterprint.app import load_project

    return load_project(golden_data_dir / _GOLDEN_CASE / "input_project.json")


def _run_env(golden_data_dir: Path) -> Any:
    """RunEnv（口径=golden expected.generated 实录：server 版本串+数据版本）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    generated = json.loads(
        (golden_data_dir / _GOLDEN_CASE / "expected_summary.json").read_text(
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


def _cass_swapped_project(golden_data_dir: Path) -> Any:
    """golden 图 aao→cass 换图（model_copy 内存态——零落盘）。

    节点替换（删 municipal_aao 增 municipal_cass={}）+边重接
    （chuchenchi→cass→erchunchi：两端 unit_id 直迁，in/out 端口同名
    合法；aao 多 sludge_out 但 golden 图未连线=换图零悬边，拓扑等价）。
    """
    project = _golden_project(golden_data_dir)
    nodes = dict(project.design.nodes)
    del nodes["municipal_aao"]
    nodes["municipal_cass"] = {}
    edges: list[dict[str, Any]] = []
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


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_mapped_checked_unit_offline_dims_differentiate(
    golden_data_dir: Path,
) -> None:
    """mapped 单元（aao）checked 路径：3 工况+offline dims 逐键分化。

    aao n=2（golden 默认档）：offline 档 n 2→1（n−1 冻结语义）；
    v_o_series/n_aerator_raw 随单系列承载全流量翻倍
    （n_aerator_raw=v_o_series/(h2·f_aerator_service)，AO-F20——
    分化键 3→4 全锚，d1-N3）；n_aerator=ceil(n_aerator_raw) 双档
    取整锚（k2-N7 cond3——approx(2×) 在 ceil(2x)=2·ceil(x) 巧合
    成立时过、一般不成立；cass 段 319-320 行同式镜像）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set

    conditions = build_condition_set(["municipal_aao"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == ["design", "avg", "design_offline_municipal_aao"]  # 2+k=3 工况
    plant = run_full_calc(
        _with_checked(_golden_project(golden_data_dir), "municipal_aao"),
        conditions,
        _run_env(golden_data_dir),
    ).plant
    assert set(plant.conditions) == set(keys)  # 全 3 工况各出整图结果
    design = plant.conditions["design"]["municipal_aao"].dims
    offline = plant.conditions["design_offline_municipal_aao"]["municipal_aao"].dims
    assert design["n"] == 2.0  # golden 案例默认池数档（anchors 非手造）
    assert offline["n"] == design["n"] - 1 == 1.0  # n−1 降级
    assert offline["v_o_series"] == pytest.approx(2 * design["v_o_series"])
    assert offline["n_aerator_raw"] == pytest.approx(2 * design["n_aerator_raw"])
    # k2-N7（cond3 批）：ceil 双档锚——n_aerator=ceil(raw)（compute
    # AO-F20 收口面）逐档各自成立，替代 approx(2×) 巧合过面。
    assert design["n_aerator"] == math.ceil(design["n_aerator_raw"])
    assert offline["n_aerator"] == math.ceil(offline["n_aerator_raw"])


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_cass_offline_whole_graph_differentiates(golden_data_dir: Path) -> None:
    """cass 整图换图亲验：3 工况在场+offline 单系列缩放面分化（k2-N 合并）。

    golden 图 aao→cass 换图（helper 内存态零落盘）；n_pool=4（manifest
    默认档）offline 4→3 → 缩放比精确 4/3=n_pool/(n_pool−1)：v_pool/
    a_pool/n_aerator_raw == design×4/3；n_aerator=ceil(n_aerator_raw)
    （取整面不锚 4/3 精确比）。其余非 inlet 单元 dims 与 design 全等
    （「该单元 n−1、其余全池」ADR-007 冻结语义换图再证）；inlet dims
    两帧恒等且恒空（进水绑定非计算单元——显式断言非循环例外）。
    分化键数 ≥4（实跑 18——下限锚防脆性；四锚键 v_pool/a_pool/
    n_aerator_raw/n_aerator 须在分化集内）+l_pool 方向锚（模数步进
    防静默不动）。静态前提两锚：①golden 原图无任何边触及 aao 的
    sludge_out（换图零悬边的静态证明）；②换图后 cass 入边恰自
    chuchenchi、出边恰往 erchunchi（边端点固化，防 golden 拓扑变更
    静默迁移）。l_pool 模数步进（47→54）、b_pool 取档非纯缩放——
    不锚 4/3（cond2 简报 §3 记档）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set

    conditions = build_condition_set(["municipal_cass"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == ["design", "avg", "design_offline_municipal_cass"]
    raw = _golden_project(golden_data_dir)
    for edge in raw.design.edges:  # 静态前提①：换图零悬边
        for side in ("src", "dst"):
            assert not (
                edge[side]["unit_id"] == "municipal_aao"
                and edge[side]["port_id"] == "sludge_out"
            ), "golden 原图 aao sludge_out 存在连线（换图零悬边前提失效）"
    swapped = _cass_swapped_project(golden_data_dir)
    assert [  # 静态前提②：边端点固化
        edge["src"]["unit_id"]
        for edge in swapped.design.edges
        if edge["dst"]["unit_id"] == "municipal_cass"
    ] == ["municipal_chuchenchi"], "cass 入边端点漂移"
    assert [
        edge["dst"]["unit_id"]
        for edge in swapped.design.edges
        if edge["src"]["unit_id"] == "municipal_cass"
    ] == ["municipal_erchunchi"], "cass 出边端点漂移"
    plant = run_full_calc(
        _with_checked(swapped, "municipal_cass"),
        conditions,
        _run_env(golden_data_dir),
    ).plant
    assert set(plant.conditions) == set(keys)  # 全 3 工况各出整图结果
    design = plant.conditions["design"]["municipal_cass"].dims
    offline = plant.conditions["design_offline_municipal_cass"]["municipal_cass"].dims
    for key in ("v_pool", "a_pool", "n_aerator_raw"):
        assert offline[key] == pytest.approx(design[key] * 4 / 3, rel=1e-12), key
    assert design["n_aerator"] == math.ceil(design["n_aerator_raw"])
    assert offline["n_aerator"] == math.ceil(offline["n_aerator_raw"])
    assert set(offline) == set(design), "cass 自身 design↔offline dims 键集漂移"
    differentiated = {key for key in offline if offline[key] != design[key]}
    assert {"v_pool", "a_pool", "n_aerator_raw", "n_aerator"} <= differentiated
    assert len(differentiated) >= 4  # 实跑 18；下限=四锚键在场的最小面
    assert "l_pool" in differentiated  # 方向锚：模数步进面在分化集
    assert offline["l_pool"] > design["l_pool"]  # 步进方向=单池加大（防静默不动）
    for unit_id, snapshot in plant.conditions["design"].items():
        if unit_id == "municipal_cass":
            continue  # 受检单元自身=分化面
        if unit_id == "inlet":
            assert (  # 进水绑定非计算单元：两帧恒等且恒空（显式断言）
                plant.conditions["design_offline_municipal_cass"][unit_id].dims
                == snapshot.dims
                == {}
            ), "inlet dims 应两帧恒等且恒空"
            continue
        assert (
            plant.conditions["design_offline_municipal_cass"][unit_id].dims
            == snapshot.dims
        ), f"其余全池面漂移：{unit_id}"


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_unmapped_checked_unit_rejected(golden_data_dir: Path) -> None:
    """unmapped 单元（bashi）勾选受检=InvalidAssemblyError（D4 拒检）。"""
    from waterprint.app import InvalidAssemblyError, assemble

    with pytest.raises(InvalidAssemblyError, match="须声明检修降级映射"):
        assemble(
            _with_checked(
                _golden_project(golden_data_dir), "municipal_bashi_jiliangcao"
            ),
            _run_env(golden_data_dir),
        )


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_baseline_summary_zero_drift_with_checked(golden_data_dir: Path) -> None:
    """基线零漂移：同一项目无 checked 与有 checked 两跑 design/avg 逐键相等。

    基线档 pool.all_pools=True → 三元真支=原值浮点透传（构造性零漂移）；
    summary 含 B4-2a 能耗药耗聚合键族——n-不变在 35 键全量上实证。
    增补（cond2 d1-W1/N2）：全单元 dims 逐键 IEEE 位串恒等+float 类型
    鉴别（struct.pack("<d") 相等强于 ==——0.0/−0.0 位面可分）；键集
    恒等先于逐键比对（checked 侧静默新增键=「错 target 键=静默新增
    无消费键」同族失效模式，须红面）；NaN 契约自包含锚（dims 禁
    NaN——GR-02；位串恒等不依赖 NaN 语义，禁 NaN 在测试内直锚）。
    """
    import struct

    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set

    project = _golden_project(golden_data_dir)
    env = _run_env(golden_data_dir)
    baseline = run_full_calc(project, build_condition_set([]), env).plant
    checked = run_full_calc(
        project, build_condition_set(["municipal_aao"]), env
    ).plant
    for key in ("design", "avg"):
        assert checked.summary[key] == baseline.summary[key], f"summary.{key} 漂移"
        base_units = baseline.conditions[key]
        checked_units = checked.conditions[key]
        assert set(checked_units) == set(base_units), f"conditions.{key} 单元集漂移"
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
