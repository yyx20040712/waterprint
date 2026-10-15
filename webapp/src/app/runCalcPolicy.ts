/**
 * runCalcPolicy 提交计算决策纯函数（v1-20261015 批自 ribbon.tsx 拆迁——
 * legacy 退役前置：zoneBand 消费的三纯函数迁独立件，ribbon 本体随旧壳
 * 物理删除；语义逐字保持〔P0-B/F3-A-1 历史锚不动〕）。
 *
 * 输入:  decideRunCalc(dirty, body, paramDraftCount)——编辑会话/载荷就绪/
 *        参数草稿计数三轴；paramDraftBlockMessage(count)——拦截文案；
 *        rawCheckedUnits(raw)——项目 raw 的 design.checked_units 宽容读取
 * 输出:  提交计算动作分派（"block-param-draft"|"save-run"|"run"|
 *        "block-unready"）+拦截文案+受检单元宽读——消费面 zoneBand.tsx
 *        （v4 顶带工具区唯一消费方）；runCalcPolicy.test.ts 锁三轴判定
 *        与文案三要素（断言自 canvasEditToolbar.test 随迁零弱化）
 */
export type RunCalcDecision = "block-param-draft" | "save-run" | "run" | "block-unready";

/** raw design.checked_units 宽容读取（constraintPicker.rawCheckedUnits 同口径）。 */
export function rawCheckedUnits(raw: unknown): string[] {
  if (typeof raw !== "object" || raw === null) {
    return [];
  }
  const design = (raw as Record<string, unknown>)["design"];
  if (typeof design !== "object" || design === null) {
    return [];
  }
  const checked = (design as Record<string, unknown>)["checked_units"];
  return Array.isArray(checked) ? checked.filter((id): id is string => typeof id === "string") : [];
}

/** P0-B 决策面（fix-plan 批2 纯函数——vitest 直测）：提交计算动作分派。
 *  dirty 编辑态：body 未就绪=阻断并提示（保存需要体）；就绪=先存后算。
 *  只读态：draft===null ⇒ body 恒 null 属正常态，直接算（呈裁⑥ 常驻
 *  提交计算语义——旧实现把 body 守卫放在最前，只读态被静默吞掉）。
 *  F3/A-1 扩：参数草稿计数非零=block-param-draft（先于存/算——工具条
 *  保存不携带参数草稿，直算=陈旧参数裸失败；禁自动 apply 红线）。 */
export function decideRunCalc(
  dirty: boolean,
  body: unknown,
  paramDraftCount = 0,
): RunCalcDecision {
  if (paramDraftCount > 0) {
    return "block-param-draft";
  }
  if (dirty) {
    return body === null ? "block-unready" : "save-run";
  }
  return "run";
}

/** F3/A-1 拦截文案（纯函数——vitest 锁三要素：计数/『提交重算』正门/
 *  「保存不携带」因果；禁含糊指路）。 */
export function paramDraftBlockMessage(count: number): string {
  return `参数面板有 ${count} 项未提交——请先在参数面板点『提交重算』（工具条保存不携带参数草稿）`;
}
