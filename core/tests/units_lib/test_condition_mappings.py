"""市政线检修降级映射声明面与引擎行为测试（cond 批 2026-10-01；
cond2 批 2026-10-01 补强——cass 整图换图/边界档位执法/位串鉴别）。

输入:  units_lib 声明面（discover_units 注册表 13 市政包 manifest）+
       golden municipal_34760 案例（19 节点全厂——引擎行为面载体）
输出:  四组断言——①声明面清点（11 有并行槽数参数单元恰 1 条正典三元式
       且 target/rule 字面恒等；bashi_jiliangcao/wushui_tisheng 两单元
       空映射锁定=不合格面明示）②mapped 单元（aao）design.checked_units
       承载路径 → 3 工况+offline dims 逐键分化（n 降一/单系列量翻倍
       ——含 n_aerator_raw 第 4 分化键全锚）③unmapped 单元（bashi）
       D4 拒检=InvalidAssemblyError（消息含「须声明检修降级映射」
       ——诚实行为）④基线零漂移（同一项目无 checked 与有 checked 两跑
       design/avg 两档 summary 逐键相等+全单元 dims IEEE 位串恒等与
       float 类型鉴别——基线档 pool.all_pools=True 真支原值透传，
       ADR-007 冻结语义）。
       cond2 增补两组——⑤cass 整图换图亲验（aao→cass 节点替换+边重接：
       3 工况在场+缩放比 4/3 精确三键+n_aerator=ceil(raw)+其余全池
       dims 全等+分化键数 ≥4）⑥边界执法面（registry 档位声明推导分类
       ——grid 下限≥2 单元 target=1 装配期拒「档位」；grid=None 自由
       参数单元 offline 归零响亮炸「必须 > 0」，禁静默通过）。

【范围界】mine_water/sludge/conveyance 线不在断言面（cond 批范围=
市政线，他线后续批）；tiaojiechi 仅 n（格数）映射——n_pump_duty 泵
台数非池数语义不映射（映射表出处=cond 批简报 §4.1，ADR-007）。
l_pool 模数步进、b_pool 取档与 n_aerator ceil 取整非纯缩放——不锚
4/3 精确比（cond2 批简报 §3 记档；l_pool 锚方向不锚比值）。
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_GOLDEN_CASE = Path("municipal_34760")

# 11 单元正典三元式表（unit_id → (target, rule)；简报 §4.1 逐字——
# target 键名与各包 manifest params 声明面逐一核对）。
_CANONICAL: dict[str, tuple[str, str]] = {
    "municipal_cugeshan": ("n", "n if pool.all_pools else n - 1"),
    "municipal_xigeshan": ("n", "n if pool.all_pools else n - 1"),
    "municipal_chenshachi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_chuchenchi": ("n", "n if pool.all_pools else n - 1"),
    # 格数映射；n_pump_duty（泵台数）不映射——非池数降级语义。
    "municipal_tiaojiechi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_aao": ("n", "n if pool.all_pools else n - 1"),
    "municipal_cass": ("n_pool", "n_pool if pool.all_pools else n_pool - 1"),
    "municipal_gaomidu": ("n", "n if pool.all_pools else n - 1"),
    "municipal_vxinglvchi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_ziwai": (
        "n_channel",
        "n_channel if pool.all_pools else n_channel - 1",
    ),
    "municipal_erchunchi": ("n", "n if pool.all_pools else n - 1"),
}

# 两单元不合格明示不映射（D4 拒检=诚实行为——测试锁定空声明面）。
_UNMAPPED: tuple[str, ...] = (
    "municipal_bashi_jiliangcao",  # 单槽构筑物，无并行槽数参数
    "municipal_wushui_tisheng",  # n_pump_duty=ceil 计算值非参数；n_standby 纯计数回显
)


def _registry() -> Any:
    """单元注册表（discover_units——32 包 manifest 装载即静态校验）。"""
    from waterprint.units_lib import discover_units

    return discover_units()


def _boundary_classification() -> tuple[
    tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]
]:
    """正典键集 × manifest target spec 档位声明分类（cond2 T3 oracle）。

    grid=None → 自由参数（target=1 装配过；offline 归零走 compute 守卫
    响亮炸）；grid 非 None 且不含 1.0 → 档位下限≥2（target=1 装配期
    _check_grid_hits 拒）。档位声明即行为分类真源——禁硬编码名单；
    声明面翻转（如 grid 增 1.0 档）时分类自动随动（自适应非脆性）。
    """
    registry = _registry()
    grid_bound: list[tuple[str, str]] = []
    free: list[tuple[str, str]] = []
    for unit_id, (target, _rule) in sorted(_CANONICAL.items()):
        spec = {s.field_id: s for s in registry[unit_id][0].params}[target]
        if spec.grid is None:
            free.append((unit_id, target))
        elif not any(math.isclose(1.0, step) for step in spec.grid):
            grid_bound.append((unit_id, target))
    return tuple(grid_bound), tuple(free)


_GRID_BOUNDARY_UNITS, _FREE_PARAM_UNITS = _boundary_classification()


# ══ ① 声明面清点 ══════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("unit_id", "expected"),
    sorted(_CANONICAL.items()),
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
    assert mapped == set(_CANONICAL)


@pytest.mark.parametrize("unit_id", _UNMAPPED)
def test_unmapped_units_declare_no_mappings(unit_id: str) -> None:
    """两单元 condition_mappings 为空（不合格面锁定——D4 拒检语义承载）。"""
    assert _registry()[unit_id][0].condition_mappings == ()


# ══ ②③④ 引擎行为面（golden municipal_34760 实跑）═════════════════

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
    import json

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
            "design": project.design.model_copy(
                update={"nodes": nodes, "edges": edges}
            )
        }
    )


def _with_node_param(project: Any, unit_id: str, key: str, value: float) -> Any:
    """节点参数覆盖注入（节点不在 golden 图=增浮节点——tiaojiechi 面对齐
    cass 换图同款处理：装配期 grid 执法先于任何拓扑面，浮节点仍受检）。"""
    nodes = dict(project.design.nodes)
    nodes[unit_id] = {**nodes.get(unit_id, {}), key: value}
    return project.model_copy(
        update={
            "design": project.design.model_copy(update={"nodes": nodes})
        }
    )


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_mapped_checked_unit_offline_dims_differentiate(
    golden_data_dir: Path,
) -> None:
    """mapped 单元（aao）checked 路径：3 工况+offline dims 逐键分化。

    aao n=2（golden 默认档）：offline 档 n 2→1（n−1 冻结语义）；
    v_o_series/n_aerator/n_aerator_raw 随单系列承载全流量翻倍
    （n_aerator_raw=v_o_series/(h2·f_aerator_service)，AO-F20——
    分化键 3→4 全锚，d1-N3）。
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
    assert offline["n_aerator"] == pytest.approx(2 * design["n_aerator"])
    assert offline["n_aerator_raw"] == pytest.approx(2 * design["n_aerator_raw"])


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


# ══ ⑤⑥ 边界执法面（cond2 批——registry 档位声明推导）═══════════════


def test_boundary_classification_covers_canonical() -> None:
    """分类自洽守卫：档位/自由两表恰覆盖正典键集+计数锚（防静默漏测）。

    grid 声明含 1.0 的单元落两表之外（n=1 合法档——边界语义不存在）；
    该单元出现时本测试红=分类须人工重审，而非静默退出断言面。
    计数锚 8/3=声明面回归探测器：档位声明任何翻转（grid 增删档/
    grid↔None 迁移/新单元入正典表）须红面人工重审参数化覆盖面
    ——意图非脆性名单，而是「翻转须走人」的响红闸；两表
    非空同锚（空表=整类边界执法面静默失守）。
    """
    assert _GRID_BOUNDARY_UNITS, "档位边界表空=整类装配执法面失守"
    assert _FREE_PARAM_UNITS, "自由参数表空=整类响亮炸面失守"
    assert len(_GRID_BOUNDARY_UNITS) == 8  # 计数锚：当前声明面实测（回炉 N4）
    assert len(_FREE_PARAM_UNITS) == 3  # 同上
    covered = {unit for unit, _ in _GRID_BOUNDARY_UNITS + _FREE_PARAM_UNITS}
    missing = set(_CANONICAL) - covered
    assert not missing, f"分类外单元（grid 含 1.0 档？须重审分类）：{sorted(missing)}"


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
@pytest.mark.parametrize(("unit_id", "target"), _GRID_BOUNDARY_UNITS)
def test_boundary_grid_unit_rejects_single(
    golden_data_dir: Path, unit_id: str, target: str
) -> None:
    """档位下限≥2 单元 target=1 装配期拒：InvalidAssemblyError 含「档位」。

    grid 声明不含 1（下限≥2）→ _check_grid_hits 装配执法（Ruling ④
    档位归 grid 层）。本测试锚定**静态参数面**装配执法（声明面 grid
    拒 n=1 设计输入）；运行期映射写值面（offline n−1 写出后不再经
    装配复检、直接进 compute——T1 aao offline n=1 正常算出为实证）
    由 T1/T2 锚定；归零面由 grid=None 单元经 compute 守卫承接。
    cass 用换图项目（golden 无 cass 节点）；tiaojiechi 同不在
    golden 图=增浮节点（grid 执法先于拓扑面）。
    """
    from waterprint.app import InvalidAssemblyError, assemble

    base = (
        _cass_swapped_project(golden_data_dir)
        if unit_id == "municipal_cass"
        else _golden_project(golden_data_dir)
    )
    with pytest.raises(InvalidAssemblyError, match="档位"):
        assemble(
            _with_node_param(base, unit_id, target, 1), _run_env(golden_data_dir)
        )


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
@pytest.mark.parametrize(("unit_id", "target"), _FREE_PARAM_UNITS)
def test_boundary_free_unit_offline_zero_fail_loud(
    golden_data_dir: Path, unit_id: str, target: str
) -> None:
    """grid=None 自由参数单元 offline 归零响亮炸：InvalidExecutionError。

    参数 target=1（grid=None 装配过）+checked=[unit] → offline 工况
    映射写 n−1=0 → compute 守卫 InvalidUnitConfig「必须 > 0」经 R5
    异常隔离层上抛 InvalidExecutionError（cugeshan/xigeshan/ziwai
    三守卫在册）——pytest.raises 即断言无静默通过（零池静默算出
    假结果=最劣分支）。match=「单元 '<id>'」前缀+「必须 > 0」合并
    正则——锁定致错单元（工况键亦含 unit_id，前缀锚防他单元同
    文案消息顶替通过）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set
    from waterprint.graph.executor import InvalidExecutionError

    project = _with_checked(
        _with_node_param(_golden_project(golden_data_dir), unit_id, target, 1),
        unit_id,
    )
    with pytest.raises(InvalidExecutionError, match=f"单元 '{unit_id}'.*必须 > 0"):
        run_full_calc(
            project, build_condition_set([unit_id]), _run_env(golden_data_dir)
        )


