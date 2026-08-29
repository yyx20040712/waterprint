/**
 * 方案应用按钮：行级 grid 字段投影→apply 原子提交（D6——服务端原子事务）。
 *
 * 输入:  行记录（SolutionRow）+gridFields（可应用标识列）+projectId/unitId
 *        +onApplied 回调（?task= 回写面——app 层 solutionsPane 注入）
 * 输出:  「应用」按钮+行内结果消息（成功=new_hash 前 8 位+design_changed；
 *        失败=Error.message 透出——WaterprintApiError 归一面）
 *
 * 规格说明（FE6 批 6b 段四，D6；骨架期「乐观更新+失败回滚」措辞随实装
 *   校正——服务端 R5 原子事务（merged.update→save→自动重算→失败回滚），
 *   前端不做乐观更新只透传结果）：
 *   - 载荷=buildApplyPayload（仅 grid 字段投影 params——dim 输出不可应用
 *     ADR-005 单单元语义；值全 number）；
 *   - onSuccess：invalidate [`/api/projects/${projectId}`]（read 键——
 *     canvas/params/假设三面联动刷新，FE5 同键复用）+onApplied 回调
 *     （recalc_task_id 通道——?task= 回写后任务态面板转向重算任务）；
 *   - design_changed=false（等值应用）非错误——消息面区分呈现；
 *   - 应用后表格数据为已提交任务快照不自动刷新（旧行保留——服务端分页
 *     只读快照语义注记；旧结果 stale 禁静默覆盖在服务端 apply 面收口）；
 *   - unitId=null=deep-link 直进而枚举单元未在下拉选定（任务 result 载荷
 *     无 unit_id 面）——按钮禁用提示，选定即恢复。
 */
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Typography } from "antd";

import { useApplySolutionApiCalcSolutionsApplyPost } from "../../../shared/api/generated/calc/calc";
import type { ApplyOutcome } from "../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../shared/api/http";
import { buildApplyPayload, type SolutionRow } from "../lib/solutionsView";

export function ApplySolutionButton({
  row,
  gridFields,
  projectId,
  unitId,
  onApplied,
}: {
  row: SolutionRow;
  gridFields: string[];
  projectId: string;
  unitId: string | null;
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

  return (
    <span style={{ whiteSpace: "nowrap" }}>
      <Button
        size="small"
        loading={apply.isPending}
        disabled={unitId === null}
        title={unitId === null ? "先在上方单元下拉选定该枚举单元（deep-link 直进面）" : undefined}
        onClick={() => {
          if (unitId === null) {
            return;
          }
          setMessage(null);
          apply.mutate({
            data: buildApplyPayload(row, gridFields, projectId, unitId),
          });
        }}
      >
        应用
      </Button>
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
