/**
 * 批量导出任务 hook（SVRB D6②）：单 body 提交→句柄 JSON 解析→GET 兜底
 * →SSE 订阅→终态 outcome（任务态消费面——修复「句柄误当 blob」现状
 * 缺陷，仅本 hook 消费；useExportArtifact 单产物面零触碰）。
 *
 * 输入:  hook 工厂参 kind（URL 模板 /api/exports/${kind}）+submitBatch(
 *        {projectId, units, conditionKey})——body 构造经 lib/batchExport
 *        单源纯函数
 * 输出:  {submitBatch: Promise<ExportBatchOutcome>, progress}——终态
 *        files/failures 双清单（乙案计数/首错消费面；列表出新行经终态
 *        invalidate ["/api/exports"] 承载——D5 乙案零下载动作）+
 *        progress {done,total,stageText}（messageApi 最小面消费源）
 *
 * 规格说明（SVRB D6②/D5/D9③ 2026-09-05）：
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
 *     ?token= 查询通道/state·progress·stale 命名事件/终态即 close 阻断
 *     自动重连循环/卸载即清理；连接层错误交浏览器自动重连不壳内重试）；
 *   - 终态 outcome：state/files/failures/error 四面（files=服务端产物
 *     清单——乙案仅计数与终态消息消费；failures 逐项 index/unit_id/
 *     condition_key/error〔截 200 字符服务端已收口〕）；
 *   - 进度面：percent 幂商式 (i+1)/(total+1) 还原 done 序数+stage 文本
 *     化（export:{kind}:{unit}→kind·unit；无-unit 项无 unit 段）；
 *   - 薄壳不测（EventSource 生命周期——useTaskFeed 先例）；可测面=
 *     submitExportBatch+四纯函数（useExportBatch.test，node 环境零 DOM）。
 */
import { useEffect, useRef, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { customInstance } from "../../../shared/api/http";
import { getApiToken } from "../../../shared/api/token";
import { buildBatchExportBody } from "../lib/batchExport";

/** 批量提交变量（units 序=items 序——Select multiple 选中序）。 */
export type ExportBatchInput = {
  projectId: string;
  units: string[];
  conditionKey: string;
};

/** 单项失败记录（worker failures 面逐项四键——SVRB D4 result schema）。 */
export type ExportBatchFailure = {
  index: number;
  unit_id: string | null;
  condition_key: string | null;
  error: string;
};

/** 任务终态产物束（files=产物清单计数面；error=failed 面任务诊断）。 */
export type ExportBatchOutcome = {
  state: string; // done|cancelled|failed
  files: string[];
  failures: ExportBatchFailure[];
  error: string | null;
};

/** 进度视图（done 序数+total+stage 文本——「导出中 i/N·kind·unit」源）。 */
export type ExportBatchProgress = {
  done: number;
  total: number;
  stageText: string;
};

/** 任务状态 JSON 松面（GET /api/calc/tasks 面——result/error 消费位）。 */
type TaskStatusFace = {
  state?: unknown;
  error?: unknown;
  result?: unknown;
};

/** 服务端批量句柄 JSON 松面（ExportHandle asdict——task_id 唯一消费字段）。 */
type ExportHandleFace = { task_id?: unknown };

/** 终态判定（状态机 done/cancelled/failed——manager 三终态单源镜像）。 */
export function isTerminalTaskState(state: string): boolean {
  return state === "done" || state === "cancelled" || state === "failed";
}

/** SSE 事件 data 解析（{type, message, percent} 三面；畸形/缺型拒 null）。 */
export function parseTaskEventData(
  data: string,
): { type: string; message: string | null; percent: number | null } | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    return null;
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return null;
  }
  const record = parsed as Record<string, unknown>;
  if (typeof record.type !== "string") {
    return null;
  }
  return {
    type: record.type,
    message: typeof record.message === "string" ? record.message : null,
    percent: typeof record.percent === "number" ? record.percent : null,
  };
}

/** 终态 outcome 投影（TaskStatus→files/failures/error 四面；result null 兜底空清单）。 */
export function toBatchOutcome(status: TaskStatusFace): ExportBatchOutcome {
  const state = typeof status.state === "string" ? status.state : "failed";
  const result =
    typeof status.result === "object" && status.result !== null && !Array.isArray(status.result)
      ? (status.result as Record<string, unknown>)
      : null;
  return {
    state,
    files: Array.isArray(result?.files)
      ? result.files.filter((file): file is string => typeof file === "string")
      : [],
    failures: Array.isArray(result?.failures)
      ? (result.failures.filter(
          (failure) => typeof failure === "object" && failure !== null,
        ) as ExportBatchFailure[])
      : [],
    error: typeof status.error === "string" ? status.error : null,
  };
}

/** 进度派生（percent 幂商式 (i+1)/(total+1) 还原序数+stage 文本化）。 */
export function deriveBatchProgress(
  percent: number,
  total: number,
  stage: string,
): ExportBatchProgress {
  return {
    done: Math.round(percent * (total + 1)),
    total,
    stageText: stage.startsWith("export:")
      ? stage.slice("export:".length).replace(/:/g, "·")
      : stage,
  };
}

/** SSE 订阅 URL（taskId 路径段编码+token 非空 ?token= 查询通道——D1 双通道）。 */
export function buildTaskStreamUrl(taskId: string, token: string | null): string {
  const base = `/api/events/tasks/${encodeURIComponent(taskId)}`;
  return token === null ? base : `${base}?token=${encodeURIComponent(token)}`;
}

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

/** 批量导出任务 hook（提交→GET 兜底→SSE→终态 outcome+列表失效）。 */
export function useExportBatch(kind: string): {
  submitBatch: (input: ExportBatchInput) => Promise<ExportBatchOutcome>;
  progress: ExportBatchProgress | null;
} {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState<ExportBatchProgress | null>(null);
  const sourceRef = useRef<EventSource | null>(null);
  useEffect(() => () => sourceRef.current?.close(), []); // 卸载即清理（无泄漏句柄）

  const fetchStatus = (taskId: string) =>
    customInstance<TaskStatusFace>({
      url: `/api/calc/tasks/${encodeURIComponent(taskId)}`,
      method: "GET",
    });

  /** SSE 订阅至终态（服务端终态任务连接即发快照 state=竞态第二兜底）。 */
  const awaitTerminal = (taskId: string, total: number) =>
    new Promise<ExportBatchOutcome>((resolve, reject) => {
      const finish = async () => {
        sourceRef.current?.close(); // 终态即收流：close 阻断自动重连循环
        sourceRef.current = null;
        try {
          const outcome = toBatchOutcome(await fetchStatus(taskId));
          void queryClient.invalidateQueries({ queryKey: ["/api/exports"] }); // D5 乙案
          resolve(outcome);
        } catch (error) {
          // R 轮 R5：终态取档失败必达 reject（Promise 不悬挂——调用方
          // ExportButton 的 catch 面接住转终态 error 消息）。
          reject(error instanceof Error ? error : new Error(String(error)));
        }
      };
      const source = new EventSource(buildTaskStreamUrl(taskId, getApiToken()));
      sourceRef.current = source;
      const consume = (event: MessageEvent) => {
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
    const taskId = await submitExportBatch(kind, input);
    // 竞态缓解（D9③）：先 GET 一次——终态即直取（零 SSE 依赖）。
    const first = await fetchStatus(taskId);
    if (typeof first.state === "string" && isTerminalTaskState(first.state)) {
      void queryClient.invalidateQueries({ queryKey: ["/api/exports"] }); // D5 乙案
      return toBatchOutcome(first);
    }
    return awaitTerminal(taskId, input.units.length);
  };

  return { submitBatch, progress };
}
