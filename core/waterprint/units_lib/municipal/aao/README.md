# municipal_aao —— AAO 生物池（市政污水线；M2a2 已实装/M2 正式验收）

厌氧-缺氧-好氧工艺同步脱氮除磷与有机物去除。

- 输入：上游端口量（chuchenchi 初沉池或 tiaojiechi 调节池）
- 输出：下游端口量（erchunchi 辐流二沉池）
- 产股口（GOLDEN4a D3，2026-08-28）：sludge_out SLUDGE 无条件产股——
  ds=AO-F6 s_y 全厂/q_wet=AO-F7（hebing ds_bio 注入链路同源）+
  moisture 0.994 与 hebing p_bio 同源
- 旧系统对应：mod `aao`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2a2 已实装，真源=docs/norms/aao.md 起草表 2026-08-25 数据
  策略 v2，数值面待追认；路线=ADR-008 ①负荷法主线+泥龄校核带）：
  AO-F1~F14（污泥负荷与分区容积[厌氧/缺氧/好氧]、需氧量、内回流与
  外回流比、剩余污泥量、污泥龄校核）；追认口径按表冻结：好氧泥龄判断
  口径（AO-F8，全池口径备考注记）、回流泵双口径（AO-F13 外回流最高时
  /AO-F14 内回流平均时，相差 Kz 倍）；
  L7 池体图元批（2026-09-04）扩 AO-F15~F19 几何族五式（CASS CA-F8/
  F24~F26/F11 同族平移——总控 L7 D3/D5 裁定，待领域专家追认）：
  a_pool=v_total/h2（容积折水面，连续流全池口径——n 保持纯计算分格
  语义）/h_pool=h_super+h2/l_pool_raw=sqrt(a_pool×ratio_lb)/
  b_pool_raw=sqrt(a_pool÷ratio_lb)/v_pool=圆整边长×h2；dims 新增 8 键
  （h2/a_pool/l_pool/b_pool/h_pool/l_pool_raw/b_pool_raw/v_pool——
  ceil 0.5 m 档收口在 compute，v_pool≥v_total 圆整裕量诚实呈现）
- 系数通道：factor.aao.\*（data/coefficients 0.2.0，经 app._unit_params
  投影；L7 扩 superheight 0.3——GB 50014 超高一般要求，与
  safety.superheight 假设键同源同值）；去除率 removal.aao.\*.
  mod_default；TN_eff=15 mg/L 为出水标准数据条目（manifest 参数
  tn_eff，非本表系数）；L7 几何形态参数三件（manifest params：
  h2 有效水深 5.0[4~6]/ratio_lb 长宽比 2.5[2~3]/side_disc_step 边长
  圆整档 0.5——CASS 同值同 range 平移）
- 物理不变性（归后续批进 tests/properties.py）：分区容积和=总容积、
  需氧量≥0、回流比>0、剩余污泥≥0

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
