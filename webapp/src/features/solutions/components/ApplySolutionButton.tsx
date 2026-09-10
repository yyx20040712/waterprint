/**
 * 方案应用按钮：行级 grid 字段投影→apply 原子提交（D6——服务端原子事务）。
 *
 * 输入:  行记录（SolutionRow）+gridFields（可应用标识列）+projectId/unitId
 *        +gateReason（P0-2 应用闸禁用因——null=放行）+driftWarn（P0-2
 *        版本漂移警示面）+onApplied 回调（?task= 回写面——app 层注入）
 * 输出:  「应用」按钮（漂移态 Popconfirm 二次确认）+行内结果消息（成功
 *        =new_hash 前 8 位+design_changed；失败=Error.message 透出）
 *
 * 规格说明（FE6 批 6b 段四 D6；P0-2 三闸 2026-09-11——op-chain-fix-plan
 *   §二 r2；服务端 R5 原子事务（merged.update→save→自动重算→失败回滚），
 *   前端不做乐观更新只透传结果）：
 *   - 载荷=buildApplyPayload（仅 grid 字段投影 params——dim 输出不可应用
 *     ADR-005 单单元语义；值全 number）；
 *   - onSuccess：invalidate [`/api/projects/${projectId}`]（read 键——
 *     canvas/params/假设三面联动刷新，FE5 同键复用）+onApplied 回调
 *     （recalc_task_id 通道——?task= 回写后任务态面板转向重算任务）；
 *   - design_changed=false（等值应用）非错误——消息面区分呈现；
 *   - 应用后表格数据为已提交任务快照不自动刷新（旧行保留——服务端分页
 *     只读快照语义注记；旧结果 stale 禁静默覆盖在服务端 apply 面收口）；
 *   - P0-2 三闸消费面：gateReason 非空=禁用+title 述因（①下拉选定≠表源
 *     单元/②表源单元已不在当前 design——禁用语义归 pane 计算层）；漂移
 *     ③=driftWarn 横幅（pane）+本钮 Popconfirm 二次确认（呈裁⑧ 甲案：
 *     警示后放行）；unitId=null 仍兜底禁用（旧任务 result 无 unit_id 面
 *     ——F5 修复后仅历史任务可达，文案不再误导「先在下拉选定」）。
 */
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Popconfirm, Typography } from "antd";

import { useApplySolutionApiCalcSolutionsApplyPost } from "../../../shared/api/generated/calc/calc";
import type { ApplyOutcome } from "../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../shared/api/http";
import type { GridField } from "../lib/solutionsFields";
import { buildApplyPayload, type SolutionRow } from "../lib/solutionsView";

/** P0-2 漂移警示文案（呈裁⑧ 甲案——警示后放行）。 */
const DRIFT_CONFIRM_TITLE =
  "设计已变更，方案表来自旧版本设计的枚举结果——仍要应用这组参数吗？";

export function ApplySolutionButton({
  row,
  gridFields,
  projectId,
  unitId,
  gateReason = null,
  driftWarn = false,
  onApplied,
}: {
  row: SolutionRow;
  gridFields: GridField[];
  projectId: string;
  unitId: string | null;
  /** 应用闸禁用因（非 null=禁用+title 述因——pane 三闸计算层）。 */
  gateReason?: string | null;
  /** 版本漂移警示（true=Popconfirm 二次确认后放行）。 */
  driftWarn?: boolean;
  onApplied?: (outcome: ApplyOutcome) => void;
}) {
  const queryClient = useQueryClient();
  // 行内结果消息（成功/失败共用槽——单行独立态，跨行不串）
  const [message, setMessage] = useState<string | null>(null);
  const apply = useApplySolutionApiCalcSolutionsApplyPost<WaterprintApiError>({
    mutation: {
      // 服务端已原子写+触发重算——失效 read 键驱动三面刷新
      onSuccess: (outcome) => {
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
        setMessage(
          `已应用（design ${outcome.new_hash.slice(0, 8)}…`
            + `${outcome.design_changed ? "，已触发重算" : "，值未变"}）`,
        );
        onApplied?.(outcome);
      },
      onError: (error) => {
        setMessage(`应用失败：${error.message}`);
      },
    },
  });

  const disabled = unitId === null || gateReason !== null;
  const title =
    gateReason !== null
      ? gateReason
      : unitId === null
        ? "未识别到方案表源单元（历史任务载荷缺 unit_id）——重新提交枚举可恢复应用"
        : undefined;

  function doApply() {
    if (unitId === null) {
      return;
    }
    setMessage(null);
    apply.mutate({
      data: buildApplyPayload(row, gridFields, projectId, unitId),
    });
  }

  const button = (
    <Button
      size="small"
      loading={apply.isPending}
      disabled={disabled}
      title={title}
      onClick={() => {
        if (disabled) {
          return;
        }
        // 漂移面经 Popconfirm onConfirm 触达（无漂移直应用）
        if (!driftWarn) {
          doApply();
        }
      }}
    >
      应用
    </Button>
  );

  return (
    <span style={{ whiteSpace: "nowrap" }}>
      {driftWarn && !disabled ? (
        <Popconfirm
          title={DRIFT_CONFIRM_TITLE}
          okText="仍要应用"
          cancelText="取消"
          onConfirm={doApply}
        >
          {button}
        </Popconfirm>
      ) : (
        button
      )}
      {driftWarn && !disabled ? (
        // 行级可见警示标记（Popconfirm 浮层开前不可见——本标记为漂移态
        // 常驻可见面+无头断言载体；pane 横幅为全局解释面）
        <Typography.Text
          type="warning"
          title={DRIFT_CONFIRM_TITLE}
          style={{ marginLeft: 6, fontSize: 11 }}
        >
          旧版本
        </Typography.Text>
      ) : null}
      {message !== null ? (
        <Typography.Text
          type={apply.isError ? "danger" : "success"}
          style={{ marginLeft: 8, fontSize: 11 }}
        >
          {message}
        </Typography.Text>
      ) : null}
    </span>
  );
}
