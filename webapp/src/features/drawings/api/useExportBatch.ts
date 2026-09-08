/**
 * 批量导出任务 hook（SVRB D6②）：单 body 提交→句柄 JSON 解析→GET 兜底
 * →SSE 订阅→终态 outcome（任务态消费面——修复「句柄误当 blob」现状
 * 缺陷，仅本 hook 消费；useExportArtifact 单产物面零触碰）。SVRB2 增
 * 取消面（cancelActive——服务端协作取消触发）+恢复面（挂载重订阅）。
 *
 * 输入:  hook 工厂参 kind（URL 模板 /api/exports/${kind}）+projectId
 *        （SVRB2 D3/R3 终裁 A 案——恢复存储键维度显式入参）+
 *        submitBatch({projectId, units, conditionKey})——body 构造经
 *        lib/batchExport 单源纯函数
 * 输出:  {submitBatch, cancelActive, activeTaskId, cancelError,
 *        cancelPending, restoreNotice, progress, lastOutcome}——终态
 *        files/failures 双清单（乙案计数/首错消费面；列表出新行经终态
 *        invalidate ["/api/exports"] 承载——D5 乙案零下载动作）+
 *        progress {done,total,stageText}（messageApi 最小面消费源）+
 *        取消/恢复面（SVRB2 PD3~PD7）
 *
 * 规格说明（SVRB D6②/D5/D9③ 2026-09-05+SVRB2 PD3~PD7 2026-09-09）：
 *   - POST/GET 经 customInstance（JSON 面——与 useExportArtifact 手写
 *     blob fetch 职责分离；错误归一/Bearer 注入/401 通知复用 http.ts
 *     单源；响应句柄 JSON 的 task_id 是唯一消费字段——path 保留原样
 *     〔P8〕）；
 *   - 竞态缓解双通道兜底（D9③）：提交后先 GET /api/calc/tasks/{id}
 *     一次（终态即直取——极快任务不依赖 SSE 建连），非终态再订阅 SSE
 *     （服务端终态任务连接即发快照 state 事件=订阅侧第二兜底）；零轮询
 *     （全库纯 SSE 先例）；
 *   - SSE 订阅本文件自建 EventSource（useTaskFeed 跨 feature import 被
 *     check_webapp 分层门禁禁——features 互不 import；形态同款复制：
 *     state·progress·stale 命名事件/终态即 close 阻断自动重连循环/
 *     卸载即清理）；B6 D3（2026-09-06）：连接层治理=onerror 连续失败
 *     计数达上限 close+reject+总时长超时拒绝（一次性 awaitTerminal 语义
 *     ——完整退避/慢探测归 useTaskFeed 长订阅面，形态裁量记档）；
 *     B6 D8：URL 构造迁 shared/api/sseUrl 单源（本文件原双实现收敛）；
 *   - 终态 outcome：state/files/failures/error 四面（files=服务端产物
 *     清单——乙案仅计数与终态消息消费；failures 逐项 index/unit_id/
 *     condition_key/error〔截 200 字符服务端已收口〕）；
 *   - 进度面：percent 幂商式 (i+1)/(total+1) 还原 done 序数+stage 文本
 *     化（export:{kind}:{unit}→kind·unit；无-unit 项无 unit 段）；
 *   - 薄壳不测（EventSource 生命周期——useTaskFeed 先例）；可测面=
 *     submitExportBatch+纯函数（useExportBatch.test，node 环境零 DOM）；
 *   - B5 D3/D4（2026-09-06 批量任务体验批）：progress 透传原始 percent
 *     （toast 进度条/状态行双消费）+lastOutcome 最近终态（BatchStatusLine
 *     消费源；新提交清空）+sourceRef 覆盖前 close 旧流（二次提交脏写
 *     防御）+batchStatusText 状态行文案单源纯函数（node 直测）。
 *   - SVRB2（2026-09-09 批量任务面二期·PD3~PD7）：取消面=cancelActive
 *     （activeTaskId 空 no-op+cancelPending 防重；404=终止订阅+清在途+
 *     清存储+行内 cancelError，网络失败=保留在途与订阅可重试；已终态
 *     竞态=服务端 200 {cancelled:false} 无害直达 SSE 终态收束）；恢复面
 *     =sessionStorage {taskId,total}（lib/batchTaskStore）挂载重订阅
 *     （决策纯函数 lib/restoreDecision——四分支 fill/resume/drop/keep；
 *     网络异常保留存储 R1；覆盖核对 R5；恢复等待拒绝以 activeTaskIdRef
 *     取代判定防污染新任务）。
 */
import { useEffect, useRef, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { useCancelTaskApiCalcTasksTaskIdCancelPost } from "../../../shared/api/generated/calc/calc";
import { customInstance, WaterprintApiError } from "../../../shared/api/http";
import { getApiToken } from "../../../shared/api/token";
import { buildTaskStreamUrl } from "../../../shared/api/sseUrl";
import { SSE_FAILURE_LIMIT } from "../../../shared/api/sseConstants";
import { buildBatchExportBody } from "../lib/batchExport";
import {
  deriveBatchProgress,
  type ExportBatchOutcome,
  type ExportBatchProgress,
  isTerminalTaskState,
  makeResumeProgress,
  parseTaskEventData,
  type TaskStatusFace,
  toBatchOutcome,
} from "../lib/batchTaskView";
import {
  clearBatchTask,
  defaultBatchStorage,
  readBatchTask,
  writeBatchTask,
} from "../lib/batchTaskStore";
import {
  isNotFoundApiError,
  resolveRestore,
  stillCurrent,
  type RestoreSnapshot,
} from "../lib/restoreDecision";

/** 批量提交变量（units 序=items 序——Select multiple 选中序）。 */
export type ExportBatchInput = {
  projectId: string;
  units: string[];
  conditionKey: string;
};

// SVRB2 实现期拆件（useExportBatch 507>500 预算红线）：纯投影面（三类型
// +六函数）迁 lib/batchTaskView——本件透传再导出保公开面（executor/
// exports_support 先例同旨；BatchStatusLine/测试件 import 零改动）。
export type {
  ExportBatchFailure,
  ExportBatchOutcome,
  ExportBatchProgress,
  TaskStatusFace,
} from "../lib/batchTaskView";
export {
  batchStatusText,
  deriveBatchProgress,
  isTerminalTaskState,
  makeResumeProgress,
  parseTaskEventData,
  toBatchOutcome,
} from "../lib/batchTaskView";

/** 服务端批量句柄 JSON 松面（ExportHandle asdict——task_id 唯一消费字段）。 */
type ExportHandleFace = { task_id?: unknown };

/** SSE 订阅 URL：shared/api/sseUrl 单源（B6 D8 迁出本文件——useTaskFeed
 * 双实现收敛；taskId 路径段编码+token 非空 ？token= 查询通道）。 */

/** SSE 等待治理（B6 D3 形态裁量）：一次性 awaitTerminal 的悬挂防线——
 * 连续失败上限（shared/api/sseConstants 单源——B7 D5 收敛：useTaskFeed
 * 同源消费，双处同值防线由注释挂账兑付为单源）+总时长上界超时拒绝。 */
const SSE_AWAIT_TIMEOUT_MS = 10 * 60 * 1000; // 10 分钟（批量导出多产物长任务余量）

/** 提交批量任务（单 body POST→句柄 JSON 取 task_id——D6②「句柄误当 blob」修复面）。 */
export async function submitExportBatch(
  kind: string,
  input: ExportBatchInput,
): Promise<string> {
  const handle = await customInstance<ExportHandleFace>({
    url: `/api/exports/${kind}`,
    method: "POST",
    data: buildBatchExportBody(input.projectId, input.units, input.conditionKey),
  });
  if (typeof handle?.task_id !== "string" || !handle.task_id) {
    throw new Error(`批量导出响应缺 task_id（非任务句柄形态——kind=${kind}）`);
  }
  return handle.task_id;
}

/** 批量导出任务 hook（提交→GET 兜底→SSE→终态 outcome+列表失效+取消/恢复面）。 */
export function useExportBatch(
  kind: string,
  projectId: string,
): {
  submitBatch: (input: ExportBatchInput) => Promise<ExportBatchOutcome>;
  cancelActive: () => Promise<void>;
  activeTaskId: string | null;
  cancelError: string | null;
  cancelPending: boolean;
  restoreNotice: string | null;
  progress: ExportBatchProgress | null;
  lastOutcome: ExportBatchOutcome | null;
} {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState<ExportBatchProgress | null>(null);
  // B5 D3：最近终态 outcome（BatchStatusLine 常驻回溯行消费源；新提交清空）
  const [lastOutcome, setLastOutcome] = useState<ExportBatchOutcome | null>(null);
  // SVRB2 D3：在途任务 id（取消动作/恢复重订阅/按钮显隐公共派生面）+
  // ref 镜像（恢复等待的取代判定读 ref——渲染期闭包陈旧态免疫）。
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const activeTaskIdRef = useRef<string | null>(null);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [cancelPending, setCancelPending] = useState(false);
  const [restoreNotice, setRestoreNotice] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);
  const cancelMutation = useCancelTaskApiCalcTasksTaskIdCancelPost<WaterprintApiError>();
  useEffect(() => () => sourceRef.current?.close(), []); // 卸载即清理（无泄漏句柄）

  /** 在途态单一写口（state+ref 镜像同步）。 */
  const setActiveTask = (taskId: string | null) => {
    activeTaskIdRef.current = taskId;
    setActiveTaskId(taskId);
  };

  const fetchStatus = (taskId: string) =>
    customInstance<TaskStatusFace>({
      url: `/api/calc/tasks/${encodeURIComponent(taskId)}`,
      method: "GET",
    });

  /** SSE 订阅至终态（服务端终态任务连接即发快照 state=竞态第二兜底）。
   *
   * B6 D3 形态裁量：awaitTerminal 是一次性等待（promise 形态）非长订阅
   * ——浏览器 EventSource 内建自动重连保留，治理=onerror 连续失败计数
   * （401/429/网络抖动同构——onerror 无 status 面）+达上限 close+reject
   * +总时长超时拒绝（防无限悬挂）；事件到达=计数归零（恢复语义同构
   * useTaskFeed，重连风暴治理彼侧承担完整退避/慢探测——语义不同不
   * 强行同构，简报 D3「同构覆盖」按此解读落地）。 */
  const awaitTerminal = (taskId: string, total: number) =>
    new Promise<ExportBatchOutcome>((resolve, reject) => {
      let failures = 0;
      const guard = setTimeout(() => {
        // 总时长上界（超时拒绝——调用方 catch 面接住转终态消息，不无限悬挂）
        fail(new Error(`批量导出 SSE 等待超时（>${SSE_AWAIT_TIMEOUT_MS / 1000}s）`));
      }, SSE_AWAIT_TIMEOUT_MS);
      const fail = (error: Error) => {
        clearTimeout(guard);
        sourceRef.current?.close(); // 停连收口（失败/超时共用出口）
        sourceRef.current = null;
        reject(error);
      };
      const finish = async () => {
        clearTimeout(guard);
        sourceRef.current?.close(); // 终态即收流：close 阻断自动重连循环
        sourceRef.current = null;
        setActiveTask(null); // SVRB2：终态退出在途面（取消按钮隐去）
        clearBatchTask(defaultBatchStorage(), projectId, kind); // SVRB2 D4 清除点①
        try {
          const outcome = toBatchOutcome(await fetchStatus(taskId));
          setLastOutcome(outcome); // B5 D3：终态回填状态行
          void queryClient.invalidateQueries({ queryKey: ["/api/exports"] }); // D5 乙案
          resolve(outcome);
        } catch (error) {
          // R 轮 R5：终态取档失败必达 reject（Promise 不悬挂——调用方
          // ExportButton 的 catch 面接住转终态 error 消息）。
          reject(error instanceof Error ? error : new Error(String(error)));
        }
      };
      const source = new EventSource(buildTaskStreamUrl(taskId, getApiToken()));
      sourceRef.current?.close(); // B5 D4：覆盖前收旧流（二次提交脏写+悬挂双收口）
      sourceRef.current = source;
      source.onerror = () => {
        // B6 D3：连续失败计数——达上限拒绝（浏览器内建重连期间计数不清零，
        // 事件到达才归零——见 consume）。
        failures += 1;
        if (failures >= SSE_FAILURE_LIMIT) {
          fail(new Error(`批量导出 SSE 连接连续失败 ${failures} 次（已停止等待）`));
        }
      };
      const consume = (event: MessageEvent) => {
        failures = 0; // 事件到达=链路健康（恢复归零）
        const parsed = parseTaskEventData(
          typeof event.data === "string" ? event.data : "",
        );
        if (parsed === null) {
          return; // 畸形 data 静默丢弃（不崩流）
        }
        if (
          parsed.type === "progress" &&
          parsed.percent !== null &&
          parsed.message !== null
        ) {
          setProgress(deriveBatchProgress(parsed.percent, total, parsed.message));
        }
        if (
          parsed.type === "state" &&
          parsed.message !== null &&
          isTerminalTaskState(parsed.message)
        ) {
          void finish();
        }
      };
      source.addEventListener("state", consume as EventListener);
      source.addEventListener("progress", consume as EventListener);
      source.addEventListener("stale", consume as EventListener);
    });

  const submitBatch = async (input: ExportBatchInput): Promise<ExportBatchOutcome> => {
    setProgress(null);
    setLastOutcome(null); // B5 D3：新提交清空终态回溯（状态行回「进行中」面）
    setCancelError(null);
    setRestoreNotice(null);
    try {
      const taskId = await submitExportBatch(kind, input);
      // SVRB2 D4：写入点=POST 成功取得 task_id 后立即（早于 SSE 订阅——
      // 订阅期刷新仍可恢复）；同键覆盖=旧任务恢复通道自然失效（U3 记档）。
      writeBatchTask(defaultBatchStorage(), projectId, kind, {
        taskId,
        total: input.units.length,
      });
      setActiveTask(taskId);
      // 竞态缓解（D9③）：先 GET 一次——终态即直取（零 SSE 依赖）。
      const first = await fetchStatus(taskId);
      if (typeof first.state === "string" && isTerminalTaskState(first.state)) {
        const early = toBatchOutcome(first);
        setLastOutcome(early); // B5 D3：快路径终态同回填状态行
        setActiveTask(null); // SVRB2：快路径同步终态清理面
        clearBatchTask(defaultBatchStorage(), projectId, kind);
        void queryClient.invalidateQueries({ queryKey: ["/api/exports"] }); // D5 乙案
        return early;
      }
      return awaitTerminal(taskId, input.units.length);
    } catch (error) {
      // B5 R4（G1-09）：提交/在途异常回填失败终态——常驻回溯行不因失败路径
      // 退化（错误原文走调用方 toast，本面记「最近一次尝试=失败」）。
      // SVRB2：activeTaskId/存储保留——POST 已成任务在服务端仍活（可取消）。
      setLastOutcome({
        state: "failed",
        files: [],
        failures: [],
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  };

  /** SVRB2 D7：取消当前在途批量任务（协作取消——SSE state=cancelled 事件
   * 既有收束闭环零改；activeTaskId 空=非在途 no-op；cancelPending 防重）。 */
  const cancelActive = async (): Promise<void> => {
    const taskId = activeTaskIdRef.current;
    if (taskId === null || cancelPending) {
      return;
    }
    setCancelPending(true);
    setCancelError(null);
    try {
      await cancelMutation.mutateAsync({ taskId });
      // 200+cancelled:false（已终态竞态）无害——SSE 终态事件随即到达收束
      //（manager.cancel 已终态返回 False，calc.py CancelResponse 实态）。
    } catch (error) {
      if (isNotFoundApiError(error)) {
        // PD7：任务不可达——终止订阅+清在途+清存储（订阅必死不留双错误面）。
        sourceRef.current?.close();
        sourceRef.current = null;
        setActiveTask(null);
        clearBatchTask(defaultBatchStorage(), projectId, kind);
      }
      // 网络失败：保留在途与订阅（任务仍在跑——可重试取消或等终态收束）。
      setCancelError(error instanceof Error ? error.message : String(error));
    } finally {
      setCancelPending(false);
    }
  };

  // SVRB2 D5：挂载恢复——读存储→GET 快照→四分支（同挂载一次不自动重试；
  // 决策纯函数 lib/restoreDecision node 直测）。恢复 resume 的等待拒绝以
  // activeTaskIdRef 取代判定兜底（R5 覆盖防护延伸到等待面：新提交
  // sourceRef 覆盖后旧流超时拒绝不污染新任务状态行）。
  useEffect(() => {
    let disposed = false;
    const stored = readBatchTask(defaultBatchStorage(), projectId, kind);
    if (stored === null) {
      return;
    }
    const restore = async () => {
      let snapshot: RestoreSnapshot;
      try {
        const status = await fetchStatus(stored.taskId);
        snapshot = {
          kind: "status",
          terminal: typeof status.state === "string" && isTerminalTaskState(status.state),
          status,
        };
      } catch (error) {
        snapshot = isNotFoundApiError(error)
          ? { kind: "notFound" }
          : { kind: "unreachable" };
      }
      if (disposed) {
        return;
      }
      const plan = resolveRestore(stored, snapshot);
      if (plan.plan === "fill" && snapshot.kind === "status") {
        setLastOutcome(toBatchOutcome(snapshot.status as TaskStatusFace));
        setActiveTask(null);
        clearBatchTask(defaultBatchStorage(), projectId, kind);
        void queryClient.invalidateQueries({ queryKey: ["/api/exports"] });
        return;
      }
      if (plan.plan === "drop") {
        clearBatchTask(defaultBatchStorage(), projectId, kind);
        setRestoreNotice("批量任务记录已失效（服务端无此任务——已清除本地记录）");
        return;
      }
      if (plan.plan === "keep") {
        setRestoreNotice("批量任务自动恢复未成功（网络异常）——刷新页面可重试");
        return;
      }
      if (!stillCurrent(readBatchTask(defaultBatchStorage(), projectId, kind), stored.taskId)) {
        return; // R5：异步窗口内已被新提交覆盖/清除——静默放弃本次恢复
      }
      setActiveTask(stored.taskId);
      setProgress(makeResumeProgress(stored.total)); // D6 合成首帧
      void awaitTerminal(stored.taskId, stored.total).catch((error) => {
        if (activeTaskIdRef.current !== stored.taskId) {
          return; // 已被新提交取代（sourceRef 覆盖致本流悬挂）——状态归新任务
        }
        setLastOutcome({
          state: "failed",
          files: [],
          failures: [],
          error: error instanceof Error ? error.message : String(error),
        });
      });
    };
    void restore();
    return () => {
      disposed = true;
    };
    // 挂载恢复恰一次（fetchStatus/awaitTerminal 为渲染期闭包——稳定依赖
    // 面仅 projectId/kind 两键；hook 消费方 ExportButton 两参恒定）。
  }, [projectId, kind]);

  return {
    submitBatch,
    cancelActive,
    activeTaskId,
    cancelError,
    cancelPending,
    restoreNotice,
    progress,
    lastOutcome,
  };
}
