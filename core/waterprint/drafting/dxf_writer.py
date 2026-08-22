"""ezdxf 封装与文件落盘：全库唯一接触 ezdxf 的文件（DXF R2018/UTF-8）。

输入:  EntityGroup（各图纸文件的实体组）+ StyleTable
输出:  .dxf 文件（R2018 AC1032、UTF-8，可被 ODA 转 DWG）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_dxf_writer.py）
#
# 【公开接口】
#   write_dxf(entities: EntityGroup, styles: StyleTable,
#             out: Path, meta: DrawingMeta) -> Path
#   class DrawingMeta：title、condition_key、repro 三元组、
#      creator（"WaterPrint x.y.z"——审计字段进 DXF 变量）
#
# 【行为规格】
#   R1 唯一接触点（§13.3）：全库除本文件禁止 import ezdxf——中立
#      EntityGroup 描述（kind/坐标/文字/标注参数）在此翻译为 ezdxf
#      实体；翻译层可快照回归（内容哈希锁结构，§6.5）。
#   R2 输出基线（§12.5/ADR-006）：DXF R2018（AC1032）、UTF-8 编码、
#      图层/线型/文字样式从 styles 装配、DWG 转换是部署侧 ODA 外挂
#      （不在本文件，§12.7）。
#   R3 确定性落盘：同 EntityGroup 同字节（时间戳进 DXF 的字段固定为
#      meta 值，禁用当前时钟——快照回归与可复算前提）。
#   R4 路径安全（§18）：输出路径限制在配置输出目录内拼接 + 分量校验，
#      拒绝 ".."/绝对路径分量——越界抛领域异常。
#   R5 m→mm 换算唯一住所：图形实体坐标（结果 m）→ 出图 mm 的比例换算
#      在本文件统一执行（换算因子来自 SheetSpec 比例），各图纸文件
#      1:1 mm 语义（sheets R3 分工）。
#
# 【测试要求】R2018 版本头断言、UTF-8 中文文字实体往返、确定性双跑
#   字节级相同、路径越界拒绝、快照回归。
#
# 【参照】重写计划 §12.5/§18 路径安全；ADR-006；R6/R7 风险行
# ══════════════════════════════════════════════════════════════════
