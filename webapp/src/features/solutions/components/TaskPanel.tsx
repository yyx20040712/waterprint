/**
 * 任务态面板：SSE 进度呈现+failed 回显+取消动作（D8——FE5 挂账③收口面）。
 *
 * 输入:  taskId+TaskView（useTaskFeed SSE 归约视图）+TaskStatus 快照
 *        （终态详情源——pane 注入）+statusError（快照查询错误文案）
 * 输出:  状态徽标+进度条+阶段文案+失败三件回显（error_type/error/
 *        error_code）+running/queued 取消按钮+stale 提示
 *
 * 规格说明（FE6 批 6b 段四，D8）：
 *   - 双源呈现：进度面=SSE 流（view——state 徽标/percent/stage）；终态
 *     详情面=TaskStatus 快照（failed 三件 error_type/error/error_code
 *     分段呈现——SSE 载荷无 error 字段，taskStatusToView 归一串兜底）；
 *   - 阶段文案中文映射（enumerate 面 load/run/rows、calc 面 load/run/
 *     serialize——未知 stage 原样呈现不猜语义）；
 *   - running/queued 显取消按钮（useCancelTask——服务端协作令牌置位，
 *     已完成结果不受影响 R3）；终态不显；
 *   - 快照 404 面=任务不存在或服务重启（任务注册表在内存——重提交
 *     枚举即新任务），statusError 透出指引；
 *   - calc 重算任务（ParamForm/方案应用触发）同面板呈现——?task= 联动
 *     单一通道（不抢焦点不跨标签跳转——挂账 UX 批）。
 */
import { useState } from "react";
import { Button, Progress, Tag, Typography } from "antd";

import { useCancelTaskApiCalcTasksTaskIdCancelPost } from "../../../shared/api/generated/calc/calc";
import type { TaskStatus } from "../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../shared/api/http";
import { taskStatusToView, type TaskView } from "../lib/taskFeed";

/** 状态徽标映射（state→中文+Tag 色）。 */
const STATE_LABELS: Record<string, { text: string; color: string }> = {
  queued: { text: "排队中", color: "default" },
  running: { text: "运行中", color: "processing" },
  done: { text: "已完成", color: "success" },
  cancelled: { text: "已取消", color: "warning" },
  failed: { text: "失败", color: "error" },
};

/** 阶段文案映射（manager stage 名——未知原样）。 */
const STAGE_LABELS: Record<string, string> = {
  queued: "排队中",
  load: "载入项目",
  run: "计算中",
  rows: "整理方案行",
  serialize: "序列化结果",
  done: "完成",
};

export function TaskPanel({
  taskId,
  view,
  status,
  statusError,
}: {
  taskId: string;
  view: TaskView | null;
  status: TaskStatus | null;
  statusError: string | null;
}) {
  // 取消失败文案（行内呈现——不弹窗）
  const [cancelError, setCancelError] = useState<string | null>(null);
  const cancel = useCancelTaskApiCalcTasksTaskIdCancelPost<WaterprintApiError>({
    mutation: {
      onError: (error) => {
        setCancelError(error.message);
      },
    },
  });
  // 双源归一：SSE 视图优先（实时），快照兜底（终态详情）
  const snapshotView = status !== null ? taskStatusToView(status) : null;
  const effective = view ?? snapshotView;
  const state = effective?.state ?? "";
  const label = STATE_LABELS[state] ?? { text: "未知状态", color: "default" };
  const percent =
    effective?.percent !== null && effective?.percent !== undefined
      ? Math.round(effective.percent * 100)
      : null;
  const stageText =
    effective !== null && effective.stage !== ""
      ? (STAGE_LABELS[effective.stage] ?? effective.stage)
      : "";
  const isFailed = state === "failed";
  const cancellable = state === "queued" || state === "running";

  return (
    <div style={{ border: "1px solid #434343", padding: 12, borderRadius: 4 }}>
      <Typography.Text
        type="secondary"
        style={{ fontFamily: "monospace", fontSize: 11 }}
      >
        任务 {taskId.slice(0, 8)}…（
        {status?.kind === "enumerate"
          ? "枚举"
          : status?.kind === "calc"
            ? "重算"
            : "任务"}
        {status !== null &&
        status.condition_key !== null &&
        status.condition_key !== ""
          ? `·工况 ${status.condition_key}`
          : ""}
        ）
      </Typography.Text>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 4 }}>
        <Tag color={label.color}>{label.text}</Tag>
        {percent !== null ? (
          <Progress
            percent={percent}
            size="small"
            style={{ width: 220, marginBottom: 0 }}
          />
        ) : null}
        {stageText !== "" ? (
          <Typography.Text type="secondary">阶段：{stageText}</Typography.Text>
        ) : null}
        {effective?.stale ? (
          <Typography.Text type="warning">结果已过期（stale）</Typography.Text>
        ) : null}
        {cancellable ? (
          <Button
            size="small"
            danger
            loading={cancel.isPending}
            onClick={() => {
              setCancelError(null);
              cancel.mutate({ taskId });
            }}
          >
            取消任务
          </Button>
        ) : null}
      </div>
      {statusError !== null ? (
        <Typography.Paragraph type="danger" style={{ marginBottom: 0, marginTop: 4 }}>
          任务状态查询失败：{statusError}——任务注册表在服务端内存，服务重启后
          任务 id 失效（重新提交枚举即新任务）。
        </Typography.Paragraph>
      ) : null}
      {isFailed ? (
        <Typography.Paragraph type="danger" style={{ marginBottom: 0, marginTop: 4 }}>
          任务失败：
          {status !== null && (status.error_type !== null || status.error !== null)
            ? `${status.error_type ?? "未知异常"}：${status.error ?? "无详情"}`
            : (effective?.error ?? "失败详情缺失")}
          {status?.error_code !== null && status?.error_code !== undefined
            ? `（HTTP ${status.error_code}）`
            : ""}
        </Typography.Paragraph>
      ) : null}
      {cancelError !== null ? (
        <Typography.Paragraph type="danger" style={{ marginBottom: 0, marginTop: 4 }}>
          取消失败：{cancelError}
        </Typography.Paragraph>
      ) : null}
    </div>
  );
}
