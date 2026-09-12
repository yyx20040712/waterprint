"""辐流二沉池参数化模板建模（Φ40×4——批3 主体第一件首族）。

输入:  bpy 无头（``blender -b --factory-startup -P build_clarifier_radial.py``）
输出:  build/clarifier_radial.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10——已签核）：
  - 坐标：Blender z-up，原点=池底中心，米制（§1 表 2 行）；
  - templateSize Φ40×4：shell AABB=[−20,20]²×[0,4]（§2 归一基准——
    normalize.assert_shell_aabb 对拍）；
  - 四组：shell 厚壁杯体[水密] / trim 周圈走道+栏杆环[缺省水平双向掩码]
    / equip 中心筒 Φ4.8（=0.12×40 比例·S3 数据链）+刮泥机桥 / inst
    栏杆立柱原型[P7：数量唯一真源=场景图 instance_count——原型平移
    保留为节点 TRS 供 instanceLayout 读]；
  - 构造法：手写顶点/面（绕序外法线约定+共享顶点索引——边入射恰二面
    按构造成立，normalize.mesh_report 快检）；无 boolean 无修改器
    （无头确定性优先）；
  - 水面层（preview_water）入 preview_only 集合——仅 PNG 缩略图消费，
    glb 导出面剔除（spec §2/§10）。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import naming
from lib import materials
from lib import normalize

# ── 模板常量（registry 同源声明——改值须与 registry.json 同窗） ─────────
FAMILY = "clarifier"            # 命名前缀（§10 例式；registry family=clarifier_radial）
TEMPLATE_SIZE = (40.0, 40.0, 4.0)  # L0/W0/H0（Φ40×4）
SEGMENTS = 48                    # 环向分段（弦长≈2.6m——站点尺度平滑档）
WALL = 0.4                       # 壁厚（含底板）
R_OUTER = TEMPLATE_SIZE[0] / 2   # 20.0
R_INNER = R_OUTER - WALL         # 19.6
H_TOP = TEMPLATE_SIZE[2]         # 4.0
WALK_WIDTH = 1.6                 # 周圈走道宽
WALK_THICK = 0.12
RAIL_RADIUS = R_OUTER + WALK_WIDTH - 0.1  # 21.5
RAIL_TUBE = 0.03
RAIL_HEIGHTS = (1.1, 0.6)        # 顶栏/中栏（规范定值——S1 不随池深缩放）
WELL_D = 0.12 * TEMPLATE_SIZE[0]  # 中心筒 Φ4.8（S3：actualFactor=0.12×D）
WELL_TOP = 3.2                   # 中心筒顶（米制定值）
BRIDGE_CLEAR = 3.7               # 刮泥机桥面高（米制定值）
BRIDGE_WIDTH = 0.9
BRIDGE_THICK = 0.14
POST_H = RAIL_HEIGHTS[0]         # 立柱高 1.1（P5 间距 1.5m 归 instanceLayout）
WATER_LEVEL = WALL + 3.0         # PNG 专用水面（h2=3.0 典型有效水深）


def _ring(radius: float, z: float) -> list[Vector]:
    return [
        Vector((radius * math.cos(2 * math.pi * i / SEGMENTS),
                radius * math.sin(2 * math.pi * i / SEGMENTS), z))
        for i in range(SEGMENTS)
    ]


def _add_mesh(name: str, verts: list[Vector], faces: list[tuple[int, ...]],
              token: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(materials.ensure_material(token))
    bpy.context.collection.objects.link(obj)
    return obj


def _thick_cup(name: str, token: str) -> bpy.types.Object:
    """厚壁杯体（外柱面+底板+内腔壁+内底+顶环沿——水密单网格）。

    绕序：外法线约定（outer lateral +r / 底面 −z / 顶环沿 +z /
    内腔壁 −r / 内底 +z——normalize._signed_volume 正号锚）。
    """
    o_bot, o_top = _ring(R_OUTER, 0.0), _ring(R_OUTER, H_TOP)
    i_top, i_bot = _ring(R_INNER, H_TOP), _ring(R_INNER, WALL)
    center_bot, center_floor = len(o_bot) * 4, len(o_bot) * 4 + 1
    verts = o_bot + o_top + i_top + i_bot + [Vector((0, 0, 0)), Vector((0, 0, WALL))]
    faces: list[tuple[int, ...]] = []
    for i in range(SEGMENTS):
        j = (i + 1) % SEGMENTS
        faces.append((i, j, SEGMENTS + j, SEGMENTS + i))            # 外柱面 +r
        faces.append((center_bot, j, i))                            # 底板 −z
        faces.append((SEGMENTS + i, SEGMENTS + j, 2 * SEGMENTS + j,
                      2 * SEGMENTS + i))                            # 顶环沿 +z
        faces.append((2 * SEGMENTS + i, 2 * SEGMENTS + j, 3 * SEGMENTS + j,
                      3 * SEGMENTS + i))                            # 内腔壁 −r
        faces.append((center_floor, 3 * SEGMENTS + i, 3 * SEGMENTS + j))  # 内底 +z
    return _add_mesh(name, verts, faces, token)


def _ring_slab(name: str, r_inner: float, r_outer: float,
               z_bottom: float, z_top: float, token: str) -> bpy.types.Object:
    """环形板（走道：外/内柱面+顶/底环面——水密）。"""
    i_bot, i_top = _ring(r_inner, z_bottom), _ring(r_inner, z_top)
    o_bot, o_top = _ring(r_outer, z_bottom), _ring(r_outer, z_top)
    verts = i_bot + i_top + o_bot + o_top
    base = SEGMENTS
    faces: list[tuple[int, ...]] = []
    for i in range(SEGMENTS):
        j = (i + 1) % SEGMENTS
        faces.append((2 * base + i, 2 * base + j, 3 * base + j, 3 * base + i))  # 外柱面 +r
        faces.append((3 * base + i, 3 * base + j, base + j, base + i))          # 顶环 +z
        faces.append((base + i, base + j, j, i))                                # 内柱面 −r
        faces.append((i, j, 2 * base + j, 2 * base + i))                        # 底环 −z
    return _add_mesh(name, verts, faces, token)


def _closed_cylinder(name: str, radius: float, z_bottom: float, z_top: float,
                     token: str, center_xy: tuple[float, float] = (0.0, 0.0),
                     segments: int = SEGMENTS) -> bpy.types.Object:
    """闭合圆柱（侧柱面+底/顶扇——水密；立柱用小分段降面数）。"""
    cx, cy = center_xy
    bot = [Vector((cx + radius * math.cos(2 * math.pi * i / segments),
                   cy + radius * math.sin(2 * math.pi * i / segments), z_bottom))
           for i in range(segments)]
    top = [v.copy() for v in bot]
    top = [Vector((v.x, v.y, z_top)) for v in top]
    cb, ct = segments * 2, segments * 2 + 1
    verts = bot + top + [Vector((cx, cy, z_bottom)), Vector((cx, cy, z_top))]
    faces: list[tuple[int, ...]] = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j, segments + i))     # 侧柱面 +r
        faces.append((cb, j, i))                            # 底 −z
        faces.append((ct, segments + i, segments + j))      # 顶 +z
    return _add_mesh(name, verts, faces, token)


def _box(name: str, center: tuple[float, float, float],
         size: tuple[float, float, float], token: str) -> bpy.types.Object:
    """轴对齐盒（八顶点六外法线面）。"""
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
    return _add_mesh(name, verts, faces, token)


def _torus(name: str, radius: float, z: float, token: str) -> bpy.types.Object:
    """栏杆环（ops 圆环——XY 平面·z 轴向；外绕序由 ops 保证）。"""
    bpy.ops.mesh.primitive_torus_add(
        location=(0, 0, z), major_radius=radius, minor_radius=RAIL_TUBE,
        major_segments=SEGMENTS, minor_segments=8,
    )
    obj = bpy.context.active_object
    assert obj is not None
    obj.name = name
    obj.data.name = name
    obj.data.materials.append(materials.ensure_material(token))
    return obj


def _under(parent: bpy.types.Object, child: bpy.types.Object) -> None:
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def build() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    # 分组父级（§10：Empty 承载——glTF 保留节点层级）
    shell_root = bpy.data.objects.new("shell", None)
    trim_root = bpy.data.objects.new("trim", None)
    equip_root = bpy.data.objects.new("equip", None)
    inst_root = bpy.data.objects.new("inst", None)
    for root in (shell_root, trim_root, equip_root, inst_root):
        scene.collection.objects.link(root)

    shell = _thick_cup(
        naming.build_name(FAMILY, "shell", "wall"), "pool_wall")
    _under(shell_root, shell)

    walkway = _ring_slab(
        naming.build_name(FAMILY, "trim", "walkway"),  # 缺省掩码=水平双向
        R_OUTER, R_OUTER + WALK_WIDTH, H_TOP, H_TOP + WALK_THICK, "pool_wall")
    _under(trim_root, walkway)
    rails = [_torus(
        naming.build_name(FAMILY, "trim", f"handrail_{int(h * 100)}"),
        RAIL_RADIUS, H_TOP + WALK_THICK + h, "steel") for h in RAIL_HEIGHTS]
    for rail in rails:
        _under(trim_root, rail)

    well = _closed_cylinder(
        naming.build_name(FAMILY, "equip", "center_well"),
        WELL_D / 2, WALL, WELL_TOP, "steel")
    _under(equip_root, well)
    bridge_len = R_OUTER + WALK_WIDTH - 0.1
    bridge = _box(
        naming.build_name(FAMILY, "equip", "bridge"),
        (bridge_len / 2, 0.0, BRIDGE_CLEAR), (bridge_len, BRIDGE_WIDTH,
                                              BRIDGE_THICK), "steel")
    _under(equip_root, bridge)
    platform = _closed_cylinder(
        naming.build_name(FAMILY, "equip", "bridge_drive"),
        0.8, BRIDGE_CLEAR, BRIDGE_CLEAR + 0.3, "steel", segments=24)
    _under(equip_root, platform)

    # 立柱原型：几何本地居中（z 0→POST_H），对象平移=节点 TRS（P7——
    # instanceLayout 读原型基座位姿分布环周；σ=𝟙 几何不缩放）
    post = _closed_cylinder(
        naming.build_name(FAMILY, "inst", "rail_post"),
        0.025, 0.0, POST_H, "steel", center_xy=(0.0, 0.0), segments=12)
    post.location = (RAIL_RADIUS, 0.0, H_TOP + WALK_THICK)
    _under(inst_root, post)

    # 平滑着色（柱面/环面——锐边自动保持；失败退平直 shading 无害）
    for obj in (shell, walkway, well, *rails):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(25.0))
        except (RuntimeError, TypeError):
            pass

    # PNG 专用水面（preview_only 集合——glb 导出剔除）
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    mesh = bpy.data.meshes.new("preview_water")
    mesh.from_pydata(
        [Vector((R_INNER * math.cos(2 * math.pi * i / SEGMENTS),
                 R_INNER * math.sin(2 * math.pi * i / SEGMENTS), WATER_LEVEL))
         for i in range(SEGMENTS)] + [Vector((0, 0, WATER_LEVEL))],
        [], [tuple(range(SEGMENTS))],
    )
    mesh.validate()
    mesh.update()
    water = bpy.data.objects.new("preview_water", mesh)
    water.data.materials.append(
        materials.ensure_material("water_surface", alpha=0.72))
    preview.objects.link(water)

    # 归一校验（§2 AABB 对拍+水密快检——违例即中止导出面）
    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    report = [normalize.mesh_report(o) for o in
              (shell, walkway, *rails, well, bridge, platform, post)]
    print("[NORMALIZE]")
    for line in report:
        print("  " + line)

    out = Path(__file__).resolve().parent / "build" / "clarifier_radial.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
