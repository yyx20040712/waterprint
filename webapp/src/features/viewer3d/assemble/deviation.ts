/**
 * 比例域降级判定（assemble/spec.md §6 规格冻结件——批3 首件）。
 *
 * 输入:  TargetDims（sceneDimsToTarget 归并）+registry ratioDomain 声明条目
 * 输出:  DeviationResult（ok=模板面可行；fallback 携 reason/明细——装配器
 *        走 FallbackBox+fallbackLog 登记，不静默不出错）
 *
 * 规格说明（brief 铁律 5+Kimi §2.2；纯数据零异常——与数学核两层分工：
 *  本函数=数据级降级决策（非正尺寸/出域→fallback 结果对象），数学核
 *  throw=漏裁防线）：
 *   - 非正尺寸（H≤0 类）→ nonpositive_dim（绝对域 sanity 同路径——
 *     L>10×典型幅等极端由比例域覆盖）；
 *   - 逐条目闭域判定：min ≤ numerator/denominator ≤ max（边界恰等 ok
 *     ——闭域口径）；首条出域即返（明细携 key/ratio/domain 供登记）；
 *   - 空声明表=无约束 ok（registry 可选面——无比例域声明的族不判域）；
 *   - typical 比（Kimi ln|actual/typical| 度量）归 registry 建条目时以
 *     templateSize 标定入 [min,max] 绝对域——运行时零典型比计算
 *     （判定与度量等价单调，取数据面更简式）。
 */

import type { DeviationResult, RatioDomainEntry, TargetDims } from "./types";

/** 比例域判定（纯数据决策——ok/fallback 二态+明细；零异常零 throw）。 */
export function deviation(
  target: TargetDims,
  domain: readonly RatioDomainEntry[],
): DeviationResult {
  for (const dim of ["L", "W", "H"] as const) {
    if (!(target[dim] > 0)) {
      return { ok: false, reason: "nonpositive_dim", dim };
    }
  }
  for (const entry of domain) {
    const ratio = target[entry.numerator] / target[entry.denominator];
    if (!(ratio >= entry.min && ratio <= entry.max)) {
      return {
        ok: false,
        reason: "ratio_out_of_domain",
        key: entry.key,
        ratio,
        domain: [entry.min, entry.max],
      };
    }
  }
  return { ok: true };
}
