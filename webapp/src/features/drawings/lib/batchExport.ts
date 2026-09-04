/**
 * 批量出图纯函数层：逐单元单产物请求构造（M5 D3 客户端编排形态——
 * 顺序循环 N 个单产物请求，零任务队列依赖）。
 *
 * 输入:  units（单元 id 序列——antd Select multiple 选中序）+conditionKey
 *        （工况键——空串=服务端缺省工况合同）
 * 输出:  buildBatchExportRequests→ExportRequestBody[]（每单元恰一项：
 *        condition_key 透传+options.unit_id 单发面）
 *
 * 规格说明（M5 D4；D3 总裁定稿 2026-09-04；R2 G1-01 删 BATCH_EXPORT_URL
 *   死代码常量 2026-09-04——零消费者，URL 面归 useExportArtifact
 *   /api/exports/${kind} 单一住所）：
 *   - 纯数据构造（零 antd/零运行期库 import——node 环境可测，drawingsView
 *     同族约束）；project_id 由调用方追加（组件持有 projectId 态——
 *     签名保持两参纯度）；
 *   - 工况空串归一：conditionKey 空串原样透传（服务端 condition_key=""
 *     =缺省工况——useExportArtifact 工况面同源合同，永不 undefined 形态）；
 *   - dedupe 责任归调用方（antd Select multiple 选中值已去重——本层
 *     不静默去重：重复入=重复出，双发如实呈现归执行态错误面）；
 *   - 顺序保持：units 序=请求序（客户端顺序循环消费面——「批量导出中
 *     i/N」逐次更新的依据；任一失败即停由执行层承载，非本层语义）；
 *   - 服务端批量对偶拒绝（无-unit dxf items×2→422）不触发：每请求
 *     单项带 options.unit_id 走即时 blob 面（零任务队列依赖——SSE/
 *     句柄消费零新增，服务端批量任务面沿册挂账二期）。
 */

/** 批量单产物请求体（POST body 面——project_id 由调用方追加）。 */
export type ExportRequestBody = {
  condition_key: string;
  options: { unit_id: string };
};

/** 每单元恰一项（纯数据构造：units.map 序保持——零排序零去重零过滤）。 */
export function buildBatchExportRequests(
  units: string[],
  conditionKey: string,
): ExportRequestBody[] {
  return units.map((unitId) => ({
    condition_key: conditionKey,
    options: { unit_id: unitId },
  }));
}
