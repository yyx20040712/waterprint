"""模板缩略图出图（P4 轻透视 50mm 等效——Eevee 512² 透明底）。

输入:  build/clarifier_radial.blend（含 preview_only 水面层——仅本工序消费）
输出:  build/clarifier_radial.png（512² RGBA——资产落位归资产工序）

规格说明（spec §11 P4 签核=轻透视 50mm 等效；§11 环境实录：Eevee
  无头出图 GPU 依赖——2026-09-12 实测本机 EEVEE_OK[spec §11 降级
  备选 Workbench/Cycles 未触发]；**批3 迭代二曝光档**[交接 §一.2/
  STYLE-BASE §2——ds 复审]：EV −1.15+AgX Medium High Contrast+光源
  双降——目标主体直方图中位 48~58%/高光峰值 ≤0.92）。
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

BUILD = Path(__file__).resolve().parent / "build"
SIZE = 512                    # 512²（交接 §三）
FOCAL_MM = 50.0               # P4 轻透视 50mm 等效（36mm 传感器）
CAM_DIR = Vector((1.0, 0.85, 1.05))  # iso 方向（俯角≈36°——走道环面可见）
CENTER = Vector((0.0, 0.0, 2.6))    # 取景中心（模板半高附近）
FIT_MARGIN = 1.00             # 水平半幅取景余量（迭代二收紧 1.08→1.00——细节放大）
EXPOSURE_EV = -1.15          # 实测迭代定档（EV+光源双降合计≈原 -2 档——
                             # 目标带 48~58% 中位为判据，EV 数值=手段非规格）
SUN_ENERGY = 3.3              # 4.5→3.3（两轮降档——中位 69%→48~58% 目标带）
FILL_ENERGY = 1.2             # 1.6→1.2（暗部金属反差保持）
WORLD_STRENGTH = 0.78         # 1.1→0.78（中性环境降+去蓝偏）


def render() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(BUILD / "clarifier_radial.blend"))
    scene = bpy.context.scene

    camera = bpy.data.cameras.new("thumb_camera")
    camera.lens = FOCAL_MM
    camera.sensor_fit = "HORIZONTAL"
    camera.sensor_width = 36.0
    cam_obj = bpy.data.objects.new("thumb_camera", camera)
    scene.collection.objects.link(cam_obj)

    # 取景：水平 fov=2·atan(18/50)≈39.6°——半幅距=对角/2/ tan(fov/2)×余量
    # （迭代二竖向包络 5.3=电机顶 4.9+余量）
    diagonal = math.hypot(40.0, 40.0, 5.3)
    half_fov = math.atan(18.0 / FOCAL_MM)
    distance = diagonal / 2 / math.tan(half_fov) * FIT_MARGIN
    direction = CAM_DIR.normalized()
    cam_obj.location = CENTER + direction * distance
    look = CENTER - cam_obj.location
    rot_quat = look.to_track_quat("-Z", "Y")
    cam_obj.rotation_euler = rot_quat.to_euler()
    scene.camera = cam_obj

    # 布光：日光源（阴影定义）+中性环境（透明底仅受光）——迭代二双降档
    sun = bpy.data.lights.new("thumb_sun", "SUN")
    sun.energy = SUN_ENERGY
    sun.angle = math.radians(6.0)
    sun_obj = bpy.data.objects.new("thumb_sun", sun)
    sun_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(28))
    scene.collection.objects.link(sun_obj)

    fill = bpy.data.lights.new("thumb_fill", "SUN")
    fill.energy = FILL_ENERGY
    fill_obj = bpy.data.objects.new("thumb_fill", fill)
    fill_obj.rotation_euler = (math.radians(120), math.radians(20), math.radians(200))
    scene.collection.objects.link(fill_obj)

    world = bpy.data.worlds.new("thumb_world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]  # type: ignore[union-attr]
    bg.inputs[0].default_value = (0.80, 0.81, 0.83, 1.0)  # type: ignore[index]
    bg.inputs[1].default_value = WORLD_STRENGTH  # type: ignore[index]
    scene.world = world

    # 迭代二曝光档（ds 复审）：EV 降档+AgX Medium High Contrast（高光
    # 滚降=高光压缩近似）；AgX 不可用回退 Filmic 同 look（记录控制台）
    # ——transform 赋值同入 try（门二 W1：无 AgX 环境下裸赋值先崩，
    # 回退分支不可达）
    view = scene.view_settings
    view.exposure = EXPOSURE_EV
    try:
        view.view_transform = "AgX"
        view.look = "AgX - Medium High Contrast"
    except TypeError:
        view.view_transform = "Filmic"
        view.look = "Filmic - Medium High Contrast"
        print("[FALLBACK] AgX 不可用——Filmic Medium High Contrast 顶替")

    scene.render.engine = "BLENDER_EEVEE"
    # 金属反射：EEVEE Next 光线追踪（不可用静默退离屏反射——平面环境
    # 哑光根因，ds「金属读成白塑料」批注的渲染面对策）
    try:
        scene.eevee.use_raytracing = True  # type: ignore[attr-defined]
        print("[RT] EEVEE raytracing on")
    except AttributeError:
        print("[RT] use_raytracing 不可用——默认反射档")
    scene.eevee.taa_render_samples = 96
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.film_transparent = True
    out = BUILD / "clarifier_radial.png"
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print(f"[PNG] {out} ({out.stat().st_size / 1024:.1f} KB——预算 ≤80KB)")


if __name__ == "__main__":
    render()
