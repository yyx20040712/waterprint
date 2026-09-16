"""旋流沉砂池族参数化模板建模（5.6×3.0×3.3——批4 第一窗）。

输入:  bpy 无头（``blender -b --factory-startup -P build_grit.py``）
输出:  build/grit_vortex.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三；取数锚
  =server 最小图 municipal_chenshachi pool_wall box 5.6×3.0×3.3
  （l_straight 直线段×d 圆池径×h_total 总深）[.workflow/b4-window1/
  anchor-sizes.md]）：
  - 构型：中央圆柱沉砂池（D3.0 厚壁环筒——局部 ring_geo 单拓扑水密，
    辐流 _thick_cup 同构独立实现）+直线进出水渠（两侧对接 x=±2.8）
    +砂斗锥（水下 trim）+池顶走道环+栏杆+搅砂机 equip；
  - shell=三件组合（圆筒+双渠厚壁 U 槽）——组合 AABB 对拍 templateSize
    （本脚本内联组合断言——normalize.assert_shell_aabb 为单件版）；
  - poolGroup：cell 域（n 池组方阵——countParam=n gap=1.0）。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import naming
from lib import normalize
from lib import rectbuild as rb

# ── 模板常量（registry 同源声明——改值须与 registry.json 同窗） ─────────
FAMILY = "grit"                 # 命名前缀（registry family=grit_vortex）
TEMPLATE_SIZE = (5.6, 3.0, 3.3)  # L0/W0/H0（server 最小图恒等锚）
WALL = 0.18
H_TOP = TEMPLATE_SIZE[2]        # 3.3
HX, HY = TEMPLATE_SIZE[0] / 2, TEMPLATE_SIZE[1] / 2
POOL_R = TEMPLATE_SIZE[1] / 2 - WALL   # 圆池内净半径 1.32（外径 3.0）
POOL_R_OUT = TEMPLATE_SIZE[1] / 2      # 圆池外半径 1.5（=W0/2）

# 渠道（直线进出水——d_upper 渠宽档 0.6，渠高低于池顶）
CHANNEL_W = 0.6
CHANNEL_H = 2.6
# 渠端贴圆筒**外壁**留 5mm 缝（门一 W4：渠端嵌入环壁 0.09m 跨件体积
# 重叠实拦——端头 x=POOL_R_OUT+0.005 相接，微缝<焊接容差各件独立闭合）
CHANNEL_LEN = HX - POOL_R_OUT - 0.005
WALK_WIDTH = 0.7
WALK_THICK = 0.10
RAIL_TUBE = 0.025
RAIL_HEIGHTS = (1.1, 0.6)
RAIL_INSET = 0.25
HOPPER_H = 0.9                  # 砂斗锥高（h4 档）
WATER_LEVEL = 2.4               # PNG 专用水面（h2 水深档）


def _under(parent: bpy.types.Object, child: bpy.types.Object) -> None:
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def ring_geo(r_out: float, r_in: float, z_bottom: float, z_top: float,
             segments: int = 24) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """厚壁圆杯（外柱面+底面全盘+内腔壁+内底全盘+顶环沿——水密单拓扑；
    辐流 _thick_cup 同构独立实现：双盘封底无裙面 T 连接）。

    绕序=外法线（外柱 +r/底盘 −z/顶环 +z/内壁 −r/内底 +z）。
    """
    n = segments
    ang = lambda i: 2 * math.pi * i / n  # noqa: E731 —— 角度参数化
    o_bot = [Vector((r_out * math.cos(ang(i)), r_out * math.sin(ang(i)), z_bottom))
             for i in range(n)]
    o_top = [Vector((r_out * math.cos(ang(i)), r_out * math.sin(ang(i)), z_top))
             for i in range(n)]
    i_top = [Vector((r_in * math.cos(ang(i)), r_in * math.sin(ang(i)), z_top))
             for i in range(n)]
    i_bot = [Vector((r_in * math.cos(ang(i)), r_in * math.sin(ang(i)),
                     z_bottom + WALL)) for i in range(n)]
    center_bot, center_floor = 4 * n, 4 * n + 1
    verts = o_bot + o_top + i_top + i_bot + [Vector((0.0, 0.0, z_bottom)),
                                             Vector((0.0, 0.0, z_bottom + WALL))]
    faces: list[tuple[int, ...]] = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))                       # 外柱面 +r
        faces.append((center_bot, j, i))                         # 底面全盘 −z
        faces.append((n + i, n + j, 2 * n + j, 2 * n + i))       # 顶环沿 +z
        faces.append((2 * n + i, 2 * n + j, 3 * n + j, 3 * n + i))  # 内腔壁 −r
        faces.append((center_floor, 3 * n + i, 3 * n + j))       # 内底全盘 +z
    return verts, faces


def cone_geo(r_top: float, r_bot: float, z_top: float, z_bot: float,
             segments: int = 16) -> tuple[list[Vector], list[tuple[int, ...]]]:
    """截锥（砂斗——锥面+底/顶全环扇；r_bot≤ε 退化为全锥无底）。"""
    top = [Vector((r_top * math.cos(2 * math.pi * i / segments),
                   r_top * math.sin(2 * math.pi * i / segments), z_top))
           for i in range(segments)]
    bot = [Vector((r_bot * math.cos(2 * math.pi * i / segments),
                   r_bot * math.sin(2 * math.pi * i / segments), z_bot))
           for i in range(segments)]
    verts = top + bot
    n = segments
    c_top, c_bot = len(verts), len(verts) + 1
    verts = verts + [Vector((0.0, 0.0, z_top)), Vector((0.0, 0.0, z_bot))]
    faces: list[tuple[int, ...]] = []
    for i in range(n):
        j = (i + 1) % n
        if r_bot > 1e-6:
            faces.append((i, j, n + j, n + i))        # 锥面外法线
        else:
            faces.append((n + i, n + j, i))           # 全锥侧面三角
    if r_bot > 1e-6:
        for i in range(n):
            j = (i + 1) % n
            faces.append((c_bot, n + j, n + i))       # 底全环扇 −z
            faces.append((c_top, i, j))               # 顶全环扇 +z
    return verts, faces


def u_channel_geo(x_center: float, length: float, width: float, height: float,
                  wall: float) -> list[tuple[list[Vector], list[tuple[int, ...]]]]:
    """厚壁 U 形渠（底板+双壁三盒闭包——**壁底留 5mm 微缝**：面贴面构造
    在 CI 焊接步产生 T 连接[实拦两轮：体积重叠版/贴邻版]，微缝<视觉
    不可辨>焊接容差 ε≈0.001m，各件独立闭合流形；与圆筒壁搭接对接）。"""
    seam = 0.005
    hx = length / 2
    hy = width / 2
    return [
        rb.box_geo((x_center, 0.0, wall / 2), (length, width, wall)),      # 底板
        rb.box_geo((x_center, -hy + wall / 2, wall + seam + (height - wall - seam) / 2),
                   (length, wall, height - wall - seam)),                  # 北壁（底缝）
        rb.box_geo((x_center, hy - wall / 2, wall + seam + (height - wall - seam) / 2),
                   (length, wall, height - wall - seam)),                  # 南壁
    ]


def build() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    shell_root = bpy.data.objects.new("shell", None)
    trim_root = bpy.data.objects.new("trim", None)
    equip_root = bpy.data.objects.new("equip", None)
    inst_root = bpy.data.objects.new("inst", None)
    for root in (shell_root, trim_root, equip_root, inst_root):
        scene.collection.objects.link(root)

    # shell 三件：圆筒（居中）+进/出水渠（两端对接）
    pool = rb.add_mesh(
        naming.build_name(FAMILY, "shell", "pool_cylinder"),
        *ring_geo(POOL_R_OUT, POOL_R, 0.0, H_TOP)[:2], token="concrete_wall")
    _under(shell_root, pool)

    chan_in = rb.merged(
        naming.build_name(FAMILY, "shell", "channel_in"),
        u_channel_geo(-(POOL_R_OUT + 0.005 + CHANNEL_LEN / 2),
                      CHANNEL_LEN, CHANNEL_W + 2 * WALL, CHANNEL_H, WALL),
        "concrete_wall")
    _under(shell_root, chan_in)
    chan_out = rb.merged(
        naming.build_name(FAMILY, "shell", "channel_out"),
        u_channel_geo(POOL_R_OUT + 0.005 + CHANNEL_LEN / 2,
                      CHANNEL_LEN, CHANNEL_W + 2 * WALL, CHANNEL_H, WALL),
        "concrete_wall")
    _under(shell_root, chan_out)

    # trim：砂斗锥（池内水下——截锥；缩略图外视被池壁遮挡属物理事实，
    # 判读面归剖切增强批）+**环形走道+圆环栏杆**（圆池制——辐流
    # _ring_slab/_torus 同构；实拦：rect 环板错接圆柱池）
    hopper = rb.add_mesh(
        naming.build_name(FAMILY, "trim", "sand_hopper"),
        *cone_geo(POOL_R - 0.10, 0.25, WALL + HOPPER_H, WALL)[:2],
        token="concrete_wall")
    _under(trim_root, hopper)

    def _ring(r: float, z: float) -> list[Vector]:
        return [Vector((r * math.cos(2 * math.pi * i / 24),
                        r * math.sin(2 * math.pi * i / 24), z))
                for i in range(24)]

    def ring_slab(name: str, r_in: float, r_out: float,
                  z0: float, z1: float, token: str) -> bpy.types.Object:
        i_bot, i_top = _ring(r_in, z0), _ring(r_in, z1)
        o_bot, o_top = _ring(r_out, z0), _ring(r_out, z1)
        verts = i_bot + i_top + o_bot + o_top
        n = 24
        faces = []
        for i in range(n):
            j = (i + 1) % n
            faces.append((2 * n + i, 2 * n + j, 3 * n + j, 3 * n + i))  # 外柱 +r
            faces.append((3 * n + i, 3 * n + j, n + j, n + i))          # 顶环 +z
            faces.append((n + i, n + j, j, i))                          # 内柱 −r
            faces.append((i, j, 2 * n + j, 2 * n + i))                  # 底环 −z
        return rb.add_mesh(name, verts, faces, token)

    def torus_rail(name: str, r: float, z: float, tube: float,
                   token: str) -> bpy.types.Object:
        # 圆环栏杆=真圆环面（24 主环×6 截面——辐流 _torus 同构独立实现；
        # 截面圆在(径向 r̂, ẑ)平面[法向=切向 t̂]——首版误用切向平面=圆沿
        # 自身平面内平移的零体积退化面[实测 V≈0 实拦]；折线杆版另有折段
        # 正反射集中[峰值 96.9%]——真圆环连续曲率先例制）
        seg_r, seg_c = 24, 6
        verts: list[Vector] = []
        for i in range(seg_r):
            theta = 2 * math.pi * i / seg_r
            cx, cy = r * math.cos(theta), r * math.sin(theta)
            rx, ry = math.cos(theta), math.sin(theta)   # 径向单位向量
            for j in range(seg_c):
                phi = 2 * math.pi * j / seg_c
                verts.append(Vector((
                    cx + rx * math.cos(phi) * tube,
                    cy + ry * math.cos(phi) * tube,
                    z + math.sin(phi) * tube)))
        faces: list[tuple[int, ...]] = []
        for i in range(seg_r):
            for j in range(seg_c):
                a = i * seg_c + j
                b = ((i + 1) % seg_r) * seg_c + j
                c = ((i + 1) % seg_r) * seg_c + (j + 1) % seg_c
                d = i * seg_c + (j + 1) % seg_c
                faces.append((a, b, c, d))   # 辐流 _sweep 同构绕序（外法线）
        return rb.add_mesh(name, verts, faces, token)

    walkway = ring_slab(
        naming.build_name(FAMILY, "trim", "walkway"),
        POOL_R_OUT, POOL_R_OUT + WALK_WIDTH, H_TOP, H_TOP + WALK_THICK,
        "concrete_walk")
    _under(trim_root, walkway)
    rail_r = POOL_R_OUT + WALK_WIDTH - RAIL_INSET
    rails = [torus_rail(
        naming.build_name(FAMILY, "trim", f"handrail_{int(h * 100)}"),
        rail_r, H_TOP + WALK_THICK + h, RAIL_TUBE, "steel_rail")
        for h in RAIL_HEIGHTS]
    for rail in rails:
        _under(trim_root, rail)

    # equip：旋流搅砂机（池中心——立轴+顶驱动头+水下叶轮长臂×4；
    # 特征高=驱动头顶实测 3.81=H_TOP+0.30+0.42/2[门一 W3：
    # 幻影轴高 3.95 死变量实拦——恒等锚=几何实测值唯一声明源]）
    agitator = rb.merged(
        naming.build_name(FAMILY, "equip", "agitator"),
        [
            rb.box_geo((0.0, 0.0, H_TOP + 0.30), (0.5, 0.5, 0.42)),        # 驱动头
            rb.rod_geo(Vector((0.0, 0.0, H_TOP + 0.09)), Vector((0.0, 0.0, 0.55)),
                       0.05, segments=8),                                  # 立轴
            rb.box_geo((0.0, 0.0, 0.45), (0.16, 0.16, 0.50)),              # 减速机座
        ] + [
            rb.rod_geo(Vector((0.0, 0.0, 0.42)),
                       Vector((r * math.cos(a), r * math.sin(a), 0.30)),
                       0.035, segments=6)
            for i, a in enumerate((0.0, math.pi / 2, math.pi, 3 * math.pi / 2))
            for r in (POOL_R - 0.25,)
        ], "steel_drive")
    _under(equip_root, agitator)

    for obj in (pool, chan_in, chan_out, hopper, walkway):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
        except (RuntimeError, TypeError):
            pass

    # PNG 专用水面（preview_only——圆池内；周界序 CCW +z 法线）
    from lib import materials
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    water_mesh = bpy.data.meshes.new("preview_water_0")
    seg = 24
    water_mesh.from_pydata(
        [Vector((POOL_R * math.cos(2 * math.pi * i / seg),
                 POOL_R * math.sin(2 * math.pi * i / seg), WATER_LEVEL))
         for i in range(seg)], [],
        [(0, i, (i + 1) % seg) for i in range(seg)],
    )
    water_mesh.validate()
    water_mesh.update()
    water = bpy.data.objects.new("preview_water_0", water_mesh)
    water.data.materials.append(materials.ensure_material("water_surface", alpha=0.85))
    preview.objects.link(water)

    # 归一校验（组合 AABB——shell 三件世界外接盒并集对拍 templateSize）
    print("[NORMALIZE]")
    l0, w0, h0 = TEMPLATE_SIZE
    mins = [1e9] * 3
    maxs = [-1e9] * 3
    for obj in (pool, chan_in, chan_out):
        for line in normalize.mesh_report(obj):
            print("  " + line)
        for v in obj.bound_box:
            w = obj.matrix_world @ Vector(v)
            for k in range(3):
                mins[k] = min(mins[k], w[k])
                maxs[k] = max(maxs[k], w[k])
    expect_min = (-l0 / 2, -w0 / 2, 0.0)
    expect_max = (l0 / 2, w0 / 2, h0)
    tol = 0.02
    for k, (axis, g0, g1, w0_, w1) in enumerate(
            zip("xyz", mins, maxs, expect_min, expect_max)):
        if abs(g0 - w0_) > tol or abs(g1 - w1) > tol:
            raise ValueError(
                f"组合壳 AABB {axis}=[{g0:.4f},{g1:.4f}] 期望 [{w0_},{w1}]"
                f"（templateSize={TEMPLATE_SIZE}——spec §2 归一基准）")
    print(f"  [组合 AABB] 过（{mins} ~ {maxs}）")
    for obj in (hopper, walkway, agitator, *rails):
        for line in normalize.mesh_report(obj):
            print("  " + line)

    out = Path(__file__).resolve().parent / "build" / "grit_vortex.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
