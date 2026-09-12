/**
 * 职责：枚举结果字段窄化+单元下拉中文化 label 纯函数（B7 R+ 自
 * solutionsPane 提取——行数预算 516>500 越界修前进；零行为变更纯搬迁；
 * B15 409 锁冲突判定面上移 shared/api/http.ts 单源——本件不再承载；
 * B2 扩面 R-1 增 unitOptionLabel——下拉 label 形态收口本件单源；
 * C2-visual F6 增 isUnitEnumerable/enumerateOptions——枚举下拉过滤
 * 判据与选项构建本件单源）。
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

/** V2 GOV5 批尾（视觉验收批注②）：dim_fields 窄化（计算派生输出量
 * 列族——与 grid_fields 同形状 [{key,dim,label_zh}]；manifest.out_dims
 * 声明面真源，未声明键 label_zh=null 直传，显示层 key 兜底）。 */
export function narrowDimFields(result: unknown): GridField[] {
  const value = resultField(result, "dim_fields");
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

/** 目录单元参数条目（F6 结构最小面——仅枚举判据所需 grid 键）。 */
export type CatalogParamEntry = {
  grid?: number[] | null;
};

/** 目录单元条目（F6 结构最小面：unit_id+params——真源形状=shared/api
 * generated model UnitMetaEntry，此处按判据所需收窄引用零整型拷贝）。 */
export type CatalogEntryLike = {
  unit_id: string;
  params?: readonly CatalogParamEntry[];
};

/** 枚举下拉选项（F6——value=node id 零漂移+disabled=不可枚举+label 附
 * 述因后缀）。 */
export type EnumerateOption = {
  value: string;
  label: string;
  disabled: boolean;
};

/** 单元可枚举判据（F6）：目录 params 任一 grid 档位数组非空（manifest
 * 网格声明——开工实核 /api/units 暴露 grid[16/36 单元可枚举]）。
 * 目录未就绪（entries=null）=fail-open 全可（与中文名回退同口径——
 * 目录数据面故障不阻断枚举提交）。 */
export function isUnitEnumerable(
  unit: UnitOptionRef,
  entries: readonly CatalogEntryLike[] | null,
): boolean {
  if (entries === null) {
    return true;
  }
  const key = unit.kind ?? unit.unitId;
  const entry = entries.find((item) => item.unit_id === key);
  const params = entry?.params;
  if (params === undefined) {
    return false; // 目录在场而该键缺席=无网格声明（诚实拒）
  }
  return params.some(
    (param) => Array.isArray(param.grid) && param.grid.length > 0,
  );
}

/** 枚举下拉选项构建（F6——全列保留+不可枚举 disabled 附提示后缀；
 * 可枚举项零后缀零行为变化）。 */
export function enumerateOptions(
  units: readonly UnitOptionRef[],
  entries: readonly CatalogEntryLike[] | null,
  nameById: Map<string, string>,
): EnumerateOption[] {
  return units.map((unit) => {
    const enumerable = isUnitEnumerable(unit, entries);
    return {
      value: unit.unitId,
      label: enumerable
        ? unitOptionLabel(unit, nameById)
        : `${unitOptionLabel(unit, nameById)}（无档位参数）`,
      disabled: !enumerable,
    };
  });
}
