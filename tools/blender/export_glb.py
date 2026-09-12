"""模板 glb 导出（spec §10 Blender 导出规约——批3 主体）。

输入:  build/clarifier_radial.blend（build_clarifier_radial.py 产物）
输出:  build/clarifier_radial.raw.glb（meshopt 压缩前——压缩归资产工序
        gltf-transform，见 tools/blender/README.md）

规格说明（spec §10）：
  - +Y up 恒（exporter yup 换轴 (x,z,−y)——§1 表同式）；
  - **勿 apply all transforms**（组节点 TRS 装配器要用——inst 原型
    平移位=instanceLayout 输入；本模板叶几何恒等式无修改器，无 apply 面）；
  - 剔除水面层（preview_only 集合不选——§2 glb 不含运行时水面）；
  - extras=custom props（__ax/__nc 双保险——§10）；
  - 无位图贴图（材质常量——materials.py 单源）。
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import bpy

BUILD = Path(__file__).resolve().parent / "build"


def _template_objects() -> list[bpy.types.Object]:
    """preview_only 集合外的全部网格对象（水面层剔除）。"""
    excluded = set()
    for coll in bpy.data.collections:
        if coll.name == "preview_only":
            excluded.update(coll.all_objects)
    return [o for o in bpy.data.objects
            if o.type == "MESH" and o not in excluded]


def export() -> None:
    blend = BUILD / "clarifier_radial.blend"
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    objects = _template_objects()
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    out = BUILD / "clarifier_radial.raw.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(out),
        export_format="GLB",
        use_selection=True,
        export_yup=True,          # +Y up 恒（§1）
        export_extras=True,       # __ax/__nc custom props → glTF extras
        export_apply=False,       # 勿 apply all transforms（§10）
        export_animations=False,
        export_skins=False,
        export_morph=False,
    )
    # GLB 结构快报（JSON chunk 节点名/材质/tri 预算——导出面自检）
    data = out.read_bytes()
    magic, _version, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, f"GLB magic 非法：{magic:#x}"
    json_len, json_type = struct.unpack_from("<II", data, 12)
    assert json_type == 0x4E4F534A
    doc = json.loads(data[20:20 + json_len])
    nodes = [n.get("name", "?") for n in doc.get("nodes", [])]
    tris = 0
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            count = doc["accessors"][prim["indices"]]["count"]
            tris += count // 3
    print(f"[GLB] {out.name}: {length / 1024:.1f} KB, nodes={len(nodes)}, "
          f"tris={tris}（预算 ≤8000）")
    for name in nodes:
        print(f"  node: {name}")
    assert tris <= 8000, f"单族 tri 超预算：{tris} > 8000（spec §10）"


if __name__ == "__main__":
    export()
