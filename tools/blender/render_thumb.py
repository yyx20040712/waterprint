"""模板缩略图出图（P4 轻透视 50mm 等效——Eevee 512² 透明底；段二 family 参数化）。

输入:  build/<family>.blend（FAMILY 环境变量选族，缺省 clarifier_radial）
输出:  build/<family>.png（512² RGBA——资产落位归资产工序）

规格说明（spec §11 P4 签核=轻透视 50mm 等效；STYLE-BASE §二曝光档
  [批3 迭代二定档——v1.0 冻结复用：EV −1.15+AgX MHC+光源双降，目标
  主体直方图中位 48~58%/高光峰值 ≤0.92]；Eevee 无头出图 GPU 实测
  EEVEE_OK[spec §11 降级备选 Workbench/Cycles 未触发]）。
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

BUILD = Path(__file__).resolve().parent / "build"
FAMILY = os.environ.get("FAMILY", "clarifier_radial")

# 取景包络（L0×W0×竖向包络——竖向含 equip 越顶余量；取景中心高度）
ENVELOPES: dict[str, tuple[float, float, float, float]] = {
    "clarifier_radial": (40.0, 40.0, 5.3, 2.6),   # 迭代二定档（不动——已审面）
    "aao_corridor": (95.0, 38.0, 6.9, 3.0),      # 安装架顶 5.3+1.36≈6.7+余量
    "cass_batch": (48.5, 19.5, 6.8, 3.0),        # 搅拌器顶 5.5+1.26≈6.8
}

SIZE = 512                    # 512²（交接 §三）
FOCAL_MM = 50.0               # P4 轻透视 50mm 等效（36mm 传感器）
CAM_DIR = Vector((1.0, 0.85, 1.05))  # iso 方向（俯角≈36°）
FIT_MARGIN = 1.00             # 水平半幅取景余量
EXPOSURE_EV = -1.15           # STYLE-BASE §二（迭代二实测定档——三族复用）
SUN_ENERGY = 3.3
FILL_ENERGY = 1.2
WORLD_STRENGTH = 0.78


def render() -> None:
    env_l, env_w, env_h, center_z = ENVELOPES[FAMILY]
    bpy.ops.wm.open_mainfile(filepath=str(BUILD / f"{FAMILY}.blend"))
    scene = bpy.context.scene

    camera = bpy.data.cameras.new("thumb_camera")
    camera.lens = FOCAL_MM
    camera.sensor_fit = "HORIZONTAL"
    camera.sensor_width = 36.0
    cam_obj = bpy.data.objects.new("thumb_camera", camera)
    scene.collection.objects.link(cam_obj)

    diagonal = math.hypot(env_l, env_w, env_h)
    half_fov = math.atan(18.0 / FOCAL_MM)
    distance = diagonal / 2 / math.tan(half_fov) * FIT_MARGIN
    center = Vector((0.0, 0.0, center_z))
    direction = CAM_DIR.normalized()
    cam_obj.location = center + direction * distance
    look = center - cam_obj.location
    rot_quat = look.to_track_quat("-Z", "Y")
    cam_obj.rotation_euler = rot_quat.to_euler()
    scene.camera = cam_obj

    # 布光：日光源+中性环境（STYLE-BASE §二——迭代二双降档三族复用）
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
    try:
        scene.eevee.use_raytracing = True  # type: ignore[attr-defined]
        print("[RT] EEVEE raytracing on")
    except AttributeError:
        print("[RT] use_raytracing 不可用——默认反射档")
    scene.eevee.taa_render_samples = 96
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.film_transparent = True
    out = BUILD / f"{FAMILY}.png"
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print(f"[PNG] {out} ({out.stat().st_size / 1024:.1f} KB——预算 ≤80KB)")


if __name__ == "__main__":
    render()
