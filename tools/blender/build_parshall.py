"""巴歇尔计量槽族参数化模板建模（3.095×1.05×0.479——批4 第一窗）。

输入:  bpy 无头（``blender -b --factory-startup -P build_parshall.py``）
输出:  build/parshall_flume.blend（+控制台归一校验报告）

规格说明（assemble/spec.md §1/§2/§10；STYLE-BASE §三；取数锚
  =server 最小图 municipal_bashi_jiliangcao pool_wall box
  3.095×1.05×0.479（l_total×b2 出口宽×ha_design 上游水头）
  [.workflow/b4-window1/anchor-sizes.md]）：
  - 构型：五段阶梯槽（进口段→收缩段→喉段→扩散段→出口段——轴对齐
    盒阶梯逼近斜收缩/扩散墙；喉段下游底板跌落 n_depress 档）；薄壁
    U 槽各段对接面贴邻（段间 0.005 微缝避共面焊接）；
  - equip：上游液位计立柱（超声波探头——特征高=杆顶）；
  - 无 poolGroup（单台计量槽）；水面 preview（进口段壅水窄条）。
  - templateSize 保留 core 原值小数（3.095/1.05/0.479——AABB 对拍
    恰等口径，shell 外沿恰在边界）。
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
FAMILY = "parshall"             # 命名前缀（registry family=parshall_flume）
TEMPLATE_SIZE = (3.095, 1.05, 0.479)  # L0/W0/H0（server 最小图恒等锚）
WALL = 0.06
H_TOP = TEMPLATE_SIZE[2]        # 0.479（上游水头档——壳全高）
HX = TEMPLATE_SIZE[0] / 2

# 五段剖面（沿 x：进口宽→喉宽 0.75→出口宽；喉段底板跌落 0.08 档）
B_THROAT = 0.75
B_END = TEMPLATE_SIZE[1]        # 1.05（进出口同宽档）
DEPRESS = 0.08                  # 喉段底板跌落（n_depress 档）
# 段长（沿流向 x+）：进口 0.9 / 收缩 0.4 / 喉 0.6 / 扩散 0.4 / 出口 0.795
SEG_LENS = (0.795, 0.4, 0.6, 0.4, 0.9)
SEAM = 0.005                    # 段间微缝（避共面）
WATER_LEVEL = 0.40              # PNG 专用水面（ha_avg 档壅水）


def _under(parent: bpy.types.Object, child: bpy.types.Object) -> None:
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def u_slot_parts(cx: float, length: float, width: float, height: float,
                 wall: float, floor_h: float
                 ) -> list[tuple[list[Vector], list[tuple[int, ...]]]]:
    """薄壁 U 形槽段（底板+双壁闭包三盒——**壁底 5mm 微缝**防 CI 焊接步
    T 连接[同 grit u_channel 两轮实拦制式]；段间 SEAM 微缝避共面）。"""
    seam = 0.005
    hy = width / 2
    return [
        rb.box_geo((cx, 0.0, floor_h + wall / 2), (length, width, wall)),
        rb.box_geo((cx, -hy + wall / 2,
                    floor_h + wall + seam + (height - wall - seam) / 2),
                   (length, wall, height - wall - seam)),
        rb.box_geo((cx, hy - wall / 2,
                    floor_h + wall + seam + (height - wall - seam) / 2),
                   (length, wall, height - wall - seam)),
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

    # shell：五段 U 槽（进口→收缩→喉[跌落]→扩散→出口——段间微缝）
    # 段宽沿流向：B_END → 收窄 → B_THROAT → 扩散 → B_END
    # 轴对齐阶梯：收缩/扩散段取两侧段宽的窄值（贴喉侧——阶梯收缩形）
    # 底板：上游/出口段抬高 DEPRESS（巴歇尔喉底跌落语义——AABB 恰 [0,H]）
    widths = (B_END, (B_END + B_THROAT) / 2, B_THROAT, (B_END + B_THROAT) / 2, B_END)
    # 段序反转后自 +x 起为出口→…→进口（壅水进口段朝相机近端）
    floors = (DEPRESS, DEPRESS, 0.0, 0.0, DEPRESS)  # 喉+扩散段低位
    heights = tuple(H_TOP - f for f in floors)
    shell_parts: list[tuple[list[Vector], list[tuple[int, ...]]]] = []
    cursor = -HX
    seg_objs = []
    for i, (seg_l, w, fl, h) in enumerate(zip(SEG_LENS, widths, floors, heights)):
        cx = cursor + seg_l / 2
        shell_parts.extend(u_slot_parts(cx, seg_l - (SEAM if 0 < i < 4 else 0),
                                        w, h, WALL, fl))
        cursor += seg_l
    flume = rb.merged(
        naming.build_name(FAMILY, "shell", "flume"), shell_parts, "concrete_wall")
    _under(shell_root, flume)
    seg_objs.append(flume)

    # trim：进出口端封翼（渠口加宽小翼板——安装找平）
    for k, cx in enumerate((-HX + 0.15, HX - 0.15)):
        wing = rb.merged(
            naming.build_name(FAMILY, "trim", f"end_wing_{k}"),
            u_slot_parts(cx, 0.15, B_END + 0.12, 0.10, WALL, 0.0),
            "concrete_coping")
        _under(trim_root, wing)
        seg_objs.append(wing)

    # equip：上游液位计（进口段北岸立柱+悬臂探头——特征高=悬臂杆顶
    # 实测 0.639=H_TOP+0.14+0.02[门一 W3 恒等锚=几何实测唯一源]）
    gauge = rb.merged(
        naming.build_name(FAMILY, "equip", "level_gauge"),
        [
            rb.box_geo((HX - 0.30, B_END / 2 + 0.08, H_TOP / 2),
                       (0.10, 0.10, H_TOP)),                       # 立柱
            rb.rod_geo(Vector((HX - 0.30, B_END / 2 + 0.03, H_TOP + 0.14)),
                       Vector((HX - 0.30, 0.0, H_TOP + 0.14)), 0.02, segments=6),
            rb.box_geo((HX - 0.30, 0.0, H_TOP + 0.08), (0.12, 0.12, 0.10)),  # 探头
        ], "steel_drive")
    _under(equip_root, gauge)

    for obj in (flume, gauge, *seg_objs[1:]):
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35.0))
        except (RuntimeError, TypeError):
            pass

    # PNG 专用水面（preview_only——进口+收缩段壅水窄条；周界序 CCW）
    from lib import materials
    preview = bpy.data.collections.new("preview_only")
    scene.collection.children.link(preview)
    in_x0, in_x1 = HX - SEG_LENS[4] + 0.03, HX - 0.03  # 仅进口段[门一 N4：越收缩段穿壁实拦]
    water_mesh = bpy.data.meshes.new("preview_water_0")
    water_mesh.from_pydata(
        [Vector((in_x0, -(B_END / 2 - WALL) , WATER_LEVEL)),
         Vector((in_x1, -(B_END / 2 - WALL), WATER_LEVEL)),
         Vector((in_x1, B_END / 2 - WALL, WATER_LEVEL)),
         Vector((in_x0, B_END / 2 - WALL, WATER_LEVEL))],
        [], [(0, 1, 2, 3)],
    )
    water_mesh.validate()
    water_mesh.update()
    water = bpy.data.objects.new("preview_water_0", water_mesh)
    water.data.materials.append(materials.ensure_material("water_surface", alpha=0.85))
    preview.objects.link(water)

    # 归一校验（§2 AABB 对拍——五段壳单网格整体对拍）
    normalize.assert_shell_aabb(flume, TEMPLATE_SIZE)
    print("[NORMALIZE]")
    for obj in (flume, gauge, *seg_objs[1:]):
        for line in normalize.mesh_report(obj):
            print("  " + line)

    out = Path(__file__).resolve().parent / "build" / "parshall_flume.blend"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    build()
