"""矿井水线单元包根（8 个单元包，M3 交付）。

输入:  各单元包的 manifest/compute 白名单导出
输出:  线级导出聚合（供 units_lib.discover_units 扫描）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M0.5 结构接线：8 包骨架已就位，内容随 M3 交付）
#
# 【本线单元包（8）】
#   input 矿井水输入、tiaojiechi 调节池、chenshachi 平流沉砂池、
#   ningjiao 混凝反应、cifenli 磁分离、gaomidu 高密沉淀、
#   vxinglvchi V型滤池、ziwai 紫外消毒
#
# 【典型流程链】input → tiaojiechi → chenshachi → ningjiao
#   →（cifenli）→ gaomidu → vxinglvchi → ziwai → 回用/排放
#
# 【边界警示（§14.3）】与市政线同名构筑物各自成包（tiaojiechi/
#   chenshachi/gaomidu/vxinglvchi/ziwai）——规范依据、参数范围、
#   出水目标不同，禁止跨线 import 或参数复用；golden 案例为
#   43,836 m3/d III类（mine_43836）。
# ══════════════════════════════════════════════════════════════════
