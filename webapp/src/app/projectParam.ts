/**
 * URL project 参数解析/合成纯函数（D5 单一真相+deep-link 面）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标 project 值/null
 * 输出:  parseProjectParam → 项目 id 或 null；withProjectParam → 新查询串
 *
 * 规格说明（FE3 批 6b 段一，D5）：
 *   - projectId 唯一真相=URL ?project= 参数：初值经 parseProjectParam 直读
 *     location.search；用户经空态下拉选择后 history.replaceState 同步回
 *     URL（不清其余参数——withProjectParam 只动 project 键，他键原序保留）；
 *   - null 语义统一=未选与移除（空串视同 null，不引入第二空态）；
 *   - URLSearchParams 忽略首 "?"（location.search 原样可直读）；产出无 "?"
 *     前缀查询串——pathname 拼接在消费面（viewer3dPane 的 replaceState）。
 */
export function parseProjectParam(search: string): string | null {
  const value = new URLSearchParams(search).get("project");
  return value === null || value === "" ? null : value;
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
