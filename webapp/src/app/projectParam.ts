/**
 * URL project/task 参数解析/合成纯函数（D5 单一真相+deep-link 面）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标 project/task 值
 *        或 null
 * 输出:  parseProjectParam → 项目 id 或 null；withProjectParam → 新查询串；
 *        normalizeProjectId → 剥 ".wp" 尾缀的归一 id；parseTaskParam →
 *        任务 id 或 null；withTaskParam → 新查询串；clearTaskParam →
 *        移除 task 键的新查询串
 *
 * 规格说明（FE3 批 6b 段一，D5；R2 补 2026-08-29；FE6 批 6b 段四 D3 补
 *   taskParam 三函数）：
 *   - projectId 唯一真相=URL ?project= 参数：初值经 parseProjectParam 直读
 *     location.search；用户经空态下拉选择后 history.replaceState 同步回
 *     URL（不清其余参数——withProjectParam 只动 project 键，他键原序保留）；
 *   - normalizeProjectId（R2/一审 M-2）：列表 id 带 ".wp" 尾缀（服务端
 *     path.stem 现状）而场景/读取端点按裸 id 解析——deep-link 初值与
 *     Select 选项共用本函数归一（对称面；服务端根治挂账 C1，根治后
 *     本函数删除动作配套记档）；null 透传（未选不造第二空态）；
 *   - null 语义统一=未选与移除（空串视同 null，不引入第二空态）；
 *   - URLSearchParams 忽略首 "?"（location.search 原样可直读）；产出无 "?"
 *     前缀查询串——pathname 拼接在消费面（viewer3dPane 的 replaceState）；
 *   - FE6 D3 task 通道：?task= 与 ?project= 双参共存（withTaskParam 只动
 *     task 键——project 等他键原序保留）；写入点三处（枚举提交/方案应用/
 *     ParamForm apply）全走 window.history.replaceState；消费面=
 *     solutionsPane（任务态面板+方案表挂载依据）；taskId 无归一尾缀面
 *     （服务端生成 id 不带 .wp）；既有 project 三函数签名零改动。
 */
export function parseProjectParam(search: string): string | null {
  const value = new URLSearchParams(search).get("project");
  return value === null || value === "" ? null : value;
}

/** ".wp" 尾缀归一（R2）：列表 id → 裸 id；null 透传；裸 id 幂等不动。 */
export function normalizeProjectId(projectId: string | null): string | null {
  return projectId === null ? null : projectId.replace(/\.wp$/, "");
}

export function withProjectParam(
  search: string,
  projectId: string | null,
): string {
  const params = new URLSearchParams(search);
  if (projectId === null || projectId === "") {
    params.delete("project");
  } else {
    params.set("project", projectId);
  }
  return params.toString();
}

/** FE6 D3：?task= 直读（任务 id 单一真相——与 ?project= 双参共存）。 */
export function parseTaskParam(search: string): string | null {
  const value = new URLSearchParams(search).get("task");
  return value === null || value === "" ? null : value;
}

/** FE6 D3：回写/移除 task 键（只动 task——project 等他键原序保留）。 */
export function withTaskParam(search: string, taskId: string | null): string {
  const params = new URLSearchParams(search);
  if (taskId === null || taskId === "") {
    params.delete("task");
  } else {
    params.set("task", taskId);
  }
  return params.toString();
}

/** FE6 D3：显式移除 task 键（语义收口——无任务态的面用）。 */
export function clearTaskParam(search: string): string {
  const params = new URLSearchParams(search);
  params.delete("task");
  return params.toString();
}
