/**
 * 职责：枚举结果字段窄化纯函数（B7 R+ 自 solutionsPane 提取——行数预算
 * 516>500 越界修前进；零行为变更纯搬迁；B15 409 锁冲突判定面上移
 * shared/api/http.ts 单源——本件不再承载）。
 *
 * 输入:  TaskStatus.result 弱类型载荷（unknown）
 * 输出:  窄化字段值/grid_fields string[]（消费方=
 *        app/solutionsPane——app 层薄壳不测面沿先例）
 */

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
