"""AAO 廊道族参数化模板建模（95×38×5.3——批3 段二·五步门③）。

输入:  bpy 无头（``blender -b --factory-startup -P build_aao.py``）
输出:  build/aao_corridor.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三 AAO 档位表
  [段二建模前调研 2026-09-13 落档]；取数锚=golden 34760 单 box
  95×38×5.3——交接「取数节点=单 box，分格表达归 trim/equip」）：
  - 坐标：Blender z-up，原点=池底中心，米制；templateSize 95×38×5.3
    （shell AABB=[−47.5,47.5]×[−19,19]×[0,5.3]——normalize 对拍）；
  - 三区沿池长（调研锚：容积比≈1:2:4 档）：厌氧 14m｜缺氧 24m｜好氧
    56.2m——两道横隔墙露顶分格（trim 缺省水平双向随壳）；好氧区两道
    纵导流墙（水下墙+端部折流缺口——3 廊道档）；
  - 周圈走道外挑 1.6+双栏杆环（矩形——规范定值 1.1/0.6 不随池深）；
  - 出水堰槽=末端内壁 U 槽（3 盒——trim）；
  - equip 推流器安装架×2（厌氧/缺氧区——等比 actualFactor 0.05×L；
    恒等锚 4.75=0.05×95）；
  - inst：曝气头原型（grid 0.8m——registry instanceSpacing；场景图
    instance_counts 空=默认 skipped+登记[P7]，探针注入路由验证）+
    栏杆立柱原型（rect 周界——角位建模约定）；
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
FAMILY = "aao"                   # 命名前缀（registry family=aao_corridor）
TEMPLATE_SIZE = (95.0, 38.0, 5.3)  # L0/W0/H0（golden 34760 恒等锚）
WALL = 0.5                       # 壁厚（大池档）
H_TOP = TEMPLATE_SIZE[2]         # 5.3
HX, HY = TEMPLATE_SIZE[0] / 2, TEMPLATE_SIZE[1] / 2
IX, IY = HX - WALL, HY - WALL
WALK_WIDTH = 1.6                 # 周圈走道外挑宽
WALK_THICK = 0.12
RAIL_TUBE = 0.03
RAIL_HEIGHTS = (1.1, 0.6)        # 顶栏/中栏（规范定值——S1 不随池深缩放）
RAIL_INSET = 0.35                # 栏杆中线自走道外缘内收
WATER_LEVEL = 5.0                # PNG 专用水面（golden level=5.0 口径）

# 三区分格（厌氧|缺氧|好氧=14|24|56.2m——调研容积比锚）
PARTITION_X = (-33.3, -8.9)      # 两道横隔墙中心线（厚 0.4）
PARTITION_T = 0.4
PARTITION_Z_TOP = 5.5            # 隔墙露顶（出水面 0.5——类型示意可辨档）
GUIDE_Y = (-HY / 3, HY / 3)      # 好氧区纵导流墙（3 廊道档）
GUIDE_T = 0.3
GUIDE_Z_TOP = 5.4                # 水下墙露头（出水面 0.4——折流墙示意档）
GUIDE_END_GAP = 1.0              # 端部折流缺口
WEIR_INSET = 0.6                 # 出水堰槽内壁让位（贴末端内壁）
WEIR_W, WEIR_D = 0.3, 0.4        # 槽宽×深（ds 复审参数同辐流）
MIXER_SPAN = 4.75                # 安装架跨度（=0.05×95 恒等锚）
POST_H = RAIL_HEIGHTS[0]         # 立柱高 1.1（rect 周界）
AERATOR_D = 0.30                 # 曝气头盘径（微孔盘典型档）
JOINT_STEP_Z = 1.2               # 池壁水平施工缝步距（ds：每 1.2m 一道）


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

    # 横隔墙×2（露顶——三区分格可辨）
    partitions = []
    for k, gx in enumerate(PARTITION_X):
        p = rb.add_mesh(
            naming.build_name(FAMILY, "trim", f"partition_{k}"),
            *rb.box_geo((gx, 0.0, (WALL + PARTITION_Z_TOP) / 2),
                        (PARTITION_T, 2 * IY, PARTITION_Z_TOP - WALL))[:2],
            token="concrete_wall")
        partitions.append(p)
        _under(trim_root, p)

    # 好氧区纵导流墙×2（水下墙+端部折流缺口）
    guides = []
    x0, x1 = -PARTITION_X[1] - PARTITION_T / 2 + 1.0, HX - WALL - GUIDE_END_GAP
    for k, gy in enumerate(GUIDE_Y):
        g = rb.add_mesh(
            naming.build_name(FAMILY, "trim", f"guide_wall_{k}"),
            *rb.box_geo(((x0 + x1) / 2, gy, (WALL + GUIDE_Z_TOP) / 2),
                        (x1 - x0, GUIDE_T, GUIDE_Z_TOP - WALL))[:2],
            token="concrete_wall")
        guides.append(g)
        _under(trim_root, g)

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

    # 出水堰槽（末端 +x 内壁 U 槽——3 盒：底条+内外壁）
    wz0 = H_TOP - WEIR_D
    wx_out = HX - WALL - 0.01                     # 外壁贴池内壁（避共面）
    wx_in = wx_out - WEIR_W
    weir = rb.merged(
        naming.build_name(FAMILY, "trim", "weir_launder"),
        [
            rb.box_geo(((wx_in + wx_out) / 2, 0.0, wz0),
                       (WEIR_W, 2 * IY, 0.08)),    # 槽底条
            rb.box_geo((wx_in, 0.0, (wz0 + H_TOP) / 2),
                       (0.08, 2 * IY, WEIR_D)),    # 内壁
            rb.box_geo((wx_out, 0.0, (wz0 + H_TOP) / 2),
                       (0.08, 2 * IY, WEIR_D)),    # 外壁
        ], "concrete_coping")
    _under(trim_root, weir)

    # equip：推流器安装架×2（厌氧/缺氧区中心——立柱双杆+横梁+导杆+
    # 潜水电机轮廓；恒等锚 4.75=0.05×95）
    def mixer_mount(cx: float, part: str) -> bpy.types.Object:
        parts = [
            rb.box_geo((cx - MIXER_SPAN / 2 + 0.1, 0.0, H_TOP + 0.55),
                       (0.2, 0.2, 1.1)),            # 左立柱
            rb.box_geo((cx + MIXER_SPAN / 2 - 0.1, 0.0, H_TOP + 0.55),
                       (0.2, 0.2, 1.1)),            # 右立柱
            rb.box_geo((cx, 0.0, H_TOP + 1.16),
                       (MIXER_SPAN, 0.16, 0.12)),  # 横梁
            rb.rod_geo(Vector((cx, 0.0, H_TOP + 1.1)),
                       Vector((cx, 0.0, H_TOP - 2.2)), 0.05, segments=8),
            rb.cyl_geo(0.22, H_TOP - 2.4, H_TOP - 1.2,
                       (cx, 0.0), segments=16),     # 潜水电机轮廓
        ]
        return rb.merged(
            naming.build_name(FAMILY, "equip", part), parts, "steel_bridge")

    # 区中心：厌氧=[−HX, PARTITION_X[0]−t/2]、缺氧=[P0+t/2, P1−t/2]
    ana_c = (HX + PARTITION_X[0] - PARTITION_T / 2) / 2
    anox_c = (PARTITION_X[0] + PARTITION_X[1]) / 2
    mount_ana = mixer_mount(ana_c, "mixer_mount_ana")
    mount_anox = mixer_mount(anox_c, "mixer_mount_anox")
    _under(equip_root, mount_ana)
    _under(equip_root, mount_anox)

    # inst：曝气头原型（grid 0.8m——好氧区池底网格；几何本地居中+
    # 对象平移=节点 TRS）+栏杆立柱原型（rect 角位建模约定）
    aer_parts = [
        rb.cyl_geo(AERATOR_D / 2, 0.0, 0.06, segments=12),   # 曝气盘
        rb.rod_geo(Vector((0.0, 0.0, 0.06)), Vector((0.0, 0.0, 0.26)),
                   0.03, segments=8),                        # 支杆
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

    # 池壁分缝（__nc 单面条带——外墙面外凸 0.01 三道水平矩形环面片）
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
            nx, ny = dy / length, -dx / length       # 外法线
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

    # 平滑着色（锐边自动保持；失败退平直无害）
    for obj in (shell, *partitions, *guides, walkway, weir, mount_ana, mount_anox):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
        except (RuntimeError, TypeError):
            pass

    # PNG 专用水面（preview_only 集合——glb 导出剔除；单面片顶面 +z）
    from lib import materials
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    water_mesh = bpy.data.meshes.new("preview_water")
    water_mesh.from_pydata(
        [Vector((x, y, WATER_LEVEL))
         for x in (-IX, IX) for y in (-IY, IY)],
        [], [(0, 1, 2, 3)],
    )
    water_mesh.validate()
    water_mesh.update()
    water = bpy.data.objects.new("preview_water", water_mesh)
    water.data.materials.append(
        materials.ensure_material("water_surface", alpha=0.72))
    preview.objects.link(water)

    # 归一校验（§2 AABB 对拍+水密快检——违例即中止；__nc 豁免）
    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    print("[NORMALIZE]")
    for obj in (shell, *partitions, *guides, walkway, weir,
                mount_ana, mount_anox, aerator, post, *rails):
        for line in normalize.mesh_report(obj):
            print("  " + line)
    print(f"  {joints.name}: [nc] verts={len(joints.data.vertices)} "
          f"tris≈{sum(len(p.vertices) - 2 for p in joints.data.polygons)}")

    out = Path(__file__).resolve().parent / "build" / "aao_corridor.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
