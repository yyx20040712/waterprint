/**
 * 职责：枚举结果字段窄化+单元下拉中文化 label 纯函数（B7 R+ 自
 * solutionsPane 提取——行数预算 516>500 越界修前进；零行为变更纯搬迁；
 * B15 409 锁冲突判定面上移 shared/api/http.ts 单源——本件不再承载；
 * B2 扩面 R-1 增 unitOptionLabel——下拉 label 形态收口本件单源）。
 *
 * 输入:  TaskStatus.result 弱类型载荷（unknown）+单元引用与目录中文名映射
 * 输出:  窄化字段值/grid_fields {key,dim,label_zh}[]（B2②对象载荷窄化；
 *        下拉选项 label（B2 扩面）；消费方=app/solutionsPane——app 层
 *        薄壳不测面沿先例（本件函数 node 直测）
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

/** 单元下拉选项引用（useProjectUnits 投影形态——node 键+内置 kind 键）。 */
export type UnitOptionRef = {
  unitId: string;
  kind: string | null;
};

/** 单元下拉选项 label（B2 扩面）：manifest 单元=目录中文名纯中文（如
 * 「AAO 生物池」）；builtin 节点=kind 中文名+（node_id）后缀辨异（如
 * 「市政输入（inlet）」）；目录未就绪/键缺席=英文 id 诚实回退——builtin
 * 回退旧形态 unitId（kind）防「inlet（inlet）」自重复（R 轮 G1-01）。 */
export function unitOptionLabel(
  unit: UnitOptionRef,
  nameById: Map<string, string>,
): string {
  if (unit.kind === null) {
    return nameById.get(unit.unitId) ?? unit.unitId;
  }
  const nameZh = nameById.get(unit.kind);
  return nameZh !== undefined
    ? `${nameZh}（${unit.unitId}）`
    : `${unit.unitId}（${unit.kind}）`;
}
