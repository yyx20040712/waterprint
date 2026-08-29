/**
 * URL project 参数解析/合成纯函数（D5 单一真相+deep-link 面）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标 project 值/null
 * 输出:  parseProjectParam → 项目 id 或 null；withProjectParam → 新查询串；
 *        normalizeProjectId → 剥 ".wp" 尾缀的归一 id
 *
 * 规格说明（FE3 批 6b 段一，D5；R2 补 2026-08-29）：
 *   - projectId 唯一真相=URL ?project= 参数：初值经 parseProjectParam 直读
 *     location.search；用户经空态下拉选择后 history.replaceState 同步回
 *     URL（不清其余参数——withProjectParam 只动 project 键，他键原序保留）；
 *   - normalizeProjectId（R2/一审 M-2）：列表 id 带 ".wp" 尾缀（服务端
 *     path.stem 现状）而场景/读取端点按裸 id 解析——deep-link 初值与
 *     Select 选项共用本函数归一（对称面；服务端根治挂账 C1，根治后
 *     本函数删除动作配套记档）；null 透传（未选不造第二空态）；
 *   - null 语义统一=未选与移除（空串视同 null，不引入第二空态）；
 *   - URLSearchParams 忽略首 "?"（location.search 原样可直读）；产出无 "?"
 *     前缀查询串——pathname 拼接在消费面（viewer3dPane 的 replaceState）。
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
