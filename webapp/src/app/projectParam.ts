/**
 * URL project/task/tab 参数解析/合成纯函数（D5 单一真相+deep-link+路由态面）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标 project/task 值
 *        或 null+目标 tab（AppRoute 冻结面成员）
 * 输出:  parseProjectParam → 项目 id 或 null；withProjectParam → 新查询串；
 *        normalizeProjectId → 剥 ".wp" 尾缀的归一 id；parseTaskParam →
 *        任务 id 或 null；withTaskParam → 新查询串；clearTaskParam →
 *        移除 task 键的新查询串；parseTabParam → 合法路由值或 null；
 *        withTabParam → 写入 tab 键的新查询串；parseTokenParam → 令牌
 *        串或 null；clearTokenParam → 移除 token 键的新查询串
 *
 * 规格说明（FE3 批 6b 段一，D5；R2 补 2026-08-29；FE6 批 6b 段四 D3 补
 *   taskParam 三函数；UX1 批 D2 补 tabParam 两函数）：
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
 *     （服务端生成 id 不带 .wp）；既有 project 三函数签名零改动；
 *   - ENG5 D6 enum 通道（裁决③——I-4 收口）：?enum= 枚举任务轨独立参数
 *     （与 ?task= 计算轨双参并存互不覆盖——枚举提交写 enum 键、方案应用/
 *     ParamForm apply 写 task 键，apply 后深链不再丢方案表）；表源轨
 *     （enumerateTaskId）读 enum 键；面板轨初值 task 优先（apply 流
 *     后写时间序）；三函数与 taskParam 同构（FE6 D3 模式复用）；
 *   - UX1 D2 tab 通道：?tab= 路由态进 URL（S4——Tabs activeKey 初值与
 *     持久化）；parseTabParam=ROUTES 成员校验（非法值 null——冻结面外
 *     不造路由，App 缺省 canvas 兜底）；withTabParam 只动 tab 键（project/
 *     task 等他键原序保留——tab 键透传语义既有测试自 FE3 起已锁）；
 *   - R2-A 批2 D2 token 通道：?token= 首参引导（deep-link 令牌注入——
 *     分享链带凭证形态）；parseTokenParam 与 project/task/enum 同构
 *     （D5 单一真相族；空串视同 null）；clearTokenParam 只动 token 键
 *     （project/task 等他键原序保留——与 clearTaskParam 同构语义）；
 *     消费编排=App.tsx 模块顶层（读→非 null 写 localStorage+
 *     replaceState 剥离——分层禁令：shared/api 的 token.ts 不得 import
 *     本文件）；token 不设 with 函数（写入面唯一=首参引导，无用户回写
 *     路由面——设置页写 localStorage 非 URL）；
 *     本文件 app 层 import router.tsx 同层合法（AppRoute 冻结面消费）。
 */
import { ROUTES, type AppRoute } from "./router";

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

/** UX1 D2（S4）：?tab= 直读（ROUTES 成员校验——非法值 null，缺省 canvas 兜底）。 */
export function parseTabParam(search: string): AppRoute | null {
  const value = new URLSearchParams(search).get("tab");
  if (value === null || value === "") {
    return null;
  }
  return (ROUTES as readonly string[]).includes(value)
    ? (value as AppRoute)
    : null;
}

/** UX1 D2（S4）：回写 tab 键（只动 tab——project/task 等他键原序保留）。 */
export function withTabParam(search: string, tab: AppRoute): string {
  const params = new URLSearchParams(search);
  params.set("tab", tab);
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
