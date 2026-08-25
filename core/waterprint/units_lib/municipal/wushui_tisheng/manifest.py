"""污水提升泵房清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  三表起草真源（docs/norms/wushui_tisheng.md，2026-08-26，数据策略 v2 待追认）+
       data/coefficients 0.4.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ TS-F1~F14 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收；公式路线 =
#   集水井调节容积法+泵扬程三分量主线——静扬程+管路损失[比阻常用
#   估算法]+自由水头；**泵扬程计算落本表，M2b1 追认点 14 泵扬程挂账
#   就此承接**；扬程链进 elevation 面消费归出图批 UF-32 契约）
#
# 【固定形态】UNIT_ID = "municipal_wushui_tisheng"；manifest =
#   load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 逐字（h_static=10.0 m/v_pipe=1.2
#   m/s/l_pipe=100 m/n_standby=1[2 用 1 备档，同调节池 TJ-F10 注记]/
#   h_well=2.0 m/t_well=10 min/dia_disc_step=0.1 m[DN 档]/g_gravity=
#   9.81[重力加速度，M1a 字段复用]/sec_per_hour=3600[时换算，AO-F13
#   同款参数形态]）；系数不落本表——单泵流量概算锚/自由水头/启停上限/
#   比阻 DN300~DN800 八档/流速带/局部损失和/集水井双带/超高/壁厚/
#   高程水损全部经 factor.wushui_tisheng.* 键消费（app._unit_params
#   投影）；去除率经 removal.wushui_tisheng.*.mod_default（提升单元
#   零去除，全 0.0；NH3N/TN/TP 不建条目）。
# 【公式注册（D1）】TS-F1~F14 逐条 FormulaSpec+register；expression=
#   三表公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；
#   常量（π=3.14159265/2[g 重力因子]/60[min→s]/900[=3600/4 启停周期
#   条文常量]）内联（本文件=units_lib manifest 白名单区，出处=
#   norm_ref）。DSL 无 ceil：工作泵台数 n_pump_duty（整台）/出水管径
#   d_pipe（0.1 m 档=DN 档）在 compute 收口；DN 档命中比阻表键
#   （dn300~dn800），越表=领域异常（档表覆盖面显式声明）。
# 【声明五件】params（range 仅表内有出处带者：h_static/v_pipe/l_pipe/
#   h_well/t_well 五参数）/ports 两口 WATER/removal_refs（零去除键同
#   引用）/norm_refs 双源标记（GB 50014-2021 §6.1+给水排水设计手册）/
#   condition_mappings=()/constraint_refs 三键（流速带/启停上限/调节
#   时间带——单泵流量带为选泵面校核仅 compute warnings 承载）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_wushui_tisheng"

_GB = (
    "GB 50014-2021 §6.1（泵站——集水池容积/备用泵一般要求；"
    "docs/norms/wushui_tisheng.md 起草表 2026-08-26，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》泵站章"
    "（docs/norms/wushui_tisheng.md 起草表 2026-08-26，待追认）"
)
_HB1 = (
    "《给水排水设计手册（第 1 册 常用资料）》水管比阻表（舍维列夫）"
    "（docs/norms/wushui_tisheng.md 起草表 2026-08-26，待追认）"
)
_D = DimKey.DIMENSIONLESS
_F = DimKey.FLOW
_VOL = DimKey.VOLUME
_L = DimKey.LENGTH
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "TS-F1",
        "n_pump_raw = q_design_h / q_per_pump",
        {
            "q_design_h": (_D, "最高时流量 m3/h（=q_design×sec_per_hour 符号合成）"),
            "q_per_pump": (_D, "单泵流量概算锚 m3/h（factor.wushui_tisheng.pump.q_per_unit）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "TS-F2",
        "q_pump = q_design_h / n_pump_duty",
        {
            "q_design_h": (_D, "最高时流量 m3/h"),
            "n_pump_duty": (_D, "工作泵台数（=ceil(n_pump_raw) 整台收口）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "TS-F3",
        "n_pump_total = n_pump_duty + n_standby",
        {
            "n_pump_duty": (_D, "工作泵台数"),
            "n_standby": (_D, "备用泵台数（参数 n_standby，2 用 1 备档）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "TS-F4",
        "d_pipe_raw = sqrt(4 * q_pump_si / (3.14159265 * v_pipe))",
        {
            "q_pump_si": (_F, "单泵流量 m3/s（=q_pump/sec_per_hour 符号合成）"),
            "v_pipe": (_V, "出水管名义流速 m/s（参数 v_pipe）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "TS-F5",
        "v_pipe_act = 4 * q_pump_si / (3.14159265 * d_pipe ** 2)",
        {
            "q_pump_si": (_F, "单泵流量 m3/s"),
            "d_pipe": (_L, "出水管径 m（0.1 m 档=DN 档 ceil 后）"),
        },
        _V,
        _HB,
    ),
    FormulaSpec(
        "TS-F6",
        "h_friction = a_pipe * l_pipe * q_pump_si ** 2",
        {
            "a_pipe": (_D, "比阻 s2/m6（factor.wushui_tisheng.pipe.resistance.dn*，DN 档键）"),
            "l_pipe": (_L, "出水管长 m（参数 l_pipe）"),
            "q_pump_si": (_F, "单泵流量 m3/s"),
        },
        _L,
        _HB1,
    ),
    FormulaSpec(
        "TS-F7",
        "h_local = zeta_total * v_pipe_act ** 2 / (2 * g_gravity)",
        {
            "zeta_total": (_D, "局部损失系数和 ζ（factor.wushui_tisheng.pipe.zeta_total）"),
            "v_pipe_act": (_V, "实际流速 m/s"),
            "g_gravity": (_D, "重力加速度 m/s2（参数 g_gravity，M1a 字段复用）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "TS-F8",
        "h_loss = h_friction + h_local",
        {"h_friction": (_L, "沿程损失 m"), "h_local": (_L, "局部损失 m")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "TS-F9",
        "h_pump = h_static + h_loss + h_free",
        {
            "h_static": (_L, "静扬程 m（参数 h_static——泵站前后水位高程定）"),
            "h_loss": (_L, "管路总损失 m"),
            "h_free": (_L, "自由水头 m（factor.wushui_tisheng.pump.free_head）"),
        },
        _L,
        "《给水排水设计手册（第 5 册 城镇排水）》泵扬程公式（三分量；"
        "M2b1 追认点 14 承接——docs/norms/wushui_tisheng.md 起草表，待追认）",
    ),
    FormulaSpec(
        "TS-F10",
        "v_well = q_pump_si * 60 * t_well",
        {
            "q_pump_si": (_F, "单泵流量 m3/s"),
            "t_well": (_D, "集水井调节时间 min（参数 t_well；60=min→s 条文常量）"),
        },
        _VOL,
        f"{_GB}（不小于最大一台泵 5 min 出水量口径）；{_HB}",
    ),
    FormulaSpec(
        "TS-F11",
        "a_well = v_well / h_well",
        {"v_well": (_VOL, "集水井调节容积 m3"), "h_well": (_L, "集水井有效水深 m（参数 h_well）")},
        DimKey.AREA,
        _HB,
    ),
    FormulaSpec(
        "TS-F12",
        "n_start = 900 * q_pump_si / v_well",
        {
            "q_pump_si": (_F, "单泵流量 m3/s"),
            "v_well": (_VOL, "集水井调节容积 m3（900=3600/4 启停周期条文常量）"),
        },
        _D,
        "《给水排水设计手册（第 5 册 城镇排水）》水泵启停频率校核"
        "（水位启停——最不利入流半泵流量口径；起草表待追认）",
    ),
    FormulaSpec(
        "TS-F13",
        "h_well_total = h_super + h_well",
        {
            "h_super": (_L, "泵房超高 m（factor.wushui_tisheng.superheight）"),
            "h_well": (_L, "有效水深 m"),
        },
        _L,
        f"{_GB}（超高一般要求）；{_HB}",
    ),
    FormulaSpec(
        "TS-F14",
        "v_concrete = a_well * h_well_total * wall_coef",
        {
            "a_well": (DimKey.AREA, "集水井平面面积 m2"),
            "h_well_total": (_L, "集水井总高 m"),
            "wall_coef": (_D, "壁厚系数（factor.wushui_tisheng.wall_thickness_coef，概算口径）"),
        },
        _VOL,
        _HB,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.municipal_wushui_tisheng",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（出处 docs/norms/wushui_tisheng.md 参数档/
        # 算例输入行）；range 仅五条有出处带参数（h_static/v_pipe/l_pipe/
        # h_well/t_well），备用台数/步长/重力/时换算无范围来源不设
        "params": [
            {
                "field_id": "h_static",
                "dim": "LENGTH",
                "default": 10.0,
                "range": {"min": 8.0, "max": 15.0},
            },
            {"field_id": "v_pipe", "dim": "VELOCITY", "default": 1.2,
             "range": {"min": 0.7, "max": 1.5}},
            {"field_id": "l_pipe", "dim": "LENGTH", "default": 100.0,
             "range": {"min": 50.0, "max": 200.0}},
            {"field_id": "n_standby", "dim": "DIMENSIONLESS", "default": 1.0},
            {"field_id": "h_well", "dim": "LENGTH", "default": 2.0,
             "range": {"min": 1.5, "max": 2.5}},
            {"field_id": "t_well", "dim": "DIMENSIONLESS", "default": 10.0,
             "range": {"min": 5.0, "max": 15.0}},
            {"field_id": "dia_disc_step", "dim": "LENGTH", "default": 0.1},
            {"field_id": "g_gravity", "dim": "DIMENSIONLESS", "default": 9.81},
            {"field_id": "sec_per_hour", "dim": "DIMENSIONLESS", "default": 3600.0},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.wushui_tisheng.bod5.mod_default",
            "CODCR": "removal.wushui_tisheng.cod.mod_default",
            "SS": "removal.wushui_tisheng.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 §6.1（泵站——集水池容积/水泵布置/备用泵一般"
            "要求；小节号随追认核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水井调节容积/"
            "水泵选型/启停水位常用值）；（第 1 册 常用资料）水管比阻表",
            "docs/norms/wushui_tisheng.md（2026-08-26 起草手算对照表，"
            "数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "wushui_tisheng.pipe.velocity_band",
            "wushui_tisheng.pump.start_band",
            "wushui_tisheng.well.t_band",
        ],
    }
)
