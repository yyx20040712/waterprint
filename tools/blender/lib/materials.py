"""模板材质库（批3 主体——与 three 场景同色值表单源）。

输入:  语义 token（与 webapp shared/ui/semanticColors.ts 同键同值——
        pool_wall #8d99a6 / water_surface #2f7fd1 / pipe(钢构) #5b8db8）
输出:  ensure_material（ Principled BSDF 常量材质——无位图贴图
        [spec §10 PBR 常量·体积预算前提]）

规格说明（spec §10 Blender 侧导出规约；色值零新字面量——增改色走
  semanticColors.ts 真源同步[单一来源纪律]，本表仅镜像三键）。
"""

from __future__ import annotations

import bpy  # noqa: F401 —— Blender 内嵌运行（-b -P）

# 与 shared/ui/semanticColors.ts 同值镜像（改色须双端同窗——R-G3 族）
PALETTE = {
    "pool_wall": (0x8D / 255, 0x99 / 255, 0xA6 / 255, 1.0),  # 灰白混凝土
    "steel": (0x5B / 255, 0x8D / 255, 0xB8 / 255, 1.0),  # 钢构（pipe 同值）
    "water_surface": (0x2F / 255, 0x7F / 255, 0xD1 / 255, 1.0),  # 蓝水体（PNG 专用层）
}

# PBR 常量档：混凝土哑光/钢材半光泽/水面低粗糙（透明度走材质 alpha）
_ROUGHNESS = {"pool_wall": 0.9, "steel": 0.45, "water_surface": 0.12}
_METALLIC = {"pool_wall": 0.0, "steel": 0.55, "water_surface": 0.0}


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
    return material
