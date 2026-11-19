/**
 * v4 顶栏（b2 壳重组批 2026-11-19——48px：品牌区+项目面包屑+右语境工具
 * 区；沿革 B1 顶带 zoneBand〔logo+六功能区页签+工具区〕——页签迁窄导航
 * 轨 navRail，工具区五钮逻辑逐字保持）。
 *
 * 输入:  useProjectId（工具区项目门）+useProjectName（面包屑项目名单源）
 * 输出:  顶栏：logo+WaterPrint 品牌+项目面包屑+工具区（保存/撤销/重做/
 *        校验/全项目计算——zoneBand 同链零改；data-region=top-bar）
 *
 * 规格说明（B1 任务书 §三.1 语境工具区——b2 批沿承；稿 topbar 段）：
 *   - 语境工具区四活一骨架：保存=手动（draftProjectRaw+PUT——CanvasEdit
 *     Toolbar 同链；草稿自动暂存 paramsStore 沿承）；校验=validate POST
 *     （结论呈现 message 即时反馈）；全项目计算=decideRunCalc 分派链
 *     复用（runCalcPolicy 导出纯函数——v1 批拆迁单源）；撤销/重做=画布
 *     引擎无撤销栈（骨架在场禁用态——实装挂账后续批）；
 *   - logo=简笔水滴线形 SVG（wireframe 屏 1 同形——stroke AC 色线性）；
 *   - 面包屑=项目 › 项目名（useProjectName 单源——未选=「未选择」，
 *     长名省略号+title 悬停全名；稿 .crumbs 形）；
 *   - 工具区五钮可见中文文字标签（v2 笔4——Button children 文本+fontSize
 *     11 字号三档内；图标/Tooltip/disabled/loading 语义全保持；撤销/
 *     重做恒禁用态加标签——撤销栈实装=在册挂账不在本批）。
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
import {
  decideRunCalc,
  paramDraftBlockMessage,
  rawCheckedUnits,
} from "../runCalcPolicy";
import { writeTaskParam } from "../solutionsUrlState";
import { useProjectId } from "../useProjectId";
import { useProjectName } from "../useProjectName";

/** logo 简笔水滴线形（wireframe 屏 1 同形——16×16 stroke AC）。 */
function BandLogo() {
  return (
    <span
      aria-hidden
      style={{
        width: 26,
        height: 26,
        border: "1.5px solid var(--wp-accent)",
        borderRadius: 6,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flex: "none",
      }}
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--wp-accent)" strokeWidth="1.4">
        <path d="M2 12c2-4 4-4 6-8 2 4 4 4 6 8" />
        <path d="M5 12h6" />
      </svg>
    </span>
  );
}

export function TopBar() {
  const [projectId] = useProjectId();
  // v2 笔3 同源：面包屑项目名单源（未选=null 显「未选择」；空白/缺名/
  // pending/失败=「未命名项目」回退——项目 hex 裸露消除）
  const projectName = useProjectName();
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
    <header className="wp-v4-band" data-region="top-bar">
      {contextHolder}
      <BandLogo />
      <span className="wp-v4-brand">WaterPrint</span>
      <div className="wp-v4-crumbs" data-testid="wp-v4-crumbs">
        <span style={{ color: "var(--wp-text-2)" }}>项目</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden style={{ color: "var(--wp-text-3)", flex: "none" }}>
          <path d="m8 10 4 4 4-4" />
        </svg>
        <strong
          title={projectName ?? undefined}
          style={{
            minWidth: 0,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            maxWidth: 320,
            fontWeight: 400,
          }}
        >
          {projectId === null ? "未选择" : projectName}
        </strong>
      </div>
      <span className="wp-v4-tools">
        <Tooltip title="保存">
          <Button
            type="text"
            size="small"
            icon={<SaveOutlined />}
            style={{ fontSize: 11 }} // v2 笔4：可见文字标签（字号三档内）
            aria-label="保存"
            data-testid="wp-v4-save"
            disabled={projectId === null || !dirty || body === null}
            loading={save.isPending}
            onClick={handleSave}
          >
            保存
          </Button>
        </Tooltip>
        <Tooltip title="撤销">
          <Button
            type="text"
            size="small"
            icon={<UndoOutlined />}
            style={{ fontSize: 11 }} // v2 笔4：恒禁用态加标签（撤销栈实装=在册挂账）
            aria-label="撤销"
            disabled
            data-testid="wp-v4-undo"
          >
            撤销
          </Button>
        </Tooltip>
        <Tooltip title="重做">
          <Button
            type="text"
            size="small"
            icon={<RedoOutlined />}
            style={{ fontSize: 11 }} // v2 笔4：恒禁用态加标签（重做栈实装=在册挂账）
            aria-label="重做"
            disabled
            data-testid="wp-v4-redo"
          >
            重做
          </Button>
        </Tooltip>
        <Tooltip title="校验">
          <Button
            type="text"
            size="small"
            icon={<SafetyCertificateOutlined />}
            style={{ fontSize: 11 }} // v2 笔4：可见文字标签（字号三档内）
            aria-label="校验"
            data-testid="wp-v4-validate"
            disabled={
              projectId === null ||
              (body === null && rawQuery.data === undefined)
            }
            loading={validate.isPending || validatePending}
            onClick={handleValidate}
          >
            校验
          </Button>
        </Tooltip>
        <Tooltip title="全项目计算">
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            style={{ fontSize: 11 }} // v2 笔4：可见文字标签（字号三档内）
            aria-label="全项目计算"
            data-testid="wp-v4-run"
            disabled={projectId === null}
            loading={run.isPending || rawQuery.isLoading}
            onClick={() => void handleRunCalc()}
          >
            全项目计算
          </Button>
        </Tooltip>
      </span>
    </header>
  );
}
