/**
 * 待摆/已摆单元显示名（V4 P3 中文化）：catalog name_zh 单源——查表键=
 * node kind ?? unitId（thumbnailFlow metaByUnit 同口径：builtin 归 kind 键
 * ——inlet→municipal_input→市政输入；节点 id ≠ catalog 键的实证面）。
 *
 * 输入:  raw 项目体（design.nodes 的 kind 面——弱类型防御读取）+catalog
 *        （useListUnitsApiUnitsGet select=unitNameIndex 投影——同键缓存
 *        与画布/三维面复用零额外请求）
 * 输出:  useUnitDisplayNames(raw) → nameOf(unitId)（catalog 命中=中文名；
 *        kind 缺席按 unitId 直查；未收录回退 id 透传——诚实呈现不猜语义，
 *        conditionLabels/dimLabels 同口径；title 悬浮原 id 归消费面）
 *
 * 规格说明（V4 前端信息面批 P3——uiglobal A3=in-register A4）：
 *   - 纯显示层映射零业务推导（design.nodes 键集/structures 键集恒一致
 *     由编辑流保证——本件只读 kind 不改键）；
 *   - hook 恒序位（早退前调用——SiteplanPane 顶层；usePoolGroups 先例
 *     同为 lib 内 hook）。
 */
import { useMemo } from "react";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { unitNameIndex } from "../../../shared/conditionLabels";

/** plain object 判定（弱类型防御读取——projectSite 同款私有面）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** design.nodes 的 unit_id → kind 投影（kind 非串=缺席——不猜语义）。 */
function kindByUnitOf(raw: unknown): Map<string, string> {
  const kindByUnit = new Map<string, string>();
  if (!isRecord(raw)) {
    return kindByUnit;
  }
  const design = raw["design"];
  const nodes = isRecord(design) ? design["nodes"] : undefined;
  if (isRecord(nodes)) {
    for (const [unitId, node] of Object.entries(nodes)) {
      if (isRecord(node) && typeof node["kind"] === "string") {
        kindByUnit.set(unitId, node["kind"]);
      }
    }
  }
  return kindByUnit;
}

/** 单元显示名 hook（catalog name_zh 单源——查表键=kind ?? unitId）。 */
export function useUnitDisplayNames(raw: unknown): (unitId: string) => string {
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};
  return useMemo(() => {
    const kindByUnit = kindByUnitOf(raw);
    return (unitId: string): string =>
      unitNames[kindByUnit.get(unitId) ?? unitId] ?? unitId;
  }, [raw, unitNames]);
}
