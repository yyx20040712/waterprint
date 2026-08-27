"""V型滤池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_vxinglvchi.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KV-F1~F11 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_vxinglvchi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=16 格/v_filter=5.0 m/h/
#   t_filter=24 h/h_media=1.0 m/h_water=1.2 m；h_plate=0.1/h_under=0.9
#   构造层高；B/L 0.1 m 档）；系数不落本表——滤速带（低滤速精滤
#   4~6 档）+强制滤速上限+自用水系数+单格长宽比+滤层厚带+砂上水深
#   带+反冲三阶段强度/历时全族+周期带+耗水率上限+超高+壁厚系数+
#   高程水损全部经 factor.mine_vxinglvchi.* 键消费（app._unit_params
#   线感知投影，mine_ 限定）；去除率经 removal.mine_vxinglvchi.{ss,cod}.
#   mod_default 键（ss 0.80 低浊进水档/cod 0.075 微量去除保守档——
#   深层过滤段；BOD5 全线不建键）。
# 【公式注册（D1）】KV-F1~F11 逐条 FormulaSpec+register；expression=
#   表公式串转受限 DSL——data 包系数（k_self/ratio_lb/h_super/
#   wall_coef/三阶段强度与历时）一律符号绑定（零系数字面量）；
#   结构常数内联（本文件=units_lib manifest 白名单区）：×86400
#   （m3/s→m³/d 流量口径注记——过滤面积按日处理量）、×24（d→h
#   日冲次数折算）、÷60（min→h 停滤折算）、×60/÷1000（L/(m²·s)·min
#   →m³/(格·次) 反冲水量折算）；sqrt 直接用。DSL 无 ceil：B/L
#   （0.1 m 档）离散在 compute 收口；t_bw（三阶段合计）在 compute
#   零字面量合成（表主算例输入 12 min=t_air+t_sim+t_water 同值——
#   ningjiao p_total 单输出导出量先例，dims 审计面 t_bw）。
# 【物理隔离】与市政同名包 municipal/vxinglvchi（GB 50013-2018
#   §9.5 均质滤料 7~10 m/h 档）零 import 零参数复用——本表低滤速
#   4~6 m/h 精滤档、滤层 0.8~1.2 m（市政 1.2~1.5），键空间经
#   mine_ 限定物理隔离（§14.3）。
# 【声明五件】params（range 仅表内有出处带者：v_filter/t_filter/
#   h_media/h_water 四有出处带者；格数/滤板厚/承托层/取整档无范围
#   来源不设）/ports 两口 WATER/removal_refs 双指标键/norm_refs
#   三源标记（GB/T 41019-2021+GB/T 31392-2022+给水排水设计手册）/
#   condition_mappings=()/constraint_refs 六键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_vxinglvchi"

_GB = (
    "GB/T 41019-2021（矿井水处理工艺——过滤段滤速与反冲，条号待核对；"
    "docs/norms/mine_water_vxinglvchi.md 起草表 2026-08-27，待追认）"
)
_GT = (
    "GB/T 31392-2022（矿井水回用水质目标，条号待核对；"
    "docs/norms/mine_water_vxinglvchi.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 3 册 城镇给水）》V 型滤池滤料/气水反冲"
    "三阶段/反冲耗水常用带（docs/norms/mine_water_vxinglvchi.md"
    " 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KV-F1",
        "q_d = q_avg_daily * 86400 * k_self",
        {
            "q_avg_daily": (
                _F,
                "平均日流量 m3/s（×86400 转 m³/d 口径——过滤面积按日处理量）",
            ),
            "k_self": (_D, "自用水系数（factor.mine_vxinglvchi.selfuse_coef，覆盖反冲耗水）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KV-F2",
        "t_w = 24 - 24 * (t_bw / 60) / t_filter",
        {
            "t_bw": (_D, "单格反冲停滤历时 min（三阶段合计，compute 合成审计面）"),
            "t_filter": (_D, "过滤周期 h（参数 t_filter）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KV-F3",
        "f_total = q_d / (v_filter * t_w)",
        {
            "q_d": (_D, "日处理量 m3/d（KV-F1）"),
            "v_filter": (_D, "正常滤速 m/h（参数 v_filter，主控参数——低滤速精滤档）"),
            "t_w": (_D, "日有效过滤时长 h（KV-F2）"),
        },
        _A,
        _GB,
    ),
    FormulaSpec(
        "KV-F4",
        "f_single = f_total / n",
        {
            "f_total": (_A, "总过滤面积 m2（KV-F3）"),
            "n": (_D, "格数"),
        },
        _A,
        _HB,
    ),
    FormulaSpec(
        "KV-F5",
        "v_force_act = n / (n - 1) * v_filter",
        {
            "n": (_D, "格数（≥2——一格冲洗时余格承载）"),
            "v_filter": (_D, "正常滤速 m/h（参数 v_filter）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KV-F6",
        "b_raw = sqrt(f_single / ratio_lb)",
        {
            "f_single": (_A, "单格过滤面积 m2（KV-F4）"),
            "ratio_lb": (
                _D,
                "单格长宽比（factor.mine_vxinglvchi.cell_ratio_lb，构造常量）",
            ),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KV-F7",
        "l_raw = f_single / b",
        {
            "f_single": (_A, "单格过滤面积 m2（KV-F4）"),
            "b": (_L, "单格宽（0.1 m 档 ceil 后）m"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KV-F8",
        "w_wash = (q_w_sim * t_sim + q_w * t_water + q_sweep * t_bw) * 60 / 1000",
        {
            "q_w_sim": (
                _D,
                "气水同时水强度 L/(m2·s)（factor.mine_vxinglvchi.wash.water_sim）",
            ),
            "t_sim": (_D, "气水同时历时 min（factor.mine_vxinglvchi.wash.t_sim）"),
            "q_w": (_D, "单独水冲强度 L/(m2·s)（factor.mine_vxinglvchi.wash.water）"),
            "t_water": (_D, "水冲历时 min（factor.mine_vxinglvchi.wash.t_water）"),
            "q_sweep": (_D, "表面扫洗强度 L/(m2·s)（factor.mine_vxinglvchi.wash.sweep）"),
            "t_bw": (_D, "单格反冲停滤历时 min（扫洗全程——三阶段合计合成值）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KV-F9",
        "eta_wash = w_wash * (24 / t_filter) / (q_d / n)",
        {
            "w_wash": (_D, "单格次反冲水量 m3/(格·次)（KV-F8）"),
            "t_filter": (_D, "过滤周期 h（参数 t_filter；24/t=日冲次数——单格日冲一次口径）"),
            "q_d": (_D, "日处理量 m3/d（KV-F1）"),
            "n": (_D, "格数"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KV-F10",
        "h_total = h_super + h_water + h_media + h_plate + h_under",
        {
            "h_super": (_L, "超高 m（factor.mine_vxinglvchi.superheight）"),
            "h_water": (_L, "砂上水深 m（参数 h_water，恒水位过滤）"),
            "h_media": (_L, "滤层厚 m（参数 h_media，均质滤料）"),
            "h_plate": (_L, "滤板厚 m（参数 h_plate）"),
            "h_under": (_L, "承托层厚 m（参数 h_under）"),
        },
        _L,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "KV-F11",
        "v_concrete = l * b * h_total * n * wall_coef",
        {
            "l": (_L, "单格长（ceil 后）m"),
            "b": (_L, "单格宽（ceil 后）m"),
            "h_total": (_L, "滤池总高 m（KV-F10）"),
            "n": (_D, "格数"),
            "wall_coef": (
                _D,
                "壁厚系数（factor.mine_vxinglvchi.wall_thickness_coef，概算口径）",
            ),
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
        "i18n_key": "units.mine_water_vxinglvchi",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_vxinglvchi.md
        # 参数档）；range 仅四条有出处带参数（v_filter_band 4~6 低滤速
        # 精滤档——异于市政 7~10、cycle_band 24~48、media.depth_band
        # 0.8~1.2 偏薄档、water_above_band 1.0~1.5），格数/滤板厚/
        # 承托层/取整档无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 16.0},
            {
                "field_id": "v_filter",
                "dim": "DIMENSIONLESS",
                "default": 5.0,
                "range": {"min": 4.0, "max": 6.0},
            },
            {
                "field_id": "t_filter",
                "dim": "DIMENSIONLESS",
                "default": 24.0,
                "range": {"min": 24.0, "max": 48.0},
            },
            {
                "field_id": "h_media",
                "dim": "LENGTH",
                "default": 1.0,
                "range": {"min": 0.8, "max": 1.2},
            },
            {
                "field_id": "h_water",
                "dim": "LENGTH",
                "default": 1.2,
                "range": {"min": 1.0, "max": 1.5},
            },
            {"field_id": "h_plate", "dim": "LENGTH", "default": 0.1},
            {"field_id": "h_under", "dim": "LENGTH", "default": 0.9},
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "SS": "removal.mine_vxinglvchi.ss.mod_default",
            "CODCR": "removal.mine_vxinglvchi.cod.mod_default",
        },
        "norm_refs": [
            "GB/T 41019-2021（矿井水处理工艺——过滤段滤速与反冲，条号待核对）",
            "GB/T 31392-2022（矿井水回用水质目标，衔接式）",
            "《给水排水设计手册（第 3 册 城镇给水）》V 型滤池滤料/气水反冲三阶段常用带",
            "docs/norms/mine_water_vxinglvchi.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_vxinglvchi.v_filter_band",
            "mine_water_vxinglvchi.forced_velocity",
            "mine_water_vxinglvchi.media_depth_band",
            "mine_water_vxinglvchi.water_above_band",
            "mine_water_vxinglvchi.cycle_band",
            "mine_water_vxinglvchi.wash_ratio",
        ],
    }
)
