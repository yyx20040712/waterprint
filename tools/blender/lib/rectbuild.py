"""矩形池族共用几何构造（段二 AAO/CASS——build_aao/build_cass 消费）。

输入:  bpy 无头（经 build_aao.py/build_cass.py 内嵌运行）+材质 token
输出:  水密网格对象（厚壁矩形池体/矩形环板走道/矩形栏杆环/盒/杆/圆柱
        几何件）+归一校验报告件

规格说明（assemble/spec.md §1/§2/§10 同守——与 build_clarifier_radial
  同构但独立实现[辐流件已过三段流，不改已审面]）：
  - 构造法=多闭包盒合并（各件水密闭包→并集自然边入射恰二面——辐流
    驱动装置先例）；无 boolean 无修改器（无头确定性）；
  - 厚壁矩形池体=底板+四墙共 5 盒合并（角部由底板/端墙覆盖无孔洞）；
  - 坐标：Blender z-up，原点=池底中心（米制——§1 表 2 行）；
  - 命名/材质经 lib.naming/lib.materials 单源（调用方组前缀拼装）。
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector


def box_geo(center: tuple[float, float, float],
            size: tuple[float, float, float]) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """轴对齐盒几何（八顶点六外法线面——水密闭包）。"""
    cx, cy, cz = center
    sx, sy, sz = (d / 2 for d in size)
    idx = [(x, y, z) for z in (cz - sz, cz + sz) for y in (cy - sy, cy + sy)
           for x in (cx - sx, cx + sx)]
    verts = [Vector(p) for p in idx]
    # idx 序：0(---)1(+--)2(-+-)3(++-)4(--)5(+-)6(-+)7(++)
    faces = [
        (0, 2, 3, 1),  # 底 −z
        (4, 5, 7, 6),  # 顶 +z
        (0, 1, 5, 4),  # 前 −y
        (2, 6, 7, 3),  # 后 +y
        (0, 4, 6, 2),  # 左 −x
        (1, 3, 7, 5),  # 右 +x
    ]
    return verts, faces


def cyl_geo(radius: float, z_bottom: float, z_top: float,
            center_xy: tuple[float, float] = (0.0, 0.0),
            segments: int = 24) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """闭合圆柱几何（侧柱面+底/顶扇——水密）。"""
    cx, cy = center_xy
    bot = [Vector((cx + radius * math.cos(2 * math.pi * i / segments),
                   cy + radius * math.sin(2 * math.pi * i / segments), z_bottom))
           for i in range(segments)]
    top = [Vector((cx + radius * math.cos(2 * math.pi * i / segments),
                   cy + radius * math.sin(2 * math.pi * i / segments), z_top))
           for i in range(segments)]
    cb, ct = segments * 2, segments * 2 + 1
    verts = bot + top + [Vector((cx, cy, z_bottom)), Vector((cx, cy, z_top))]
    faces: list[tuple[int, ...]] = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j, segments + i))     # 侧柱面 +r
        faces.append((cb, j, i))                            # 底 −z
        faces.append((ct, segments + i, segments + j))      # 顶 +z
    return verts, faces


def rod_geo(p0: Vector, p1: Vector, radius: float,
            segments: int = 12) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """任意轴向圆杆几何（侧柱面+两端帽——水密；桁架杆/栏杆）。"""
    d = (p1 - p0).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = d.cross(ref).normalized()
    v = d.cross(u).normalized()
    bot, top = [], []
    for i in range(segments):
        offset = u * (radius * math.cos(2 * math.pi * i / segments)) + \
                 v * (radius * math.sin(2 * math.pi * i / segments))
        bot.append(p0 + offset)
        top.append(p1 + offset)
    cb, ct = segments * 2, segments * 2 + 1
    verts = bot + top + [p0.copy(), p1.copy()]
    faces: list[tuple[int, ...]] = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j, segments + i))     # 侧柱面 +r
        faces.append((cb, j, i))                            # 底帽 −d
        faces.append((ct, segments + i, segments + j))      # 顶帽 +d
    return verts, faces


def add_mesh(name: str, verts: list[Vector], faces: list[tuple[int, ...]],
             token: str) -> bpy.types.Object:
    """网格对象落场（材质经 lib.materials 单源——调用方 import 传 token）。"""
    from lib import materials
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(materials.ensure_material(token))
    bpy.context.collection.objects.link(obj)
    return obj


def merged(name: str, parts: list[tuple[list[Vector], list[tuple[int, ...]]]],
           token: str) -> bpy.types.Object:
    """多闭包件合并单网格（各件水密闭包→并集自然边入射恰二面）。"""
    verts: list[Vector] = []
    faces: list[tuple[int, ...]] = []
    for part_verts, part_faces in parts:
        base = len(verts)
        verts.extend(part_verts)
        faces.extend(tuple(base + idx for idx in face) for face in part_faces)
    return add_mesh(name, verts, faces, token)


def thick_rect_pool(name: str, length: float, width: float, height: float,
                    wall: float, token: str) -> bpy.types.Object:
    """厚壁矩形池体（盒中盒单拓扑水密网格，顶开敞）。

    外沿 [±L/2, ±W/2]×[0,H]，内腔 [±L/2−t, ±W/2−t]×[t,H]（底板厚=壁厚）。
    **单拓扑非盒合并**（首版 5 盒合并的角部体积重叠在 CI 焊接步暴露
    边入射 4 面——check_templates 实拦记档）；绕序=外法线（外壳正体积+
    内腔反转=净壳实体体积，辐流 _thick_cup 同构）。
    """
    hx, hy = length / 2, width / 2
    ix, iy = hx - wall, hy - wall
    ob = [(-hx, -hy, 0.0), (hx, -hy, 0.0), (hx, hy, 0.0), (-hx, hy, 0.0)]
    ot = [(-hx, -hy, height), (hx, -hy, height), (hx, hy, height), (-hx, hy, height)]
    ib = [(-ix, -iy, wall), (ix, -iy, wall), (ix, iy, wall), (-ix, iy, wall)]
    it = [(-ix, -iy, height), (ix, -iy, height), (ix, iy, height), (-ix, iy, height)]
    verts = [Vector(p) for p in ob + ot + ib + it]
    # 索引基：外下 0-3 / 外上 4-7 / 内下 8-11（z=t）/ 内上 12-15
    faces = [
        (0, 3, 2, 1),        # 外底 −z
        (0, 1, 5, 4),        # 外墙 −y
        (1, 2, 6, 5),        # 外墙 +x
        (2, 3, 7, 6),        # 外墙 +y
        (3, 0, 4, 7),        # 外墙 −x
        (4, 5, 13, 12),      # 顶环 前段（−y）+z
        (5, 6, 14, 13),      # 顶环 东段（+x）
        (6, 7, 15, 14),      # 顶环 后段（+y）
        (7, 4, 12, 15),      # 顶环 西段（−x）
        (9, 8, 12, 13),      # 内墙 −y（法线朝腔内 +y）
        (10, 9, 13, 14),     # 内墙 +x
        (11, 10, 14, 15),    # 内墙 +y
        (8, 11, 15, 12),     # 内墙 −x
        (8, 9, 10, 11),      # 内底 +z（z=t）
    ]
    return add_mesh(name, verts, faces, token)


def rect_walkway(name: str, length_outer: float, width_outer: float,
                 length_inner: float, width_inner: float, z_bottom: float,
                 z_top: float, token: str) -> bpy.types.Object:
    """矩形环板走道（四条带盒合并——外/内沿全宽；水密单网格）。"""
    hxo, hyo = length_outer / 2, width_outer / 2
    hxi, hyi = length_inner / 2, width_inner / 2
    assert hxo > hxi and hyo > hyi, "走道内外沿非包络（零/负宽环=数据病）"
    parts = [
        box_geo((0.0, -(hyi + hyo) / 2, (z_bottom + z_top) / 2),
                (2 * hxo, hyo - hyi, z_top - z_bottom)),                # 前带
        box_geo((0.0, (hyi + hyo) / 2, (z_bottom + z_top) / 2),
                (2 * hxo, hyo - hyi, z_top - z_bottom)),                # 后带
        box_geo((-((hxi + hxo) / 2), 0.0, (z_bottom + z_top) / 2),
                (hxo - hxi, 2 * hyi, z_top - z_bottom)),                # 左带
        box_geo(((hxi + hxo) / 2, 0.0, (z_bottom + z_top) / 2),
                (hxo - hxi, 2 * hyi, z_top - z_bottom)),                # 右带
    ]
    return merged(name, parts, token)


def rect_rail(name: str, hx: float, hy: float, z: float, tube: float,
              token: str) -> bpy.types.Object:
    """矩形栏杆环（水平面 x-y 闭环 4 杆——每杆独立水密闭包）。"""
    parts = [
        rod_geo(Vector((-hx, -hy, z)), Vector((hx, -hy, z)), tube, segments=8),
        rod_geo(Vector((hx, -hy, z)), Vector((hx, hy, z)), tube, segments=8),
        rod_geo(Vector((hx, hy, z)), Vector((-hx, hy, z)), tube, segments=8),
        rod_geo(Vector((-hx, hy, z)), Vector((-hx, -hy, z)), tube, segments=8),
    ]
    return merged(name, parts, token)
