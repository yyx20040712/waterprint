/**
 * v4 枚举配置 Modal（B1 骨架批 2026-10-09——⟳重新枚举唯一入口：EnumerateBar
 * 承载+提交 useRunEnumeration；枚举轨 enum/task 双键回写+TASK_EVENT——
 * ribbon EnumerateModalBody 接线面同源重装配〔M1 件零改红线——私有件不
 * 导出，本件=app 组合层重装配非复制件〕）。
 *
 * 输入:  open/onClose（designZone 右栏持有）+projectId+unitId（选中工艺——
 *        预选目标单元）+useProjectUnits（画布单元清单）+useConstraints
 *        （约束目录）+useReadProjectApiProjectsProjectIdGet（勾选恢复/保存
 *        基座——CP2 同链）
 * 输出:  Modal（枚举配置：单元下拉+约束勾选+提交钮+两错误行——EnumerateBar
 *        复用）+提交成功 message+onDone 关闭
 *
 * 规格说明（B1 任务书 §三.3 右栏——「⟳重新枚举钮=枚举配置 Modal 唯一入口
 *   ——复用现行 enumerateBar」；B2 批处置完整数据流）：
 *   - 提交载荷=toPayloadItems（R-3 本组投影空回 null 同链）；
 *   - 勾选持久=PUT withConstraintChoices（CP2 D4 合成全集——服务端权威）；
 *   - 成功=writeEnumParam+writeTaskParam+TASK_EVENT（ENG5 D6 双轨+联动）。
 */
import { useEffect, useState } from "react";
import { Modal, message } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { EnumerateBar } from "../enumerateBar";
import { useConstraints } from "../../features/params/api/useConstraints";
import {
  filterSelectable,
  mergeGroupSelection,
  restoreConstraintKeys,
  toPayloadItems,
} from "../../features/params/lib/constraintPicker";
import { withConstraintChoices } from "../../features/params/lib/designParams";
import { useProjectUnits } from "../../features/solutions/api/useProjectUnits";
import { useRunEnumerationApiCalcEnumeratePost } from "../../shared/api/generated/calc/calc";
import {
  useReadProjectApiProjectsProjectIdGet,
  useSaveProjectApiProjectsProjectIdPut,
} from "../../shared/api/generated/projects/projects";
import type { WaterprintApiError } from "../../shared/api/http";
import { isLockConflict, LOCK_HINT } from "../../shared/api/http";
import { TASK_EVENT } from "../../shared/events";
import { writeEnumParam, writeTaskParam } from "../solutionsUrlState";

export function EnumerateModal({
  open,
  onClose,
  projectId,
  unitId,
}: {
  open: boolean;
  onClose: () => void;
  projectId: string | null;
  /** 选中工艺（右栏上下文——预选下拉）。 */
  unitId: string | null;
}) {
  const [selectedUnit, setSelectedUnit] = useState<string | null>(unitId);
  const [constraintKeys, setConstraintKeys] = useState<string[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const queryClient = useQueryClient();
  const unitsQuery = useProjectUnits(projectId);
  // 回炉 R13：约束目录 open 门（与 rawQuery 同制——关闭态免取数）
  const constraintsQuery = useConstraints(open);
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId ?? "", {
    query: { enabled: projectId !== null && open },
  });

  // 开态随选中工艺预选（unitId 变更同步——右栏上下文进 Modal）
  useEffect(() => {
    if (open) {
      setSelectedUnit(unitId);
    }
  }, [open, unitId]);

  // CP2 D3 恢复：raw 到达→恢复勾选全集
  useEffect(() => {
    const raw = rawQuery.data;
    if (raw !== undefined) {
      setConstraintKeys(restoreConstraintKeys(raw));
    }
  }, [rawQuery.data]);

  const saveConstraints = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>({
    mutation: {
      onSuccess: (_outcome, variables) => {
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${variables.projectId}`],
        });
      },
    },
  });

  const enumerate = useRunEnumerationApiCalcEnumeratePost<WaterprintApiError>({
    mutation: {
      onSuccess: (response) => {
        writeEnumParam(response.task_id);
        writeTaskParam(response.task_id);
        window.dispatchEvent(
          new CustomEvent(TASK_EVENT, { detail: response.task_id }),
        );
        messageApi.success(
          `枚举任务已提交：${response.task_id.slice(0, 8)}（进度见底栏任务条）`,
        );
        onClose();
      },
      onError: (error) => {
        messageApi.error(
          error instanceof Error ? error.message : "枚举提交失败",
        );
      },
    },
  });

  const selectableConstraints = filterSelectable(
    constraintsQuery.data ?? [],
    selectedUnit,
  );

  /** CP2 D4+R-1：勾选=本组变更合成全集（跨单元键保留）→乐观 set+PUT。 */
  const handleConstraintChange = (nextKeys: string[]) => {
    const raw = rawQuery.data;
    const prevKeys = constraintKeys;
    const groupKeys = selectableConstraints.map((entry) => entry.key);
    const mergedKeys = mergeGroupSelection(constraintKeys, groupKeys, nextKeys);
    setConstraintKeys(mergedKeys);
    if (raw === undefined || projectId === null) {
      messageApi.warning("项目数据未就绪，勾选暂未保存");
      return;
    }
    saveConstraints.mutate(
      { projectId, data: withConstraintChoices(raw, mergedKeys) },
      {
        onError: (error) => {
          setConstraintKeys(prevKeys);
          messageApi.error(
            isLockConflict(error)
              ? LOCK_HINT
              : `约束勾选保存失败：${error instanceof Error ? error.message : "未知错误"}`,
          );
        },
      },
    );
  };

  return (
    <Modal
      title="枚举配置"
      open={open}
      onCancel={onClose}
      footer={null}
      width={640}
      destroyOnHidden
      data-testid="wp-v4-enumerate-modal"
    >
      {contextHolder}
      {projectId === null ? (
        <span style={{ color: "var(--wp-text-2)", fontSize: 12 }}>
          尚未选择项目——先在「项目」区打开或新建
        </span>
      ) : (
        <EnumerateBar
          units={unitsQuery.data ?? []}
          unitId={selectedUnit}
          onUnitChange={setSelectedUnit}
          constraintEntries={selectableConstraints}
          constraintKeys={constraintKeys}
          onConstraintChange={handleConstraintChange}
          enumeratePending={enumerate.isPending}
          onEnumerate={() => {
            if (selectedUnit === null || projectId === null) {
              return;
            }
            // R-3 同链：本组投影空回 null（禁发 {constraints:[]}）
            const items = toPayloadItems(selectableConstraints, constraintKeys);
            enumerate.mutate({
              data: {
                project_id: projectId,
                unit_ids: [selectedUnit],
                options: items.length === 0 ? null : { constraints: items },
              },
            });
          }}
          enumerateError={
            enumerate.isError
              ? enumerate.error instanceof Error
                ? enumerate.error.message
                : "未知错误"
              : null
          }
          unitsLoading={unitsQuery.isLoading}
          unitsError={
            unitsQuery.isError
              ? unitsQuery.error instanceof Error
                ? unitsQuery.error.message
                : "未知错误"
              : null
          }
        />
      )}
    </Modal>
  );
}
