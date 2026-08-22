"""厂区总平面图：构筑物布置 + 道路管线走廊 + 坐标网（M5 交付）。

输入:  厂区布置数据（M5 布置编辑器产物，design 态）+ PlantResult + styles
输出:  总平面图 DXF 实体组
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_site_plan.py）
#
# 【公开接口】
#   site_layout(site_design, plant_result, styles,
#               options: SiteOptions) -> EntityGroup
#   class SiteOptions：coord_grid（坐标网间距）、风玫瑰（数据条目）
#
# 【行为规格】
#   R1 里程碑边界（M5）：依赖厂区布置编辑器的数据 schema；M0~M4 期间
#      本文件保持骨架——接口签名先冻结（防 M5 起步时推翻消费方）。
#   R2 布置是设计输入（design 态）：构筑物摆放/间距/道路走向来自用户
#      编辑保存的 site_design，不是自动布局结果；自动布局辅助
#      （若做）是独立功能，产出写入 site_design 后再出图。
#   R3 构筑物轮廓尺寸来自 PlantResult（纯投影）；间距/防火间距校核
#      属 constraint_kb 数据约束（警告通道，不在出图代码里判）。
#   R4 图纸目录联动：本图图号进入 sheets 标题栏与图纸目录页
#      （图纸目录批量出图 = M5，实体生成复用 sheets）。
#   R5 纯投影 + 零 ezdxf（同 plan_view R2）。
#
# 【测试要求】（M5 实装时细化）M0 期仅冻结：模块存在 + 契约头 +
#   接口签名稳定性由 test_site_plan.py 的结构断言守卫。
#
# 【参照】重写计划 §7 M5/§10.3 厂区图纸行；ADR-006
# ══════════════════════════════════════════════════════════════════
