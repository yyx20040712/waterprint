"""内置图节点：市政输入 / 汇流 / 水质编辑三 kind 工厂（非单元包，§14.3）。

输入:  kind 字符串 + design 节点 params（Mapping，规范单位裸值）
输出:  Unit 协议实例（executor R6"本包内提供"）；构造非法 = InvalidNodeError
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7b 新建 D2 裁决 2026-08-25；探针② + test_app 链路）
#
# 【公开接口】
#   builtin_unit(kind: str, params: Mapping[str, Any]) -> Unit
#       唯一工厂正门——按 kind 构造 Unit 协议实例（manifest 经
#       contracts.manifest.load_manifest 最小 dict 构造：ports 声明 +
#       condition_mappings=()；params 声明面最小=()，design 值自由面
#       GR-21 注记）。四 kind：
#       - municipal_input（市政输入，图源）：无入边；params 含
#         q_avg_daily（m3/s 规范单位裸值）/kz/水质指标（⊆ INDICATORS）
#         → outflows=WaterFlow（经 make_flow 正门域校验）+
#         outqualities=WaterQuality（指标构造正门）；多余参数拒/
#         缺必需参数拒（消息含缺失与多余键清单，GR-09）。
#       - junction（汇流）：多入单出——v1 冻结两口 in_1/in_2（三股
#         以上=串接 junction 或 GR-21 扩展）；入边数 < 2 时构造期不
#         拒、compute 期按实际入边混合，空入边=InvalidNodeError；
#         出流 q_avg=Σ、kz=max（R2 保守，propagate 同款）；出水质=
#         负荷加权（复用 graph.propagate.mix，权重=q_avg_daily，
#         WATER 通道）；SLUDGE 入边拒（内置节点 v1 只做 WATER）。
#       - quality_edit（水质编辑）：一入一出；流量透传；params 指定
#         指标覆盖（键 ⊆ INDICATORS）、其余透传（覆盖值经 WaterQuality
#         域校验）。
#       - recycle_junction（回流转换，GOLDEN3 D1 2026-08-28）：单入
#         SLUDGE → 单出 WATER 的泥→水投影节点（上清液/滤液回流前端
#         变换器）；恰一入边（空入/多入拒）、WATER 股拒（投影单向）；
#         出流 WaterFlow(q_avg_daily=q_wet, kz=1.0——回流为连续均匀
#         流无峰化，工程裁量 I2 追认)；出水质只投 SS=ds/q_wet×1000
#         mg/L（kg/s÷m³/s=kg/m³→mg/L 纯量纲换算；其余指标由
#         propagate 部分缺项语义=上游原值）；dims 两键 q_recycle
#         （q_wet×86400 回 m³/d 工程口径回显）/ss_recycle（同 SS 值）；
#         入流 q_wet 须为正有限值（SS 投影 ds/q 无定义——GR-14 显式
#         拒）；v1 回流=前向叠加口径（回流边跨子图 forward，环不闭合
#         不标 recycle——真环迭代挂账 GOLDEN4，D0 定调）。
#   class InvalidNodeError(Exception)（GR-11 族，本文件定义）
#
# 【行为规格】
#   R1 三节点 UnitResult：outflows/outqualities 两个 Mapping 口、
#      dims={}、warnings=()、formula_ids 含 kind 标识（如
#      "builtin.municipal_input"——进计算迹索引用，非数值无出处问题）。
#   R2 compute 纯函数（unit_api R1）；工况感知禁止（ADR-007 compute
#      禁工况分支——junction 固定 q_avg_daily 权重由此，与 propagate
#      层工况加权[ADR-005，语义归属 propagate.py 同端口多股合并]分立，
#      记档 T7b 报告）。
#   R3 值域校验走正门：make_flow/WaterQuality 原生领域异常不包装
#      （GR-08）；非数值类型值 = 原生 TypeError（GR-08 程序/数据缺陷
#      口径，propagate KeyError 先例）。
#   R4 汇流 WaterFlow 直接构造不经 make_flow（图内传播 Q=0 合法
#      GR-04，propagate 同款），构造前有限性检查 GR-02。
#   R5 入流缺 quality 视为空 WaterQuality（quality.py P6 缺项语义
#      的单位元——mix 不参与混合，非静默默认值）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 0/1；单位换算
#   因子不抄系数（R2 禁手写换算系数——dxf_writer._mm_per_meter 先例）：
#   秒/日=m³/d→m³/s 因子（parse(1,"m3/d")）之倒数；kg/m³→mg/L 因子
#   1000 无 UF-20 白名单单位对，经 mm→m 因子倒数派生（量纲借用注记
#   同 dxf_writer——I2 追认，见 _KG_M3_TO_MG_L）。
#
# 【测试要求】探针②：三 kind 构造+域校验拒/junction 混合数值手算
#   对照/quality_edit 覆盖透传；链路断言经 test_app（D8）。
#
# 【参照】重写计划 §14.3 归属表；ADR-007；简报 T7b D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from typing import Any, Final, final

from waterprint.contracts.flow import WaterFlow, make_flow
from waterprint.contracts.manifest import UnitManifest, load_manifest
from waterprint.contracts.ports import PortRef
from waterprint.contracts.quality import INDICATORS, WaterQuality
from waterprint.contracts.quantity import DimKey, Quantity, parse
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import Unit, UnitContext, UnitResult
from waterprint.graph.propagate import mix

_EMPTY: Final[WaterQuality] = WaterQuality({})
_NORM_REF: Final[str] = "内置图节点（重写计划 §14.3 归属表）"
# 单位换算因子经 pint 正门派生（R2 禁手写系数——dxf_writer._mm_per_meter
# 先例；模块级 Final 常量=唯一住所）：秒/日=m³/d→m³/s 换算因子之倒数；
# kg/m³→mg/L 因子（1000）无 UF-20 白名单单位对，经 mm→m 因子倒数派生
# （量纲借用注记同 dxf_writer——I2 追认）。
_SECS_PER_DAY: Final[float] = 1.0 / parse(1.0, "m3/d", DimKey.FLOW)
_KG_M3_TO_MG_L: Final[float] = 1.0 / parse(1.0, "mm", DimKey.LENGTH)


class InvalidNodeError(Exception):
    """内置图节点构造/计算非法（参数键集/入边形态/通道类型）——领域异常（GR-11 族）。"""


def _manifest(kind: str, ports: tuple[tuple[str, str, str], ...]) -> UnitManifest:
    """最小清单构造（ports 三元组 (port_id, fluid, direction)）。"""
    return load_manifest(
        {
            "unit_id": f"builtin_{kind}",
            "i18n_key": f"builtin.{kind}",
            "version": "1.0",
            # 四线枚举无"线无关"值：内置三节点按 §14.3 归市政图源族取
            # municipal（记档 T7b 报告；GR-21 扩展随 M2 复核）。
            "business_line": "municipal",
            "params": [],
            "ports": [
                {"port_id": port_id, "fluid": fluid, "direction": direction}
                for port_id, fluid, direction in ports
            ],
            "removal_refs": {},
            "norm_refs": [_NORM_REF],
            "condition_mappings": [],
            "constraint_refs": [],
        }
    )


def _out_port(unit_id: str) -> PortRef:
    """出端口引用（三 kind 统一 out）。"""
    return PortRef(unit_id=unit_id, port_id="out")


@final
class _MunicipalInput:
    """市政输入（图源）：params → 出流 + 出水质（构造期正门校验）。"""

    manifest: UnitManifest = _manifest(
        "municipal_input", (("out", "WATER", "OUT"),)
    )

    def __init__(self, params: Mapping[str, Any]) -> None:
        required = {"q_avg_daily", "kz"}
        missing = sorted(required - set(params))
        if missing:
            raise InvalidNodeError(
                f"municipal_input 缺必需参数：{missing}"
                f"（必需 {sorted(required)}，可选水质指标 {sorted(INDICATORS)}——GR-09）"
            )
        extras = sorted(set(params) - required - INDICATORS)
        if extras:
            raise InvalidNodeError(
                f"municipal_input 多余参数：{extras}"
                f"（合法键 = 必需 {sorted(required)} ∪ 指标 {sorted(INDICATORS)}）"
            )
        self._flow = make_flow(
            Quantity(magnitude=params["q_avg_daily"], unit="m3/s"), params["kz"]
        )
        self._quality = WaterQuality(
            {key: value for key, value in params.items() if key in INDICATORS}
        )

    def compute(self, ctx: UnitContext) -> UnitResult:
        """图源产出（纯：构造期定形，ctx 只供 unit_id）。"""
        out = _out_port(ctx.unit_id)
        return UnitResult(
            outflows={out: self._flow},
            outqualities={out: self._quality},
            dims={},
            warnings=(),
            formula_ids=("builtin.municipal_input",),
        )


@final
class _Junction:
    """汇流：多入单出（v1 两口 in_1/in_2），q_avg=Σ、kz=max、水质负荷加权。"""

    manifest: UnitManifest = _manifest(
        "junction",
        (
            ("in_1", "WATER", "IN"),
            ("in_2", "WATER", "IN"),
            ("out", "WATER", "OUT"),
        ),
    )

    def compute(self, ctx: UnitContext) -> UnitResult:
        """按实际入边混合（WATER 通道；空入边/SLUDGE 拒）。"""
        refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
        if not refs:
            raise InvalidNodeError(
                f"junction {ctx.unit_id} 无入边（空入边拒——compute 期按"
                "实际入边混合，多入单出语义无意义）"
            )
        stocks = [ctx.inflows[ref] for ref in refs]
        flows: list[WaterFlow] = []
        for stock in stocks:
            if isinstance(stock, SludgeFlow):
                raise InvalidNodeError(
                    f"junction {ctx.unit_id} 收到 SLUDGE 入边（内置节点 v1 只做"
                    " WATER 通道——记档 §14.3 归属表 v1 裁决）"
                )
            flows.append(stock)
        q_total = 0.0
        for flow in flows:
            q_total += flow.q_avg_daily
        kz_max = max(flow.kz for flow in flows)
        if not isfinite(q_total) or not isfinite(kz_max):
            raise InvalidNodeError(
                f"junction {ctx.unit_id} 汇流结果非有限值拒绝（GR-02）："
                f"q_avg={q_total!r}, kz={kz_max!r}"
            )
        quality = mix(
            [ctx.inqualities.get(ref, _EMPTY) for ref in refs],
            [flow.q_avg_daily for flow in flows],
        )
        out = _out_port(ctx.unit_id)
        return UnitResult(
            outflows={out: WaterFlow(q_avg_daily=q_total, kz=kz_max)},
            outqualities={out: quality},
            dims={},
            warnings=(),
            formula_ids=("builtin.junction",),
        )


@final
class _QualityEdit:
    """水质编辑：一入一出；流量透传；params 指标覆盖、其余透传。"""

    manifest: UnitManifest = _manifest(
        "quality_edit",
        (
            ("in", "WATER", "IN"),
            ("out", "WATER", "OUT"),
        ),
    )

    def __init__(self, params: Mapping[str, Any]) -> None:
        extras = sorted(set(params) - INDICATORS)
        if extras:
            raise InvalidNodeError(
                f"quality_edit 参数键越界：{extras}"
                f"（仅水质指标 {sorted(INDICATORS)} 可覆盖——GR-09）"
            )
        # 覆盖值经 WaterQuality 域校验（构造期正门，失败=装配失败）。
        self._overrides = WaterQuality(dict(params))

    def compute(self, ctx: UnitContext) -> UnitResult:
        """透传流量 + 指标覆盖（缺项入流按空水质单位元，R5）。"""
        refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
        if len(refs) != 1:
            raise InvalidNodeError(
                f"quality_edit {ctx.unit_id} 须恰一入边：得到 {len(refs)} 条"
                "（一入一出语义）"
            )
        stock = ctx.inflows[refs[0]]
        if isinstance(stock, SludgeFlow):
            raise InvalidNodeError(
                f"quality_edit {ctx.unit_id} 收到 SLUDGE 入边（内置节点 v1"
                " 只做 WATER 通道——记档 §14.3 归属表 v1 裁决）"
            )
        merged = dict(ctx.inqualities.get(refs[0], _EMPTY).concentrations)
        merged.update(self._overrides.concentrations)
        out = _out_port(ctx.unit_id)
        return UnitResult(
            outflows={out: stock},
            outqualities={out: WaterQuality(merged)},
            dims={},
            warnings=(),
            formula_ids=("builtin.quality_edit",),
        )


@final
class _RecycleJunction:
    """回流转换：单入 SLUDGE → 单出 WATER（泥→水投影，GOLDEN3 D1）。

    v1 前向叠加口径（D0 定调）：回流边为跨子图 forward 边，本节点只做
    股类型变换——出流 kz=1.0（回流为连续均匀流无峰化，工程裁量 I2
    追认）、出水质只投 SS（其余指标由 propagate 部分缺项语义=上游
    原值）；真环迭代（hebing 实体化+水线产泥口）挂账 GOLDEN4。
    """

    manifest: UnitManifest = _manifest(
        "recycle_junction",
        (
            ("in", "SLUDGE", "IN"),
            ("out", "WATER", "OUT"),
        ),
    )

    def compute(self, ctx: UnitContext) -> UnitResult:
        """SLUDGE 股 → WATER 股：流量直入+kz=1+SS=ds/q_wet×1000 mg/L。"""
        refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
        if len(refs) != 1:
            raise InvalidNodeError(
                f"recycle_junction {ctx.unit_id} 须恰一入边：得到 {len(refs)} 条"
                "（单入转换语义——空入/多入拒）"
            )
        stock = ctx.inflows[refs[0]]
        if not isinstance(stock, SludgeFlow):
            raise InvalidNodeError(
                f"recycle_junction {ctx.unit_id} 入流须 SLUDGE 股：得到 "
                f"{type(stock).__name__}（泥→水投影单向——WATER 股拒）"
            )
        if not isfinite(stock.q_wet) or stock.q_wet <= 0:
            raise InvalidNodeError(
                f"recycle_junction {ctx.unit_id} 入流 q_wet 须为正有限值"
                "（SS 投影 ds/q_wet 无定义——GR-14 显式拒，工程裁量 I2"
                f" 追认）：得到 {stock.q_wet!r}"
            )
        ss = stock.ds / stock.q_wet * _KG_M3_TO_MG_L
        if not isfinite(ss):
            raise InvalidNodeError(
                f"recycle_junction {ctx.unit_id} SS 投影非有限值拒绝（GR-02）："
                f"{ss!r}（ds={stock.ds!r}）"
            )
        out = _out_port(ctx.unit_id)
        return UnitResult(
            outflows={out: WaterFlow(q_avg_daily=stock.q_wet, kz=1.0)},
            outqualities={out: WaterQuality({"SS": ss})},
            dims={
                "q_recycle": stock.q_wet * _SECS_PER_DAY,
                "ss_recycle": ss,
            },
            warnings=(),
            formula_ids=("builtin.recycle_junction",),
        )


# builtin 单位标签：manifest unit_id 用下划线形态（load_manifest 的 GR-26
# 标识符守卫拒点号）；formula_ids 用点式展示形态（GR-09 同款纪律）。
_BUILTIN_KINDS: Final[tuple[str, ...]] = (
    "municipal_input",
    "junction",
    "quality_edit",
    "recycle_junction",
)


def builtin_unit(kind: str, params: Mapping[str, Any]) -> Unit:
    """唯一工厂正门：按 kind 构造内置图节点（未知 kind = InvalidNodeError）。"""
    if kind == "municipal_input":
        return _MunicipalInput(params)
    if kind == "junction":
        return _Junction()
    if kind == "quality_edit":
        return _QualityEdit(params)
    if kind == "recycle_junction":
        return _RecycleJunction()
    raise InvalidNodeError(
        f"未知内置节点 kind：{kind!r}"
        f"（合法 {sorted(_BUILTIN_KINDS)}——§14.3 归属表 v1 三 kind"
        "+GOLDEN3 D1 回流转换）"
    )
