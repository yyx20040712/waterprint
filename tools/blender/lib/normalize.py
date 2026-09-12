"""模板归一校验（assemble/spec.md §2/§8——导出前置质量门）。

输入:  壳组对象 + templateSize（L0/W0/H0 米）+ 全部规约名对象
输出:  assert_shell_aabb（壳 AABB 对拍 templateSize——Blender 系
        x=长/y=宽/z=深 即 [−L0/2,L0/2]×[−W0/2,W0/2]×[0,H0]）/mesh_report
        （逐对象顶点/面/边入射计数+有符号体积——CI 四步的 Blender 侧
        前置快检，权威校验在 webapp check_templates）

规格说明（spec §2 壳归一基准=registry templateSize 对拍；§8 水密四步
  的焊接步在本源可省——构造期共享顶点索引无重位拆分；位置焊接容差
  归 CI 面对解码后网格）。
"""

from __future__ import annotations

import math

import bpy  # noqa: F401 —— Blender 内嵌运行（-b -P）

AABB_TOLERANCE = 0.02  # 米——建模顶点精确值下的安全余量（量化误差归 CI 面容差）


def _object_aabb(obj: bpy.types.Object) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """对象世界系 AABB（Blender z-up 模板本地=世界系——对象变换恒等式）。"""
    coords = [obj.matrix_world @ v.co for v in obj.data.vertices]  # type: ignore[attr-defined]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    zs = [c.z for c in coords]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def assert_shell_aabb(obj: bpy.types.Object, size: tuple[float, float, float]) -> None:
    """壳 AABB 对拍 templateSize（spec §2：L0/W0/H0——Blender 轴序
    x=长/y=宽/z=深；违例 raise ValueError=模板源病，导出中止）。"""
    l0, w0, h0 = size
    (min_x, min_y, min_z), (max_x, max_y, max_z) = _object_aabb(obj)
    expected = [(-l0 / 2, -w0 / 2, 0.0), (l0 / 2, w0 / 2, h0)]
    actual = [(min_x, min_y, min_z), (max_x, max_y, max_z)]
    for got, want in zip(actual, expected):
        for name, g, w in zip(("x", "y", "z"), got, want):
            if abs(g - w) > AABB_TOLERANCE:
                raise ValueError(
                    f"壳 AABB 越界：{obj.name!r} {name}={g:.4f} 期望 {w:.4f}"
                    f"（templateSize={size}——spec §2 归一基准对拍失败）"
                )


def _signed_volume(obj: bpy.types.Object) -> float:
    """有符号体积 V=Σ(v0·(v1×v2))/6（spec §8 绕序一致性同式——外法线
    绕序约定下为正；负/近零=绕序病或退化体）。"""
    verts = [tuple(obj.matrix_world @ v.co) for v in obj.data.vertices]  # type: ignore[attr-defined]
    total = 0.0
    for poly in obj.data.polygons:  # type: ignore[attr-defined]
        fan = poly.vertices
        v0 = verts[fan[0]]
        for i in range(1, len(fan) - 1):
            v1 = verts[fan[i]]
            v2 = verts[fan[i + 1]]
            total += (
                v0[0] * (v1[1] * v2[2] - v1[2] * v2[1])
                - v0[1] * (v1[0] * v2[2] - v1[2] * v2[0])
                + v0[2] * (v1[0] * v2[1] - v1[1] * v2[0])
            )
    return total / 6.0


def mesh_report(obj: bpy.types.Object) -> str:
    """逐对象快检：边入射恰二面+有符号体积正——CI 四步前置（构造期
    共享顶点 → 焊接步天然满足）。返回人读摘要，违例 raise。"""
    edge_faces: dict[tuple[int, int], int] = {}
    for poly in obj.data.polygons:  # type: ignore[attr-defined]
        fan = list(poly.vertices)
        for i in range(len(fan)):
            a, b = fan[i], fan[(i + 1) % len(fan)]
            edge_faces[(min(a, b), max(a, b))] = edge_faces.get((min(a, b), max(a, b)), 0) + 1
    bad = {e: n for e, n in edge_faces.items() if n != 2}
    if bad:
        sample = sorted(bad.items())[:3]
        raise ValueError(
            f"边入射非二面：{obj.name!r} {len(bad)} 条（样例 {sample}）"
            "——开口/非流形，spec §8 水密违例"
        )
    volume = _signed_volume(obj)
    if not volume > 1e-6:
        raise ValueError(
            f"有符号体积非正：{obj.name!r} V={volume:.6f}——绕序翻转或退化体"
            "（spec §8 绕序一致性违例）"
        )
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)  # type: ignore[attr-defined]
    return (
        f"{obj.name}: verts={len(obj.data.vertices)} "  # type: ignore[attr-defined]
        f"tris≈{tris} V={volume:.2f}m³"
    )
