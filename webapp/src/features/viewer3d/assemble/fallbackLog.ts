/**
 * 装配降级登记簿（brief 铁律 5：不静默不出错——降级可观测）。
 *
 * 输入:  降级事件（unit_id+原因+明细）
 * 输出:  logFallback 追加+fallbackEntries 快照（probe/测试消费——
 *        window.__probe.viewer3d.fallbacks 登记面）
 *
 * 规格说明（spec §6 两层分工的消费面：deviation 判定→装配器走
 *   FallbackBox+本登记；P7 inst 组无场景数量→不渲染+本登记；glb
 *   加载失败→原语回退+本登记。合法态不登记：status=pending 走原语
 *   渲染=声明面行为；无 registry 条目=非本系统单元）。
 */

export type FallbackEntry = {
  readonly unitId: string;
  readonly reason: string;
  readonly detail?: string;
  readonly at: number;
};

const MAX_ENTRIES = 200;
const entries: FallbackEntry[] = [];

/** 追加降级事件（环形截断 200——单会话可观测面足够）。 */
export function logFallback(unitId: string, reason: string, detail?: string): void {
  entries.push({ unitId, reason, detail, at: Date.now() });
  if (entries.length > MAX_ENTRIES) {
    entries.splice(0, entries.length - MAX_ENTRIES);
  }
}

/** 登记快照（新数组——消费方免并发变异）。 */
export function fallbackEntries(): readonly FallbackEntry[] {
  return [...entries];
}

/** 测试复位（生产面零消费）。 */
export function resetFallbackLog(): void {
  entries.length = 0;
}
