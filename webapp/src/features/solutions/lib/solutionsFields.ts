/**
 * 职责：枚举结果字段窄化纯函数（B7 R+ 自 solutionsPane 提取——行数预算
 * 516>500 越界修前进；零行为变更纯搬迁；B15 409 锁冲突判定面上移
 * shared/api/http.ts 单源——本件不再承载）。
 *
 * 输入:  TaskStatus.result 弱类型载荷（unknown）
 * 输出:  窄化字段值/grid_fields {key,dim,label_zh}[]（B2②对象载荷窄化；
 *        消费方=app/solutionsPane——app 层薄壳不测面沿先例）
 */

/** result 载荷字段窄化（弱类型 Mapping——app 层内联，薄壳不测面）。 */
export function resultField(result: unknown, key: string): unknown {
  if (typeof result !== "object" || result === null) {
    return null;
  }
  return (result as Record<string, unknown>)[key] ?? null;
}

/** grid_fields 条目（B2② server worker 对象载荷）：key=field_id（apply
 * payload 键/calcbook 追溯链）；dim=DimKey 枚举名；label_zh=manifest 中文
 * 真源（null=真源缺失诚实缺省——显示层 key 兜底，禁降级填充混入数据层）。 */
export type GridField = {
  key: string;
  dim: string;
  label_zh: string | null;
};

/** grid_fields 元素形状判定（key/dim 字符串+label_zh string|null——与
 * narrowSolutionPage 同口径读已知键，不拒多余键）。 */
function isGridField(item: unknown): item is GridField {
  if (typeof item !== "object" || item === null) {
    return false;
  }
  const record = item as Record<string, unknown>;
  return (
    typeof record["key"] === "string" &&
    typeof record["dim"] === "string" &&
    (record["label_zh"] === null || typeof record["label_zh"] === "string")
  );
}

/** grid_fields 窄化（[{key,dim,label_zh}] 形状非法→空——表挂载仍可无应用列）。 */
export function narrowGridFields(result: unknown): GridField[] {
  const value = resultField(result, "grid_fields");
  return Array.isArray(value) && value.every(isGridField)
    ? (value as GridField[])
    : [];
}
