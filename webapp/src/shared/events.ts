/**
 * 跨面板事件名常量（AUDIT2 FIX2 S12——原四处内联收敛）。
 *
 * 输入:  无（纯常量——零依赖零运行期逻辑）
 * 输出:  TASK_EVENT = "wp:task"（apply 重算后 ?task= 回写通知已挂载 pane
 *        的 CustomEvent 事件名——Tabs 保活不卸载，监听方靠本事件失效
 *        各自查询键）
 *
 * 规格：事件名原在 ParamForm（派发）与 solutionsPane/elevationPane/
 *   costPane（监听）各处字面量内联——一字漂移即静默断链（AUDIT2
 *   R-5/C-2：方案应用路径漏派发即高程/概算停更的根因族）。常量收口
 *   shared（分层禁令不受扰——纯常量无依赖方向问题）。
 */
export const TASK_EVENT = "wp:task";
