"""调节池单池族参数化模板建模（53×22×5.5——批4 第一窗）。

输入:  bpy 无头（``blender -b --factory-startup -P build_eqbasin.py``）
输出:  build/eq_basin_cell.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三；取数锚
  =server 最小图 municipal_tiaojiechi pool_wall box 53×22×5.5
  （l/b=单池圆整档 a1=l×b——cell 域 n 池方阵）
  [.workflow/b4-window1/anchor-sizes.md]）：
  - 构型：厚壁矩形大池（CASS 制式复用）+周圈走道+双栏杆+池壁分缝
    （__nc 单面条带）+equip 潜水搅拌器安装架×2（恒等锚
    MIXER_SPAN=0.05×53=2.65——p_stir 70kW 档双区布置）+inst 栏杆
    立柱（rect）；
  - poolGroup：cell 域（countParam=n gap=1.0——n grid [2..6]）；
  - 水面 preview（water_surface 原水蓝——调蓄池非生化段）。
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
FAMILY = "eqbasin"              # 命名前缀（registry family=eq_basin_cell）
TEMPLATE_SIZE = (53.0, 22.0, 5.5)  # L0/W0/H0（server 最小图恒等锚）
WALL = 0.45
H_TOP = TEMPLATE_SIZE[2]        # 5.5
HX, HY = TEMPLATE_SIZE[0] / 2, TEMPLATE_SIZE[1] / 2
IX, IY = HX - WALL, HY - WALL
WALK_WIDTH = 1.6
WALK_THICK = 0.12
RAIL_TUBE = 0.03
RAIL_HEIGHTS = (1.1, 0.6)
RAIL_INSET = 0.35
MIXER_SPAN = 2.65               # 搅拌器安装架跨度（=0.05×53 恒等锚）
POST_H = RAIL_HEIGHTS[0]
JOINT_STEP_Z = 1.2
WATER_LEVEL = 5.0               # PNG 专用水面（h2 有效水深档）


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

    # 周圈走道+双栏杆环（CASS 同制）
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

    # equip：潜水搅拌器安装架×2（几何直接世界位构造——CASS mixer_mount
    # 同制；双区布置=池长 1/3/2/3 位）
    def mixer_mount(cx: float, part: str) -> bpy.types.Object:
        parts = [
            rb.box_geo((cx - MIXER_SPAN / 2 + 0.1, 0.0, H_TOP + 0.55),
                       (0.2, 0.2, 1.1)),
            rb.box_geo((cx + MIXER_SPAN / 2 - 0.1, 0.0, H_TOP + 0.55),
                       (0.2, 0.2, 1.1)),
            rb.box_geo((cx, 0.0, H_TOP + 1.16),
                       (MIXER_SPAN, 0.16, 0.12)),
            rb.rod_geo(Vector((cx, 0.0, H_TOP + 1.1)),
                       Vector((cx, 0.0, H_TOP - 2.2)), 0.05, segments=8),
            rb.cyl_geo(0.22, H_TOP - 2.4, H_TOP - 1.2, (cx, 0.0), segments=16),
        ]
        return rb.merged(
            naming.build_name(FAMILY, "equip", part), parts, "steel_bridge")

    mount_a = mixer_mount(-HX + TEMPLATE_SIZE[0] / 3, "mixer_mount_a")
    mount_b = mixer_mount(-HX + 2 * TEMPLATE_SIZE[0] / 3, "mixer_mount_b")
    _under(equip_root, mount_a)
    _under(equip_root, mount_b)

    # inst：栏杆立柱原型（rect——数量=场景图；CASS 同制）
    post = rb.add_mesh(
        naming.build_name(FAMILY, "inst", "rail_post"),
        *rb.cyl_geo(0.025, 0.0, POST_H, segments=12)[:2], token="steel_rail")
    post.location = (rail_hx, rail_hy, H_TOP + WALK_THICK)
    _under(inst_root, post)

    # 池壁分缝（__nc 单面条带——CASS 同制）
    band_verts = []
    band_faces = []
    n_z = JOINT_STEP_Z
    while n_z < H_TOP - 0.3:
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
        n_z += JOINT_STEP_Z
    joints = rb.add_mesh(
        naming.build_name(FAMILY, "trim", "wall_joints", nc=True),
        band_verts, band_faces, "joint")
    _under(trim_root, joints)

    for obj in (shell, walkway, mount_a, mount_b):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
        except (RuntimeError, TypeError):
            pass

    # PNG 专用水面（preview_only——原水调蓄蓝；周界序 CCW +z 法线）
    from lib import materials
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    water_mesh = bpy.data.meshes.new("preview_water_0")
    water_mesh.from_pydata(
        [Vector((-IX, -IY, WATER_LEVEL)), Vector((IX, -IY, WATER_LEVEL)),
         Vector((IX, IY, WATER_LEVEL)), Vector((-IX, IY, WATER_LEVEL))],
        [], [(0, 1, 2, 3)],
    )
    water_mesh.validate()
    water_mesh.update()
    water = bpy.data.objects.new("preview_water_0", water_mesh)
    water.data.materials.append(materials.ensure_material("water_surface", alpha=0.85))
    preview.objects.link(water)

    # 归一校验（§2 AABB 对拍+水密快检——违例即中止；__nc 豁免）
    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    print("[NORMALIZE]")
    for obj in (shell, walkway, mount_a, mount_b, post, *rails):
        for line in normalize.mesh_report(obj):
            print("  " + line)
    print(f"  {joints.name}: [nc] verts={len(joints.data.vertices)} "
          f"tris≈{sum(len(p.vertices) - 2 for p in joints.data.polygons)}")

    out = Path(__file__).resolve().parent / "build" / "eq_basin_cell.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
