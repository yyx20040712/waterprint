"""矿井水输入清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_input.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KI-F1~F7 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_input"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（Q_avg_daily=43836 m³/d/Kz=1.5
#   井下脉动独立口径/DN=800 mm/z_water_inlet=100.0/z_ground=102.0/
#   h_pool=3.0；进水水质六指标=GB/T 19223-2015 含悬浮物类典型值——
#   全厂流量口径与进水水质的唯一注入点）；系数不落本表——进水水头
#   损失/超高下限经 factor.mine_input.* 键消费（app._unit_params 线
#   感知投影，mine_ 限定）；去除率零键（输入源单元无处理功能不建
#   removal.mine_input.*，与市政线内置输入节点零键口径镜像）。
# 【公式注册（D1）】KI-F1~F7 逐条 FormulaSpec+register；expression=表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；
#   结构常数（24/86400/4/1000）内联（本文件=units_lib manifest 白名单
#   区，表串原文常量）；表内 π 内联 3.14159265 按模板惯例经符号 pi
#   绑定 math.pi（M2a2 等价形态）；表流量口径 q_avg_daily=m³/d（参数
#   面），KI-F1 的 /86400 兼任 m³/d→m3/s 规范单位换算（WaterFlow 正
#   门口径）；Kz 无档位来源不设 grid。
# 【声明五件】params（range 仅表内有出处带者：kz/dn_inlet/h_pool 三
#   参数）/ports 两口 WATER/removal_refs 空映射/norm_refs 双源标记
#   （GB/T 19223-2015+GB/T 41019-2021+给水排水设计手册）/
#   condition_mappings=()/constraint_refs 一键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_input"

_GB_CLASS = (
    "GB/T 19223-2015（煤矿矿井水分类——含悬浮物类进水核定；"
    "docs/norms/mine_water_input.md 起草表 2026-08-27，待追认）"
)
_GB_FLOW = (
    "GB/T 41019-2021（矿井水处理工艺设计水量口径，条号待核对；"
    "docs/norms/mine_water_input.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 3 册 城镇给水）》取水构筑物水位/管流常用值"
    "（docs/norms/mine_water_input.md 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KI-F1",
        "q_design = q_avg_daily * kz / 86400",
        {
            "q_avg_daily": (_D, "平均日流量 m3/d（参数 q_avg_daily，/86400 转 m3/s 规范单位）"),
            "kz": (_D, "总变化系数（参数 kz，井下排水脉动独立口径）"),
        },
        _F,
        _GB_FLOW,
    ),
    FormulaSpec(
        "KI-F2",
        "q_avg_h = q_avg_daily / 24",
        {"q_avg_daily": (_D, "平均日流量 m3/d（参数 q_avg_daily）")},
        _D,
        _GB_FLOW,
    ),
    FormulaSpec(
        "KI-F3",
        "v_inlet = (q_avg_daily / 86400) / (pi / 4 * (dn_inlet / 1000) ** 2)",
        {
            "q_avg_daily": (_D, "平均日流量 m3/d（/86400 转 m3/s 口径）"),
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
            "dn_inlet": (_D, "进水管径 mm（参数 dn_inlet，/1000 转 m）"),
        },
        _V,
        _HB,
    ),
    FormulaSpec(
        "KI-F4",
        "z_pipe_bottom = z_water_inlet - dn_inlet / 1000",
        {
            "z_water_inlet": (_L, "进水水面标高 m（参数 z_water_inlet）"),
            "dn_inlet": (_D, "进水管径 mm（/1000 转 m 口径）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KI-F5",
        "z_water = z_water_inlet - h_loss",
        {
            "z_water_inlet": (_L, "进水水面标高 m（参数 z_water_inlet）"),
            "h_loss": (_L, "进水水头损失 m（factor.mine_input.elevation_loss）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KI-F6",
        "z_bottom = z_water - h_pool",
        {
            "z_water": (_L, "进水水面标高减水损后标高 m"),
            "h_pool": (_L, "井下提升有效水深 m（参数 h_pool，声明面构造默认 3.0）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KI-F7",
        "freeboard = z_ground - z_water",
        {
            "z_ground": (_L, "地面标高 m（参数 z_ground，校核 ≥ freeboard.min）"),
            "z_water": (_L, "进水水面标高减水损后标高 m"),
        },
        _L,
        _GB_FLOW,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.mine_water_input",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_input.md 参数档）；
        # range 仅三条有出处带参数（kz 1.3~1.5 井下脉动/dn_inlet 600~1000 mm/
        # h_pool 2.5~4.0 m），标高与水质注入面无范围来源不设
        "params": [
            {"field_id": "q_avg_daily", "dim": "DIMENSIONLESS", "default": 43836.0},
            {
                "field_id": "kz",
                "dim": "DIMENSIONLESS",
                "default": 1.5,
                "range": {"min": 1.3, "max": 1.5},
            },
            {
                "field_id": "dn_inlet",
                "dim": "DIMENSIONLESS",
                "default": 800.0,
                "range": {"min": 600.0, "max": 1000.0},
            },
            {"field_id": "z_water_inlet", "dim": "LENGTH", "default": 100.0},
            {"field_id": "z_ground", "dim": "LENGTH", "default": 102.0},
            {
                "field_id": "h_pool",
                "dim": "LENGTH",
                "default": 3.0,
                "range": {"min": 2.5, "max": 4.0},
            },
            {"field_id": "ss_in", "dim": "CONCENTRATION", "default": 800.0},
            {"field_id": "cod_in", "dim": "CONCENTRATION", "default": 200.0},
            {"field_id": "bod5_in", "dim": "CONCENTRATION", "default": 5.0},
            {"field_id": "nh3n_in", "dim": "CONCENTRATION", "default": 1.0},
            {"field_id": "tn_in", "dim": "CONCENTRATION", "default": 60.0},
            {"field_id": "tp_in", "dim": "CONCENTRATION", "default": 2.0},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {},
        "norm_refs": [
            "GB/T 19223-2015（煤矿矿井水分类——进水类别核定：含悬浮物矿井水）",
            "GB/T 41019-2021（矿井水处理工艺设计水量口径，条号待核对）",
            "《给水排水设计手册（第 3 册 城镇给水）》取水构筑物水位/管流常用值",
            "docs/norms/mine_water_input.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_input.freeboard_band",
        ],
    }
)
