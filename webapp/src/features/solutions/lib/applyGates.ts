/**
 * 方案应用闸纯函数层（P0-2——F5 深链死锁修复 r2 三守卫；2026-09-11）。
 *
 * 输入:  表源任务 result 载荷（unit_id/design_hash 扩源键）+当前项目 raw
 *        GET 体（metadata.content_hash）+下拉/固化单元态+design 投影单元表
 * 输出:  EnumSource 窄化（三源值）/applyGateReason（闸①②禁用因——null=
 *        放行）/applyDriftWarn（闸③漂移警示）
 *
 * 规格说明（op-chain-fix-plan §二 r2——solutionsPane 行数预算越界修沿
 *   solutionsFields.ts B7 先例抽取）：
 *   - 回填源：result.unit_id（worker 扩源——服务面 submit 已守 len==1
 *     ADR-005 单单元语义）；漂移源：result.design_hash（枚举时点 design
 *     摘要——calc result 同键先例）对当前 metadata.content_hash（B4 双
 *     胖子镜像锁与 core 真源逐字节一致——比对口径成立）；
 *   - 闸①：下拉选定≠表源单元→禁用+述因（应用目标恒为表源单元 R2 固化
 *     ——差异态禁用防误配；下拉空=null 视为未选定不触发——回填 effect
 *     已同步恢复下拉显示）；
 *   - 闸②：表源单元不在 design.nodes 投影→禁用（P0-3 删除能力引入后
 *     可达——前置守卫）；
 *   - 闸③：漂移=警示不硬禁（呈裁⑧ 甲案：横幅+应用钮二次确认后放行）；
 *     旧任务载荷缺键=null 诚实降级（不猜不阻断）。
 */
export type UnitOption = { unitId: string };

/** 表源扩源窄化结果（三源——null=载荷缺键/未就绪诚实降级）。 */
export type EnumSource = {
  resultUnitId: string | null;
  resultDesignHash: string | null;
  currentDesignHash: string | null;
};

/** 窄化字符串键（非空串才收——空串=缺键同义）。 */
function narrowString(value: unknown): string | null {
  return typeof value === "string" && value !== "" ? value : null;
}

/** result 载荷+当前项目体→三源窄化（pane 单行消费面）。 */
export function narrowEnumSource(
  result: unknown,
  rawProject: unknown,
): EnumSource {
  const metadata = (
    rawProject as { metadata?: { content_hash?: unknown } } | undefined
  )?.metadata;
  return {
    resultUnitId: narrowString(
      (result as Record<string, unknown> | null)?.unit_id,
    ),
    resultDesignHash: narrowString(
      (result as Record<string, unknown> | null)?.design_hash,
    ),
    currentDesignHash: narrowString(metadata?.content_hash),
  };
}

/** 闸①②：应用禁用因（null=放行；表未挂载恒 null——无应用面）。 */
export function applyGateReason(options: {
  enumeratedUnitId: string | null;
  unitId: string | null;
  units: readonly UnitOption[];
  tableEnabled: boolean;
}): string | null {
  const { enumeratedUnitId, unitId, units, tableEnabled } = options;
  if (!tableEnabled) {
    return null;
  }
  if (enumeratedUnitId === null) {
    // 历史任务载荷缺 unit_id（P0-2 server 扩源前建的任务）——重提交可恢复
    return "未识别到方案表源单元（历史任务载荷缺 unit_id）——重新提交枚举可恢复应用";
  }
  if (unitId !== null && unitId !== enumeratedUnitId) {
    return `单元下拉已选 ${unitId}，方案表来自 ${enumeratedUnitId} 的枚举——切回 ${enumeratedUnitId} 或重新提交枚举后再应用`;
  }
  if (!units.some((unit) => unit.unitId === enumeratedUnitId)) {
    return "方案表源单元已不在当前项目设计中（可能已被删除）——不可应用";
  }
  return null;
}

/** 闸③：版本漂移警示（两源齐且不等——缺任一源=不可证漂移不警示）。 */
export function applyDriftWarn(source: EnumSource, tableEnabled: boolean): boolean {
  return (
    tableEnabled &&
    source.resultDesignHash !== null &&
    source.currentDesignHash !== null &&
    source.resultDesignHash !== source.currentDesignHash
  );
}
