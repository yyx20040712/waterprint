"""污泥合并清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/sludge_hebing.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.6.0 键名（factor.hebing.* 裸短名 12 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ HB-F1~HB-F13 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "sludge_hebing"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（三股排泥=市政 34760 案例实值：
#   ds_primary=3240.12/p_primary=0.96/ds_bio=1928.690/p_bio=0.994/
#   ds_chem=137.7050/p_chem=0.98 + 衡算面 q_avg_daily=34760.7/
#   s0_bod=123.2996/se_bod=12.32996/v_bio=10714.95/x_vss=3000/
#   t_design=15——表"衔接参数"节逐字）；系数不落本表——产率 y/y 带/
#   合成产率 Y 及带/Kd₂₀ 及带/θ/互校偏差上限/高程水损共 12 键全经
#   factor.hebing.*（裸短名——app._unit_params 剥 sludge_ 前缀投影）；
#   removal_refs 全空（污泥单元零 removal 键——manifest 声明面注记，
#   removal_rates.yaml 0.6.0 零新增口径）。
# 【公式注册（D1）】HB-F1~HB-F13 逐条 FormulaSpec+register；expression=
#   表公式串逐字（汇流三式 HB-F6/F7 与 contracts.sludge.mix P4 干基
#   质量恒等镜像）；无 π 无构造档取整；1000 为 kg/t·mg/L 换算常量、
#   20 为 Kd 温度修正基准 ℃（表串原文常量，本文件=units_lib manifest
#   白名单区）。
# 【单位换算（实装面）】表公式全按工程口径 m³/d、kg/d；出流 SludgeFlow
#   契约口径 m3/s、kg/s——SECS_PER_DAY 模块常量（表头"单位换算归
#   M3b2 实装面"授权；本文件=数值白名单区）由 compute 消费。
# 【图源形态】GOLDEN4a D1 起三股 IN 口实体化（in_primary/in_bio/
#   in_chem——上游产泥单元 sludge_out 口接通面，GOLDEN4b 真环基础）；
#   三口无边=参数注入模式（现行行为不变），全有边=入流直值模式（D2
#   双模，compute 消费）；ports=三 IN 口+一出流口，全 SLUDGE。
# 【声明五件】params（含水率三参数 (0,1) 域在 compute 守卫，无出处带
#   不设 range）/ports 三 IN+一 OUT 全 SLUDGE（GOLDEN4a D1）/removal_refs
#   空映射/norm_refs
#   双源标记（GB 50014-2021 §8.1+给水排水设计手册第 5 册；CJJ
#   131-2009 仅叙述列）/condition_mappings=()/constraint_refs 一键
#   （互校偏差上限——表唯一显式校核带）。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "sludge_hebing"

_GB = (
    "GB 50014-2021 §8.1（污泥量计算——§8.1.4 表 5 污泥产率 y，ADR-008 ④"
    " 拍板口径；条号随追认核对；docs/norms/sludge_hebing.md 起草表"
    " 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》污泥处理章（污泥量衡算/"
    "含水率换算/活性污泥动力学；docs/norms/sludge_hebing.md 起草表"
    " 2026-08-27，待追认）"
)
_ADR = (
    "ADR-008 ④（工艺计算方法路线——经验产率法主线+机理互校已拍板，"
    "2026-08-22；偏差>20% 出警告提示核对 SS/BOD 比）"
)
_D = DimKey.DIMENSIONLESS

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s——表头
# "单位换算归 M3b2 实装面"授权；manifest=数值白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "HB-F1",
        "q_primary = ds_primary / ((1 - p_primary) * 1000)",
        {
            "ds_primary": (_D, "初沉股干泥 kg/d（参数——市政表 CC-F10 衔接实值）"),
            "p_primary": (_D, "初沉污泥含水率（参数 p_primary）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "HB-F2",
        "q_bio = ds_bio / ((1 - p_bio) * 1000)",
        {
            "ds_bio": (_D, "剩余污泥股干泥 kg/d（参数——aao 表 AO-F6~F7 衔接实值）"),
            "p_bio": (_D, "剩余污泥含水率（参数 p_bio）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "HB-F3",
        "q_chem = ds_chem / ((1 - p_chem) * 1000)",
        {
            "ds_chem": (_D, "化学污泥股干泥 kg/d（参数——gaomidu 表 GM-F12~F13 衔接实值）"),
            "p_chem": (_D, "化学污泥含水率（参数 p_chem）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "HB-F4",
        "ds_total = ds_primary + ds_bio + ds_chem",
        {
            "ds_primary": (_D, "初沉股干泥 kg/d"),
            "ds_bio": (_D, "剩余污泥股干泥 kg/d"),
            "ds_chem": (_D, "化学污泥股干泥 kg/d"),
        },
        _D,
        "contracts.sludge.mix R1 镜像（汇流 Σds 守恒）",
    ),
    FormulaSpec(
        "HB-F5",
        "q_total = q_primary + q_bio + q_chem",
        {
            "q_primary": (_D, "初沉股湿泥量 m³/d（HB-F1）"),
            "q_bio": (_D, "剩余污泥股湿泥量 m³/d（HB-F2）"),
            "q_chem": (_D, "化学污泥股湿泥量 m³/d（HB-F3）"),
        },
        _D,
        "contracts.sludge.mix R1 镜像（汇流 Σq_wet）",
    ),
    FormulaSpec(
        "HB-F6",
        (
            "w_water = ds_primary * p_primary / (1 - p_primary)"
            " + ds_bio * p_bio / (1 - p_bio)"
            " + ds_chem * p_chem / (1 - p_chem)"
        ),
        {
            "ds_primary": (_D, "初沉股干泥 kg/d"),
            "p_primary": (_D, "初沉污泥含水率"),
            "ds_bio": (_D, "剩余污泥股干泥 kg/d"),
            "p_bio": (_D, "剩余污泥含水率"),
            "ds_chem": (_D, "化学污泥股干泥 kg/d"),
            "p_chem": (_D, "化学污泥含水率"),
        },
        _D,
        "contracts.sludge.mix P4 镜像（干基水质量恒等 kg/d）",
    ),
    FormulaSpec(
        "HB-F7",
        "p_merged = w_water / (w_water + ds_total)",
        {
            "w_water": (_D, "合并股水质量 kg/d（HB-F6）"),
            "ds_total": (_D, "合并干泥量 kg/d（HB-F4）"),
        },
        _D,
        "contracts.sludge.mix P4 镜像（含水率干基反解——非简单平均）",
    ),
    FormulaSpec(
        "HB-F8",
        "s_y = q_avg_daily * (s0_bod - se_bod) * y_yield / 1000",
        {
            "q_avg_daily": (_D, "平均日流量 m³/d（参数——全厂水线口径）"),
            "s0_bod": (_D, "生物池进水 BOD5 mg/L（参数，aao 表衔接式）"),
            "se_bod": (_D, "生物池出水 BOD5 mg/L（参数）"),
            "y_yield": (_D, "污泥产率 y（factor.hebing.yield.y——GB §8.1.4 表 5）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "HB-F9",
        "k_dt = k_d20 * theta_kd ** (t_design - 20)",
        {
            "k_d20": (_D, "自身氧化率 Kd@20℃ d⁻¹（factor.hebing.k_decay20）"),
            "theta_kd": (_D, "Kd 温度修正系数 θ（factor.hebing.theta_kd）"),
            "t_design": (_D, "设计水温 ℃（参数 t_design，20=修正基准）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "HB-F10",
        (
            "dx_bio = y_syn * q_avg_daily * (s0_bod - se_bod) / 1000"
            " - k_dt * v_bio * x_vss / 1000"
        ),
        {
            "y_syn": (_D, "合成产率 Y（factor.hebing.yield_syn）"),
            "q_avg_daily": (_D, "平均日流量 m³/d"),
            "s0_bod": (_D, "生物池进水 BOD5 mg/L"),
            "se_bod": (_D, "生物池出水 BOD5 mg/L"),
            "k_dt": (_D, "温度修正 Kd d⁻¹（HB-F9）"),
            "v_bio": (_D, "生物池容积 m³（参数，aao 表主算例值）"),
            "x_vss": (_D, "MLVSS mg/L（参数，aao 表主算例值）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "HB-F11",
        "dev_pct = abs(s_y - dx_bio) / s_y * 100",
        {
            "s_y": (_D, "经验产率法剩余污泥量 kg/d（HB-F8）"),
            "dx_bio": (_D, "机理互校产率 kg/d（HB-F10）"),
        },
        _D,
        _ADR,
    ),
    FormulaSpec(
        "HB-F12",
        "ds_check = ds_primary + s_y + ds_chem",
        {
            "ds_primary": (_D, "初沉股干泥 kg/d"),
            "s_y": (_D, "产率法剩余污泥量 kg/d（HB-F8）"),
            "ds_chem": (_D, "化学污泥股干泥 kg/d"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "HB-F13",
        "dev_close = abs(ds_total - ds_check) / ds_total * 100",
        {
            "ds_total": (_D, "汇流干泥量 kg/d（HB-F4）"),
            "ds_check": (_D, "产率法口径全厂干泥量 kg/d（HB-F12）"),
        },
        _D,
        _GB,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

# GOLDEN4a D2 双模（2026-08-28）：三股湿量式 HB-F1~F3 在入流直值模式
# 不重算（入流即真值——避免双源冲突），入流模式 formula_ids 用此收窄集
# （审计口径：formula_ids=本次实际应用公式——与 trace 一致）。
_STOCK_FORMULA_IDS = frozenset({"HB-F1", "HB-F2", "HB-F3"})
FORMULA_IDS_FLOW: tuple[str, ...] = tuple(
    spec.formula_id for spec in _FORMULAS if spec.formula_id not in _STOCK_FORMULA_IDS
)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.sludge_hebing",
        "version": "1.0",
        "business_line": "sludge",
        # 默认值=表主算例逐字（出处 docs/norms/sludge_hebing.md"衔接参数"节）；
        # 含水率三参数 (0,1) 开域、ds 三股/流量/水质/BOD 对均无出处带——
        # 不设 range/grid（域守卫在 compute，缺出处不编造档位）
        "params": [
            {"field_id": "ds_primary", "dim": "DIMENSIONLESS", "default": 3240.12},
            {"field_id": "p_primary", "dim": "DIMENSIONLESS", "default": 0.96},
            {"field_id": "ds_bio", "dim": "DIMENSIONLESS", "default": 1928.690},
            {"field_id": "p_bio", "dim": "DIMENSIONLESS", "default": 0.994},
            {"field_id": "ds_chem", "dim": "DIMENSIONLESS", "default": 137.7050},
            {"field_id": "p_chem", "dim": "DIMENSIONLESS", "default": 0.98},
            {"field_id": "q_avg_daily", "dim": "DIMENSIONLESS", "default": 34760.7},
            {"field_id": "s0_bod", "dim": "CONCENTRATION", "default": 123.2996},
            {"field_id": "se_bod", "dim": "CONCENTRATION", "default": 12.32996},
            {"field_id": "v_bio", "dim": "VOLUME", "default": 10714.95},
            {"field_id": "x_vss", "dim": "CONCENTRATION", "default": 3000.0},
            {"field_id": "t_design", "dim": "DIMENSIONLESS", "default": 15.0},
        ],
        # GOLDEN4a D1（2026-08-28）：三股 IN 口实体化（in_primary/in_bio/
        # in_chem——与 ds_primary 参数族对应）+出流一口 SLUDGE。三口全无边
        # =参数注入模式（现行三案例形态，行为逐字节不变）；全有边=入流
        # 直值模式（GOLDEN4b 真边接通）；部分有边=compute 显式拒。
        "ports": [
            {"port_id": "in_primary", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "in_bio", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "in_chem", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        # 污泥单元无水质去除概念——removal_refs 恒空（泥量/含水率变换，
        # removal_rates.yaml 0.6.0 零新增；M3b1 变更记录注记在册）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §8.1（污泥量计算——§8.1.4 表 5 产率 y；条号随追认核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》污泥处理章"
            "（污泥量衡算/含水率换算/活性污泥动力学常用带）",
            "docs/norms/sludge_hebing.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认；CJJ 131-2009 仅叙述性依据——"
            "数值 source 不标，I3 挂账）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "sludge_hebing.dev_band",
        ],
    }
)
