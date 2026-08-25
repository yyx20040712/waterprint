# municipal_bashi_jiliangcao —— 巴歇尔计量槽（市政污水线；M2c 已实装/M2 正式验收）

标准型巴歇尔量水槽（B7 七档全档流量式主线：Q=C·ha^n——C/n 按喉宽档
从手册表录入；标准尺寸比构造 + 淹没度自由流判别 + 槽身水头损失估算），
出水明渠计量，提供流量计量与记录；计量单元零去除（终水穿流）。

- 输入：上游端口量（ziwai 紫外消毒，全厂终水）
- 输出：下游端口量（排放口）
- 旧系统对应：mod `bashi_jiliangcao（社区）`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2c 已实装，真源=docs/norms/bashi_jiliangcao.md 起草表
  2026-08-26 数据策略 v2，数值面待追认）：BL-F1~BL-F9（实测水头流量
  读数/设计与平均水头反解选档校核/收缩-喉道-扩散段标准尺寸/槽总长/
  淹没度 σ=Hb/Ha ≤ scrit 自由流判别/水头损失估算）；喉宽 b_throat
  grid=B7 七档 [0.25,0.45,0.75,1.0,1.2,1.5,2.1]（简报枚举 0.5/1.25/2.0
  非手册标准档按最近标准档映射——起草表追认点 1）
- 系数通道：factor.bashi_jiliangcao.flume.<档>.\*（七档 C/n/scrit/
  hmin/hmax 共 35 键，data/coefficients 0.4.0 经 app._unit_params 投影；
  "CJ/T 3008.3-1993 正式文本核对"降级为追认点注记[Q3 挂账口径]）；
  去除率 removal.bashi_jiliangcao.\*.mod_default 全 0.0（计量单元无
  处理——出水质=入水质逐键透传不经 apply，ziwai 零去除形态同款）
- 物理不变性（归后续批进 tests/properties.py）：流量-水头关系单调
  （C>0、n>1）、喉宽取标准档位（非档位域拒）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
