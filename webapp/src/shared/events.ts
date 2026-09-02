/**
 * 跨面板事件名常量（AUDIT2 FIX2 S12——原多处内联收敛；UX1 S3 增 project 面；
 * R2-A 批2 增 auth 面）。
 *
 * 输入:  无（纯常量——零依赖零运行期逻辑）
 * 输出:  TASK_EVENT = "wp:task"（apply 重算后 ?task= 回写通知已挂载 pane
 *        的 CustomEvent 事件名——Tabs 保活不卸载，监听方靠本事件失效
 *        各自查询键）；PROJECT_EVENT = "wp:project"（?project= 回写后
 *        通知已挂载 pane 重读 URL——useProjectId setter 写后派发）；
 *        AUTH_EVENT = "wp:auth"（customInstance 收 401 后派发——App.tsx
 *        监听自动开连接设置 Modal=自愈回路）
 *
 * 规格：事件名原在 ParamForm（派发）与 solutionsPane/elevationPane/
 *   costPane（监听）各处字面量内联——一字漂移即静默断链（AUDIT2
 *   R-5/C-2：方案应用路径漏派发即高程/概算停更的根因族）。常量收口
 *   shared（分层禁令不受扰——纯常量无依赖方向问题）。UX1 S3：project
 *   面同机制（PROJECT_EVENT——写方 canvas/viewer3d 经 useProjectId
 *   setter 派发，六 pane 经 hook 监听重读 location.search）。R2-A 批2：
 *   auth 面第三常量（AUTH_EVENT——派发方 shared/api/http.ts 401 面，
 *   监听方 app/App.tsx；错误归一化 throw 语义不变，仅加通知面）。
 */
export const TASK_EVENT = "wp:task";

export const PROJECT_EVENT = "wp:project";

export const AUTH_EVENT = "wp:auth";
