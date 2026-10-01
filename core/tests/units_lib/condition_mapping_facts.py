"""检修降级映射正典表单一事实源（cond3 批 2026-10-01 C4 拆分件）。

输入:  cond 批简报 §4.1（市政 11 单元正典三元式逐字）+cond3 批简报
       §4.1（三线 11 单元——mine_water 6/sludge 2/conveyance 3，三线
       全同 target="n"/rule="n if pool.all_pools else n - 1"）+
       registry discover_units 档位声明（classify_boundary 推导真源）
输出:  CANONICAL/UNMAPPED（市政面）+CANONICAL_LINES/UNMAPPED_LINES
       （三线面）+classify_boundary（grid 档位声明→边界行为分类）。
       非 test_ 前缀=pytest 不收集（python_files 白名单外）——消费面=
       test_condition_mappings{,_boundary,_lines}.py 三件 importlib
       路径装载（包内测试零跨测试件 import 纪律，n1 电池同款口径）。
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（cond3 批 2026-10-01；cond/cond2 批表迁移+他线扩容）
#
# 【单一事实源】市政表自 test_condition_mappings.py 迁入（内容逐字
#   零变更——485 行预算墙拆分件）；三线表为本批新增。表键=unit_id，
#   值=(target, rule) 与各包 manifest 声明面字面恒等（test 件断言）。
# 【分类推导】classify_boundary(canonical) 由 registry 档位声明推导
#   （cond2 T3 oracle 泛化）：grid=None → 自由参数（target=1 装配过、
#   offline 归零走 compute 守卫响亮炸）；grid 非 None 且不含 1.0 →
#   档位下限≥2（target=1 装配期 _check_grid_hits 拒「档位」）。档位
#   声明即行为分类真源——禁硬编码名单；声明面翻转（grid 增 1.0 档）
#   时分类自动随动，计数锚红面=「翻转须走人」闸（boundary 件承载）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math

# 市政线 11 单元正典三元式表（unit_id → (target, rule)；cond 批 §4.1
# 逐字——target 键名与各包 manifest params 声明面逐一核对）。
CANONICAL: dict[str, tuple[str, str]] = {
    "municipal_cugeshan": ("n", "n if pool.all_pools else n - 1"),
    "municipal_xigeshan": ("n", "n if pool.all_pools else n - 1"),
    "municipal_chenshachi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_chuchenchi": ("n", "n if pool.all_pools else n - 1"),
    # 格数映射；n_pump_duty（泵台数）不映射——非池数降级语义。
    "municipal_tiaojiechi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_aao": ("n", "n if pool.all_pools else n - 1"),
    "municipal_cass": ("n_pool", "n_pool if pool.all_pools else n_pool - 1"),
    "municipal_gaomidu": ("n", "n if pool.all_pools else n - 1"),
    "municipal_vxinglvchi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_ziwai": (
        "n_channel",
        "n_channel if pool.all_pools else n_channel - 1",
    ),
    "municipal_erchunchi": ("n", "n if pool.all_pools else n - 1"),
}

# 市政线两单元不合格明示不映射（D4 拒检=诚实行为——空声明面锁定）。
UNMAPPED: tuple[str, ...] = (
    "municipal_bashi_jiliangcao",  # 单槽构筑物，无并行槽数参数
    "municipal_wushui_tisheng",  # n_pump_duty=ceil 计算值非参数；n_standby 纯计数回显
)

# 三线 11 单元正典三元式表（cond3 批 §4.1——mine_water 6/sludge 2/
# conveyance 3；三线全同 target/rule：target="n" 皆并联数参数键名）。
CANONICAL_LINES: dict[str, tuple[str, str]] = {
    # mine_water 6：全 grid=None 自由参数（分格数/池数/渠数构造参数）。
    "mine_water_tiaojiechi": ("n", "n if pool.all_pools else n - 1"),
    "mine_water_chenshachi": ("n", "n if pool.all_pools else n - 1"),
    "mine_water_ningjiao": ("n", "n if pool.all_pools else n - 1"),
    "mine_water_gaomidu": ("n", "n if pool.all_pools else n - 1"),
    "mine_water_vxinglvchi": ("n", "n if pool.all_pools else n - 1"),
    "mine_water_ziwai": ("n", "n if pool.all_pools else n - 1"),
    # sludge 2：n 池数 grid [2,3,4]（nongsuo 表交叉对照「≥2 grid」口径）。
    "sludge_nongsuo": ("n", "n if pool.all_pools else n - 1"),
    "sludge_xiaohua": ("n", "n if pool.all_pools else n - 1"),
    # conveyance 3：n 并联系列数 grid [2,3,4]（GB 50014 §7.1 并联系列≥2）。
    "conveyance_peishuijing": ("n", "n if pool.all_pools else n - 1"),
    "conveyance_jipeishuijing": ("n", "n if pool.all_pools else n - 1"),
    "conveyance_peishuiqu": ("n", "n if pool.all_pools else n - 1"),
}

# 三线 8 单元不合格明示不映射（cond3 批 §4.2——逐单元实义理由注记
# 在各 manifest 头注；此处仅锁空声明面）。
UNMAPPED_LINES: tuple[str, ...] = (
    "mine_water_input",  # 进水绑定非计算单元
    "mine_water_cifenli",  # 设备流道单机语义（流道几何归厂商样本）
    "sludge_hebing",  # 合建构无并联数
    "sludge_shusong",  # 压力管道输送
    "sludge_bengzhan",  # 泵台数 ceil 计算值非池数参数（wushui_tisheng 先例）
    "sludge_tuoshui",  # 脱水单机设备
    "sludge_ganhua",  # 干化单机设备
    "conveyance_jishuijing",  # 单井
)


def classify_boundary(
    canonical: dict[str, tuple[str, str]],
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    """正典键集 × manifest target spec 档位声明分类（cond2 T3 oracle 泛化）。

    grid=None → 自由参数（target=1 装配过；offline 归零走 compute 守卫
    响亮炸）；grid 非 None 且不含 1.0 → 档位下限≥2（target=1 装配期
    _check_grid_hits 拒）。grid 含 1.0 的单元落两表之外（n=1 合法档
    ——边界语义不存在；出现时守卫测试红面=分类须人工重审）。
    """
    from waterprint.units_lib import discover_units

    registry = discover_units()
    grid_bound: list[tuple[str, str]] = []
    free: list[tuple[str, str]] = []
    for unit_id, (target, _rule) in sorted(canonical.items()):
        spec = {s.field_id: s for s in registry[unit_id][0].params}[target]
        if spec.grid is None:
            free.append((unit_id, target))
        elif not any(math.isclose(1.0, step) for step in spec.grid):
            grid_bound.append((unit_id, target))
    return tuple(grid_bound), tuple(free)
