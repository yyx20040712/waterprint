"""CASS 序批族参数化模板建模（48.5×19.5×5.5——批3 段二·五步门③）。

输入:  bpy 无头（``blender -b --factory-startup -P build_cass.py``）
输出:  build/cass_batch.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三 CASS 档位表
  [段二建模前调研 2026-09-13 落档]；取数锚=server 最小图 34760.7 m³/d
  单 box 48.5×19.5×5.5——交接「取数节点=单 box，分格表达归 trim/equip」）：
  - 坐标：Blender z-up，原点=池底中心，米制；templateSize 48.5×19.5×5.5
    （shell AABB=[−24.25,24.25]×[−9.75,9.75]×[0,5.5]）；
  - 沿池长前部预反应区（生物选择区≈池长 14%——隔墙带上/下段中留
    1.2m 过水孔）+主反应区；中隔墙分 2 格并联（格宽≈9.5m 档）；
  - 周圈走道外挑 1.6+双栏杆环（规范定值 1.1/0.6）；
  - inst：滗水器原型（line_z 沿宽轴均布——数量=场景图 n_decant
    [CA-F15 整台 ceil，golden=2]）+曝气头原型（grid 0.8m——场景
    instance_counts 无键=skipped+登记[P7]）+栏杆立柱原型（rect）；
  - equip 预反应区搅拌器安装架（恒等锚 2.425=0.05×48.5）；
  - 水面层 preview_only（仅 PNG 消费——glb 导出面剔除）。
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
FAMILY = "cass"                  # 命名前缀（registry family=cass_batch）
TEMPLATE_SIZE = (48.5, 19.5, 5.5)  # L0/W0/H0（server 最小图恒等锚）
WALL = 0.45
H_TOP = TEMPLATE_SIZE[2]         # 5.5
HX, HY = TEMPLATE_SIZE[0] / 2, TEMPLATE_SIZE[1] / 2
IX, IY = HX - WALL, HY - WALL
WALK_WIDTH = 1.6
WALK_THICK = 0.12
RAIL_TUBE = 0.03
RAIL_HEIGHTS = (1.1, 0.6)
RAIL_INSET = 0.35
WATER_LEVEL = 4.75               # PNG 专用水面（曝气期满水位档——总深-超高）

# 预反应区（生物选择区≈池长 14%）+中隔墙（2 格）
SELECT_X = -HX + 7.0             # 预反应区隔墙中心线（7m≈14.4%）
SELECT_T = 0.35
SELECT_HOLE_Z0, SELECT_HOLE_Z1 = 0.95, 2.15   # 过水孔段（中留 1.2m）
DIVIDER_T = 0.3                  # 中隔墙厚（2 格并联）
MIXER_SPAN = 2.425               # 搅拌器安装架跨度（=0.05×48.5 恒等锚）
DECANT_X = HX - WALL - 2.2       # 滗水器安装线（主反应区末端内侧）
POST_H = RAIL_HEIGHTS[0]
AERATOR_D = 0.30
JOINT_STEP_Z = 1.2


def _under(parent: bpy.types.Object, child: bpy.types.Object) -> None:
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


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

    shell = rb.thick_rect_pool(
        naming.build_name(FAMILY, "shell", "wall"),
        TEMPLATE_SIZE[0], TEMPLATE_SIZE[1], H_TOP, WALL, "concrete_wall")
    _under(shell_root, shell)

    # 预反应区隔墙（上/下两段——中留过水孔）
    sel_parts = [
        rb.box_geo((SELECT_X, 0.0, (WALL + SELECT_HOLE_Z0) / 2),
                   (SELECT_T, 2 * IY, SELECT_HOLE_Z0 - WALL)),   # 下坎
        rb.box_geo((SELECT_X, 0.0, (SELECT_HOLE_Z1 + H_TOP) / 2),
                   (SELECT_T, 2 * IY, H_TOP - SELECT_HOLE_Z1)),  # 上墙
    ]
    selector = rb.merged(
        naming.build_name(FAMILY, "trim", "selector_wall"),
        sel_parts, "concrete_wall")
    _under(trim_root, selector)

    # 中隔墙（2 格并联——全墙到顶）
    divider = rb.add_mesh(
        naming.build_name(FAMILY, "trim", "divider_wall"),
        *rb.box_geo((0.0, 0.0, (WALL + H_TOP) / 2),
                    (2 * (HX - WALL) - 0.01, DIVIDER_T, H_TOP - WALL))[:2],
        token="concrete_wall")
    _under(trim_root, divider)

    # 周圈走道+双栏杆环
    walkway = rb.rect_walkway(
        naming.build_name(FAMILY, "trim", "walkway"),
        2 * (HX + WALK_WIDTH), 2 * (HY + WALK_WIDTH),
        TEMPLATE_SIZE[0], TEMPLATE_SIZE[1],
        H_TOP, H_TOP + WALK_THICK, "concrete_walk")
    _under(trim_root, walkway)
    rail_hx = HX + WALK_WIDTH - RAIL_INSET
    rail_hy = HY + WALK_WIDTH - RAIL_INSET
    rails = [rb.rect_rail(
        naming.build_name(FAMILY, "trim", f"handrail_{int(h * 100)}"),
        rail_hx, rail_hy, H_TOP + WALK_THICK + h, RAIL_TUBE, "steel_rail")
        for h in RAIL_HEIGHTS]
    for rail in rails:
        _under(trim_root, rail)

    # equip：预反应区搅拌器安装架（立柱+横梁+导杆+潜水电机轮廓——
    # 几何直接世界位构造[TRS=0，equip 渲染不剥 TRS——辐流 equip 同制]）
    mx = (-HX + SELECT_X - SELECT_T / 2) / 2    # 预反应区中心
    mixer = rb.merged(
        naming.build_name(FAMILY, "equip", "mixer_mount"),
        [
            rb.box_geo((mx - MIXER_SPAN / 2 + 0.1, 0.0, H_TOP + 0.55),
                       (0.2, 0.2, 1.1)),
            rb.box_geo((mx + MIXER_SPAN / 2 - 0.1, 0.0, H_TOP + 0.55),
                       (0.2, 0.2, 1.1)),
            rb.box_geo((mx, 0.0, H_TOP + 1.16),
                       (MIXER_SPAN, 0.16, 0.12)),
            rb.rod_geo(Vector((mx, 0.0, H_TOP + 1.1)),
                       Vector((mx, 0.0, H_TOP - 2.0)), 0.05, segments=8),
            rb.cyl_geo(0.20, H_TOP - 2.2, H_TOP - 1.1, (mx, 0.0), segments=16),
        ], "steel_bridge")
    _under(equip_root, mixer)

    # inst：滗水器原型（旋转撇水悬臂桁架+堰槽+撇渣板——**本地化建模**：
    # x/z 平面居中+竖直 0 起（门一 W2 勘误：首版几何竖直 4.3~5.35 未
    # 本地化——strippedClone 剥 TRS 后 baseY 双偏移悬空）；TRS=(安装线,
    # 0, boom_z) 承载安装高度；line_z 沿宽轴——数量=场景图 n_decant
    # [CA-F15 整台 ceil]）
    decant = rb.merged(
        naming.build_name(FAMILY, "inst", "decant"),
        [
            # 悬臂桁架（下弦+上弦+腹杆三根——6m 悬伸；z 自 0 起）
            rb.rod_geo(Vector((-3.47, 0.0, 0.0)),
                       Vector((2.53, 0.0, 0.0)), 0.09, segments=8),
            rb.rod_geo(Vector((-3.47, 0.0, 0.7)),
                       Vector((2.13, 0.0, 0.7)), 0.09, segments=8),
            rb.rod_geo(Vector((-3.47, 0.0, 0.0)),
                       Vector((-0.67, 0.0, 0.7)), 0.06, segments=8),
            rb.rod_geo(Vector((-0.67, 0.0, 0.7)),
                       Vector((2.13, 0.0, 0.0)), 0.06, segments=8),
            rb.rod_geo(Vector((-0.67, 0.0, 0.0)),
                       Vector((2.13, 0.0, 0.7)), 0.06, segments=8),
            # 撇水堰槽（悬臂末端——开口盒；底 -0.3 下探）
            rb.box_geo((2.9, 0.0, -0.3), (1.2, 4.0, 0.1)),
            rb.box_geo((2.9, -2.0, -0.05), (1.2, 0.1, 0.5)),
            rb.box_geo((2.9, 2.0, -0.05), (1.2, 0.1, 0.5)),
            rb.box_geo((2.35, 0.0, -0.05), (0.1, 4.0, 0.5)),
            # 撇渣挡板（堰槽外沿）
            rb.box_geo((3.5, 0.0, 0.05), (0.06, 4.0, 0.45)),
        ], "steel_bridge")
    # TRS：x=堰槽中心 2.9 落在 DECANT_X；z=boom_z 安装高（门二 P1 勘误：
    # 渲染 y 锚=AABB 中心[4.25+5.39]/2≈4.82 非 boom_z 4.6——堰槽下探
    # 0.35 使几何中心略低于安装线，几何中心语义下自然闭合）
    decant.location = (DECANT_X - 2.9, 0.0, H_TOP - 0.9)
    _under(inst_root, decant)

    aer_parts = [
        rb.cyl_geo(AERATOR_D / 2, 0.0, 0.06, segments=12),
        rb.rod_geo(Vector((0.0, 0.0, 0.06)), Vector((0.0, 0.0, 0.26)),
                   0.03, segments=8),
    ]
    aerator = rb.merged(
        naming.build_name(FAMILY, "inst", "aerator"), aer_parts, "steel_rail")
    aerator.location = (0.0, 0.0, WALL)
    _under(inst_root, aerator)

    post = rb.add_mesh(
        naming.build_name(FAMILY, "inst", "rail_post"),
        *rb.cyl_geo(0.025, 0.0, POST_H, segments=12)[:2], token="steel_rail")
    post.location = (rail_hx, rail_hy, H_TOP + WALK_THICK)
    _under(inst_root, post)

    # 池壁分缝（__nc 单面条带——同 AAO 制）
    band_verts = []
    band_faces = []
    for n_z in (JOINT_STEP_Z, 2 * JOINT_STEP_Z, 3 * JOINT_STEP_Z, 4 * JOINT_STEP_Z):
        if n_z >= H_TOP - 0.3:
            break
        for edge in ((-HX, -HY, HX, -HY), (HX, -HY, HX, HY),
                     (HX, HY, -HX, HY), (-HX, HY, -HX, -HY)):
            x0, y0, x1, y1 = edge
            dx, dy = (x1 - x0), (y1 - y0)
            length = math.hypot(dx, dy)
            nx, ny = dy / length, -dx / length
            o = 0.01
            base = len(band_verts)
            band_verts.extend([
                Vector((x0 + nx * o, y0 + ny * o, n_z)),
                Vector((x1 + nx * o, y1 + ny * o, n_z)),
                Vector((x1 + nx * o, y1 + ny * o, n_z + 0.04)),
                Vector((x0 + nx * o, y0 + ny * o, n_z + 0.04)),
            ])
            band_faces.append((base, base + 1, base + 2, base + 3))
    joints = rb.add_mesh(
        naming.build_name(FAMILY, "trim", "wall_joints", nc=True),
        band_verts, band_faces, "joint")
    _under(trim_root, joints)

    for obj in (shell, selector, divider, walkway, mixer):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
        except (RuntimeError, TypeError):
            pass

    # PNG 专用水面（preview_only 集合——**分工序水色**[用户裁定+调研锚]：
    # 预反应区深色混合/主反应区好氧茶褐；周界序 CCW +z 法线——蝴蝶结
    # 四边形用户目检实拦教训）
    from lib import materials
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    cass_zones = (
        ("water_selector", -IX, SELECT_X - SELECT_T / 2),   # 预反应区
        ("water_aerobic", SELECT_X + SELECT_T / 2, IX),     # 主反应区
    )
    for zi, (token, zx0, zx1) in enumerate(cass_zones):
        water_mesh = bpy.data.meshes.new(f"preview_water_{zi}")
        water_mesh.from_pydata(
            [Vector((x, y, WATER_LEVEL))
             for x, y in ((zx0, -IY), (zx1, -IY), (zx1, IY), (zx0, IY))],
            [], [(0, 1, 2, 3)],
        )
        water_mesh.validate()
        water_mesh.update()
        water = bpy.data.objects.new(f"preview_water_{zi}", water_mesh)
        water.data.materials.append(materials.ensure_material(token, alpha=0.85))
        preview.objects.link(water)

    # 归一校验（§2 AABB 对拍+水密快检——违例即中止；__nc 豁免）
    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    print("[NORMALIZE]")
    for obj in (shell, selector, divider, walkway, mixer,
                decant, aerator, post, *rails):
        for line in normalize.mesh_report(obj):
            print("  " + line)
    print(f"  {joints.name}: [nc] verts={len(joints.data.vertices)} "
          f"tris≈{sum(len(p.vertices) - 2 for p in joints.data.polygons)}")

    out = Path(__file__).resolve().parent / "build" / "cass_batch.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
