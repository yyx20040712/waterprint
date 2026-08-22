"""单体平面图生成：manifest 驱动的池体平面布置（管道/设备/标注）。

输入:  PlantResult 单元结果（几何字段 ID）+ styles 样式表 + 图幅选择
输出:  平面图 DXF 实体组（1:1 mm，布图缩放归 SheetSpec/调用方）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_plan_view.py）
#
# 【公开接口】
#   unit_plan(unit_result, manifest, styles, condition_key,
#             options: PlanOptions) -> EntityGroup
#   class PlanOptions：annotation_level（主要尺寸/全部尺寸）、
#      pipe_routing（是否画连接管示意）
#
# 【行为规格】
#   R1 manifest 驱动：图元来源 = manifest 声明的几何字段 ID（哪些尺寸
#      上图由清单声明，加单元不改出图代码——§13.6 四件套的图纸半）。
#   R2 纯投影：尺寸/个数只按字段 ID 取数；本文件零业务公式、
#      零中文匹配、零 ezdxf import（实体类型是本包内中立描述，
#      由 dxf_writer 翻译——保证可快照回归与渲染器无关）。
#   R3 标注完备性（M2 验收"AutoCAD 中标注完整可读"）：总尺寸/分格
#      尺寸/管径标注/标高符号；标注文字经 styles 文字样式；
#      数字单位与结果字段一致（mm 出图时换算在 dxf_writer 统一处理，
#      换算规则挂 scene/drafting 公共约定）。
#   R4 工况标注：图纸右下角注明 condition_key 与三元组摘要
#      （可复算，§14.1"图纸标注所属工况"）。
#   R5 性能：<5s/单元（§18.1，benchmark 守卫）。
#
# 【测试要求】已知矩形池平面实体数量/坐标断言、标注实体存在性、
#   工况/三元组标注、快照回归（内容哈希）。
#
# 【参照】重写计划 §10.3 单体图纸行/§12.5/§13.6；ADR-006
# ══════════════════════════════════════════════════════════════════
