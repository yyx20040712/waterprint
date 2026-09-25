/**
 * 联合枚举 app 层薄壳（批2d——R-B44b-4 兑现：提交条+结果面整体抽取，
 * solutionsPane 行数不涨反降；跨 feature 组合归 app 层——enumerateBar 同款）。
 *
 * 输入:  projectId（pane 单一真相透传）+units（pane 单元清单查询共享——
 *        零重复取数）+unitsLoading/unitsError；?task= URL（面板轨复用）
 * 输出:  联合枚举提交条（多选单元 ≥2——可枚举判据复用 isUnitEnumerable）+
 *        提交/清单错误回显+done 结果面（combos 表+三图 Tabs——窄化门
 *        error 呈现非静默）；任务态走既有面板轨（?task= 写 task 键+
 *        TASK_EVENT 事件桥——pane TaskPanel+SSE 消费，本件零重复面板）
 *
 * 规格说明（批2d 简报③ DoD 2）：
 *   - 提交走 generated useRunJointEnumerationApiSolutionJointEnumeratePost
 *     （unit_ids minItems 2——前端 disabled 面控制，服务端 422 详情直显
 *     不重复预检；options 省略=默认 grids/constraints 空=全档）；
 *   - URL 轨：?task= 面板轨复用（写 task 键+派发 TASK_EVENT）；不写
 *     enum 键（表源轨仍属单单元枚举——双轨语义不混）；
 *   - 本件自监听 TASK_EVENT 重读 ?task=（pane 同款第三处先例——Tabs
 *     保活下 URL 回写驱动已挂载面）；任务快照与 pane 面板轨同查询键
 *     （同任务单次取数——SSE 终态失效联动）；
 *   - 结果面挂载门：kind=joint_enumerate 且 state=done；combos 空=
 *     DiagnosisPanel（无解诊断沿枚举同款语义）；窄化非法=错误段落
 *     呈现（JointViewError message 带定位——非静默）；
 *   - 切项目重置（pane R-2 同款：单元选择+联合任务轨）；
 *   - Select 不用占位文案属性（FE3 C3 grep 门禁规避沿册）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactElement } from "react";
import { Button, Card, Select, Typography } from "antd";

import { useGetTaskStatusApiCalcTasksTaskIdGet } from "../shared/api/generated/calc/calc";
import { useRunJointEnumerationApiSolutionJointEnumeratePost } from "../shared/api/generated/solution/solution";
import { WaterprintApiError } from "../shared/api/http";
import { TASK_EVENT } from "../shared/events";
import { useUnitCatalog } from "../features/params/api/useUnitCatalog";
import {
  enumerateOptions,
  type UnitOptionRef,
} from "../features/solutions/lib/solutionsFields";
import { narrowJointResult } from "../features/solutions/lib/jointView";
import { JointSolutionsPanel } from "../features/solutions/components/JointSolutionsPanel";
import { parseTaskParam } from "./projectParam";
import { writeTaskParam } from "./solutionsUrlState";

/** 提交钮下限提示（JointEnumerateRequest unit_ids minItems 2——服务端契约面）。 */
const MIN_UNITS = 2;

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

  // TASK_EVENT 自监听（pane 同款——URL 回写驱动已挂载面；同值早退）
  useEffect(() => {
    const onTaskParam = () => {
      const next = parseTaskParam(window.location.search);
      setJointTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

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

  // 窄化门（error 呈现非静默——JointViewError message 带定位）
  let panel: ReactElement | null = null;
  if (jointDone) {
    try {
      panel = <JointSolutionsPanel result={narrowJointResult(status?.result)} />;
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
      {status !== null && status.kind === "joint_enumerate" && !jointDone ? (
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          联合枚举任务进行中——结果将在完成后呈现（进度见上方任务面板）。
        </Typography.Paragraph>
      ) : null}
      {panel}
    </Card>
  );
}
