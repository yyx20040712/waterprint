/**
 * 职责：枚举结果字段窄化与 409 锁冲突判定纯函数（B7 R+ 自 solutionsPane
 * 提取——行数预算 516>500 越界修前进；零行为变更纯搬迁）。
 *
 * 输入:  TaskStatus.result 弱类型载荷（unknown）+HTTP 错误对象
 * 输出:  窄化字段值/grid_fields string[]/锁冲突布尔+提示文案（消费方=
 *        app/solutionsPane——app 层薄壳不测面沿先例）
 */

import { WaterprintApiError } from "../../../shared/api/http";

/** 409 锁冲突保守提示（CP2 D2——照 UX2 AssumptionsPanel 口径不 force 不重试）。 */
export const LOCK_HINT = "项目已被他处修改，请刷新后重试（并发写锁守门——不自动覆盖）";

/** 409 面=锁文件冲突（server error_type=ProjectLockedError；HTTP_409 兜底）。 */
export function isLockConflict(error: unknown): boolean {
  return (
    error instanceof WaterprintApiError &&
    (error.code === "ProjectLockedError" || error.code === "HTTP_409")
  );
}

/** result 载荷字段窄化（弱类型 Mapping——app 层内联，薄壳不测面）。 */
export function resultField(result: unknown, key: string): unknown {
  if (typeof result !== "object" || result === null) {
    return null;
  }
  return (result as Record<string, unknown>)[key] ?? null;
}

/** grid_fields 窄化（string[] 形状非法→空——表挂载仍可无应用列）。 */
export function narrowGridFields(result: unknown): string[] {
  const value = resultField(result, "grid_fields");
  return Array.isArray(value) && value.every((f) => typeof f === "string")
    ? (value as string[])
    : [];
}
