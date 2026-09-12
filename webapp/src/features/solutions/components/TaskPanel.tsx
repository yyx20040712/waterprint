/**
 * 任务态面板：SSE 进度呈现+failed 回显+取消动作（D8——FE5 挂账③收口面）。
 *
 * 输入:  taskId+TaskView（useTaskFeed SSE 归约视图）+TaskStatus 快照
 *        （终态详情源——pane 注入）+statusError（快照查询错误文案）
 *        +connection（SSE 连接态提示面——B7 D4：reconnecting/probing 显
 *        中断 warning 行，ok/null 零渲染——与 statusError danger 段不同行
 *        不同语义零互斥）
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
import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { conditionLabel, unitNameIndex } from "../../../shared/conditionLabels";
import { WaterprintApiError } from "../../../shared/api/http";
import { type ConnectionState } from "../api/useTaskFeed";
import { taskStatusToView, type TaskView } from "../lib/taskFeed";

/** 状态徽标映射（state→中文+Tag 色）。 */
const STATE_LABELS: Record<string, { text: string; color: string }> = {
  queued: { text: "排队中", color: "default" },
  running: { text: "运行中", color: "processing" },
  done: { text: "已完成", color: "success" },
  cancelled: { text: "已取消", color: "warning" },
  failed: { text: "失败", color: "error" },
};

/** 阶段文案映射（manager stage 名——未知原样；R5（zM-3）补终态两键：
 * state 事件 message 直通 stage 面，cancelled/failed 不再英文原样——
 * 终态定性文案仍以徽标为准，本表只保阶段列观感）。 */
const STAGE_LABELS: Record<string, string> = {
  queued: "排队中",
  load: "载入项目",
  run: "计算中",
  rows: "整理方案行",
  serialize: "序列化结果",
  done: "完成",
  cancelled: "已取消",
  failed: "已失败",
};

export function TaskPanel({
  taskId,
  view,
  connection,
  status,
  statusError,
}: {
  taskId: string;
  view: TaskView | null;
  connection?: ConnectionState | null;
  status: TaskStatus | null;
  statusError: string | null;
}) {
  // 取消失败文案（行内呈现——不弹窗）
  const [cancelError, setCancelError] = useState<string | null>(null);
  // 工况面 UX 反馈批件 1：工况后缀中文名（catalog name_zh 真源）
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};
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
  // R6（zM-4）：失败文案单源——taskStatusToView 组装（error_type+error+
  // HTTP 段完整），组件内第二套内联组装退役（同义不同文漂移面消除）
  const failureText =
    snapshotView?.error ?? effective?.error ?? "失败详情缺失";
  const state = effective?.state ?? "";
  const label = STATE_LABELS[state] ?? { text: "未知状态", color: "default" };
  const percent =
    effective?.percent !== null && effective?.percent !== undefined
      ? Math.round(effective.percent * 100)
      : null;
  // FIX-ACC1①：done 态显示层归一 100%——服务端阶段点位 percent=(index+1)/
  // (total+1)（worker._report 幂商式），三阶段任务终值=75% 且 done 事件不再
  // 发射 100%；任务实际已完成，进度条停在 75% 误导验收（用户报告 2026-09-09）。
  // cancelled/failed 不覆写——保留诚实末值（半途语义）。
  const displayPercent = state === "done" ? 100 : percent;
  const stageText =
    effective !== null && effective.stage !== ""
      ? (STAGE_LABELS[effective.stage] ?? effective.stage)
      : "";
  const isFailed = state === "failed";
  const cancellable = state === "queued" || state === "running";

  return (
    <div style={{ border: "1px solid var(--wp-border-2)", padding: 12, borderRadius: 4 }}>
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
        status.condition_key !== "" ? (
          // 件 1：工程全称+悬浮原始键（monospace 面内嵌 span 承载 title）
          <span title={status.condition_key}>
            ·工况 {conditionLabel(status.condition_key, unitNames)}
          </span>
        ) : null}
        ）
      </Typography.Text>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 4 }}>
        <Tag color={label.color}>{label.text}</Tag>
        {displayPercent !== null ? (
          <Progress
            percent={displayPercent}
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
        {connection === "reconnecting" || connection === "probing" ? (
          // B7 D4：连接中断系统态信息（与 stale 同位同形态 warning 行）。
          // 文案不写死退避秒数防漂移；probing 60s=useTaskFeed
          // SSE_PROBE_INTERVAL_MS 固定值——改彼处须同步本文案。
          <Typography.Text type="warning">
            {connection === "probing"
              ? "连接中断，每 60 秒重试一次…"
              : "连接中断，自动重连中…"}
          </Typography.Text>
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
          任务失败：{failureText}
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
