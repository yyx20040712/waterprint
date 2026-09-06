/**
 * SSE 重连治理共享常量单源（B7 D5：useTaskFeed/useExportBatch 双处同值
 * 收敛——B6「双处注释防线」挂账兑付）。
 *
 * 输入:  无（常量单源——两 hook 同源消费防漂移）
 * 输出:  SSE_FAILURE_LIMIT=5（连续失败上限：useTaskFeed 达限切 60s 慢探测
 *        〔planRecovery〕/useExportBatch 达限拒绝等待〔awaitTerminal〕——
 *        同值同构两消费面，features 互不 import 门禁下经 shared 单源对齐）
 */
/** 连续失败上限：达限置错误态停连（激进重连终止——B6 D3；B7 D5 双 hook 单源）。 */
export const SSE_FAILURE_LIMIT = 5;
