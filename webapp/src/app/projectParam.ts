/**
 * URL project/task/enum/token 参数解析/合成纯函数（D5 单一真相+deep-link
 * 态面。v1-20261015 转正批：parseTabParam/withTabParam/LEGACY_TAB_COMPAT
 * 随 legacy 槽路由退役删除——tab 键现归 zoneParam（V4ZoneTarget 两级值域
 * +LEGACY_ZONE_COMPAT 旧链归一）单源；project/task/enum/token 四通道
 * v4 全消费语义零变）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标 project/task/
 *        enum 值或 null
 * 输出:  parseProjectParam → 项目 id 或 null；withProjectParam → 新查询串；
 *        normalizeProjectId → 剥 ".wp" 尾缀的归一 id；parseTaskParam →
 *        任务 id 或 null；withTaskParam → 新查询串；clearTaskParam →
 *        移除 task 键的新查询串；parseEnumParam/withEnumParam/
 *        clearEnumParam → enum 轨同构三函数；parseTokenParam → 令牌串
 *        或 null；clearTokenParam → 移除 token 键的新查询串
 *
 * 规格说明（FE3 批 6b 段一，D5；R2 补 2026-08-29；FE6 批 6b 段四 D3 补
 *   taskParam 三函数；ENG5 D6 enum 三函数；R2-A 批2 D2 token 两函数）：
 *   - projectId 唯一真相=URL ?project= 参数：初值经 parseProjectParam 直读
 *     location.search；用户经空态下拉选择后 history.replaceState 同步回
 *     URL（withProjectParam 动 project 键+HC25-F4 剔除 enum/task 两键——
 *     任务 id 无项目分区；他键原序保留）；
 *   - normalizeProjectId（R2/一审 M-2）：列表 id 带 ".wp" 尾缀（服务端
 *     path.stem 现状）而场景/读取端点按裸 id 解析——deep-link 初值与
 *     Select 选项共用本函数归一（对称面；服务端根治挂账 C1，根治后
 *     本函数删除动作配套记档）；null 透传（未选不造第二空态）；
 *   - null 语义统一=未选与移除（空串视同 null，不引入第二空态）；
 *   - URLSearchParams 忽略首 "?"（location.search 原样可直读）；产出无 "?"
 *     前缀查询串——pathname 拼接在消费面（viewer3dPane 的 replaceState）；
 *   - FE6 D3 task 通道：?task= 与 ?project= 双参共存（withTaskParam 只动
 *     task 键——project 等他键原序保留）；taskId 无归一尾缀面（服务端
 *     生成 id 不带 .wp）；
 *   - ENG5 D6 enum 通道（裁决③——I-4 收口）：?enum= 枚举任务轨独立参数
 *     （与 ?task= 计算轨双参并存互不覆盖）；三函数与 taskParam 同构；
 *   - R2-A 批2 D2 token 通道：?token= 首参引导（deep-link 令牌注入）；
 *     clearTokenParam 只动 token 键（他键原序保留——与 clearTaskParam
 *     同构语义）；消费编排=App.tsx 模块顶层（读→非 null 写 localStorage+
 *     replaceState 剥离——分层禁令：shared/api 的 token.ts 不得 import
 *     本文件）；token 不设 with 函数（写入面唯一=首参引导，无用户回写
 *     路由面——设置页写 localStorage 非 URL）。
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
  // HC25-F4（P2-A）：项目切换同步剔除 enum/task 两键——其值（任务 id）
  // 无项目分区，旧项目任务深链对新项目无意义且可诱发跨项目残留面；
  // 其余键（tab/token 等）语义不动（写方=useProjectId setter，恒切换面）。
  params.delete("enum");
  params.delete("task");
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

/** ENG5 D6（裁决③/I-4 收口）：?enum= 直读（枚举任务轨单一真相）。 */
export function parseEnumParam(search: string): string | null {
  const value = new URLSearchParams(search).get("enum");
  return value === null || value === "" ? null : value;
}

/** ENG5 D6：回写/移除 enum 键（只动 enum——task/project 等他键原序保留）。 */
export function withEnumParam(search: string, enumId: string | null): string {
  const params = new URLSearchParams(search);
  if (enumId === null || enumId === "") {
    params.delete("enum");
  } else {
    params.set("enum", enumId);
  }
  return params.toString();
}

/** ENG5 D6：显式移除 enum 键（taskParam 同构语义收口）。 */
export function clearEnumParam(search: string): string {
  const params = new URLSearchParams(search);
  params.delete("enum");
  return params.toString();
}

/** R2-A 批2 D2：?token= 直读（首参引导——App.tsx 模块顶层消费）。 */
export function parseTokenParam(search: string): string | null {
  const value = new URLSearchParams(search).get("token");
  return value === null || value === "" ? null : value;
}

/** R2-A 批2 D2：显式移除 token 键（引导剥离——他键原序保留，taskParam 同构）。 */
export function clearTokenParam(search: string): string {
  const params = new URLSearchParams(search);
  params.delete("token");
  return params.toString();
}
