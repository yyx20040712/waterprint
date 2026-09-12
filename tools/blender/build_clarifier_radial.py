"""辐流二沉池参数化模板建模（Φ40×4——批3 主体第一件首族·迭代二）。

输入:  bpy 无头（``blender -b --factory-startup -P build_clarifier_radial.py``）
输出:  build/clarifier_radial.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10——已签核；迭代二=交接 §一.1
  部件清单[中心传动刮泥机调研]五项几何增强）：
  - 坐标：Blender z-up，原点=池底中心，米制（§1 表 2 行）；
  - templateSize Φ40×4：shell AABB=[−20,20]²×[0,4]（§2 归一基准——
    normalize.assert_shell_aabb 对拍）；
  - 四组：shell 厚壁杯体[水密] / trim 周圈走道+栏杆环+**周边出水堰槽+
    齿形堰板+撇渣装置+分缝条带[__nc 单面装饰]**（缺省水平双向掩码——
    随壳水平缩放）/ equip 中心筒 Φ4.8（=0.12×40 比例·S3 数据链）+
    **桁架化刮泥机桥（三角桁架+桥面走道）**+**驱动装置（平台+电机座）**
    / inst 栏杆立柱原型[P7：数量唯一真源=场景图 instance_count]；
  - 构造法：手写顶点/面（绕序外法线约定+共享顶点索引——边入射恰二面
    按构造成立，normalize.mesh_report 快检）；无 boolean 无修改器
    （无头确定性优先——桁架杆件=参数化圆柱面直写，不走 ops/修改器）；
    equip 件顶越出 templateSize H0=4（桁架顶 4.35/电机顶 4.88——门一
    W1 记档：shell 包络门不受影响，消费方[取景/装配/间距]均无以
    templateSize 作整体包络的 clamp，缩略图对角已按 5.3 实高取景）；
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
POST_H = RAIL_HEIGHTS[0]         # 立柱高 1.1（P5 间距 1.5m 归 instanceLayout）
WATER_LEVEL = WALL + 3.0         # PNG 专用水面（h2=3.0 典型有效水深）

# ── 迭代二新增（交接 §一.1 部件清单——ds 复审+刮泥机调研参数） ──────────
LAUNDER_R_IN = 19.20             # 出水堰槽内壁（槽宽 0.3×深 0.4——ds）
LAUNDER_Z_BOT = 3.60             # 槽底（堰槽悬挑于池内壁）
WEIR_R_IN = 19.26                # 齿形堰板内面（堰槽内壁内面 19.25+0.01
                                 # 避共面 z-fight——门一 W3）
WEIR_THICK = 0.08                # 堰板厚（缩略 10cm/px 可辨下限权衡）
WEIR_Z_BOT = 3.90                # 堰板底
WEIR_Z_TOOTH = 4.20              # 齿尖（齿幅 0.2=2px 可辨）
WEIR_Z_NOTCH = 4.00              # 缺口根（齿距=环向 2 分段≈5.05m 三角齿）
TRUSS_X0 = 2.6                   # 桁架西端（中心筒外缘让位）
TRUSS_X1 = R_OUTER + WALK_WIDTH - 0.1  # 21.5（外端齐栏杆环）
TRUSS_CHORD_R = 0.10             # 弦/腹杆径（调研 0.06→0.10：缩略 10cm/px
                                 # 下 2px 可辨下限——STYLE-BASE §3 权衡记档）
TRUSS_HALF_W = 0.38              # 下弦半宽（桥面宽内收）
TRUSS_TOP_UP = 0.55              # 上弦抬高（三角桁架高）
TRUSS_PANELS = 10                # 腹杆分格
DECK_THICK = 0.05                # 桥面走道板厚（格栅平铺近似）
SCUM_TUBE_L = 2.0                # 撇渣管长（半桥外缘——浮渣撇渣装置）
MOTOR_SEAT = 0.55                # 驱动电机座边长
MOTOR_R = 0.22                   # 减速电机半径
JOINT_STEP_Z = 1.2               # 池壁水平施工缝步距（ds：每 1.2m 一道）
JOINT_WALK_N = 36                # 走道径向分缝道数（≈3.6m 弧距——3.5m 规范近似）
JOINT_R_OUT = R_OUTER + 0.01     # 条带外凸量（避 z-fight）


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


def _sweep_ring(name: str, profile: list[tuple[float, float]],
                token: str) -> bpy.types.Object:
    """闭合截面环向扫掠（堰槽 U 形截面——水密环体）。

    profile=(r,z) 闭合回路 **CCW**（r→右 z→上视图正面积）；面绕序
    (v(i,s), v(j,s), v(j,s+1), v(i,s+1)) 与 _ring_slab 外柱面同构
    （外法线+有符号体积正——normalize 快检锚）。
    """
    n = len(profile)
    verts: list[Vector] = []
    for r, z in profile:
        verts.extend(_ring(r, z))
    faces: list[tuple[int, ...]] = []
    for s in range(n):
        s2 = (s + 1) % n
        for i in range(SEGMENTS):
            j = (i + 1) % SEGMENTS
            faces.append((s * SEGMENTS + i, s * SEGMENTS + j,
                          s2 * SEGMENTS + j, s2 * SEGMENTS + i))
    return _add_mesh(name, verts, faces, token)


def _weir_plate(name: str, token: str) -> bpy.types.Object:
    """齿形堰板（环形薄板+隔齿交替高低的齿口——水密）。

    顶缘 z 逐分段交替 TOOTH/NOTCH=三角齿口；四条带面（内/外/顶/底）
    绕序沿 _ring_slab 内柱面/外柱面/顶环/底环同构。
    """
    r_out = WEIR_R_IN + WEIR_THICK
    z_top = [WEIR_Z_TOOTH if i % 2 == 0 else WEIR_Z_NOTCH for i in range(SEGMENTS)]
    ib = _ring(WEIR_R_IN, WEIR_Z_BOT)
    ob = _ring(r_out, WEIR_Z_BOT)
    it, ot = [], []
    for i in range(SEGMENTS):
        c, s = math.cos(2 * math.pi * i / SEGMENTS), math.sin(2 * math.pi * i / SEGMENTS)
        it.append(Vector((WEIR_R_IN * c, WEIR_R_IN * s, z_top[i])))
        ot.append(Vector((r_out * c, r_out * s, z_top[i])))
    verts = ib + ob + it + ot  # 环序：ib(0)/ob(b)/it(2b)/ot(3b)
    b = SEGMENTS
    faces: list[tuple[int, ...]] = []
    for i in range(SEGMENTS):
        j = (i + 1) % SEGMENTS
        faces.append((2 * b + i, 2 * b + j, j, i))          # 内柱面 −r（it↔ib）
        faces.append((b + i, b + j, 3 * b + j, 3 * b + i))  # 外柱面 +r（ob↔ot）
        faces.append((3 * b + i, 3 * b + j, 2 * b + j, 2 * b + i))  # 顶齿带 +z（ot→it）
        faces.append((i, j, b + j, b + i))                  # 底环 −z（ib→ob）
    return _add_mesh(name, verts, faces, token)


def _cyl_geo(radius: float, z_bottom: float, z_top: float,
             center_xy: tuple[float, float] = (0.0, 0.0),
             segments: int = SEGMENTS) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """闭合圆柱几何（侧柱面+底/顶扇——水密；返回几何便于多件合并）。"""
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


def _box_geo(center: tuple[float, float, float],
             size: tuple[float, float, float]) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """轴对齐盒几何（八顶点六外法线面——返回几何便于多件合并）。"""
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


def _rod_geo(p0: Vector, p1: Vector, radius: float,
             segments: int = 12) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """任意轴向圆杆几何（侧柱面+两端帽——水密；桁架弦/腹杆）。

    基 (u,v,d) 右手系：环序 θ 增 CCW（自 +d 视）+ p0→p1 沿 d——
    绕序与 _cyl_geo z 轴柱同构（外法线）。
    """
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


def _merged(name: str, parts: list[tuple[list[Vector], list[tuple[int, ...]]]],
            token: str) -> bpy.types.Object:
    """多闭包件合并单网格（各件水密闭包→并集自然边入射恰二面）。"""
    verts: list[Vector] = []
    faces: list[tuple[int, ...]] = []
    for part_verts, part_faces in parts:
        base = len(verts)
        verts.extend(part_verts)
        faces.extend(
            tuple(base + idx for idx in face) for face in part_faces)
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
        naming.build_name(FAMILY, "shell", "wall"), "concrete_wall")
    _under(shell_root, shell)

    walkway = _ring_slab(
        naming.build_name(FAMILY, "trim", "walkway"),  # 缺省掩码=水平双向
        R_OUTER, R_OUTER + WALK_WIDTH, H_TOP, H_TOP + WALK_THICK, "concrete_walk")
    _under(trim_root, walkway)
    rails = [_torus(
        naming.build_name(FAMILY, "trim", f"handrail_{int(h * 100)}"),
        RAIL_RADIUS, H_TOP + WALK_THICK + h, "steel_rail") for h in RAIL_HEIGHTS]
    for rail in rails:
        _under(trim_root, rail)

    # 迭代二·堰槽+堰板（交接 §一.1 优先 1——周边出水槽随壳水平缩放[trim
    # 缺省掩码]；堰槽 U 形闭截面=槽宽 0.3×槽体总深 0.4（腔净深 0.32——
    # 底板厚 0.08），实心域=[la_in,la_out]×[3.6,4.0] 矩形减槽腔；
    # la_out 内收 0.01 避与壳内壁共面 z-fight——门一 W3）
    la_in, la_out = LAUNDER_R_IN, R_INNER - 0.01  # 槽腔=[la_in+0.05, la_out−0.05]
    launder_profile = [
        (la_in, H_TOP),                        # 内壁外顶
        (la_in, LAUNDER_Z_BOT),                # 内壁外底 ↓
        (la_out, LAUNDER_Z_BOT),               # 底连续 →（外壁底）
        (la_out, H_TOP),                       # 外壁顶 ↑（贴池内壁留缝）
        (la_out - 0.05, H_TOP),                # 外壁内顶 ←
        (la_out - 0.05, LAUNDER_Z_BOT + 0.08),  # 槽腔底面 ↓
        (la_in + 0.05, LAUNDER_Z_BOT + 0.08),  # 槽腔底面 ←
        (la_in + 0.05, H_TOP),                 # 内壁内面 ↑（闭回路）
    ]
    launder = _sweep_ring(
        naming.build_name(FAMILY, "trim", "weir_launder"),
        launder_profile, "concrete_coping")
    _under(trim_root, launder)
    weir = _weir_plate(
        naming.build_name(FAMILY, "trim", "weir_plate"), "steel_rail")
    _under(trim_root, weir)

    well = _add_mesh(
        naming.build_name(FAMILY, "equip", "center_well"),
        *_cyl_geo(WELL_D / 2, WALL, WELL_TOP), token="steel_well")
    _under(equip_root, well)

    # 迭代二·桁架化刮泥机桥（优先 2：三角桁架=下双弦+上单弦+ Warren 腹杆
    # +桥面走道板；单网格合并——equip bridge 规格链[templateFeature=跨径]
    # 不变，AABB 随桁架实形由扫描层实时派生）
    chord_z = BRIDGE_CLEAR - TRUSS_CHORD_R
    deck_z = chord_z + TRUSS_CHORD_R + DECK_THICK / 2  # 走道板贴下弦顶
    top_z = BRIDGE_CLEAR + TRUSS_TOP_UP
    bridge_parts: list[tuple[list[Vector], list[tuple[int, ...]]]] = []
    for y in (-TRUSS_HALF_W, TRUSS_HALF_W):  # 下双弦
        bridge_parts.append(_rod_geo(
            Vector((TRUSS_X0, y, chord_z)), Vector((TRUSS_X1, y, chord_z)),
            TRUSS_CHORD_R))
    bridge_parts.append(_rod_geo(  # 上单弦
        Vector((TRUSS_X0, 0.0, top_z)), Vector((TRUSS_X1, 0.0, top_z)),
        TRUSS_CHORD_R))
    panel = (TRUSS_X1 - TRUSS_X0) / TRUSS_PANELS
    for k in range(TRUSS_PANELS):  # Warren 腹杆（左右成对 V 形）
        x0 = TRUSS_X0 + k * panel
        x1 = x0 + panel
        for y in (-TRUSS_HALF_W, TRUSS_HALF_W):
            bridge_parts.append(_rod_geo(
                Vector((x0, y, chord_z)), Vector((x1, 0.0, top_z)),
                TRUSS_CHORD_R))
    bridge_parts.append(_box_geo(  # 桥面走道板（格栅平铺近似）
        ((TRUSS_X0 + TRUSS_X1) / 2, 0.0, deck_z),
        (TRUSS_X1 - TRUSS_X0, BRIDGE_WIDTH, DECK_THICK)))
    bridge = _merged(
        naming.build_name(FAMILY, "equip", "bridge"), bridge_parts, "steel_bridge")
    _under(equip_root, bridge)

    # 迭代二·驱动装置细节（优先 4：平台+电机座+减速电机——单网格并入
    # equip bridge_drive[平台径=templateFeature 1.6 数据链不变]）
    drive_parts = [
        _cyl_geo(0.8, BRIDGE_CLEAR, BRIDGE_CLEAR + 0.3, segments=24),  # 平台
        _box_geo((0.0, 0.0, BRIDGE_CLEAR + 0.3 + MOTOR_SEAT / 4),  # 电机座
                 (MOTOR_SEAT, MOTOR_SEAT, MOTOR_SEAT / 2)),
        _cyl_geo(MOTOR_R, BRIDGE_CLEAR + 0.3 + MOTOR_SEAT / 2,
                 BRIDGE_CLEAR + 0.3 + MOTOR_SEAT / 2 + 0.6, segments=16),
    ]
    drive = _merged(
        naming.build_name(FAMILY, "equip", "bridge_drive"),
        drive_parts, "steel_drive")
    _under(equip_root, drive)

    # 迭代二·撇渣装置（优先 3：半桥外缘撇渣管+撇渣板——trim 附件随壳）
    scum_parts = [
        _box_geo((TRUSS_X1 - SCUM_TUBE_L / 2 - 0.3, BRIDGE_WIDTH / 2 + 0.1,
                  BRIDGE_CLEAR + 0.15), (SCUM_TUBE_L, 0.12, 0.12)),  # 撇渣管
        _box_geo((TRUSS_X1 - SCUM_TUBE_L / 2 - 0.3, BRIDGE_WIDTH / 2 + 0.1,
                  BRIDGE_CLEAR - 0.25), (SCUM_TUBE_L, 0.04, 0.4)),   # 撇渣板
    ]
    scum = _merged(
        naming.build_name(FAMILY, "trim", "scum_skimmer"),
        scum_parts, "steel_rail")
    _under(trim_root, scum)

    # 立柱原型：几何本地居中（z 0→POST_H），对象平移=节点 TRS（P7——
    # instanceLayout 读原型基座位姿分布环周；σ=𝟙 几何不缩放）
    post_verts, post_faces = _cyl_geo(0.025, 0.0, POST_H, segments=12)
    post = _add_mesh(
        naming.build_name(FAMILY, "inst", "rail_post"),
        post_verts, post_faces, "steel_rail")
    post.location = (RAIL_RADIUS, 0.0, H_TOP + WALK_THICK)
    _under(inst_root, post)

    # 迭代二·池壁分缝（优先 5：__nc 单面条带——缝色 #8E8E88 材质带；
    # 512 可见性权衡取面带而非几何线槽[ds]）
    band_verts: list[Vector] = []
    band_faces: list[tuple[int, ...]] = []
    for n, z in enumerate([JOINT_STEP_Z, 2 * JOINT_STEP_Z, 3 * JOINT_STEP_Z]):
        base = len(band_verts)
        band_verts.extend(_ring(JOINT_R_OUT, z))
        band_verts.extend(_ring(JOINT_R_OUT, z + 0.04))
        for i in range(SEGMENTS):
            j = (i + 1) % SEGMENTS
            band_faces.append((base + i, base + j,
                               base + SEGMENTS + j, base + SEGMENTS + i))  # +r
    wall_joints = _add_mesh(
        naming.build_name(FAMILY, "trim", "wall_joints", nc=True),
        band_verts, band_faces, "joint")
    _under(trim_root, wall_joints)
    walk_top = H_TOP + WALK_THICK + 0.005
    joint_verts: list[Vector] = []
    joint_faces: list[tuple[int, ...]] = []
    for k in range(JOINT_WALK_N):
        theta = 2 * math.pi * k / JOINT_WALK_N
        half = 0.01 / 20.8  # 缝宽 0.02 的半角（走道中径≈20.8）
        r0, r1 = R_OUTER + 0.05, R_OUTER + WALK_WIDTH - 0.05
        base = len(joint_verts)
        joint_verts.extend([
            Vector((r0 * math.cos(theta - half), r0 * math.sin(theta - half), walk_top)),
            Vector((r0 * math.cos(theta + half), r0 * math.sin(theta + half), walk_top)),
            Vector((r1 * math.cos(theta + half), r1 * math.sin(theta + half), walk_top)),
            Vector((r1 * math.cos(theta - half), r1 * math.sin(theta - half), walk_top)),
        ])
        joint_faces.append((base, base + 3, base + 2, base + 1))  # +z（CCW）
    walkway_joints = _add_mesh(
        naming.build_name(FAMILY, "trim", "walkway_joints", nc=True),
        joint_verts, joint_faces, "joint")
    _under(trim_root, walkway_joints)

    # 平滑着色（柱面/环面/杆件——锐边自动保持[盒类 90° 恒锐]；35°=12 段
    # 杆件面夹角 30° 入平滑带；失败退平直 shading 无害）
    for obj in (shell, walkway, well, launder, weir, bridge, drive, scum, *rails):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
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

    # 归一校验（§2 AABB 对拍+水密快检——违例即中止导出面；__nc 单面
    # 装饰件[分缝条带]不入水密报告——按 §10 标记豁免，CI 面同口径）
    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    report = [normalize.mesh_report(o) for o in
              (shell, walkway, *rails, launder, weir, well, bridge, drive,
               scum, post)]
    print("[NORMALIZE]")
    for line in report:
        print("  " + line)
    for nc_obj in (wall_joints, walkway_joints):
        print(f"  {nc_obj.name}: [nc] verts={len(nc_obj.data.vertices)} "
              f"tris≈{sum(len(p.vertices) - 2 for p in nc_obj.data.polygons)}")

    out = Path(__file__).resolve().parent / "build" / "clarifier_radial.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
