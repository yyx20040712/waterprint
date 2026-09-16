"""粗格栅渠道族参数化模板建模（1.8×0.6×1.0——批4 第一窗）。

输入:  bpy 无头（``blender -b --factory-startup -P build_coarse_screen.py``）
输出:  build/coarse_screen.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三；取数锚
  =server 最小图 municipal_cugeshan pool_wall box 1.8×0.6×1.0
  [.workflow/b4-window1/anchor-sizes.md]）：
  - 坐标：Blender z-up，原点=渠底中心，米制；templateSize 1.8×0.6×1.0
    （shell AABB=[−0.9,0.9]×[−0.3,0.3]×[0,1.0]）；
  - 构型：单条矩形栅渠（厚壁）+斜置栅条组（75° 档——9 根沿槽宽排[r1 加密档]）
    +inst 链耙清渣机原型（mech_cleaner——数量=场景图 instance_counts
    mech_clean，grid 模式 count=1 退化为池心单台）；
  - poolGroup：cell 域（n 台渠方阵——countParam=n gap=0.8 归 registry）；
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
FAMILY = "coarse"               # 命名前缀（registry family=coarse_screen）
TEMPLATE_SIZE = (1.8, 0.6, 1.0)  # L0/W0/H0（server 最小图恒等锚）
WALL = 0.10
H_TOP = TEMPLATE_SIZE[2]        # 1.0
HX, HY = TEMPLATE_SIZE[0] / 2, TEMPLATE_SIZE[1] / 2
IX, IY = HX - WALL, HY - WALL

# 栅条组（75° 斜置——粗格栅 b=65mm 档，渠净宽 0.4 排 9 根[r1 加密]）
SCREEN_X = -0.15                # 栅条平面中心线（渠进口段内）
SCREEN_TILT = math.radians(75.0)
BAR_R = 0.028                   # 栅条杆半径（s=10mm 档视觉放大表达）
BAR_N = 9                       # 栅条根数（n_gap 档）
BAR_PITCH = 2 * IY / (BAR_N - 1) if BAR_N > 1 else 0.0
WATER_LEVEL = 0.6               # PNG 专用水面（栅前水深 h=0.6 档）


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

    # 栅条组（75° 斜杆×5 沿槽宽排+顶/底支承梁——多闭包合并）
    bar_len = (H_TOP - WALL) / math.sin(SCREEN_TILT)
    tilt_dir = Vector((math.cos(SCREEN_TILT), 0.0, math.sin(SCREEN_TILT)))
    screen_parts = []
    for k in range(BAR_N):
        y = -IY + k * BAR_PITCH
        p0 = Vector((SCREEN_X - tilt_dir.x * bar_len / 2, y, 0.0))
        p1 = Vector((SCREEN_X + tilt_dir.x * bar_len / 2, y, bar_len * math.sin(SCREEN_TILT)))
        screen_parts.append(rb.rod_geo(p0, p1, BAR_R, segments=6))
    # 顶/底支承梁（沿槽宽——栅条上下端锚固）
    # 顶/底支承梁（沿槽宽——贴栅条上/下端连线[门一 N3：首版梁位不触
    # 栅条视觉漂浮实拦——梁 x 随倾斜端点走]）
    for z, sx in ((WALL + 0.02, -1), (H_TOP - 0.02, 1)):
        bx = SCREEN_X + sx * tilt_dir.x * bar_len / 2
        screen_parts.append(rb.rod_geo(
            Vector((bx, -IY, z)), Vector((bx, IY, z)), 0.018, segments=6))
    screen = rb.merged(
        naming.build_name(FAMILY, "trim", "screen_bars"), screen_parts, "steel_rail")
    _under(trim_root, screen)

    # 周圈压顶沿（薄环板——渠顶找平层）
    coping = rb.rect_walkway(
        naming.build_name(FAMILY, "trim", "coping"),
        2 * (HX + 0.08), 2 * (HY + 0.08),
        TEMPLATE_SIZE[0], TEMPLATE_SIZE[1],
        H_TOP, H_TOP + 0.06, "concrete_coping")
    _under(trim_root, coping)

    # equip：无（清渣机走 inst——instance_counts mech_clean）

    # inst：链耙清渣机原型（本地化建模 z 自 0 起+x/z 居中：跨渠门架+
    # 环形链框+耙齿；TRS=渠中心顶面——grid 模式 count=1 渠心单台）
    gate_w = IY + WALL * 0.5      # 门架半跨（骑渠壁）
    cleaner_parts = [
        rb.box_geo((0.0, -gate_w, 0.45), (0.12, 0.08, 0.9)),    # 立柱×2
        rb.box_geo((0.0, gate_w, 0.45), (0.12, 0.08, 0.9)),
        rb.box_geo((0.0, 0.0, 0.92), (0.14, 2 * gate_w, 0.10)), # 顶横梁
        rb.rod_geo(Vector((0.0, -IY, 0.85)), Vector((0.0, IY, 0.85)), 0.02, segments=6),
        rb.rod_geo(Vector((0.0, -IY, 0.45)), Vector((0.0, IY, 0.45)), 0.02, segments=6),
        rb.rod_geo(Vector((0.0, -IY, 0.45)), Vector((0.0, -IY, 0.85)), 0.02, segments=6),
        rb.rod_geo(Vector((0.0, IY, 0.45)), Vector((0.0, IY, 0.85)), 0.02, segments=6),
        # 耙齿×3（链框前侧短杆——斜向下耙）
        rb.rod_geo(Vector((-0.05, -IY + 0.06, 0.75)), Vector((0.10, -IY + 0.06, 0.60)), 0.014, segments=6),
        rb.rod_geo(Vector((-0.05, 0.0, 0.65)), Vector((0.10, 0.0, 0.50)), 0.014, segments=6),
        rb.rod_geo(Vector((-0.05, IY - 0.06, 0.75)), Vector((0.10, IY - 0.06, 0.60)), 0.014, segments=6),
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

    # PNG 专用水面（preview_only——栅前段渠内；周界序 CCW +z 法线）
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

    # 归一校验（§2 AABB 对拍+水密快检——违例即中止）
    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    print("[NORMALIZE]")
    for obj in (shell, screen, coping, cleaner):
        for line in normalize.mesh_report(obj):
            print("  " + line)

    out = Path(__file__).resolve().parent / "build" / "coarse_screen.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
