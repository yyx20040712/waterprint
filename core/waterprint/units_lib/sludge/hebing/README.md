# sludge_hebing —— 污泥合并（污泥线，M3b2 已实装）

各线排泥汇流（初沉/剩余/化学三股参数注入）+ 全厂污泥产量衡算节点
（经验产率法主线 Sy=Q(S₀−Sₑ)·y/1000 + 机理互校 ΔX=Y·QΔS−Kd·V·Xv，
ADR-008 ④ 已拍板路线）。

- 输入：三股排泥面（ds/p 六参数——市政 34760 案例实值衔接；GOLDEN4a
  起三 IN 口实体化 in_primary/in_bio/in_chem 双模：三口无边=参数注入
  [现行三案例形态，行为不变]/全有边=入流直值[HB-F1~F3 不重算，入流即
  真值]/部分有边=显式拒——GOLDEN4b 真边接通的地基，等价迁移断言在册）
- 输出：下游端口量（sludge_shusong 污泥输送，SLUDGE 出流三量）
- 旧系统对应：mod `wuni_hebing`（交叉对照，非依据）
- golden 绑定：污泥链全流程（主算例出流 ds 5306.515 kg/d / q 409.3365833333 m³/d /
  含水率 0.9870363041）
- 公式组（已实装）：HB-F1~F13——三股湿泥量/汇流 DS·湿量·干基水量·合并
  含水率（mix P4 镜像）/经验产率/Kd 温度修正/机理互校/偏差/闭合校核
- 物理不变性（后续批进 tests/properties.py）：湿泥量加和守恒、DS
  （干固体）加和守恒（contracts/properties_sludge.py 锁定 mix 面在册）
- 数值真源：docs/norms/sludge_hebing.md（M3b1 表，待追认）+
  data/coefficients 0.6.0（factor.hebing.* 裸短名 12 键；removal 零键——
  污泥单元无水质去除概念）
- 语义注记：互校偏差 >20% 出 WARN 不阻断（ADR-008 校核侧语义）；
  CJJ 131-2009 已纳出处白名单（I3 改标 2026-08-28 九裁②）——本包
  无 CJJ 改标对象（yield 三键 GB §8.1.4 表 5 明确条号九裁⑤挂账，
  其余手册单源）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
