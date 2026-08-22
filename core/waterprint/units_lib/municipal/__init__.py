"""市政污水线单元包根（13 个单元包，M2 交付）。

输入:  各单元包的 manifest/compute 白名单导出
输出:  线级导出聚合（供 units_lib.discover_units 扫描）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M0.5 结构接线：13 包骨架已就位，内容随 M2 交付）
#
# 【本线单元包（13，业务总表见 docs/structure-graph.md §3）】
#   cugeshan 粗格栅、xigeshan 细格栅、chenshachi 旋流沉砂池、
#   chuchenchi 辐流初沉池、tiaojiechi 调节池、aao AAO 生物池、
#   cass CASS 生物池、gaomidu 高密沉淀池、vxinglvchi V型滤池、
#   ziwai 紫外消毒（10 核心）+ erchunchi 辐流二沉池、
#   bashi_jiliangcao 巴歇尔计量槽、wushui_tisheng 污水提升泵房
#   （并入的 3 个社区单元）
#
# 【典型流程链】进水 → wushui_tisheng → cugeshan → xigeshan
#   → chenshachi →（chuchenchi | tiaojiechi）→（aao | cass）
#   → erchunchi → gaomidu → vxinglvchi → ziwai → bashi_jiliangcao → 排放
#
# 【规则】本 __init__ 只做白名单聚合导出，零计算逻辑；
#   单元包互相 import = CI 失败（import-linter 独立性契约）。
# ══════════════════════════════════════════════════════════════════
