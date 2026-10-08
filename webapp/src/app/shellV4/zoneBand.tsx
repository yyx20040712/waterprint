/**
 * v4 顶带（B1 骨架批 2026-10-09——48px：logo 简笔水滴线形+六功能区页签
 * 〔选中=白底+AC 色字+描边——wireframe .mod.on 形〕+右语境工具区）。
 *
 * 输入:  target（当前 zone——V4_ZONES 声明序渲染）+onZoneChange（切换
 *        唯一通道——shellV4 setZone）+useProjectId（工具区项目门）
 * 输出:  顶带：logo+六页签（button 元素 data-zone 锚——探针 N1 逐区单点
 *        可达）+工具区（保存/撤销/重做/校验/全项目计算——简笔线性图标
 *        antd icons 线性族）
 *
 * 规格说明（B1 任务书 §三.1——plan §九.1）：
 *   - 语境工具区四活一骨架：保存=手动（draftProjectRaw+PUT——CanvasEdit
 *     Toolbar 同链；草稿自动暂存 paramsStore 沿承）；校验=validate POST
 *     （结论呈现迁 dock-tasks=B2 处置——B1 message 即时反馈）；全项目
 *     计算=decideRunCalc 分派链复用（ribbon 导出纯函数——M1 件零改）；
 *     撤销/重做=画布引擎无撤销栈（B1 骨架在场禁用态——实装挂账后续批）；
 *   - logo=简笔水滴线形 SVG（wireframe 屏 1 同形——stroke AC 色线性）；
 *   - 页签次序=V4_ZONES 单源（项目→计算说明）；切换经 onZoneChange 单通道。
 */
import { useEffect, useState } from "react";
import {
  PlayCircleOutlined,
  RedoOutlined,
  SafetyCertificateOutlined,
  SaveOutlined,
  UndoOutlined,
} from "@ant-design/icons";
import { Button, message, Tooltip } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { draftProjectRaw } from "../../features/canvas/lib/designWriter";
import {
  useCanvasStore,
  useDirty,
  useDraft,
} from "../../features/canvas/store/canvasStore";
import { useParamsStore } from "../../features/params/store/paramsStore";
import { useRunCalculationApiCalcRunPost } from "../../shared/api/generated/calc/calc";
import {
  useReadProjectApiProjectsProjectIdGet,
  useSaveProjectApiProjectsProjectIdPut,
  useValidateProjectApiProjectsProjectIdValidatePost,
} from "../../shared/api/generated/projects/projects";
import type { WaterprintApiError } from "../../shared/api/http";
import { TASK_EVENT } from "../../shared/events";
import { decideRunCalc, paramDraftBlockMessage } from "../ribbon";
import { writeTaskParam } from "../solutionsUrlState";
import { useProjectId } from "../useProjectId";
import { V4_ZONE_LABELS } from "./shellV4";
import { V4_ZONES, type V4ZoneTarget } from "../zoneParam";

/** logo 简笔水滴线形（wireframe 屏 1 同形——16×16 stroke AC）。 */
function BandLogo() {
  return (
    <span
      aria-hidden
      style={{
        width: 26,
        height: 26,
        border: "1.5px solid var(--wpv4-ac)",
        borderRadius: 6,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flex: "none",
      }}
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--wpv4-ac)" strokeWidth="1.4">
        <path d="M2 12c2-4 4-4 6-8 2 4 4 4 6 8" />
        <path d="M5 12h6" />
      </svg>
    </span>
  );
}

/** raw design.checked_units 宽容读取（ribbon 同口径小件——M1 件零改红线
 *  下的重声明；checked_units=工况过滤面）。 */
function rawCheckedUnits(raw: unknown): string[] {
  if (typeof raw !== "object" || raw === null) {
    return [];
  }
  const design = (raw as Record<string, unknown>)["design"];
  if (typeof design !== "object" || design === null) {
    return [];
  }
  const checked = (design as Record<string, unknown>)["checked_units"];
  return Array.isArray(checked)
    ? checked.filter((id): id is string => typeof id === "string")
    : [];
}

export function ZoneBand({
  target,
  onZoneChange,
}: {
  target: V4ZoneTarget;
  /** zone 切换唯一通道（shellV4 setZone——replaceState 写 ?tab=）。 */
  onZoneChange: (next: V4ZoneTarget) => void;
}) {
  const [projectId] = useProjectId();
  const dirty = useDirty(projectId);
  const draft = useDraft(projectId);
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId ?? "", {
    query: { enabled: projectId !== null },
  });
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const store = useCanvasStore;
  const paramDraftCount = useParamsStore((s) =>
    projectId !== null ? s.draftHint[projectId] ?? 0 : 0,
  );
  const [validatePending, setValidatePending] = useState(false);
  useEffect(() => {
    setValidatePending(false);
  }, [projectId]);

  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>();
  const validate = useValidateProjectApiProjectsProjectIdValidatePost();
  const run = useRunCalculationApiCalcRunPost<WaterprintApiError>({
    mutation: {
      onSuccess: (outcome) => {
        writeTaskParam(outcome.task_id);
        window.dispatchEvent(
          new CustomEvent(TASK_EVENT, { detail: outcome.task_id }),
        );
      },
    },
  });

  /** 保存体：时点最新 raw+草稿四面（红线⑤ 双守口径——CanvasEditToolbar 同链）。 */
  const body =
    draft !== null && rawQuery.data !== undefined
      ? draftProjectRaw(rawQuery.data, draft)
      : null;

  const handleSave = () => {
    if (body === null || projectId === null) {
      return;
    }
    save.mutate(
      { projectId, data: body },
      {
        onSuccess: () => {
          store.getState().markSaved();
          void queryClient.invalidateQueries({
            queryKey: [`/api/projects/${projectId}`],
          });
          messageApi.success("图面已保存");
        },
        onError: (error) => {
          messageApi.error(
            error instanceof Error ? error.message : "保存失败",
          );
        },
      },
    );
  };

  const handleValidate = () => {
    if (projectId === null || (body === null && rawQuery.data === undefined)) {
      return;
    }
    setValidatePending(true);
    validate.mutate(
      { projectId, data: body ?? rawQuery.data },
      {
        onSuccess: (report) => {
          setValidatePending(false);
          if (report.valid && report.errors.length === 0) {
            messageApi.success("校验通过");
          } else {
            messageApi.warning(
              `校验 ${report.errors.length} 项警告——${report.errors[0] ?? ""}`,
            );
          }
        },
        onError: (error) => {
          setValidatePending(false);
          messageApi.error(
            error instanceof Error ? error.message : "校验失败",
          );
        },
      },
    );
  };

  const handleRunCalc = async () => {
    if (projectId === null) {
      return;
    }
    const decision = decideRunCalc(dirty, body, paramDraftCount);
    if (decision === "block-param-draft") {
      messageApi.warning(paramDraftBlockMessage(paramDraftCount));
      return;
    }
    if (decision === "block-unready") {
      messageApi.error("项目数据未就绪——稍候重试");
      return;
    }
    try {
      if (decision === "save-run") {
        if (body === null) {
          return;
        }
        await save.mutateAsync({ projectId, data: body });
        store.getState().markSaved();
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
      }
      run.mutate(
        {
          data: {
            project_id: projectId,
            ...(draft !== null
              ? draft.checkedUnits.length > 0
                ? { conditions: draft.checkedUnits }
                : {}
              : rawQuery.data !== undefined &&
                  rawCheckedUnits(rawQuery.data).length > 0
                ? { conditions: rawCheckedUnits(rawQuery.data) }
                : {}),
          },
        },
        {
          onError: (error: WaterprintApiError) => {
            messageApi.error(
              error instanceof Error ? error.message : "提交计算失败",
            );
          },
        },
      );
    } catch {
      messageApi.error("保存失败——未提交计算（请检查网络/锁冲突后重试）");
    }
  };

  return (
    <header className="wp-v4-band" data-region="zone-band">
      {contextHolder}
      <BandLogo />
      <nav className="wp-v4-mods">
        {V4_ZONES.map((zone) => (
          <button
            key={zone}
            type="button"
            className={`wp-v4-mod${target.zone === zone ? " on" : ""}`}
            data-zone={zone}
            data-testid={`wp-v4-zone-${zone}`}
            onClick={() =>
              onZoneChange(
                zone === target.zone
                  ? target
                  : ({ zone } as V4ZoneTarget),
              )
            }
          >
            {V4_ZONE_LABELS[zone]}
          </button>
        ))}
      </nav>
      <span className="wp-v4-tools">
        <Tooltip title="保存">
          <Button
            type="text"
            size="small"
            icon={<SaveOutlined />}
            aria-label="保存"
            data-testid="wp-v4-save"
            disabled={projectId === null || !dirty || body === null}
            loading={save.isPending}
            onClick={handleSave}
          />
        </Tooltip>
        <Tooltip title="撤销">
          <Button
            type="text"
            size="small"
            icon={<UndoOutlined />}
            aria-label="撤销"
            disabled
            data-testid="wp-v4-undo"
          />
        </Tooltip>
        <Tooltip title="重做">
          <Button
            type="text"
            size="small"
            icon={<RedoOutlined />}
            aria-label="重做"
            disabled
            data-testid="wp-v4-redo"
          />
        </Tooltip>
        <Tooltip title="校验">
          <Button
            type="text"
            size="small"
            icon={<SafetyCertificateOutlined />}
            aria-label="校验"
            data-testid="wp-v4-validate"
            disabled={
              projectId === null ||
              (body === null && rawQuery.data === undefined)
            }
            loading={validate.isPending || validatePending}
            onClick={handleValidate}
          />
        </Tooltip>
        <Tooltip title="全项目计算">
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            aria-label="全项目计算"
            data-testid="wp-v4-run"
            disabled={projectId === null}
            loading={run.isPending || rawQuery.isLoading}
            onClick={() => void handleRunCalc()}
          />
        </Tooltip>
      </span>
    </header>
  );
}
