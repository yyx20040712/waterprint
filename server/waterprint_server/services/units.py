"""units 服务用例：单元目录/假设清单静态投影（META1——params/canvas 数据面前置）。

输入:  core.discover_units（32 包 manifest）+ DEFAULT_ASSUMPTIONS（21 条）+ D1 中文名映射
输出:  UnitCatalog/AssumptionCatalog（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（META1 D1~D7 2026-08-29；镜像测试 server/tests/services/test_units.py）
#
# 【公开接口】
#   list_units() -> UnitCatalog（36 条=32 包+4 内置 kind；unit_id 排序+
#      内置四 kind 排末（kind 序）——D6 不分页整发）
#   list_assumptions() -> AssumptionCatalog（21 条——registry 声明序）
#   UnitCatalog/UnitMetaEntry/ParamEntry/RangeEntry/PortEntry/
#   AssumptionCatalog/AssumptionEntry（响应模型面——routers response_model
#   直用，SceneGraph 服务层再导出先例：禁协议层重复声明漂移面）
#
# 【行为规格】
#   R1 真源投影：参数五字段（field_id/dim[DimKey 枚举名]/default/
#      range/grid）与 ports 逐字来自 manifest——服务层零数值字面量、
#      不建工程单位映射（D3）；中文名=D1 映射（源 docs/structure-graph.md
#      §3 总表 32 行+内置四 kind——影子双源风险以镜像测试键集恰等钳制
#      「缺名/多影即红」；manifest 扩中文字段归数据批收口）。
#   R2 builtin 投影（D7）：参数面 server 硬编码（municipal_input=
#      q_avg_daily/kz+INDICATORS 六键、quality_edit=INDICATORS 六键、
#      junction/recycle_junction 空参；default/range/grid=null 诚实缺省
#      ——core nodes.py 参数面散在 __init__ 校验无声明面，挂账数据批）；
#      端口表按冻结 §二常量（municipal_input=out；junction=in_1/in_2+out；
#      quality_edit=in+out；recycle_junction=in SLUDGE+out WATER 泥进水出）。
#   R3 assumptions 投影：DEFAULT_ASSUMPTIONS 六字段取五（tuning_direction
#      =tuning_impact.direction；constraint_keys 不交付——constraint_kb
#      0.0.0 空槽无数据，D2）。
#   R4 确定性/缓存（D5）：静态只读 catalog——lru_cache(maxsize=1) 模块级
#      缓存（get_settings 同款先例；返回 pydantic frozen 实例，「无全局
#      可变态」与不可变缓存相容——main R1 工厂可重复构建不破）；双跑
#      sort_keys 字节同（端点测试常驻断言）。
#
# 【测试要求】D1 键集恰等钳制、D7 builtin 投影、参数五字段深度、
#   端口表（aao 三口/hebing 三入一口/recycle 恰两口）、缓存单例、双跑字节同。
#
# 【参照】docs/structure-graph.md §3；META1 简报 D1~D7；UF-33（core 只经
#   waterprint.app+waterprint.contracts 两允许面——import-linter 硬墙）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from functools import lru_cache
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict
from waterprint import app as core
from waterprint.contracts.manifest import ParamSpec, UnitManifest
from waterprint.contracts.ports import Port
from waterprint.contracts.quality import INDICATORS

__all__ = [
    "AssumptionCatalog",
    "AssumptionEntry",
    "ParamEntry",
    "PortEntry",
    "RangeEntry",
    "UnitCatalog",
    "UnitMetaEntry",
    "list_assumptions",
    "list_units",
]

# ── D1 中文名映射（36 条=32 包+4 内置 kind；源=docs/structure-graph.md §3
#    总表逐行誊录+内置 kind（nodes.py 规格头中文名）。禁前端本地映射——
#    中文名属服务端数据面；新单元须同步登记（镜像测试键集恰等钳制）。──
_UNIT_NAMES: Final[dict[str, str]] = {
    # 市政污水线 13
    "municipal_cugeshan": "粗格栅",
    "municipal_xigeshan": "细格栅",
    "municipal_chenshachi": "旋流沉砂池",
    "municipal_chuchenchi": "辐流初沉池",
    "municipal_tiaojiechi": "调节池",
    "municipal_aao": "AAO 生物池",
    "municipal_cass": "CASS 生物池",
    "municipal_gaomidu": "高密沉淀池",
    "municipal_vxinglvchi": "V型滤池",
    "municipal_ziwai": "紫外消毒",
    "municipal_erchunchi": "辐流二沉池",
    "municipal_bashi_jiliangcao": "巴歇尔计量槽",
    "municipal_wushui_tisheng": "污水提升泵房",
    # 矿井水线 8
    "mine_water_input": "矿井水输入",
    "mine_water_tiaojiechi": "调节池",
    "mine_water_chenshachi": "平流沉砂池",
    "mine_water_ningjiao": "混凝反应",
    "mine_water_cifenli": "磁分离",
    "mine_water_gaomidu": "高密沉淀",
    "mine_water_vxinglvchi": "V型滤池",
    "mine_water_ziwai": "紫外消毒",
    # 污泥线 7
    "sludge_hebing": "污泥合并",
    "sludge_shusong": "污泥输送",
    "sludge_bengzhan": "污泥泵站",
    "sludge_nongsuo": "污泥浓缩",
    "sludge_xiaohua": "污泥消化",
    "sludge_tuoshui": "污泥脱水",
    "sludge_ganhua": "污泥干化",
    # 集配水线 4
    "conveyance_jishuijing": "集水井",
    "conveyance_peishuijing": "配水井",
    "conveyance_jipeishuijing": "集配水井",
    "conveyance_peishuiqu": "配水渠",
    # 内置 kind 4（graph 内置节点——nodes.py 规格头中文名）
    "municipal_input": "市政输入",
    "junction": "汇流",
    "quality_edit": "水质编辑",
    "recycle_junction": "回流转换",
}

# ── D7 builtin 声明面（core nodes.py 参数面无声明面——server 投影硬编码；
#    dim 枚举名串/端口三元组属声明面合法，无数值字面量）。──
_BUILTIN_KINDS: Final[tuple[str, ...]] = (
    "municipal_input",
    "junction",
    "quality_edit",
    "recycle_junction",
)
_BUILTIN_PARAM_DIMS: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    "municipal_input": (
        ("q_avg_daily", "FLOW"),
        ("kz", "DIMENSIONLESS"),
        *((key, "CONCENTRATION") for key in sorted(INDICATORS)),
    ),
    "quality_edit": tuple((key, "CONCENTRATION") for key in sorted(INDICATORS)),
    "junction": (),
    "recycle_junction": (),
}
# 端口表 (port_id, fluid, direction)——冻结 §二逐字（recycle_junction 泥进水出）。
_BUILTIN_PORTS: Final[dict[str, tuple[tuple[str, str, str], ...]]] = {
    "municipal_input": (("out", "WATER", "OUT"),),
    "junction": (
        ("in_1", "WATER", "IN"),
        ("in_2", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ),
    "quality_edit": (("in", "WATER", "IN"), ("out", "WATER", "OUT")),
    "recycle_junction": (("in", "SLUDGE", "IN"), ("out", "WATER", "OUT")),
}


class RangeEntry(BaseModel):
    """参数闭区间范围（manifest (min, max) 二元组的结构面——GR-06）。"""

    model_config = ConfigDict(frozen=True)

    min: float
    max: float


class ParamEntry(BaseModel):
    """单参数条目：五字段全出（D3——dim=DimKey 枚举名，不建工程单位映射）。"""

    model_config = ConfigDict(frozen=True)

    field_id: str
    dim: str
    default: float | None = None  # builtin 无声明面=null 诚实缺省（D7）
    range: RangeEntry | None = None
    grid: tuple[float, ...] | None = None


class PortEntry(BaseModel):
    """端口条目：流体/方向枚举名+回流标记（contracts.ports 契约镜像）。"""

    model_config = ConfigDict(frozen=True)

    port_id: str
    fluid: Literal["WATER", "SLUDGE"]
    direction: Literal["IN", "OUT"]
    recycle: bool


class UnitMetaEntry(BaseModel):
    """单元条目：标识/中文名/业务线/kind/参数面/端口面。"""

    model_config = ConfigDict(frozen=True)

    unit_id: str
    name_zh: str
    business_line: str
    kind: Literal["unit", "builtin"]
    params: tuple[ParamEntry, ...] = ()
    ports: tuple[PortEntry, ...] = ()


class UnitCatalog(BaseModel):
    """单元目录响应体（D6 不分页整发）。"""

    model_config = ConfigDict(frozen=True)

    units: tuple[UnitMetaEntry, ...]


class AssumptionEntry(BaseModel):
    """假设条目：registry 六字段取五（constraint_keys 不交付——D2 空槽）。"""

    model_config = ConfigDict(frozen=True)

    key: str
    default: float
    dim: str
    source: str
    note: str
    tuning_direction: str


class AssumptionCatalog(BaseModel):
    """假设清单响应体（D6 不分页整发）。"""

    model_config = ConfigDict(frozen=True)

    assumptions: tuple[AssumptionEntry, ...]


def _param_entry(spec: ParamSpec) -> ParamEntry:
    """manifest ParamSpec → ParamEntry（五字段逐字——R1）。"""
    return ParamEntry(
        field_id=spec.field_id,
        dim=str(spec.dim),
        default=spec.default,
        range=None if spec.range is None else RangeEntry(min=spec.range[0], max=spec.range[1]),
        grid=spec.grid,
    )


def _port_entry(port: Port) -> PortEntry:
    """manifest Port → PortEntry（枚举名串——R1）。"""
    return PortEntry(
        port_id=port.port_id,
        fluid=port.fluid.value,
        direction=port.direction.value,
        recycle=port.recycle,
    )


def _unit_entry(unit_id: str, manifest: UnitManifest) -> UnitMetaEntry:
    """注册表单元 → UnitMetaEntry（manifest 真源逐字投影——R1）。"""
    return UnitMetaEntry(
        unit_id=unit_id,
        name_zh=_UNIT_NAMES[unit_id],
        business_line=manifest.business_line,
        kind="unit",
        params=tuple(_param_entry(spec) for spec in manifest.params),
        ports=tuple(_port_entry(port) for port in manifest.ports),
    )


def _builtin_entry(kind: str) -> UnitMetaEntry:
    """内置 kind → UnitMetaEntry（D7 声明面投影；unit_id=kind=design.nodes 值键同面）。"""
    return UnitMetaEntry(
        unit_id=kind,
        name_zh=_UNIT_NAMES[kind],
        business_line="municipal",  # core nodes _manifest 归市政图源族（§14.3 v1 裁决）
        kind="builtin",
        params=tuple(
            ParamEntry(field_id=field_id, dim=dim)
            for field_id, dim in _BUILTIN_PARAM_DIMS[kind]
        ),
        ports=tuple(
            PortEntry(port_id=port_id, fluid=fluid, direction=direction, recycle=False)
            for port_id, fluid, direction in _BUILTIN_PORTS[kind]
        ),
    )


@lru_cache(maxsize=1)
def list_units() -> UnitCatalog:
    """单元目录正门（D6 不分页）：32 包 manifest 投影+4 内置 kind 排末（kind 序）。"""
    discovered = core.discover_units()
    missing = sorted(set(discovered) - _UNIT_NAMES.keys())
    if missing:  # D1 影子双源防线：新单元未登记中文名=显式拒（测试键集钳制同面）
        raise RuntimeError(
            f"单元缺中文名映射：{missing}（_UNIT_NAMES 源=docs/structure-graph.md"
            " §3 总表——新单元须同步登记，META1 D1）"
        )
    units = tuple(_unit_entry(unit_id, discovered[unit_id][0]) for unit_id in sorted(discovered))
    return UnitCatalog(units=units + tuple(_builtin_entry(kind) for kind in _BUILTIN_KINDS))


@lru_cache(maxsize=1)
def list_assumptions() -> AssumptionCatalog:
    """假设清单正门：DEFAULT_ASSUMPTIONS registry 声明序投影（六字段取五——R3）。"""
    entries: list[AssumptionEntry] = []
    for item in core.DEFAULT_ASSUMPTIONS:
        impact = item.tuning_impact
        if impact is None:  # 不可达（registry R2 构造期拒 None）——防御直拒不静默
            raise RuntimeError(
                f"假设 {item.key!r} 缺 tuning_impact（registry R2 构造期已拒——不可达防御）"
            )
        entries.append(
            AssumptionEntry(
                key=item.key,
                default=item.default,
                dim=str(item.dim),
                source=item.source,
                note=item.note,
                tuning_direction=impact.direction,
            )
        )
    return AssumptionCatalog(assumptions=tuple(entries))
