"""模板缩略图出图（P4 轻透视 50mm 等效——Eevee 512² 透明底）。

输入:  build/clarifier_radial.blend（含 preview_only 水面层——仅本工序消费）
输出:  build/clarifier_radial.png（512² RGBA——资产落位归资产工序）

规格说明（spec §11 P4 签核=轻透视 50mm 等效；§11 环境实录：Eevee
  无头出图 GPU 依赖——2026-09-12 实测本机 EEVEE_OK[spec §11 降级
  备选 Workbench/Cycles 未触发]）。
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
FIT_MARGIN = 1.08             # 水平半幅取景余量（首渲 1.35 偏小收口）


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
    diagonal = math.hypot(40.0, 40.0, 5.2)
    half_fov = math.atan(18.0 / FOCAL_MM)
    distance = diagonal / 2 / math.tan(half_fov) * FIT_MARGIN
    direction = CAM_DIR.normalized()
    cam_obj.location = CENTER + direction * distance
    look = CENTER - cam_obj.location
    rot_quat = look.to_track_quat("-Z", "Y")
    cam_obj.rotation_euler = rot_quat.to_euler()
    scene.camera = cam_obj

    # 布光：日光源（阴影定义）+中性环境（透明底仅受光）
    sun = bpy.data.lights.new("thumb_sun", "SUN")
    sun.energy = 4.5
    sun.angle = math.radians(6.0)
    sun_obj = bpy.data.objects.new("thumb_sun", sun)
    sun_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(28))
    scene.collection.objects.link(sun_obj)

    fill = bpy.data.lights.new("thumb_fill", "SUN")
    fill.energy = 1.6
    fill_obj = bpy.data.objects.new("thumb_fill", fill)
    fill_obj.rotation_euler = (math.radians(120), math.radians(20), math.radians(200))
    scene.collection.objects.link(fill_obj)

    world = bpy.data.worlds.new("thumb_world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]  # type: ignore[union-attr]
    bg.inputs[0].default_value = (0.78, 0.81, 0.86, 1.0)  # type: ignore[index]
    bg.inputs[1].default_value = 1.1  # type: ignore[index]
    scene.world = world

    scene.render.engine = "BLENDER_EEVEE"
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
