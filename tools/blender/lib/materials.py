"""模板材质库（批3 迭代二——STYLE-BASE.md 材质板·glb 自持多档）。

输入:  材质 token（本表=风格基准材质板真源——混凝土三档/金属三档+
        驱动亮银/缝色/水体）
输出:  ensure_material（ Principled BSDF 常量材质——无位图贴图
        [spec §10 PBR 常量·体积预算前提]）

规格说明（STYLE-BASE.md §1——2026-09-12 用户批注 a+ds 复审参数
  [.workflow/b3-probe/thumb-review-ds.md] 逐条固化；交接 §一.2 裁定：
  **glb 材质自持多档**，FE 模板走 glb 材质单源——本表与
  semanticColors.ts[PoolBox 原语面]分立互不约束（spec §10 材质=glb
  单源）；water_surface 仍同值镜像（preview 层与 FE 水色同源纪律）。
  程序糙度=混凝土档噪声 bump（幅度 0.03/特征尺度≈2.9m 落 2~5m 带）
  ——**仅渲染面消费**且**仅挂 Normal 输入**（门一 W2 实测：链接任何
  因子输入即使导出器丢常量——baseColorFactor=None=glb 面落白；法向
  无因子导出面恒安全）。glb 面平粗糙度=远景可接受，记档 STYLE-BASE §1。
"""

from __future__ import annotations

import bpy  # noqa: F401 —— Blender 内嵌运行（-b -P）

# STYLE-BASE.md §1 材质板（basecolor sRGB→linear 由 Blender 输入口处理）
PALETTE = {
    # 混凝土三档（较 #a3a9ad 明度再降 12~18%——ds 复审）
    "concrete_wall": (0xB8 / 255, 0xB8 / 255, 0xB1 / 255, 1.0),   # 池壁
    "concrete_walk": (0xC0 / 255, 0xBE / 255, 0xB6 / 255, 1.0),   # 走道/桥面
    "concrete_coping": (0xA8 / 255, 0xA8 / 255, 0xA2 / 255, 1.0),  # 压顶/堰槽
    # 金属三档+驱动亮银（ds 复审分档——栏杆/筒/桥各持档）
    "steel_rail": (0xC9 / 255, 0xCD / 255, 0xD1 / 255, 1.0),   # 不锈钢栏杆
    "steel_well": (0x6F / 255, 0x7A / 255, 0x82 / 255, 1.0),   # 灰蓝钢·中心筒
    "steel_bridge": (0x5E / 255, 0x69 / 255, 0x71 / 255, 1.0),  # 结构钢·桁架
    "steel_drive": (0xD0 / 255, 0xD4 / 255, 0xD8 / 255, 1.0),  # 驱动亮银
    # 分缝缝内色（ds 复审 #8E8E88——单面装饰条带消费）
    "joint": (0x8E / 255, 0x8E / 255, 0x88 / 255, 1.0),
    # 水体（preview 层专用——semanticColors water_surface 同值镜像）
    "water_surface": (0x2F / 255, 0x7F / 255, 0xD1 / 255, 1.0),
}

# PBR 常量档（STYLE-BASE §1 逐档）
_ROUGHNESS = {
    "concrete_wall": 0.84, "concrete_walk": 0.86, "concrete_coping": 0.78,
    "steel_rail": 0.31, "steel_well": 0.42, "steel_bridge": 0.50,
    "steel_drive": 0.25, "joint": 0.90, "water_surface": 0.12,
}
_METALLIC = {
    "concrete_wall": 0.0, "concrete_walk": 0.0, "concrete_coping": 0.0,
    "steel_rail": 1.0, "steel_well": 0.90, "steel_bridge": 0.90,
    "steel_drive": 1.0, "joint": 0.0, "water_surface": 0.0,
}

# 程序噪声 bump 档（仅混凝土族——渲染面消费，导出面自然剔除）
_NOISE_BUMP = {"concrete_wall", "concrete_walk", "concrete_coping"}
_BUMP_STRENGTH = 0.03      # 幅度带 0.01~0.02 上探——缩略尺度可辨权衡
_NOISE_SCALE = 0.35        # 特征尺度≈1/0.35≈2.9m（2~5m 带）


def _add_noise_bump(material: bpy.types.Material) -> None:
    """混凝土程序糙度（Noise→Bump→Normal——无贴图约束下的渲染面近似）。

    **导出纪律（门一 W2 实测记档）**：任何 Principled 输入一旦被链接，
    glTF 导出器即无法回提常量因子——baseColorFactor 消失=glb 面落
    默认白。故 **只允许 Normal 输入接程序节点**（法向无因子导出面）；
    Base Color/Roughness/Metallic 恒常量（色斑驳曾以 Mix 挂 Base
    Color——实测三档混凝土导出 None 即撤）。
    """
    tree = material.node_tree
    bsdf = tree.nodes.get("Principled BSDF")  # type: ignore[union-attr]
    noise = tree.nodes.new("ShaderNodeTexNoise")  # type: ignore[union-attr]
    noise.inputs["Scale"].default_value = _NOISE_SCALE  # type: ignore[index]
    noise.inputs["Detail"].default_value = 4.0  # type: ignore[index]
    noise.inputs["Roughness"].default_value = 0.55  # type: ignore[index]
    bump = tree.nodes.new("ShaderNodeBump")  # type: ignore[union-attr]
    bump.inputs["Strength"].default_value = _BUMP_STRENGTH  # type: ignore[index]
    tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])  # type: ignore[union-attr]
    tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])  # type: ignore[union-attr]


def ensure_material(token: str, *, alpha: float = 1.0) -> bpy.types.Material:
    """按 token 取/建共享材质（同名复用——单模板一材质实例）。"""
    name = f"wp_{token}"
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")  # type: ignore[union-attr]
    rgba = PALETTE[token]
    bsdf.inputs["Base Color"].default_value = rgba  # type: ignore[index]
    bsdf.inputs["Roughness"].default_value = _ROUGHNESS[token]  # type: ignore[index]
    bsdf.inputs["Metallic"].default_value = _METALLIC[token]  # type: ignore[index]
    if alpha < 1.0:
        material.blend_method = "BLEND"
        bsdf.inputs["Alpha"].default_value = alpha  # type: ignore[index]
    if token in _NOISE_BUMP:
        _add_noise_bump(material)
    return material
