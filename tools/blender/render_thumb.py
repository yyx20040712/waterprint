"""模板缩略图出图（P4 轻透视 50mm 等效——透明底；段二用户裁定四项
画质升级 2026-09-13：引擎全量切 Cycles[OptiX 实测 512² 仅 2.1s]/
材质拟真[HDRI 环境]/分辨率 512→1024/取景全包络不裁角）。

输入:  build/<family>.blend（FAMILY 环境变量选族，缺省 clarifier_radial）
输出:  build/<family>.png（1024² RGBA——资产落位归资产工序）

规格说明（STYLE-BASE §二 v1.1——冻结面变更批：引擎/分辨率/环境/取景
  四项经用户裁定，三族重渲+三段流+验收随批；曝光档 EV −1.15+AgX 沿
  v1.0 基准数值，目标主体中位 48~58%/峰值 ≤0.92 复验口径不变）。
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

BUILD = Path(__file__).resolve().parent / "build"
FAMILY = os.environ.get("FAMILY", "clarifier_radial")

# 取景包络（含走道/栏杆外挑全幅度——首版只算池壁：CASS 左缘 352px
# 越框实录[用户裁定③取景全包络]；竖向含 equip 越顶；取景中心高度）
ENVELOPES: dict[str, tuple[float, float, float, float]] = {
    "clarifier_radial": (43.2, 43.2, 5.3, 2.6),   # 栏杆环 R21.5+管径→43.2
    "aao_corridor": (98.2, 41.2, 6.9, 3.0),      # 走道外挑 49.1/20.6
    "cass_batch": (51.7, 22.7, 6.8, 3.0),        # 25.85/11.35
}

SIZE = 1024                   # 用户裁定②分辨率提升（512→1024）
FOCAL_MM = 50.0               # P4 轻透视 50mm 等效（36mm 传感器）
CAM_DIR = Vector((1.0, 0.85, 1.05))  # iso 方向（俯角≈36°）
FIT_MARGIN = 1.08             # 用户裁定③取景全包络（球面切框余量 1.00→
                              # 1.08——1.00 恰切=包络角越框裁角实录）
EXPOSURE_EV = -0.85           # Cycles 物理光照提档（Eevee -1.15 实测中位
                              # 44/38/36 低于带——+0.3EV 复验 48~58 带内）
SUN_ENERGY = 3.3
FILL_ENERGY = 1.2
HDRI_PATH = r"D:\blender_work\HDRI\studio_small_08_4k.exr"  # 用户指定库
HDRI_STRENGTH = 0.50          # HDRI=环境反射/补光（0.55 实测辐流峰值 92.4%
                              # 微超 0.92 带——降 0.05 复验）
CYCLES_SAMPLES = 128          # OptiX 降噪档（5070Ti 实测 2.1s@512² 档）


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

    # 取景：外接球半径=对角/2；dist=r/tan(half_fov)×margin（球面切框
    # 余量 1.08——全构筑物入框不裁角[用户裁定③]）
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

    # 布光：日光源（阴影定义）+HDRI 世界环境（用户指定 D:\blender_work
    # \HDRI——金属反射/环境光真实来源[材质拟真裁定①]）
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
    tree = world.node_tree
    bg = tree.nodes["Background"]  # type: ignore[union-attr]
    env_tex = tree.nodes.new("ShaderNodeTexEnvironment")  # type: ignore[union-attr]
    try:
        env_tex.image = bpy.data.images.load(HDRI_PATH)  # type: ignore[union-attr]
        tree.links.new(env_tex.outputs["Color"], bg.inputs["Color"])  # type: ignore[union-attr]
    except (RuntimeError, OSError):
        print(f"[FALLBACK] HDRI 不可读：{HDRI_PATH}——纯色环境顶替")
        bg.inputs[0].default_value = (0.80, 0.81, 0.83, 1.0)  # type: ignore[index]
    bg.inputs[1].default_value = HDRI_STRENGTH  # type: ignore[index]
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

    # 引擎全量切 Cycles（用户裁定——OptiX GPU+降噪；设备不可用回退
    # CPU 安全档并记录）
    scene.render.engine = "CYCLES"
    scene.cycles.samples = CYCLES_SAMPLES
    scene.cycles.use_denoising = True
    try:
        cycles_prefs = bpy.context.preferences.addons["cycles"].preferences
        cycles_prefs.compute_device_type = "OPTIX"
        cycles_prefs.get_devices()
        for dev in cycles_prefs.devices:
            dev.use = dev.type == "OPTIX"
        scene.cycles.device = "GPU"
        print(f"[GPU] OptiX on: {[d.name for d in cycles_prefs.devices if d.use]}")
    except Exception as exc:  # noqa: BLE001 —— 设备面回退非致命
        print(f"[GPU-FALLBACK] OptiX 不可用（{exc}）——CPU 档")
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.film_transparent = True
    out = BUILD / f"{FAMILY}.png"
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print(f"[PNG] {out} ({out.stat().st_size / 1024:.1f} KB——1024² 预算随"
          " 分辨率档调，check_templates 口径同步）")
if __name__ == "__main__":
    render()
