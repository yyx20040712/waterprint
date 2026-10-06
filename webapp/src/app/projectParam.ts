/**
 * URL project/task/tab 参数解析/合成纯函数（D5 单一真相+deep-link+路由态面）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标 project/task 值
 *        或 null+目标 tab（AppRoute 冻结面成员）
 * 输出:  parseProjectParam → 项目 id 或 null；withProjectParam → 新查询串；
 *        normalizeProjectId → 剥 ".wp" 尾缀的归一 id；parseTaskParam →
 *        任务 id 或 null；withTaskParam → 新查询串；clearTaskParam →
 *        移除 task 键的新查询串；parseTabParam → TabTarget（两级值域+
 *        兼容归一）或 null；withTabParam → 写入 tab 键的新查询串；
 *        parseTokenParam → 令牌串或 null；clearTokenParam → 移除 token
 *        键的新查询串
 *
 * 规格说明（FE3 批 6b 段一，D5；R2 补 2026-08-29；FE6 批 6b 段四 D3 补
 *   taskParam 三函数；UX1 批 D2 补 tabParam 两函数）：
 *   - projectId 唯一真相=URL ?project= 参数：初值经 parseProjectParam 直读
 *     location.search；用户经空态下拉选择后 history.replaceState 同步回
 *     URL（withProjectParam 动 project 键+HC25-F4 剔除 enum/task 两键——
 *     任务 id 无项目分区；tab/token 等他键原序保留）；
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
 *     持久化）；M1 批（2026-10-06 mapping-2b4 §B 终核）升两级值域：语法=
 *     ?tab=<槽> 或 ?tab=studio.<子面>（点分复合——R-D2 命名空间原则）；
 *     parseTabParam 两级解析（split(".")+两级成员校验：单段→SLOTS 成员
 *     〔studio 单值归一 {slot:"studio",subface:"study"}——边缘语义 b〕；
 *     双段→首段须 studio+次段 STUDIO_SUBFACES 成员；三段以上/任一不合法
 *     →null）；兼容归一=解析期单点收口（旧十值：solutions→studio.study、
 *     drawings/cost/compare/trust→studio.同名、opsdebug→canvas——
 *     新值域优先于兼容表，防未来扩值歧义）；withTabParam 只动 tab 键
 *     （project/task 等他键原序保留——tab 键透传语义既有测试自 FE3 起
 *     已锁；target 带 subface→studio.<子面>，否则裸槽值）；
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
import { SLOTS, STUDIO_SUBFACES, type SlotId, type StudioSubface, type TabTarget } from "./router";

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

/** 兼容归一表（M1 单点收口——旧十值中非直通六值；直通四值经 SLOTS
 *  同名命中，不入表）。新值域优先：parse 先查两级值域再查本表。 */
const LEGACY_TAB_COMPAT: Readonly<Record<string, TabTarget>> = {
  solutions: { slot: "studio", subface: "study" },
  drawings: { slot: "studio", subface: "drawings" },
  cost: { slot: "studio", subface: "cost" },
  compare: { slot: "studio", subface: "compare" },
  trust: { slot: "studio", subface: "trust" },
  opsdebug: { slot: "canvas" },
};

/** M1 两级解析（UX1 D2 承袭+mapping-2b4 §B 终核）：?tab=<槽> 或
 *  studio.<子面>——单段：SLOTS 成员（studio 归一 study——边缘语义 b；
 *  其余四槽裸槽值）；双段：首段须 studio+次段子面成员；任一不合法/
 *  三段以上 → null。兼容归一在新值域之后（新值优先）。 */
export function parseTabParam(search: string): TabTarget | null {
  const value = new URLSearchParams(search).get("tab");
  if (value === null || value === "") {
    return null;
  }
  const parts = value.split(".");
  if (parts.length === 1) {
    if (value === "studio") {
      return { slot: "studio", subface: "study" };
    }
    if ((SLOTS as readonly string[]).includes(value)) {
      return { slot: value as SlotId };
    }
    return LEGACY_TAB_COMPAT[value] ?? null;
  }
  if (
    parts.length === 2 &&
    parts[0] === "studio" &&
    (STUDIO_SUBFACES as readonly string[]).includes(parts[1] ?? "")
  ) {
    return { slot: "studio", subface: parts[1] as StudioSubface };
  }
  return null;
}

/** UX1 D2（S4）承袭：回写 tab 键（只动 tab——project/task 等他键原序
 *  保留；target 带 subface → studio.<子面>，否则裸槽值）。 */
export function withTabParam(search: string, target: TabTarget): string {
  const params = new URLSearchParams(search);
  params.set(
    "tab",
    target.subface === undefined ? target.slot : `studio.${target.subface}`,
  );
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
