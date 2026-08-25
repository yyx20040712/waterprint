"""巴歇尔计量槽清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  三表起草真源（docs/norms/bashi_jiliangcao.md，2026-08-26，数据策略 v2 待追认）+
       data/coefficients 0.4.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ BL-F1~F9 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收；公式路线 =
#   B7 七档全档流量式主线 Q=C·h^n——C/n/scrit/hmin/hmax 逐档从手册
#   标准型表录入，"CJ/T 3008.3-1993 正式文本核对"降级为追认点注记
#   [business-logic §10 Q3 挂账口径]）
#
# 【固定形态】UNIT_ID = "municipal_bashi_jiliangcao"；manifest =
#   load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 逐字（b_throat=0.75 m，b075 档
#   主算例选档——563 L/s ≈ 51% 满档能力）；系数不落本表——七档
#   C/n/scrit/hmin/hmax 共 35 键+构造常量 4 键+hb_design/loss_ratio/
#   elevation_loss 全部经 factor.bashi_jiliangcao.* 键消费
#   （app._unit_params 投影）；去除率经 removal.bashi_jiliangcao.*.
#   mod_default（计量单元零去除，全 0.0；NH3N/TN/TP 不建条目）。
# 【公式注册（D1）】BL-F1~F9 逐条 FormulaSpec+register；expression=
#   三表公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；
#   换算/构造常量（1000[流量 m³/s→L/s]/1.2/0.48/0.5/0.3[手册标准型
#   构造尺寸表回归系数，逐档验证]）内联（本文件=units_lib manifest
#   白名单区，出处=norm_ref）。无 ceil 离散（喉宽=grid 档位直接取值）。
# 【档位声明（Ruling ④/business-logic §7）】喉宽 b_throat grid=B7
#   七档 [0.25,0.45,0.75,1.0,1.2,1.5,2.1]——简报枚举值 0.5/1.25/2.0
#   非手册标准喉宽档，按最近标准档映射 0.45/1.20/2.10（起草表追认
#   点 1）；compute 只保 b>0+档位命中，档位面经 grid 声明承载。
# 【声明五件】params（b_throat 单参数无 range=grid 承载选档面）/
#   ports 两口 WATER/removal_refs（零去除键同引用）/norm_refs 双源
#   标记（GB 50014-2021+给水排水设计手册+CJ/T 核对追认注记）/
#   condition_mappings=()/constraint_refs 14 键（七档 ha 适用带+七档
#   淹没度，逐档生成——选档切换时各档表达式独立成立）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_bashi_jiliangcao"

# B7 七档档名（factor.bashi_jiliangcao.flume.<档名>.* 键段）——与
# data/coefficients 0.4.0 键名逐字对齐（手册标准型喉宽档）。
GRADES: tuple[str, ...] = ("b025", "b045", "b075", "b100", "b120", "b150", "b210")
_THROAT_GRID: tuple[float, ...] = (0.25, 0.45, 0.75, 1.0, 1.2, 1.5, 2.1)

_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》量水堰槽章"
    "（docs/norms/bashi_jiliangcao.md 起草表 2026-08-26，待追认；"
    "CJ/T 3008.3-1993 正式文本核对归追认点——business-logic §10 Q3）"
)
_GB = "GB 50014-2021 §7（出水计量一般要求）"
_D = DimKey.DIMENSIONLESS
_F = DimKey.FLOW
_L = DimKey.LENGTH

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "BL-F1",
        "q_meas = c_coef * ha ** n_exp",
        {
            "c_coef": (_D, "流量系数 C（factor.bashi_jiliangcao.flume.<档>.c，Q L/s）"),
            "ha": (_L, "实测（上游）水头 m"),
            "n_exp": (_D, "流量指数 n（factor.bashi_jiliangcao.flume.<档>.n）"),
        },
        _F,
        _HB,
    ),
    FormulaSpec(
        "BL-F2",
        "ha_design = (q_design * 1000 / c_coef) ** (1 / n_exp)",
        {
            "q_design": (_F, "最高时设计流量 m3/s（×1000 转 L/s 口径）"),
            "c_coef": (_D, "流量系数 C"),
            "n_exp": (_D, "流量指数 n"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "BL-F3",
        "ha_avg = (q_avg_daily * 1000 / c_coef) ** (1 / n_exp)",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×1000 转 L/s 口径）"),
            "c_coef": (_D, "流量系数 C"),
            "n_exp": (_D, "流量指数 n"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "BL-F4",
        "b1 = 1.2 * b_throat + 0.48",
        {"b_throat": (_L, "喉宽 m（参数 b_throat，B7 七档 grid）")},
        _L,
        "《给水排水设计手册（第 5 册 城镇排水）》巴歇尔槽标准型构造尺寸表"
        "（收缩段上游宽回归式，全档逐行验证；docs/norms/bashi_jiliangcao.md"
        " 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "BL-F5",
        "l1 = 1.2 + 0.5 * b_throat",
        {"b_throat": (_L, "喉宽 m")},
        _L,
        "《给水排水设计手册（第 5 册 城镇排水）》巴歇尔槽标准型构造尺寸表"
        "（收缩段长回归式，全档逐行验证；起草表待追认）",
    ),
    FormulaSpec(
        "BL-F6",
        "b2 = b_throat + 0.3",
        {"b_throat": (_L, "喉宽 m")},
        _L,
        "《给水排水设计手册（第 5 册 城镇排水）》巴歇尔槽标准型构造尺寸表"
        "（扩散段出口宽回归式，全档逐行验证；起草表待追认）",
    ),
    FormulaSpec(
        "BL-F7",
        "l_total = l1 + l_throat + l_diffuse",
        {
            "l1": (_L, "收缩段长 m"),
            "l_throat": (_L, "喉道段长 m（factor...geometry.l_throat，标准型常数）"),
            "l_diffuse": (_L, "扩散段长 m（factor...geometry.l_diffuse，常数）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "BL-F8",
        "sigma = hb_design / ha_design",
        {
            "hb_design": (_L, "下游（淹没）水深设计假定 m（factor.bashi_jiliangcao.hb_design）"),
            "ha_design": (_L, "设计水头 m"),
        },
        _D,
        "《给水排水设计手册（第 5 册 城镇排水）》巴歇尔槽自由流/淹没流判别"
        "（σ=Hb/Ha ≤ 临界淹没度 scrit；起草表待追认）",
    ),
    FormulaSpec(
        "BL-F9",
        "h_loss = loss_ratio * ha_design",
        {
            "loss_ratio": (_D, "槽身水头损失比（factor.bashi_jiliangcao.loss_ratio，估算口径）"),
            "ha_design": (_L, "设计水头 m"),
        },
        _L,
        "《给水排水设计手册（第 5 册 城镇排水）》量水槽水头损失估算"
        "（起草表待追认）",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.municipal_bashi_jiliangcao",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（b075 档主算例选档）；grid=B7 七档
        # （Ruling ④：档位面经 grid 声明承载，compute 只保 b>0+档位命中）
        "params": [
            {
                "field_id": "b_throat",
                "dim": "LENGTH",
                "default": 0.75,
                "grid": list(_THROAT_GRID),
            },
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.bashi_jiliangcao.bod5.mod_default",
            "CODCR": "removal.bashi_jiliangcao.cod.mod_default",
            "SS": "removal.bashi_jiliangcao.ss.mod_default",
        },
        "norm_refs": [
            "《给水排水设计手册（第 5 册 城镇排水）》量水堰槽章——巴歇尔槽"
            "标准型 C·n 系数表/构造尺寸表/淹没度判别",
            "GB 50014-2021 §7（出水计量一般要求；小节号随追认核对）",
            "CJ/T 3008.3-1993 巴歇尔水槽——正式文本逐字核对归追认点"
            "（business-logic §10 Q3 挂账口径）",
            "docs/norms/bashi_jiliangcao.md（2026-08-26 起草手算对照表，"
            "数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            f"bashi_jiliangcao.{check}.{grade}"
            for grade in GRADES
            for check in ("ha_band", "submergence")
        ],
    }
)
