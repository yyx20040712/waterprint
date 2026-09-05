"""L3 图纸生成包根：参数化 DXF，纯计算无 UI（dxf_writer 是唯一 ezdxf 接触点）。

输入:  PlantResult / ElevationProfile / 样式基线（styles）
输出:  DXF 实体组（dxf_writer 落盘正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【导出白名单】
#   styles:          base_styles
#   sheets:          title_block, sheet_frame
#   plan_view:       unit_plan
#   section_view:    unit_section
#   site_plan:       site_layout
#   catalog:         catalog_sheet, sheet_origin_below
#   profile_drawing: profile_sheet
#   dxf_writer:      write_dxf
# 铁律：图纸是结果的纯投影（§10.2）；除 dxf_writer 外任何文件禁止
# import ezdxf（评审拒绝项，写进各文件规格）。
# ══════════════════════════════════════════════════════════════════
