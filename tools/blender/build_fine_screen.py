"""细格栅渠道族参数化模板建模（1.9×0.8×1.0——批4 第一窗）。

输入:  bpy 无头（``blender -b --factory-startup -P build_fine_screen.py``）
输出:  build/fine_screen.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三；取数锚
  =server 最小图 municipal_xigeshan pool_wall box 1.9×0.8×1.0
  [.workflow/b4-window1/anchor-sizes.md]）：
  - 构型与粗格栅同族异档（build_coarse_screen 同制）：细栅 b=8mm 档
    栅距密（杆密排 13 根[r1 加密档]）+回流弧形栅面示意（trim 上/下弦杆）；
  - poolGroup：cell 域（n 台渠方阵——countParam=n gap=0.8）；
  - inst 链耙清渣机原型（mech_cleaner——instance_counts mech_clean）。
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
FAMILY = "fine"                 # 命名前缀（registry family=fine_screen）
TEMPLATE_SIZE = (1.9, 0.8, 1.0)  # L0/W0/H0（server 最小图恒等锚）
WALL = 0.10
H_TOP = TEMPLATE_SIZE[2]
HX, HY = TEMPLATE_SIZE[0] / 2, TEMPLATE_SIZE[1] / 2
IX, IY = HX - WALL, HY - WALL

# 栅条组（70° 斜置——细格栅 b=8mm 档密排）
SCREEN_X = -0.15
SCREEN_TILT = math.radians(70.0)
BAR_R = 0.020                   # 栅条杆半径（s=3mm 档视觉放大）
BAR_N = 13                      # 密排档（n_gap 细栅倍粗栅）
BAR_PITCH = 2 * IY / (BAR_N - 1) if BAR_N > 1 else 0.0
WATER_LEVEL = 0.6


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

    # 栅条组（70° 斜杆×13 密排+顶/底支承梁）
    bar_len = (H_TOP - WALL) / math.sin(SCREEN_TILT)
    tilt_dir = Vector((math.cos(SCREEN_TILT), 0.0, math.sin(SCREEN_TILT)))
    screen_parts = []
    for k in range(BAR_N):
        y = -IY + k * BAR_PITCH
        screen_parts.append(rb.rod_geo(
            Vector((SCREEN_X - tilt_dir.x * bar_len / 2, y, 0.0)),
            Vector((SCREEN_X + tilt_dir.x * bar_len / 2, y, bar_len * math.sin(SCREEN_TILT))),
            BAR_R, segments=6))
    # 顶/底支承梁（贴栅条上/下端连线[门一 N3 同 coarse]）
    for z, sx in ((WALL + 0.02, -1), (H_TOP - 0.02, 1)):
        bx = SCREEN_X + sx * tilt_dir.x * bar_len / 2
        screen_parts.append(rb.rod_geo(
            Vector((bx, -IY, z)), Vector((bx, IY, z)), 0.015, segments=6))
    screen = rb.merged(
        naming.build_name(FAMILY, "trim", "screen_bars"), screen_parts, "steel_rail")
    _under(trim_root, screen)

    coping = rb.rect_walkway(
        naming.build_name(FAMILY, "trim", "coping"),
        2 * (HX + 0.08), 2 * (HY + 0.08),
        TEMPLATE_SIZE[0], TEMPLATE_SIZE[1],
        H_TOP, H_TOP + 0.06, "concrete_coping")
    _under(trim_root, coping)

    # inst：链耙清渣机原型（细栅档——立柱窄+耙齿密×4；TRS=渠中心顶面）
    gate_w = IY + WALL * 0.5
    cleaner_parts = [
        rb.box_geo((0.0, -gate_w, 0.45), (0.10, 0.08, 0.9)),
        rb.box_geo((0.0, gate_w, 0.45), (0.10, 0.08, 0.9)),
        rb.box_geo((0.0, 0.0, 0.92), (0.12, 2 * gate_w, 0.10)),
        rb.rod_geo(Vector((0.0, -IY, 0.85)), Vector((0.0, IY, 0.85)), 0.018, segments=6),
        rb.rod_geo(Vector((0.0, -IY, 0.45)), Vector((0.0, IY, 0.45)), 0.018, segments=6),
        rb.rod_geo(Vector((0.0, -IY, 0.45)), Vector((0.0, -IY, 0.85)), 0.018, segments=6),
        rb.rod_geo(Vector((0.0, IY, 0.45)), Vector((0.0, IY, 0.85)), 0.018, segments=6),
        rb.rod_geo(Vector((-0.04, -IY + 0.05, 0.78)), Vector((0.09, -IY + 0.05, 0.64)), 0.012, segments=6),
        rb.rod_geo(Vector((-0.04, -IY / 3, 0.70)), Vector((0.09, -IY / 3, 0.56)), 0.012, segments=6),
        rb.rod_geo(Vector((-0.04, IY / 3, 0.70)), Vector((0.09, IY / 3, 0.56)), 0.012, segments=6),
        rb.rod_geo(Vector((-0.04, IY - 0.05, 0.78)), Vector((0.09, IY - 0.05, 0.64)), 0.012, segments=6),
    ]
    cleaner = rb.merged(
        naming.build_name(FAMILY, "inst", "mech_cleaner"), cleaner_parts, "steel_bridge")
    cleaner.location = (0.0, 0.0, H_TOP + 0.06)
    _under(inst_root, cleaner)

    for obj in (shell, screen, coping):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
        except (RuntimeError, TypeError):
            pass

    from lib import materials
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    water_mesh = bpy.data.meshes.new("preview_water_0")
    water_mesh.from_pydata(
        [Vector((-HX + 0.02, -IY, WATER_LEVEL)), Vector((-HX + 0.02, IY, WATER_LEVEL)),
         Vector((HX - 0.02, IY, WATER_LEVEL)), Vector((HX - 0.02, -IY, WATER_LEVEL))],
        [], [(0, 1, 2, 3)],
    )
    water_mesh.validate()
    water_mesh.update()
    water = bpy.data.objects.new("preview_water_0", water_mesh)
    water.data.materials.append(materials.ensure_material("water_surface", alpha=0.85))
    preview.objects.link(water)

    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    print("[NORMALIZE]")
    for obj in (shell, screen, coping, cleaner):
        for line in normalize.mesh_report(obj):
            print("  " + line)

    out = Path(__file__).resolve().parent / "build" / "fine_screen.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
