"""V 型滤池单格族参数化模板建模（10×4.5×3.9——批4 第一窗）。

输入:  bpy 无头（``blender -b --factory-startup -P build_vfilter.py``）
输出:  build/vfilter_cell.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三；取数锚
  =server 最小图 municipal_vxinglvchi pool_wall box 10×4.5×3.9
  （l/b=a_cell 单格语义——cell 域分格 n 份渲染）
  [.workflow/b4-window1/anchor-sizes.md]）：
  - 构型：厚壁矩形单格滤池+中央排水槽（沿长轴 U 槽出顶）+两侧 V 型
    进水槽（沿双边池壁窄槽——V 滤进水布槽特征）+周圈走道+双栏杆；
  - 剖面档（h_water_above 1.3/h_sand 1.3/h_bottom 1.0——滤层不建模
    实体，滤料顶面走 preview 分色水面表达）；
  - poolGroup：cell 域（n 格方阵——countParam=n gap=0.2 格间共壁档）。
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
FAMILY = "vfilter"               # 命名前缀（registry family=vfilter_cell）
TEMPLATE_SIZE = (10.0, 4.5, 3.9)  # L0/W0/H0（server 最小图恒等锚）
WALL = 0.30
H_TOP = TEMPLATE_SIZE[2]        # 3.9
HX, HY = TEMPLATE_SIZE[0] / 2, TEMPLATE_SIZE[1] / 2
IX, IY = HX - WALL, HY - WALL

# 中央排水槽（洗砂水收集——出顶 0.35 可辨档）
FLUME_W, FLUME_D = 0.45, 0.60
FLUME_Z_TOP = H_TOP + 0.35
# 两侧 V 型进水槽（窄 U 槽贴池壁）
VIN_W, VIN_D = 0.28, 0.30
WALK_WIDTH = 1.0
WALK_THICK = 0.10
RAIL_TUBE = 0.025
RAIL_HEIGHTS = (1.1, 0.6)
RAIL_INSET = 0.22
WATER_LEVEL = 3.4               # PNG 专用水面（砂面上水深 1.3 档）
SAND_LEVEL = 2.1                # 滤料顶示意（h_sand 1.3 底部空间 1.0 之上）


def _under(parent: bpy.types.Object, child: bpy.types.Object) -> None:
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def u_trough_parts(cx: float, cy: float, length: float, width: float,
                   z0: float, z1: float, wall: float, axis: str = "x"
                   ) -> list[tuple[list[Vector], list[tuple[int, ...]]]]:
    """U 形槽三盒闭包（底+双壁——**壁底 5mm 微缝**：面贴面/重叠构造在
    CI 焊接步产生 T 连接/内面暴露[grit/parshall 两轮实拦终制——门一
    W2 回归统一制]；axis=x 沿长轴/y 沿短轴）。"""
    seam = 0.005
    if axis == "x":
        return [
            rb.box_geo((cx, cy, z0 + wall / 2), (length, width, wall)),
            rb.box_geo((cx, cy - width / 2 + wall / 2,
                        z0 + wall + seam + (z1 - z0 - wall - seam) / 2),
                       (length, wall, z1 - z0 - wall - seam)),
            rb.box_geo((cx, cy + width / 2 - wall / 2,
                        z0 + wall + seam + (z1 - z0 - wall - seam) / 2),
                       (length, wall, z1 - z0 - wall - seam)),
        ]
    return [
        rb.box_geo((cx, cy, z0 + wall / 2), (width, length, wall)),
        rb.box_geo((cx - length / 2 + wall / 2, cy,
                    z0 + wall + seam + (z1 - z0 - wall - seam) / 2),
                   (wall, length, z1 - z0 - wall - seam)),
        rb.box_geo((cx + length / 2 - wall / 2, cy,
                    z0 + wall + seam + (z1 - z0 - wall - seam) / 2),
                   (wall, length, z1 - z0 - wall - seam)),
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

    shell = rb.thick_rect_pool(
        naming.build_name(FAMILY, "shell", "wall"),
        TEMPLATE_SIZE[0], TEMPLATE_SIZE[1], H_TOP, WALL, "concrete_wall")
    _under(shell_root, shell)

    # 中央排水槽（沿长轴——底+双壁，出顶 0.2）
    flume = rb.merged(
        naming.build_name(FAMILY, "trim", "drain_flume"),
        u_trough_parts(0.0, 0.0, 2 * IX - 0.02, FLUME_W,
                       FLUME_Z_TOP - FLUME_D, FLUME_Z_TOP, 0.07),
        "concrete_coping")
    _under(trim_root, flume)

    # 两侧 V 型进水槽（贴南北内壁窄 U 槽——V 滤布水槽特征）
    for k, cy in enumerate((-IY + VIN_W / 2 + 0.05, IY - VIN_W / 2 - 0.05)):
        vsink = rb.merged(
            naming.build_name(FAMILY, "trim", f"v_inlet_{k}"),
            u_trough_parts(0.0, cy, 2 * IX - 0.02, VIN_W,
                           H_TOP - VIN_D, H_TOP, 0.05),
            "concrete_coping")
        _under(trim_root, vsink)

    # 周圈走道+双栏杆
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

    for obj in (shell, flume, walkway):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
        except (RuntimeError, TypeError):
            pass

    # PNG 专用水面（preview_only 两层：滤料顶示意砂色+砂上清水面；
    # 中央槽占位镂空=分区面周界序 CCW +z 法线）
    from lib import materials
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    zones = (
        ("preview_sand", -IX, IX, -IY, -IY + 0.55, SAND_LEVEL, "water_aerobic"),
        ("preview_sand", -IX, IX, IY - 0.55, IY, SAND_LEVEL, "water_aerobic"),
        ("preview_water", -IX, IX, -IY + 0.55, -FLUME_W / 2, WATER_LEVEL, "water_clarified"),
        ("preview_water", -IX, IX, FLUME_W / 2, IY - 0.55, WATER_LEVEL, "water_clarified"),
    )
    for zi, (_, x0, x1, y0, y1, z, token) in enumerate(zones):
        water_mesh = bpy.data.meshes.new(f"preview_water_{zi}")
        water_mesh.from_pydata(
            [Vector((x0, y0, z)), Vector((x1, y0, z)),
             Vector((x1, y1, z)), Vector((x0, y1, z))],
            [], [(0, 1, 2, 3)],
        )
        water_mesh.validate()
        water_mesh.update()
        water = bpy.data.objects.new(f"preview_water_{zi}", water_mesh)
        water.data.materials.append(materials.ensure_material(token, alpha=0.85))
        preview.objects.link(water)

    # 归一校验（§2 AABB 对拍+水密快检——违例即中止）
    normalize.assert_shell_aabb(shell, TEMPLATE_SIZE)
    print("[NORMALIZE]")
    for obj in (shell, flume, walkway, *rails):
        for line in normalize.mesh_report(obj):
            print("  " + line)

    out = Path(__file__).resolve().parent / "build" / "vfilter_cell.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
