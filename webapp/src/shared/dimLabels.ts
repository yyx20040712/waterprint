/**
 * 量纲显示映射：DimKey 枚举 →（中文量名, 单位符号）。
 *
 * 输入:  entry.dim 字符串（/api/units params 与结果载荷的 DimKey 枚举名——
 *        core contracts/quantity.py DimKey 10 成员）
 * 输出:  dimLabel(dim) → 中文量名+单位符号显示串（如 FLOW→「流量 m³/d」）；
 *        未知枚举原样返回（诚实呈现不猜语义——与 STAGE_LABELS 同口径）
 *
 * 规格说明（FIX-ACC1③，2026-09-09 验收缺陷 B1）：参数元数据此前直出
 * DIMENSIONLESS/CONCENTRATION 裸枚举名——无物理意义（用户报告）。本映射
 * =纯显示层：单位符号随 core CANONICAL_UNITS 真源（FLOW→m3/d 等），仅做
 * 展示美化（m3/d→m³/d 上标），**不做任何数值换算**（换算只发生在 core
 * parse 边界——AGENTS 边界约沿袭）；白名单外写法不出现（枚举名是内核
 * 类型面非自由文本）。POWER 规范单位=W（真源口径，不换 kW）。
 */

/** 量纲条目：中文量名 + 单位符号（DIMENSIONLESS 单位串为空）。 */
export type DimLabel = { name: string; unit: string };

/** DimKey → 显示条目（10 成员全量——core quantity.py CANONICAL_UNITS 镜像）。 */
const DIM_LABELS: Record<string, DimLabel> = {
  FLOW: { name: "流量", unit: "m³/d" },
  CONCENTRATION: { name: "浓度", unit: "mg/L" },
  LENGTH: { name: "长度", unit: "m" },
  AREA: { name: "面积", unit: "m²" },
  VOLUME: { name: "体积", unit: "m³" },
  MASS: { name: "质量", unit: "kg" },
  TIME: { name: "时间", unit: "s" },
  VELOCITY: { name: "流速", unit: "m/s" },
  POWER: { name: "功率", unit: "W" },
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
