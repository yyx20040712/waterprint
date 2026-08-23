"""端口与边契约（水/泥类型化端口、回流标记——回路与连接合法性的唯一裁判）。

输入:  单元 manifest 的端口声明、用户的连线意图
输出:  Port / Edge 不可变类型与 FluidKind 枚举
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T3 冻结；镜像测试 tests/contracts/test_ports.py）
#
# 【公开接口】
#   class FluidKind(Enum)：WATER / SLUDGE
#   class Direction(Enum)：IN / OUT
#   class InvalidConnection(Exception)
#       连接非法领域异常（GR-11 Invalid* 族：流体不匹配/方向非 OUT→IN/
#       端口未声明；消息必含两端 ref 与原因——GR-09）。
#   class Port(不可变)：port_id、fluid: FluidKind、direction: Direction、
#       recycle: bool = False（回流/内回流边标记，驱动 SCC 划分与固定点迭代）
#   class PortRef(不可变)：unit_id + port_id 两位置构造（边的端点）
#   class Edge(不可变)：src: PortRef、dst: PortRef
#   validate_edge(edge: Edge, ports_index: Mapping[(unit_id, port_id) → Port])
#       -> None    连接合法性唯一裁判；非法抛 InvalidConnection（含人类可读原因）
#
# 【行为规格】
#   R1 类型不匹配（水→泥、泥→水）= InvalidConnection；前端连线规则与
#      本规则同源（端口颜色=流体语义只是显示，真相在这里）。
#   R2 方向必须 OUT→IN；一入多出/多入一出由图级校验（graph 层）处理，
#      本文件只管单条边的局部合法性。
#   R3 recycle=True 的边：语义为"循环回流"（污泥回流 R、内回流 Ri），
#      图引擎据此把环从异常变为可解对象（§3 保证 3，病灶"DAG 环路直接异常"）。
#   R4 端口 ID 稳定：进项目文件序列化，改名必须走迁移链（project/migration.py）。
#
# 【T3 冻结注记】（总控简报 D 系裁决，2026-08-23）
#   - ports_index 形态照锁定测试：(unit_id, port_id) 二元组键 → Port；
#      端口未在索引中声明 = InvalidConnection（裁判前提失败，同样必含
#      ref 与原因——静默通过 = 连接真相缺位）。
#   - 异常消息冻结口径（GR-09，进发布即冻结）：必含「两端
#      unit_id.port_id + 实际流体/方向 + 期望语义」；三拒例
#      （流体不匹配/方向非 OUT→IN/端口未声明）消息文本互可区分。
#   - 数值纪律：本文件不在魔法数字白名单——零数值字面量。
#
# 【测试要求】类型/方向非法拒绝（含错误消息可读）、recycle 标记缺省 False、
#   不可变性（赋值即异常）。
#
# 【参照】重写计划 §3-3/§14.2；ADR-003；简报 T3 §2 接口层
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import final


class FluidKind(Enum):
    """流体类型：水 / 泥（类型化端口的流体语义，R1 裁判依据）。"""

    WATER = "WATER"
    SLUDGE = "SLUDGE"


class Direction(Enum):
    """端口方向：入 / 出（OUT→IN 是唯一合法边方向，R2）。"""

    IN = "IN"
    OUT = "OUT"


# N818 豁免理由：InvalidConnection 之名由锁定测试 test_ports.py 与
# file-contracts.md 输出列双重冻结（M0 骨架既定公开面），改名 = 破坏锁定契约。
class InvalidConnection(Exception):  # noqa: N818
    """连接非法（流体不匹配/方向非 OUT→IN/端口未声明）——领域异常。"""


@dataclass(frozen=True)
@final
class Port:
    """单元端口（不可变）：流体类型 + 方向 + 回流标记（R3）。"""

    port_id: str
    fluid: FluidKind
    direction: Direction
    recycle: bool = False


@dataclass(frozen=True)
@final
class PortRef:
    """边端点（不可变）：unit_id + port_id（两位置构造）。"""

    unit_id: str
    port_id: str


@dataclass(frozen=True)
@final
class Edge:
    """连接边（不可变）：src PortRef → dst PortRef。"""

    src: PortRef
    dst: PortRef


def _ref(ref: PortRef) -> str:
    """端点的稳定展示形态 unit_id.port_id（异常消息 GR-09 冻结口径用）。"""
    return f"{ref.unit_id}.{ref.port_id}"


def _port_of(ports_index: Mapping[tuple[str, str], Port], ref: PortRef) -> Port:
    """按二元组键取端口；未声明 = InvalidConnection（裁判前提失败）。"""
    try:
        return ports_index[(ref.unit_id, ref.port_id)]
    except KeyError as exc:
        raise InvalidConnection(
            f"端口未声明：{_ref(ref)} 不在端口索引中"
            "（两端端口须先经 manifest 声明，R1 裁判前提）"
        ) from exc


def validate_edge(
    edge: Edge, ports_index: Mapping[tuple[str, str], Port]
) -> None:
    """连接合法性唯一裁判：流体匹配（R1）+ 方向 OUT→IN（R2）；非法即拒。"""
    src = _port_of(ports_index, edge.src)
    dst = _port_of(ports_index, edge.dst)
    if src.fluid is not dst.fluid:
        raise InvalidConnection(
            f"流体类型不匹配：{_ref(edge.src)} 为 {src.fluid.name}"
            f"，{_ref(edge.dst)} 为 {dst.fluid.name}"
            "（水/泥端口不可互连，R1）"
        )
    if src.direction is not Direction.OUT or dst.direction is not Direction.IN:
        raise InvalidConnection(
            f"边方向非法：须 OUT→IN，得到 {_ref(edge.src)} 为"
            f" {src.direction.name} → {_ref(edge.dst)} 为 {dst.direction.name}"
            "（R2）"
        )
