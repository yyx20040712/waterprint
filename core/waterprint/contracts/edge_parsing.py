"""design.edges 解析内核：raw 映射 → PortRef/Edge（拒绝异常类注入）。

输入:  design.edges 原始元素（src/dst/recycle 映射）+ 消费方拒绝异常类
输出:  PortRef / Edge 元组（边转换校验与消息单源——B4 双胞胎收敛件）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3-c 批 2c 收敛 2026-09-19，三段通道定案=docs/design/
#   2026-09-19_b4-twins-convergence-design.md）：
#   app_assembly._endpoint/_edges 与 executor_assembly._endpoint/
#   _edges_from_design 双胞胎收敛——校验/消息/遍历结构单源于此，
#   拒绝载体经 error 注入（批 3a latest_calc not_found 先例同型）；
#   消息文本统一为含「得到」版（定案 J3 呈案 A：_edges 侧两版现状
#   已含、_endpoint 侧 executor 版补齐；app 侧文本零变故
#   validate_design_structure 汇总面零连带）。
# 【公开接口】
#   endpoint_from(raw, side, index, *, error) -> PortRef
#   edges_from(raw_edges, *, error) -> tuple[Edge, ...]
#   error=拒绝异常类（单参消息构造；在册载体=InvalidAssemblyError/
#   InvalidExecutionError——HTTP 400/422 契约面经注入保恒等）
# 【铁律】L0 零内部依赖——仅 import 同包 ports+标准库（GR-36 类③
#   受限内核，expr.py 先例）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence

from waterprint.contracts.ports import Edge, PortRef


def endpoint_from(
    raw: object, side: str, index: int, *, error: type[Exception]
) -> PortRef:
    """边端点转换：{"unit_id","port_id"} → PortRef（键缺失/类型错=error 拒）。"""
    if not isinstance(raw, Mapping):
        raise error(
            f"design.edges[{index}].{side} 须为对象（含 unit_id/port_id）："
            f"得到 {type(raw).__name__}"
        )
    unit_id = raw.get("unit_id")
    port_id = raw.get("port_id")
    if not isinstance(unit_id, str) or not isinstance(port_id, str):
        raise error(
            f"design.edges[{index}].{side} 须含字符串 unit_id/port_id："
            f"得到 {unit_id!r}, {port_id!r}"
        )
    return PortRef(unit_id=unit_id, port_id=port_id)


def edges_from(
    raw_edges: Sequence[object], *, error: type[Exception]
) -> tuple[Edge, ...]:
    """design.edges（D3 冻结元素形态）→ Edge 元组（端点经 endpoint_from）。"""
    edges: list[Edge] = []
    for index, element in enumerate(raw_edges):
        if not isinstance(element, Mapping):
            raise error(
                f"design.edges[{index}] 须为对象（src/dst/recycle）："
                f"得到 {type(element).__name__}"
            )
        recycle = element.get("recycle", False)
        if not isinstance(recycle, bool):
            raise error(f"design.edges[{index}].recycle 须为布尔：得到 {recycle!r}")
        edges.append(
            Edge(src=endpoint_from(element.get("src"), "src", index, error=error),
                 dst=endpoint_from(element.get("dst"), "dst", index, error=error),
                 recycle=recycle))
    return tuple(edges)
