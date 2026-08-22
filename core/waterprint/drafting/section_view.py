"""单体剖面图生成：池体纵剖/横剖（水位线/设备安装高程/标注）。

输入:  PlantResult 单元结果 + ElevationProfile（标高数据，经 app 装配）
       + styles + 图幅选择
输出:  剖面图 DXF 实体组
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_section_view.py）
#
# 【公开接口】
#   unit_section(unit_result, profile_station, styles, condition_key,
#                options: SectionOptions) -> EntityGroup
#   class SectionOptions：cut_position（剖切位置参数，如 1-1 剖面）、
#      annotation_level
#
# 【行为规格】
#   R1 剖切语义：剖面位置由平面图剖切符号联动（plan_view 声明剖切线，
#      section_view 按同一参数生成——剖切一致性由两文件共享
#      CutPosition 值对象保证）。
#   R2 标高数据唯一真源 = ElevationProfile（水面/池底/地面），
#      本文件禁止自行推算标高（总线消费，§16 A4）；水位线/池底线/
#      地面线三线齐备（M5 高程纵断图同源）。
#   R3 设备安装高程（曝气头距底、搅拌器浸深等）来自 assumptions/
#      结果字段，标注来源键。
#   R4 纯投影 + 零 ezdxf（同 plan_view R2）；标注完备性同 R3 条款。
#   R5 工况标注与三元组摘要（同 plan_view R4）。
#
# 【测试要求】三线（水面/池底/地面）实体存在、标高值 == Profile 值、
#   剖切位置联动一致、快照回归。
#
# 【参照】重写计划 §10.3/§12.5；ADR-006
# ══════════════════════════════════════════════════════════════════
