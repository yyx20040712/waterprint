/**
 * 量纲显示映射：DimKey 枚举 →（中文量名, 单位符号）。
 *
 * 输入:  entry.dim 字符串（/api/units params 与结果载荷的 DimKey 枚举名——
 *        core contracts/quantity.py DimKey 15 成员）
 * 输出:  dimLabel(dim) → 中文量名+单位符号显示串（如 FLOW→「流量 m³/d」）；
 *        未知枚举原样返回（诚实呈现不猜语义——与 STAGE_LABELS 同口径）
 *
 * 规格说明（FIX-ACC1③，2026-09-09 验收缺陷 B1；2A2 批 2026-10-05 注释
 * 勘正——UF-62①：原句「单位符号随 core CANONICAL_UNITS 真源」失实）：
 * 参数元数据此前直出 DIMENSIONLESS/CONCENTRATION 裸枚举名——无物理
 * 意义（用户报告）。本映射=**手写显示层表，非 CANONICAL_UNITS 派生**：
 * 15 成员中 14 成员单位符号与 core 规范串一致（仅 m2→m²/m3→m³/
 * degC→℃ 显示美化）；**FLOW 为刻意分歧**——标签 m³/d 锚定进水参数面
 * 绑定点（municipal_input q_avg_daily m³/d，inlet-m3d 契约批 2026-10-02
 * 用户裁决「统一为 m³/d」；params_guard A-1~A-3 同面），内核规范单位
 * 仍 m3/s（ADR-002——换算只在 core parse 边界，白名单 FLOW 两写法
 * {"m3/s","m3/d"} 均合法输入）；FLOW 维度**输出面**（方案表 dim 列/
 * 对比矩阵 aao·cass q_air 行）值=规范 m3/s 而标签随本表 m³/d=已知
 * 错配（UF-63 登记，后续批裁量）。**不做任何数值换算**（FE 零换算
 * 纪律）；白名单外写法不出现（枚举名是内核类型面非自由文本）。
 * POWER 规范单位=W（真源口径，不换 kW）。
 */

/** 量纲条目：中文量名 + 单位符号（DIMENSIONLESS 单位串为空）。 */
export type DimLabel = { name: string; unit: string };

/** DimKey → 显示条目（15 成员全量——与 core quantity.py CANONICAL_UNITS
 * 逐键对齐复核，FLOW 单键刻意分歧〔标签 m³/d=进水参数面口径，内核规范
 * m3/s——见上规格说明 UF-62①/UF-63 注记〕；2A2 批 2026-10-05 勘正：
 * 原「CANONICAL_UNITS 镜像」短语失实）；
 * DimKey 扩成员批 2026-09-12：+TIME_H/TIME_D/FLOW_H 刻度档；参数面单位批
 * 同制补齐：+TIME_MIN/TEMPERATURE——degC→℃ 纯显示层美化，零换算）。 */
const DIM_LABELS: Record<string, DimLabel> = {
  FLOW: { name: "流量", unit: "m³/d" },
  FLOW_H: { name: "流量", unit: "m³/h" },
  CONCENTRATION: { name: "浓度", unit: "mg/L" },
  LENGTH: { name: "长度", unit: "m" },
  AREA: { name: "面积", unit: "m²" },
  VOLUME: { name: "体积", unit: "m³" },
  MASS: { name: "质量", unit: "kg" },
  TIME: { name: "时间", unit: "s" },
  TIME_H: { name: "时间", unit: "h" },
  TIME_MIN: { name: "时间", unit: "min" },
  TIME_D: { name: "时间", unit: "d" },
  VELOCITY: { name: "流速", unit: "m/s" },
  POWER: { name: "功率", unit: "W" },
  TEMPERATURE: { name: "温度", unit: "℃" },
  DIMENSIONLESS: { name: "无量纲", unit: "" },
};

/** 量纲显示串：已知枚举→「量名 单位」（无单位→仅量名）；未知→原样。 */
export function dimLabel(dim: string): string {
  const entry = DIM_LABELS[dim];
  if (entry === undefined) {
    return dim;
  }
  return entry.unit === "" ? entry.name : `${entry.name} ${entry.unit}`;
}

/** 单位符号直取（C2-params Q4：输入控件单位后缀消费[原 addonAfter——
 * C2VD V6 迁移 Space.Compact+后缀 span]——与 dimLabel 同表同源零换算；
 * 无量纲/未知→空串=无后缀，量名经声明面悬浮通道）。 */
export function dimUnit(dim: string): string {
  return DIM_LABELS[dim]?.unit ?? "";
}
