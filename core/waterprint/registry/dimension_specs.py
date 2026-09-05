"""维度登记数据件：pool_length+八批次组参数字段纯五元组序列（B3 R3）。

输入:  无（纯数据面——零 import dimensions 环免疫；dim 为 DimKey 成员
       名字符串，FieldSpec.__post_init__ D6 归一语义保）
输出:  DIMENSION_SPECS 五元组序列（field_id, dim, unit, i18n_key,
       category 位置序=FieldSpec 构造参数序——dimensions.py 构造循环
       register_dimension(FieldSpec(*tup)) 消费，登记守卫=转写安全网）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3 R3 拆分 2026-09-05：数据登记面自 dimensions.py
#   L203-500 机械转写——FieldSpec(...) 声明逐条改五元组字面量，各批次
#   组注释随迁逐字保留；八批次分组（M1a/M2a2/M2b2/M2c/M3a2/M3a3/
#   M3b2）+pool_length 预置共九组；registry/** 魔法数字白名单区）
#
# 【行为规格】转写安全网：错数据（元数/键序/dim 名）必在 dimensions
#   import 期的 FieldSpec 构造/register_dimension 守卫显式红——与
#   拆分前同款防线；组注释=字段语义出处（docs/norms 各表），禁删。
#
# 【测试要求】B3-R11 test_dimension_specs 数据形态契约（每项恰五元组
#   且全 str、组数>0）。
#
# 【参照】B3 简报 R3；重写计划 §2 单位制行/§12.1；简报 T3 D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Final

DIMENSION_SPECS: Final[tuple[tuple[str, str, str, str, str], ...]] = (
    # ── 模块级预置（D2 冻结）：pool_length——几何取数首个冻结字段。 ──
    ("pool_length", "LENGTH", "m", "units.fields.pool_length", "geometry"),
    # ── M1a 三单元切片参数字段（2026-08-25；出处=docs/norms/{cugeshan,
    #    xigeshan,chenshachi}.md 三表签字参数列——粗/细格栅参数表意共用字段
    #    ID，同名跨线不耦合：各包 manifest 各写各的默认值，AGENTS §11 R4）。
    #    角度（alpha/theta）与日数（t_clean）、表面负荷（q_surf，m³/(m²·h)）、
    #    重力加速度（g_gravity，m/s²）、时换算（sec_per_hour，s/h）在 DimKey
    #    无对应量类，按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键走，三表
    #    口径：°/d/m³·m⁻²·h⁻¹/m·s⁻²/s）。 ──
    ("n", "DIMENSIONLESS", "", "units.fields.n", "equipment"),
    ("b", "LENGTH", "m", "units.fields.b", "geometry"),
    ("alpha", "DIMENSIONLESS", "", "units.fields.alpha", "geometry"),
    ("h", "LENGTH", "m", "units.fields.h", "geometry"),
    ("v", "VELOCITY", "m/s", "units.fields.v", "load"),
    ("v1", "VELOCITY", "m/s", "units.fields.v1", "load"),
    ("s", "LENGTH", "m", "units.fields.s", "geometry"),
    ("bar_shape", "DIMENSIONLESS", "", "units.fields.bar_shape", "equipment"),
    ("g_gravity", "DIMENSIONLESS", "", "units.fields.g_gravity", "load"),
    ("length_disc_step", "LENGTH", "m", "units.fields.length_disc_step",
     "geometry"),
    ("q_surf", "DIMENSIONLESS", "", "units.fields.q_surf", "load"),
    ("t_retention", "TIME", "s", "units.fields.t_retention", "load"),
    ("t_clean", "DIMENSIONLESS", "", "units.fields.t_clean", "operation"),
    ("theta", "DIMENSIONLESS", "", "units.fields.theta", "geometry"),
    ("d_r", "LENGTH", "m", "units.fields.d_r", "geometry"),
    ("b_channel", "LENGTH", "m", "units.fields.b_channel", "geometry"),
    ("v_channel", "VELOCITY", "m/s", "units.fields.v_channel", "load"),
    ("sec_per_hour", "DIMENSIONLESS", "", "units.fields.sec_per_hour", "load"),
    # ── M2a2 核心三单元参数字段（2026-08-25；出处=docs/norms/{chuchenchi,aao,
    #    erchunchi}.md 三表参数列/算例 1 输入行——同名跨单元字段 ID 不耦合：
    #    各包 manifest 各写各的默认值，AGENTS §11 R4；x_mlss/h2/r_external 等
    #    联动值由调用侧取同值，注册表只登记字段语义）。小时/日/负荷带类单位
    #    在 DimKey 无对应量类者按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键
    #    走，三表口径：h/d/m³·m⁻²·h⁻¹/kgBOD5·kgMLSS⁻¹·d⁻¹）。 ──
    # chuchenchi 辐流初沉池（算例 1：q'=2.3/T=1.2 h/T_sludge=2 d/r1=1.8/
    # r2=0.8/h5=1.5；D 档 0.5 m/长度档 0.1 m）
    ("q_prime", "DIMENSIONLESS", "", "units.fields.q_prime", "load"),
    ("t_settle", "DIMENSIONLESS", "", "units.fields.t_settle", "load"),
    ("t_sludge", "DIMENSIONLESS", "", "units.fields.t_sludge", "operation"),
    ("r1", "LENGTH", "m", "units.fields.r1", "geometry"),
    ("r2", "LENGTH", "m", "units.fields.r2", "geometry"),
    ("h5", "LENGTH", "m", "units.fields.h5", "geometry"),
    ("dia_disc_step", "LENGTH", "m", "units.fields.dia_disc_step", "geometry"),
    # aao AAO 生物池（算例 1：Ns=0.10/X=4000/t_p=1.5 h/R=1.0/Ri=2.0/
    # TN_eff=15；sec_per_hour=3600 时换算）
    ("ns", "DIMENSIONLESS", "", "units.fields.ns", "load"),
    ("x_mlss", "CONCENTRATION", "mg/L", "units.fields.x_mlss", "load"),
    ("t_p", "DIMENSIONLESS", "", "units.fields.t_p", "load"),
    ("r_external", "DIMENSIONLESS", "", "units.fields.r_external", "operation"),
    ("r_internal", "DIMENSIONLESS", "", "units.fields.r_internal", "operation"),
    ("tn_eff", "CONCENTRATION", "mg/L", "units.fields.tn_eff", "load"),
    # erchunchi 辐流二沉池（算例 1：q_nom=1.2/X=4000 联动/R=1.0 联动/
    # h2=3.0/r_pit=1.0）
    ("q_nom", "DIMENSIONLESS", "", "units.fields.q_nom", "load"),
    ("r_pit", "LENGTH", "m", "units.fields.r_pit", "geometry"),
    ("h2", "LENGTH", "m", "units.fields.h2", "geometry"),
    # ── M2b2 深度处理段四单元参数字段（2026-08-25；出处=docs/norms/{tiaojiechi,
    #    gaomidu,vxinglvchi,ziwai}.md 四表参数档/算例 1 输入行——同名跨单元字段
    #    ID 不耦合：各包 manifest 各写各的默认值，AGENTS §11 R4；小时/分钟/负荷
    #    带类单位在 DimKey 无对应量类者按 DIMENSIONLESS 裸值登记（单位语义随
    #    i18n 键走，四表口径：h/min/m³·m⁻²·h⁻¹/m·h⁻¹/支/模块）。side_disc_step
    #    为平面边长 0.5 m 离散档（tiaojiechi B/L、gaomidu B、vxinglvchi B/L
    #    共用语义形态，与 M2a2 dia_disc_step 池径档对称）。 ──
    # tiaojiechi 调节池（算例 1：t_reg=8.0 h/h2=5.0 m/ratio_lb=2.5/
    # n_pump_duty=2；B/L 档 0.5 m、DN 档 0.1 m）
    ("t_reg", "DIMENSIONLESS", "", "units.fields.t_reg", "load"),
    ("ratio_lb", "DIMENSIONLESS", "", "units.fields.ratio_lb", "geometry"),
    ("n_pump_duty", "DIMENSIONLESS", "", "units.fields.n_pump_duty", "equipment"),
    ("side_disc_step", "LENGTH", "m", "units.fields.side_disc_step", "geometry"),
    # gaomidu 高密沉淀池（算例 1：q_surface=15/r_sludge=0.04/t_mix=1.5 min/
    # t_floc=12 min/l_tube=1.0/h_clear=1.2/h_buffer=1.2/h_thick=2.0；
    # B 档 0.5 m、h_total 档 0.1 m）
    ("q_surface", "DIMENSIONLESS", "", "units.fields.q_surface", "load"),
    ("r_sludge", "DIMENSIONLESS", "", "units.fields.r_sludge", "operation"),
    ("t_mix", "DIMENSIONLESS", "", "units.fields.t_mix", "load"),
    ("t_floc", "DIMENSIONLESS", "", "units.fields.t_floc", "load"),
    ("l_tube", "LENGTH", "m", "units.fields.l_tube", "geometry"),
    ("h_clear", "LENGTH", "m", "units.fields.h_clear", "geometry"),
    ("h_buffer", "LENGTH", "m", "units.fields.h_buffer", "geometry"),
    ("h_thick", "LENGTH", "m", "units.fields.h_thick", "geometry"),
    # vxinglvchi V 型滤池（算例 1：v_filter=8.0 m/h/ratio_lb=2.5/
    # h_water_above=1.3/h_sand=1.3/h_bottom=1.0/t_cycle=24；B/L 档 0.5 m）
    ("v_filter", "DIMENSIONLESS", "", "units.fields.v_filter", "load"),
    ("h_water_above", "LENGTH", "m", "units.fields.h_water_above", "geometry"),
    ("h_sand", "LENGTH", "m", "units.fields.h_sand", "geometry"),
    ("h_bottom", "LENGTH", "m", "units.fields.h_bottom", "geometry"),
    ("t_cycle", "DIMENSIONLESS", "", "units.fields.t_cycle", "operation"),
    # ziwai 紫外消毒（算例 1：n_channel=2/v_channel=0.4/b_c=1.2/
    # n_lamp_module=8/l_module=0.6/l_stab=1.2/h_module=0.5；h_w 档 0.1 m）
    ("n_channel", "DIMENSIONLESS", "", "units.fields.n_channel", "equipment"),
    ("b_c", "LENGTH", "m", "units.fields.b_c", "geometry"),
    ("n_lamp_module", "DIMENSIONLESS", "", "units.fields.n_lamp_module",
     "equipment"),
    ("l_module", "LENGTH", "m", "units.fields.l_module", "equipment"),
    ("l_stab", "LENGTH", "m", "units.fields.l_stab", "geometry"),
    ("h_module", "LENGTH", "m", "units.fields.h_module", "equipment"),
    # ── M2c 市政余三单元参数字段（2026-08-26；出处=docs/norms/{cass,
    #    bashi_jiliangcao,wushui_tisheng}.md 三表参数档/算例 1 输入行——同名跨
    #    单元字段 ID 不耦合：各包 manifest 各写各的默认值，AGENTS §11 R4；
    #    t_cycle/t_settle 沿用既有字段（CASS 周期/沉淀时段 h 语义，V 滤过滤
    #    周期/初沉沉淀时间同名不同包默认值）；小时/分钟档类在 DimKey 无对应
    #    量类者按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键走，三表口径：
    #    h/min/台）。 ──
    # cass CASS 生物池（算例 1：n_pool=4/t_cycle=4 h/t_react=2.0/
    # t_settle=1.0[复用 M2a2]/t_draw=1.0/t_selector=0.75 h；L/B 0.5 m 档）
    ("n_pool", "DIMENSIONLESS", "", "units.fields.n_pool", "equipment"),
    ("t_react", "DIMENSIONLESS", "", "units.fields.t_react", "operation"),
    ("t_draw", "DIMENSIONLESS", "", "units.fields.t_draw", "operation"),
    ("t_selector", "DIMENSIONLESS", "", "units.fields.t_selector", "load"),
    # bashi_jiliangcao 巴歇尔计量槽（算例 1：b_throat=0.75 m，B7 七档离散）
    ("b_throat", "LENGTH", "m", "units.fields.b_throat", "geometry"),
    # wushui_tisheng 污水提升泵房（算例 1：t_well=10 min/h_static=10.0 m/
    # v_pipe=1.2 m/s/l_pipe=100 m/n_standby=1/h_well=2.0 m；DN 0.1 m 档）
    ("t_well", "DIMENSIONLESS", "", "units.fields.t_well", "load"),
    ("h_static", "LENGTH", "m", "units.fields.h_static", "load"),
    ("v_pipe", "VELOCITY", "m/s", "units.fields.v_pipe", "load"),
    ("l_pipe", "LENGTH", "m", "units.fields.l_pipe", "geometry"),
    ("n_standby", "DIMENSIONLESS", "", "units.fields.n_standby", "equipment"),
    ("h_well", "LENGTH", "m", "units.fields.h_well", "geometry"),
    # ── M3a2 矿井水线前段单元参数字段（2026-08-27；出处=docs/norms/
    #    mine_water_{input,tiaojiechi,chenshachi,ningjiao}.md 四表参数档/
    #    算例 1 输入行——同名跨单元字段 ID 不耦合：各包 manifest 各写各的
    #    默认值，AGENTS §11 R4；tiaojiechi/chenshachi/ningjiao 参数面全部
    #    复用既有字段（t_reg/h2/ratio_lb/n/side_disc_step/length_disc_step/
    #    t_mix/t_floc/t_clean——默认值跨包独立），仅 input 线首注入面与
    #    chenshachi/ningjiao 专属档新增登记。流量（m³/d 口径）/管径（mm）/
    #    停留（s·min·h）类在 DimKey 无对应量类或口径与规范单位不一致者按
    #    DIMENSIONLESS 裸值登记（单位语义随 i18n 键走，四表口径：
    #    m³/d/mm/s/min）。 ──
    # mine_water_input 矿井水输入（算例 1：Q_avg_daily=43836 m³/d/Kz=1.5/
    # DN=800 mm/z_water_inlet=100.0/z_ground=102.0/h_pool=3.0；进水水质
    # 六指标注入=GB/T 19223-2015 含悬浮物类典型值）
    ("q_avg_daily", "DIMENSIONLESS", "", "units.fields.q_avg_daily", "load"),
    ("kz", "DIMENSIONLESS", "", "units.fields.kz", "load"),
    ("dn_inlet", "DIMENSIONLESS", "", "units.fields.dn_inlet", "equipment"),
    ("z_water_inlet", "LENGTH", "m", "units.fields.z_water_inlet", "geometry"),
    ("z_ground", "LENGTH", "m", "units.fields.z_ground", "geometry"),
    ("h_pool", "LENGTH", "m", "units.fields.h_pool", "geometry"),
    ("ss_in", "CONCENTRATION", "mg/L", "units.fields.ss_in", "quality"),
    ("cod_in", "CONCENTRATION", "mg/L", "units.fields.cod_in", "quality"),
    ("bod5_in", "CONCENTRATION", "mg/L", "units.fields.bod5_in", "quality"),
    ("nh3n_in", "CONCENTRATION", "mg/L", "units.fields.nh3n_in", "quality"),
    ("tn_in", "CONCENTRATION", "mg/L", "units.fields.tn_in", "quality"),
    ("tp_in", "CONCENTRATION", "mg/L", "units.fields.tp_in", "quality"),
    # mine_water_chenshachi 平流沉砂池（算例 1：v_h=0.25 m/s/t_stay=60 s/
    # h2=0.5 m 复用/n=8 复用/t_clean=2 d 复用 M1A；l_cell 0.5 m 档/
    # B 0.1 m 档复用 side_disc_step/length_disc_step）
    ("v_h", "VELOCITY", "m/s", "units.fields.v_h", "load"),
    ("t_stay", "DIMENSIONLESS", "", "units.fields.t_stay", "load"),
    # mine_water_ningjiao 混凝反应池（算例 1：t_mix=1.0/t_floc=3.0 复用
    # M2B2；t_seed=2.0/t_ripen=1.5 新增；h2/ratio_lb/n/B 0.5 m 档复用）
    ("t_seed", "DIMENSIONLESS", "", "units.fields.t_seed", "load"),
    ("t_ripen", "DIMENSIONLESS", "", "units.fields.t_ripen", "load"),
    # ── M3a3 矿井水线后段单元参数字段（2026-08-27；出处=docs/norms/
    #    mine_water_{cifenli,gaomidu,vxinglvchi,ziwai}.md 四表参数档/
    #    算例 1 输入行——同名跨单元字段 ID 不耦合：各包 manifest 各写各的
    #    默认值，AGENTS §11 R4；q_surf/t_mix/t_floc/n/h2 族/l_tube/h_clear/
    #    h_thick/v_filter/side_disc_step/b_channel 复用既有登记（默认值跨包
    #    独立），仅各表专属参数新增登记。转速（rpm）/磁种投加（kg/d）/
    #    停留（min·h）/功率（W）/穿透率（%）/指数/剂量（mJ/cm²）类在
    #    DimKey 无对应量类者按 DIMENSIONLESS 裸值登记（单位语义随 i18n 键
    #    走，四表口径）。 ──
    # mine_water_cifenli 磁分离（主算例：n_units=4 台/omega=3 rpm/
    # q_surf=25 复用 M1A；m_seed=21918 kg/d=ningjiao KN-F13 口径参数面衔接）
    ("n_units", "DIMENSIONLESS", "", "units.fields.n_units", "equipment"),
    ("omega", "DIMENSIONLESS", "", "units.fields.omega", "equipment"),
    ("m_seed", "DIMENSIONLESS", "", "units.fields.m_seed", "operation"),
    # mine_water_gaomidu 高密沉淀（主算例：n=2 复用/t_mix=0.5/t_floc=12.0/
    # q_surf=6.0/l_tube=1.0/h_clear=1.0/h_thick=0.5 复用 M2B2；h_dist=1.5
    # 新增布水区高；B/L 0.5 m 档复用 side_disc_step）
    ("h_dist", "LENGTH", "m", "units.fields.h_dist", "geometry"),
    # mine_water_vxinglvchi V 型滤池（主算例：n=16 复用/v_filter=5.0 复用
    # M2B2；t_filter=24 h/h_media=1.0/h_water=1.2/h_plate=0.1/h_under=0.9
    # 新增；B/L 0.1 m 档复用 side_disc_step 包独立默认）
    ("t_filter", "DIMENSIONLESS", "", "units.fields.t_filter", "operation"),
    ("h_media", "LENGTH", "m", "units.fields.h_media", "geometry"),
    ("h_water", "LENGTH", "m", "units.fields.h_water", "geometry"),
    ("h_plate", "LENGTH", "m", "units.fields.h_plate", "geometry"),
    ("h_under", "LENGTH", "m", "units.fields.h_under", "geometry"),
    # mine_water_ziwai 紫外消毒渠（主算例：n=3 复用/b_channel=1.7 复用
    # M1A；h_channel=1.2/p_lamp=250 W/n_layer=6/d_long=0.12/xi_total=3/
    # n_t=1.5/t254=65 % 百分数口径新增）
    ("h_channel", "LENGTH", "m", "units.fields.h_channel", "geometry"),
    ("p_lamp", "DIMENSIONLESS", "", "units.fields.p_lamp", "equipment"),
    ("n_layer", "DIMENSIONLESS", "", "units.fields.n_layer", "equipment"),
    ("d_long", "LENGTH", "m", "units.fields.d_long", "equipment"),
    ("xi_total", "DIMENSIONLESS", "", "units.fields.xi_total", "load"),
    ("n_t", "DIMENSIONLESS", "", "units.fields.n_t", "load"),
    ("t254", "DIMENSIONLESS", "", "units.fields.t254", "quality"),
    # ── M3b2 污泥线七单元参数字段（sludge_*.md 七表参数档；口径同前段注）──
    ("ds_primary", "DIMENSIONLESS", "", "units.fields.ds_primary", "sludge"),
    ("p_primary", "DIMENSIONLESS", "", "units.fields.p_primary", "sludge"),
    ("ds_bio", "DIMENSIONLESS", "", "units.fields.ds_bio", "sludge"),
    ("p_bio", "DIMENSIONLESS", "", "units.fields.p_bio", "sludge"),
    ("ds_chem", "DIMENSIONLESS", "", "units.fields.ds_chem", "sludge"),
    ("p_chem", "DIMENSIONLESS", "", "units.fields.p_chem", "sludge"),
    ("s0_bod", "CONCENTRATION", "mg/L", "units.fields.s0_bod", "load"),
    ("se_bod", "CONCENTRATION", "mg/L", "units.fields.se_bod", "load"),
    ("v_bio", "VOLUME", "m3", "units.fields.v_bio", "geometry"),
    ("x_vss", "CONCENTRATION", "mg/L", "units.fields.x_vss", "load"),
    ("t_design", "DIMENSIONLESS", "", "units.fields.t_design", "operation"),
    ("v_press", "VELOCITY", "m/s", "units.fields.v_press", "load"),
    ("d_grav", "LENGTH", "m", "units.fields.d_grav", "geometry"),
    ("q_solid", "DIMENSIONLESS", "", "units.fields.q_solid", "load"),
    ("t_thicken", "DIMENSIONLESS", "", "units.fields.t_thicken", "load"),
    ("h_eff", "LENGTH", "m", "units.fields.h_eff", "geometry"),
    ("p_out", "DIMENSIONLESS", "", "units.fields.p_out", "sludge"),
    ("h_cone", "LENGTH", "m", "units.fields.h_cone", "geometry"),
    ("t_digest", "DIMENSIONLESS", "", "units.fields.t_digest", "operation"),
    ("t_digest_temp", "DIMENSIONLESS", "", "units.fields.t_digest_temp",
     "operation"),
    ("eta_vs", "DIMENSIONLESS", "", "units.fields.eta_vs", "sludge"),
    ("r_biogas", "DIMENSIONLESS", "", "units.fields.r_biogas", "operation"),
    ("machine_type", "DIMENSIONLESS", "", "units.fields.machine_type",
     "equipment"),
    ("dose_pam", "DIMENSIONLESS", "", "units.fields.dose_pam", "operation"),
    ("p_cake", "DIMENSIONLESS", "", "units.fields.p_cake", "sludge"),
    ("t_op", "DIMENSIONLESS", "", "units.fields.t_op", "operation"),
    ("r_evap", "DIMENSIONLESS", "", "units.fields.r_evap", "equipment"),
)
