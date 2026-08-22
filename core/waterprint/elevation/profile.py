"""水面/池底/埋深/超高沿程推算：从进厂标高沿流程拓扑生成纵断数据。

输入:  PlantResult（各单元几何结果）+ Losses + 进厂水面标高配置 + assumptions（超高）
输出:  纵断数据（每单元：水面/池底/埋深/地面标高序列，按 condition_key）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/elevation/test_profile.py）
#
# 【公开接口】
#   build_profile(plant_result, losses, inlet_config, assumptions,
#                 condition_key) -> ElevationProfile
#   class ElevationProfile(不可变)：stations（沿流程有序的单元序列）、
#       每站 {water_level, floor_elev, ground_elev, bury_depth, freeboard}、
#       condition_key、trace（公式迹）
#
# 【行为规格】
#   R1 推算方向：自进厂水面标高起，沿流程拓扑逐单元扣损失、定水面、
#      由水深定池底、由超高假设定埋深——顺序与中间量显式进计算迹。
#   R2 超高等默认值只经 assumptions 取得（带出处）；进厂标高是设计输入
#      （design 态），不是假设（§14.3"折叠为配置"）。
#   R3 按工况索引：design/avg 两档与检修敏感性工况各自成 Profile
#      （水位不同），condition_key 贯穿标注。
#   R4 埋深越界（过深/出地面）产生 Warning（非异常——留给用户决策），
#      Warning 进结果供 UI/图纸标注。
#   R5 纵断数据是 drafting/profile_drawing（高程纵断图）与
#      cost（土方按实际挖深，M3 高程-概算联动）的唯一数据源——
#      两处消费同一 Profile，不存在第二份推导。
#
# 【测试要求】线性三单元纵断连续性（下游水面 <= 上游水面 − 损失）、
#   工况档差异、超高来源断言、越界 Warning 触发。
#
# 【参照】重写计划 §13.3/§14.3 折叠行/§16 A4 总线消费
# ══════════════════════════════════════════════════════════════════
