/**
 * 参数表单纯函数层（F5 批 2026-11-20 自 ParamForm 抽出+扩面）：草稿文本
 * 归一原语+声明面悬浮文本合成+进水必填门。
 *
 * 输入:  ParamEntry 目录条目（含第七字段 required——服务端 builtin 构造期
 *        必填集镜像）+design 覆盖值+表单草稿（string 形态）
 * 输出:  纯函数族（draftValueOf/normalizeDraftText 草稿文本归一〔自
 *        ParamForm 迁驻——B1 R2/M1 原语零变〕；metaTooltipText 声明面悬浮
 *        文本〔Q3 迁驻零变〕；effectiveRequiredValue 必填有效值/
 *        missingRequiredFields 必填缺失清单——E2E 审计 F5：进水参数为
 *        项目基础资料无默认值（目录 required 面），提交门前置到表单
 *        〔空态引导替代 422 撞墙〕，物理域检仍归 server 显式提交面）
 */

import type { ParamEntry } from "../../../shared/api/generated/model";
import { dimLabel } from "../../../shared/dimLabels";
import { normalizeDraftValue, trimFloatNoise } from "./designParams";

/** F8 通道口归一（InputNumber onChange——步进/键入值 trimFloatNoise；
 * 非数值形态[防御]原样走 invalid 诚实拒路径；自 ParamForm 迁驻零变）。 */
export const draftValueOf = (value: number | string | null): string =>
  value === null || value === ""
    ? ""
    : typeof value === "number"
      ? trimFloatNoise(value)
      : value;

/** 草稿字段归一原语（失焦/Enter 两通道共享——B1 R2/M1 提取避免复制；
 *  可解析→trimFloatNoise 归一串；非数/空原样保留（诚实拒路径——
 *  invalidFields 判定留在 collectParamChanges 层，本层不吞；迁驻零变）。 */
export const normalizeDraftText = (text: string): string => {
  const parsed = normalizeDraftValue(text);
  return parsed === null ? text : trimFloatNoise(parsed);
};

/** 声明面悬浮全量（Q3：MetaLine 常显收敛进 title——dim/默认/范围/档位；
 *  自 ParamForm 迁驻零变）。 */
export function metaTooltipText(entry: ParamEntry): string {
  const parts = [dimLabel(entry.dim)];
  if (entry.default !== null && entry.default !== undefined) {
    parts.push(`默认 ${entry.default}`);
  }
  if (entry.range) {
    parts.push(`范围 [${entry.range.min}, ${entry.range.max}]`);
  }
  if (entry.grid) {
    parts.push(`档位 [${entry.grid.join(", ")}]`);
  }
  parts.push(`field_id: ${entry.field_id}`);
  return parts.join(" · ");
}

/**
 * 必填项有效值（F5）：草稿（归一数）→ design 覆盖 → default → null。
 *
 * 草稿在场但非数（空/NaN）=null 缺失态（诚实拒——不以旧值顶替用户清空）。
 */
export function effectiveRequiredValue(
  entry: ParamEntry,
  designValues: Record<string, number>,
  drafts: Record<string, string>,
): number | null {
  const draftText = drafts[entry.field_id];
  if (draftText !== undefined) {
    return normalizeDraftValue(draftText);
  }
  const designValue = designValues[entry.field_id];
  if (designValue !== undefined) {
    return designValue;
  }
  return entry.default ?? null;
}

/**
 * 必填缺失清单（F5 提交门判据）：required 条目中有效值为 null 者
 * （空数组=门可通过）。有效值回退序与 collectParamChanges 脏比较基准
 * 同构（design 覆盖 ?? manifest 默认）。
 */
export function missingRequiredFields(
  entries: ParamEntry[],
  designValues: Record<string, number>,
  drafts: Record<string, string>,
): ParamEntry[] {
  return entries.filter(
    (entry) =>
      entry.required === true &&
      effectiveRequiredValue(entry, designValues, drafts) === null,
  );
}
