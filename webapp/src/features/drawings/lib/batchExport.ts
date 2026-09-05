/**
 * 批量出图纯函数层：服务端批量任务请求体构造（SVRB 单 body 形态——
 * 替换 M5 D3 客户端顺序循环 N 请求编排，批量消费转任务态 hook 面）。
 *
 * 输入:  projectId+units（单元 id 序列——antd Select multiple 选中序）
 *        +conditionKey（工况键——空串=服务端缺省工况合同）
 * 输出:  buildBatchExportBody→BatchExportBody（单 body：options.items
 *        每单元恰一项 {unit_id, condition_key}——items>1 即服务端
 *        export_batch 批量转任务面）
 *
 * 规格说明（M5 D4→SVRB D6① 改写 2026-09-05）：
 *   - 纯数据构造（零 antd/零运行期库 import——node 环境可测，drawingsView
 *     同族约束）；单 body 形态（M5 的 N 请求数组已废——多单元经服务端
 *     items 面承载，逐项 unit_id「item 覆盖批级」语义）；
 *   - 工况空串归一：conditionKey 空串原样透传（服务端 condition_key=""
 *     =缺省工况——永不 undefined 形态）；
 *   - 批级 unit_id 不落键：items 逐项自带（混合单元/同单元多工况均
 *     逐项自表——零批级兜底面）；
 *   - dedupe 责任归调用方（antd Select multiple 选中值已去重——本层
 *     不静默去重：重复入=重复出，双发如实呈现归执行态错误面）；
 *   - 顺序保持：units 序=items 序（服务端 items 序=进度 stage 段/落盘
 *     序——「导出中 i/N·kind·unit」逐次更新的依据）。
 */

/** 批量任务请求体（POST body 面——服务端 ExportRequest 合同单 body）。 */
export type BatchExportBody = {
  project_id: string;
  condition_key: string;
  options: { items: Array<{ unit_id: string; condition_key: string }> };
};

/** 每单元恰一项（纯数据构造：units.map 序保持——零排序零去重零过滤）。 */
export function buildBatchExportBody(
  projectId: string,
  units: string[],
  conditionKey: string,
): BatchExportBody {
  return {
    project_id: projectId,
    condition_key: conditionKey,
    options: {
      items: units.map((unitId) => ({
        unit_id: unitId,
        condition_key: conditionKey,
      })),
    },
  };
}
