# sludge_shusong —— 污泥输送（污泥线，M3b2 已实装）

管道水力输送污泥段：压力流管径/流速（GB 50014-2021 §8）+ 重力自流最小
坡度/流速（曼宁满流）两式主线——DS/含水率穿流守恒显式。

- 输入：上游端口量（sludge_hebing 污泥合并，SLUDGE 入流三量）
- 输出：下游端口量（sludge_bengzhan 污泥泵站，SLUDGE 出流三量穿流）
- 旧系统对应：mod `wuni_shusong`（交叉对照，非依据）
- golden 绑定：污泥链全流程（主算例 DN75 压力管 v_act=1.0724 m/s 带内/
  DN150 重力档 v_grav=0.8618 m/s ≥0.7 合格）
- 公式组（已实装）：ST-F1~F9——时/秒输泥量、压力管径（0.025 m 档 ceil）、
  实流速校核、曼宁最小坡度反解、整定坡度 max、重力流速、DS/含水率穿流
- 物理不变性（后续批进 tests/properties.py）：流速在防淤积带内、损失≥0
- 数值真源：docs/norms/sludge_shusong.md（M3b1 表，待追认）+
  data/coefficients 0.6.0（factor.shusong.* 裸短名 6 键；removal 零键）
- 语义注记：无构筑物（wall_thickness_coef 不建——bashi_jiliangcao 先例
  口径）；CJJ 131-2009 已纳出处白名单（I3 改标 2026-08-28 九裁②）
  ——本包 2 键 source 规程级标注

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥。
