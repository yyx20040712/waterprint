/**
 * 联合枚举提交条（批2d R-B44b-4 兑现 → M1 批 2026-10-06 裁剪定形：
 * JointSubmitForm=Ribbon 联合枚举 Modal 承载件〔三入口收编一——mapping
 * §A/§D〕；结果面段〔JointSolutionsPanel 挂载/statusQuery/sensitivity/
 * 三图〕删除——M6 study 子面接管；旧 JointSolutionsSection 随 solutionsPane
 * 退役）。
 *
 * 输入:  projectId+onSubmitted（Ribbon Modal 关闭回调）；单元清单/目录
 *        组件内自取（Modal 开态才挂载——随开随取）
 * 输出:  提交条段（多选 unitIds ≥2——可枚举判据复用 enumerateOptions
 *        单源+提交/清单错误回显；onSuccess=writeTaskParam+TASK_EVENT
 *        派发+message 反馈 task_id〔进度呈现面席位接管/结果面 M6——过渡
 *        态诚实反馈〕+onSubmitted 关 Modal）
 *
 * 规格说明（批2d 简报③ DoD 2；M1 批 brief D5 裁剪面）：
 *   - 提交走 generated useRunJointEnumerationApiSolutionJointEnumeratePost
 *     （unit_ids minItems 2——前端 disabled 面控制，服务端 422 详情直显
 *     不重复预检；options 省略=默认 grids/constraints 空=全档）；
 *   - URL 轨：?task= 面板轨复用（写 task 键+派发 TASK_EVENT——枚举/计算
 *     轨经 TASK_EVENT 事件桥驱动已挂载面）；不写 enum 键（表源轨仍属
 *     单单元枚举——双轨语义不混）；
 *   - Select 不用占位文案属性（FE3 C3 grep 门禁规避沿册）。
 */
import { useMemo, useState } from "react";
import { Button, Select, Typography, message } from "antd";

import { useRunJointEnumerationApiSolutionJointEnumeratePost } from "../shared/api/generated/solution/solution";
import { WaterprintApiError } from "../shared/api/http";
import { TASK_EVENT } from "../shared/events";
import { useUnitCatalog } from "../features/params/api/useUnitCatalog";
import { enumerateOptions } from "../features/solutions/lib/solutionsFields";
import { useProjectUnits } from "../features/solutions/api/useProjectUnits";
import { writeTaskParam } from "./solutionsUrlState";

/** 提交钮下限提示（JointEnumerateRequest unit_ids minItems 2——服务端契约面）。 */
const MIN_UNITS = 2;

/** M1 裁剪件：联合枚举提交条段（Ribbon Modal 承载——结果面段 M6 接管）。 */
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
            `联合枚举任务已提交：${response.task_id}（进度见右侧 AI 席位「任务」分页——结果呈现随 M6 批）`,
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
        {submit.error != null ? (
          <Typography.Text type="danger">
            提交失败：{submit.error instanceof Error ? submit.error.message : "未知错误"}
          </Typography.Text>
        ) : null}
      </div>
      {unitsQuery.error != null ? (
        <Typography.Paragraph type="danger">
          单元清单加载失败：
          {unitsQuery.error instanceof Error ? unitsQuery.error.message : "未知错误"}
        </Typography.Paragraph>
      ) : null}
    </div>
  );
}
