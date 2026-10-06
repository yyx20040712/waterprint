/**
 * 联合枚举 app 层薄壳（批2d——R-B44b-4 兑现：提交条+结果面整体抽取，
 * solutionsPane 行数不涨反降；跨 feature 组合归 app 层——enumerateBar 同款；
 * M1 批 2026-10-06 裁剪：新增 JointSubmitForm=提交条段独立承载件〔Ribbon
 * 联合枚举 Modal 消费——三入口收编一；结果面段〔JointSolutionsPanel 挂载/
 * statusQuery/sensitivity〕归 M6 study 子面接管〕；JointSolutionsSection=
 * solutionsPane 旧装载面，随 ⑤笔 solutionsPane 退役删除〔过渡并存〕）。
 *
 * 输入:  JointSubmitForm：projectId+onSubmitted（Ribbon Modal 关闭回调；
 *        单元清单组件内自取——Modal 开态才挂载随开随取）；
 *        JointSolutionsSection：projectId（pane 单一真相透传）+units
 *        （pane 单元清单查询共享）+unitsLoading/unitsError；?task= URL
 * 输出:  JointSubmitForm=提交条段（多选 unitIds ≥2+提交/清单错误回显+
 *        onSuccess=writeTaskParam+TASK_EVENT 派发+message 反馈 task_id
 *        〔进度呈现面 M6/M7 接管——过渡态诚实反馈〕+onSubmitted 关 Modal）；
 *        JointSolutionsSection=旧提交条+done 结果面（combos 表+三图 Tabs）
 *
 * 规格说明（批2d 简报③ DoD 2；M1 批 brief D5 裁剪面）：
 *   - 提交走 generated useRunJointEnumerationApiSolutionJointEnumeratePost
 *     （unit_ids minItems 2——前端 disabled 面控制，服务端 422 详情直显
 *     不重复预检；options 省略=默认 grids/constraints 空=全档）；
 *   - URL 轨：?task= 面板轨复用（写 task 键+派发 TASK_EVENT）；不写
 *     enum 键（表源轨仍属单单元枚举——双轨语义不混）；
 *   - 枚举判据 enumerateOptions 复用沿现状（可枚举单元多选面）；
 *   - 切项目重置（pane R-2 同款：单元选择+联合任务轨）；
 *   - Select 不用占位文案属性（FE3 C3 grep 门禁规避沿册）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactElement } from "react";
import { Button, Card, Select, Typography, message } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { useGetTaskStatusApiCalcTasksTaskIdGet } from "../shared/api/generated/calc/calc";
import { useRunJointEnumerationApiSolutionJointEnumeratePost } from "../shared/api/generated/solution/solution";
import { WaterprintApiError } from "../shared/api/http";
import { TASK_EVENT } from "../shared/events";
import { useUnitCatalog } from "../features/params/api/useUnitCatalog";
import {
  enumerateOptions,
  type UnitOptionRef,
} from "../features/solutions/lib/solutionsFields";
import { jointTaskNotice } from "../features/solutions/lib/jointTaskNotice";
import { narrowJointResult } from "../features/solutions/lib/jointView";
import { useSensitivityQuery } from "../features/solutions/api/useSensitivityQuery";
import { useProjectUnits } from "../features/solutions/api/useProjectUnits";
import { JointSolutionsPanel } from "../features/solutions/components/JointSolutionsPanel";
import { parseTaskParam } from "./projectParam";
import { writeTaskParam } from "./solutionsUrlState";

/** 提交钮下限提示（JointEnumerateRequest unit_ids minItems 2——服务端契约面）。 */
const MIN_UNITS = 2;

/** M1 裁剪件：联合枚举提交条段（Ribbon Modal 承载——结果面段 M6 接管；
 *  单元清单/目录组件内自取，Modal 开态挂载随开随取）。 */
export function JointSubmitForm({
  projectId,
  onSubmitted,
}: {
  projectId: string;
  onSubmitted: () => void;
}) {
  const [unitIds, setUnitIds] = useState<string[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const unitsQuery = useProjectUnits(projectId);
  const catalogQuery = useUnitCatalog();
  const nameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const entry of catalogQuery.data?.units ?? []) {
      map.set(entry.unit_id, entry.name_zh);
    }
    return map;
  }, [catalogQuery.data]);
  const options = useMemo(
    () =>
      enumerateOptions(
        unitsQuery.data ?? [],
        catalogQuery.data?.units ?? null,
        nameById,
      ),
    [unitsQuery.data, catalogQuery.data, nameById],
  );

  const submit = useRunJointEnumerationApiSolutionJointEnumeratePost<WaterprintApiError>(
    {
      mutation: {
        onSuccess: (response) => {
          // 面板轨复用：写 task 键+派发 TASK_EVENT；enum 键不动（双轨不混）
          writeTaskParam(response.task_id);
          window.dispatchEvent(
            new CustomEvent(TASK_EVENT, { detail: response.task_id }),
          );
          messageApi.success(
            `联合枚举任务已提交：${response.task_id}（进度与结果呈现随 M6/M7 批接管）`,
          );
          onSubmitted();
        },
      },
    },
  );

  return (
    <div>
      {contextHolder}
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Select
          mode="multiple"
          style={{ minWidth: 360 }}
          value={unitIds}
          loading={unitsQuery.isLoading}
          status={unitsQuery.isError ? "error" : undefined}
          showSearch
          optionFilterProp="label"
          options={options}
          onChange={(values) => {
            setUnitIds(values);
          }}
        />
        <Button
          type="primary"
          loading={submit.isPending}
          disabled={unitIds.length < MIN_UNITS}
          onClick={() => {
            if (unitIds.length < MIN_UNITS) {
              return;
            }
            submit.mutate({
              data: { project_id: projectId, unit_ids: unitIds },
            });
          }}
        >
          提交联合枚举
        </Button>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          至少选 {MIN_UNITS} 个可枚举单元（无档位参数项不可选）。
        </Typography.Text>
        {submit.error instanceof Error ? (
          <Typography.Text type="danger">
            提交失败：{submit.error.message}
          </Typography.Text>
        ) : null}
      </div>
      {unitsQuery.error instanceof Error ? (
        <Typography.Paragraph type="danger">
          单元清单加载失败：{unitsQuery.error.message}
        </Typography.Paragraph>
      ) : null}
    </div>
  );
}

/** 错误文案（Error.message 优先，未知错误兜底——pane errorText 同款）。 */
function errorText(error: unknown, isError: boolean): string | null {
  if (!isError) return null;
  return error instanceof Error ? error.message : "未知错误";
}

export function JointSolutionsSection({
  projectId,
  units,
  unitsLoading,
  unitsError,
}: {
  projectId: string;
  units: readonly UnitOptionRef[];
  unitsLoading: boolean;
  unitsError: string | null;
}) {
  const [unitIds, setUnitIds] = useState<string[]>([]);
  const queryClient = useQueryClient();
  // 联合任务轨（?task= 面板轨复用——初值 task 键；enum 键不读不写）
  const [jointTaskId, setJointTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search),
  );
  const prevProject = useRef(projectId);
  const catalogQuery = useUnitCatalog();
  const nameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const entry of catalogQuery.data?.units ?? []) {
      map.set(entry.unit_id, entry.name_zh);
    }
    return map;
  }, [catalogQuery.data]);
  const options = useMemo(
    () => enumerateOptions(units, catalogQuery.data?.units ?? null, nameById),
    [units, catalogQuery.data, nameById],
  );

  // TASK_EVENT 自监听（pane 同款——URL 回写驱动已挂载面；同值早退；
  // 批6e 回炉 W5：终态事件同时失效 sensitivity 键——calc 重算后 stale
  // 报告即时重取，消除「输入已变/缓存未刷」静默窗口=comparePane 同款）
  useEffect(() => {
    const onTaskParam = () => {
      const next = parseTaskParam(window.location.search);
      setJointTaskId((prev) => (prev === next ? prev : next));
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/sensitivity/${projectId}`],
      });
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  // 切项目重置（pane R-2 同款——初挂载 prev 同值早退保深链初值）
  useEffect(() => {
    if (prevProject.current === projectId) return;
    prevProject.current = projectId;
    setJointTaskId(null);
    setUnitIds([]);
  }, [projectId]);

  // 任务快照（与 pane 面板轨同查询键——SSE 终态失效联动共享缓存）
  const statusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(jointTaskId ?? "", {
    query: { enabled: jointTaskId !== null },
  });
  const status = statusQuery.data ?? null;
  const jointDone =
    status?.kind === "joint_enumerate" && status?.state === "done";

  // 批6e：全工况投影（最近完成计算快照——龙卷风幅度轴；404 无结果集=
  // data null 降级提示，窄化非法=查询 error 态呈现于组件注记面）
  const sensitivityQuery = useSensitivityQuery(projectId);
  const sensitivity = sensitivityQuery.data ?? null;
  // 回炉 k1-W2：404/损坏面详情透传（服务端 fail-loud 原因——非「尚未计算」折叠）
  const sensitivityIssue = sensitivityQuery.isError
    ? sensitivityQuery.error instanceof Error
      ? sensitivityQuery.error.message
      : "未知错误"
    : null;

  // 窄化门（error 呈现非静默——JointViewError message 带定位）
  let panel: ReactElement | null = null;
  if (jointDone) {
    try {
      panel = (
        <JointSolutionsPanel
          result={narrowJointResult(status?.result)}
          sensitivity={sensitivity}
          sensitivityIssue={sensitivityIssue}
        />
      );
    } catch (error) {
      panel = (
        <Typography.Paragraph type="danger">
          联合枚举结果载荷非法：
          {error instanceof Error ? error.message : "未知错误"}
        </Typography.Paragraph>
      );
    }
  }

  const submit = useRunJointEnumerationApiSolutionJointEnumeratePost<WaterprintApiError>(
    {
      mutation: {
        onSuccess: (response) => {
          setJointTaskId(response.task_id);
          // 面板轨复用：写 task 键+派发 TASK_EVENT（pane TaskPanel+SSE 接管
          // 进度呈现——enum 键不动，双轨语义不混）
          writeTaskParam(response.task_id);
          window.dispatchEvent(
            new CustomEvent(TASK_EVENT, { detail: response.task_id }),
          );
        },
      },
    },
  );
  const submitError = errorText(submit.error, submit.isError);

  // 批6f（批2d 欠账②）：非 done 态文案分派——failed/cancelled 终态各就位
  // （明细=taskStatusToView 快照单源），「进行中」幽灵退役；done 态 null
  const jointNotice =
    status !== null && status.kind === "joint_enumerate" && !jointDone
      ? jointTaskNotice(status)
      : null;

  return (
    <Card size="small" title="联合枚举（方案比选——多单元组合）" style={{ marginTop: 12 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Select
          mode="multiple"
          style={{ minWidth: 360 }}
          value={unitIds}
          loading={unitsLoading}
          status={unitsError !== null ? "error" : undefined}
          showSearch
          optionFilterProp="label"
          options={options}
          onChange={(values) => {
            setUnitIds(values);
          }}
        />
        <Button
          type="primary"
          loading={submit.isPending}
          disabled={unitIds.length < MIN_UNITS}
          onClick={() => {
            if (unitIds.length < MIN_UNITS) {
              return;
            }
            submit.mutate({
              data: { project_id: projectId, unit_ids: unitIds },
            });
          }}
        >
          提交联合枚举
        </Button>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          至少选 {MIN_UNITS} 个可枚举单元（无档位参数项不可选）；提交后任务
          进度在上方任务面板呈现，完成后此处展示方案比选表与三图。
        </Typography.Text>
        {submitError !== null ? (
          <Typography.Text type="danger">提交失败：{submitError}</Typography.Text>
        ) : null}
      </div>
      {unitsError !== null ? (
        <Typography.Paragraph type="danger">单元清单加载失败：{unitsError}</Typography.Paragraph>
      ) : null}
      {jointNotice !== null ? (
        <Typography.Paragraph
          type={
            jointNotice.kind === "failed"
              ? "danger"
              : jointNotice.kind === "cancelled"
                ? "warning"
                : "secondary"
          }
          style={{ marginBottom: 0 }}
        >
          {jointNotice.text}
        </Typography.Paragraph>
      ) : null}
      {panel}
    </Card>
  );
}
