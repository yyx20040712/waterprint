"""磁分离清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_cifenli.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KS-F1~F8 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_cifenli"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n_units=4 台/omega=3 rpm/
#   q_surf=25 m³/(m²·h)；m_seed=21918.0 kg/d=ningjiao 表 KN-F13 口径
#   ——上游 dims 不跨单元传递，磁种投加量经参数面衔接，主算例值与
#   ningjiao m_seed dims 同源一致）；系数不落本表——表面负荷带+
#   盘径/浸没比/转速上限+磁种回收率+磁泥含水率/密度+超高+壁厚系数+
#   高程水损全部经 factor.mine_cifenli.* 键消费（app._unit_params
#   线感知投影，mine_ 限定）；去除率经 removal.mine_cifenli.{ss,cod}.
#   mod_default 键（ss 0.90 磁絮体磁盘截留/cod 0.60 颗粒态煤粉随絮体
#   带出；KS-F6 截留率 eta_ss 同取 SS 去除键——表系数列原文；BOD5
#   全线不建键）。
# 【公式注册（D1）】KS-F1~F8+MS-F1 逐条 FormulaSpec+register（MS-F1=矿井
#   泥线链级衔接式磁泥股干基——GOLDEN4b R1 登记 2026-08-28，sludge_out
#   产股消费）；expression=
#   表公式串转受限 DSL——data 包系数（d_disk/eta_im/eta_recover/
#   p_sludge/rho_sludge）一律符号绑定（零系数字面量）；结构常数
#   内联（本文件=units_lib manifest 白名单区）：×3600（m3/s→m³/h
#   流量口径注记，表内 q_design_h 展开内联——市政 KG-F1 同型）/
#   10⁶（mg/L×m³/d→t/d 折算）/×1000（t/d→kg/d 磁泥湿量折算）；
#   表 π 内联 3.14159265 按模板惯例经符号 pi 绑定 math.pi（KI/KT
#   先例，差 1.45e-9 在容差内）；/60（rpm→r/s）。DSL 无 ceil：盘片
#   数整台向上取整在 compute 收口（取整前 n_disks_raw 审计面）。
#   KS-F8 DSL 逐字输出 kg/d（表期望列 1.0959 t/d 为显示口径）。
# 【声明五件】params（range 仅表内有出处带者：q_surf 表面负荷带
#   20~40；台数/转速/磁种投加量无档位来源不设）/ports 两口 WATER+
#   sludge_out SLUDGE 产股口（GOLDEN4a D3——无条件产股，无边也产；
#   nongsuo sup 先例同构）/removal_refs 双指标键/norm_refs 双源标记
#   （GB/T 41019-2021+给水排水设计手册）/condition_mappings=()/
#   constraint_refs 两键。
# 【选型面边界】流道停留/流道流速两键为设备选型校核键（流道几何
#   归厂商样本），本包不落几何公式不消费——表"其他数据键"原文。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_cifenli"

_GB = (
    "GB/T 41019-2021（矿井水处理工艺——磁加载混凝分离路线与表面负荷，"
    "条号待核对；docs/norms/mine_water_cifenli.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 3 册 城镇给水）》高浊度水混凝分离/泥量衡算"
    "常用带（docs/norms/mine_water_cifenli.md 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW

# GOLDEN4a D3 产股口常量（数值白名单区，compute 零字面量消费）——
# SECS_PER_DAY 工程口径 m³/d、kg/d → SludgeFlow 契约口径 m3/s、kg/s；
# KG_PER_TON=KS-F6 w_ss（t/d）→ MS-F1 干基 kg/d 的 kg/t 换算（手算表
# mine_water_sludge_line.md 三股语义映射表磁泥股——ρ=1100 湿量经 KS-F7
# 系数键直用，无新键）。
SECS_PER_DAY: Final[float] = 86400.0
KG_PER_TON: Final[float] = 1000.0
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KS-F1",
        "q_1h = q_design * 3600 / n_units",
        {
            "q_design": (
                _F,
                "最高时设计流量 m3/s（×3600 转 m³/h 口径——表内 q_design_h 展开内联）",
            ),
            "n_units": (_D, "分离机台数（参数 n_units）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KS-F2",
        "a_disk = 2 * pi * d_disk ** 2 / 4 * eta_im",
        {
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
            "d_disk": (_L, "磁盘直径 m（factor.mine_cifenli.disk.diameter）"),
            "eta_im": (
                _D,
                "盘浸没比（factor.mine_cifenli.disk.immersion，单盘双面有效面积）",
            ),
        },
        _A,
        _GB,
    ),
    FormulaSpec(
        "KS-F3",
        "a_total_req = q_1h / q_surf",
        {
            "q_1h": (_D, "单台处理流量 m3/h（KS-F1）"),
            "q_surf": (_D, "盘面表面负荷 m3/(m2·h)（参数 q_surf，主控参数）"),
        },
        _A,
        _GB,
    ),
    FormulaSpec(
        "KS-F4",
        "n_disks = a_total_req / a_disk",
        {
            "a_total_req": (_A, "单台需盘面总面积 m2（KS-F3）"),
            "a_disk": (_A, "单盘双面有效面积 m2（KS-F2）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KS-F5",
        "v_line = pi * d_disk * omega / 60",
        {
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
            "d_disk": (_L, "磁盘直径 m（factor.mine_cifenli.disk.diameter）"),
            "omega": (_D, "盘转速 rpm（参数 omega，÷60 折 r/s；盘缘线速度 ≤0.3 m/s 校核）"),
        },
        _V,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "KS-F6",
        "w_ss = q_avg_daily * 86400 * ss_in * eta_ss / 1000000",
        {
            "q_avg_daily": (
                _F,
                "平均日流量 m3/s（×86400 转 m³/d 口径——截留泥量按平均日）",
            ),
            "ss_in": (_D, "进水 SS mg/L（衔接链值，入流水质取数）"),
            "eta_ss": (
                _D,
                "截留率（removal.mine_cifenli.ss.mod_default 同键——表系数列原文）",
            ),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KS-F7",
        "q_sludge = w_ss * 1000 / ((1 - p_sludge) * rho_sludge)",
        {
            "w_ss": (_D, "日截留干固体 t/d（KS-F6）"),
            "p_sludge": (_D, "磁泥含水率（factor.mine_cifenli.sludge.moisture）"),
            "rho_sludge": (_D, "磁泥密度 kg/m3（factor.mine_cifenli.sludge.density）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KS-F8",
        "m_seed_net = m_seed * (1 - eta_recover)",
        {
            "m_seed": (_D, "磁种投加 kg/d（参数 m_seed，ningjiao 表 KN-F13 口径）"),
            "eta_recover": (
                _D,
                "磁种回收率（factor.mine_cifenli.seed.recovery，净耗=投加×未回收比）",
            ),
        },
        _D,
        _GB,
    ),
    # GOLDEN4b R1（总控裁决 2026-08-28）：矿井泥线链级衔接式 MS-F1~F3 之
    # 磁泥股——登记落点=各产泥包 manifest（不进 hebing，审计口径
    # "formula_ids=实际应用"保持）；compute 侧内联同式实现（R4 测试背书）。
    FormulaSpec(
        "MS-F1",
        "ds_primary = w_ss * 1000",
        {
            "w_ss": (_D, "日截留干固体 t/d（KS-F6 链值——×1000 kg/t 折干基 kg/d）"),
        },
        _D,
        "docs/norms/mine_water_sludge_line.md（矿井泥线三股语义映射表——MS-F1 "
        "磁泥干基链级衔接式，GOLDEN4b R1 登记 2026-08-28）+《给水排水设计手册"
        "（第 5 册 城镇排水）》污泥处理章泥量衡算",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.mine_water_cifenli",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_cifenli.md 参数档）；
        # range 仅一条有出处带参数（surface_load_band 20~40 m³/(m²·h)），
        # 台数/转速/磁种投加量无范围来源不设
        "params": [
            {"field_id": "n_units", "dim": "DIMENSIONLESS", "default": 4.0},
            {"field_id": "omega", "dim": "DIMENSIONLESS", "default": 3.0},
            {
                "field_id": "q_surf",
                "dim": "DIMENSIONLESS",
                "default": 25.0,
                "range": {"min": 20.0, "max": 40.0},
            },
            {"field_id": "m_seed", "dim": "DIMENSIONLESS", "default": 21918.0},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
            # GOLDEN4a D3 产股口（2026-08-28）：无条件产股（无边也产——
            # nongsuo sup 先例同构）；产股三量=MS-F1 衔接式换算（w_ss×
            # KG_PER_TON 干基——FormulaSpec 登记本批[GOLDEN4b R1]；q_wet=
            # KS-F7 ρ=1100 直算口径；moisture=factor.mine_cifenli.sludge.
            # moisture 0.92 hebing p_primary 注入位同源）。
            {"port_id": "sludge_out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        "removal_refs": {
            "SS": "removal.mine_cifenli.ss.mod_default",
            "CODCR": "removal.mine_cifenli.cod.mod_default",
        },
        "norm_refs": [
            "GB/T 41019-2021（矿井水处理工艺——磁加载混凝分离路线与表面负荷，条号待核对）",
            "《给水排水设计手册（第 3 册 城镇给水）》高浊度水混凝分离/泥量衡算常用带",
            "docs/norms/mine_water_cifenli.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_cifenli.surface_load_band",
            "mine_water_cifenli.disk_speed",
        ],
    }
)
