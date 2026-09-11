/**
 * 画布编辑工具条（P0-3——task-c2-edit-plan §一.4/一.5 落位件）。
 *
 * 输入:  projectId+useProjectQuery raw（保存/校验体非 design 面基座——
 *        时点最新）+canvasStore 编辑会话 selector（editing/dirty/draft）
 * 输出:  工具条两态：只读=[编辑][提交计算]；编辑=[退出编辑][校验]
 *        [保存][提交计算]+未保存徽标+校验结果 Alert（⑦甲：警告放行
 *        ——validate 仅提示不阻断保存）
 *
 * 规格说明（task-c2-edit-plan 呈裁⑤⑥⑦+红线③⑤）：
 *   - 呈裁⑤ 显式「编辑」钮=编辑会话开关挂点（beginEdit 快照摄入/
 *      退出带 dirty Popconfirm 二次确认——误退护）；
 *   - 呈裁⑥ 常驻「提交计算」（不依赖选中+dirty——F4 残余根治）：
 *      dirty 时先保存再提交（mutateAsync 链——保存失败即止不计算）；
 *      成功镜像 AssumptionsPanel：?task= 回写+TASK_EVENT 派发（六标签
 *      联动）；conditions=受检单元清单（编辑态草稿面/只读态 raw 面）；
 *   - 呈裁⑦ 校验失败=警告放行（校验钮独立呈报 core 结构发现——
 *      Alert warning 非阻断；保存钮不看校验结果）；
 *   - 红线⑤：保存体=时点最新 raw 的非 design 面+草稿 design 面
 *      （快照隔离不回流+不回写陈旧面双守）；保存成功 markSaved 基座
 *      复归+失效项目键（缩略图/参数面随 refetch 刷新）。
 */
import { useEffect, useState } from "react";
import { Alert, Button, Popconfirm, Typography, message } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { useProjectQuery } from "../features/canvas/api/useProjectQuery";
import { draftProjectRaw } from "../features/canvas/lib/designWriter";
import {
  useCanvasStore,
  useDirty,
  useDraft,
  useEditing,
} from "../features/canvas/store/canvasStore";
import { useRunCalculationApiCalcRunPost } from "../shared/api/generated/calc/calc";
import {
  useSaveProjectApiProjectsProjectIdPut,
  useValidateProjectApiProjectsProjectIdValidatePost,
} from "../shared/api/generated/projects/projects";
import type { WaterprintApiError } from "../shared/api/http";
import { TASK_EVENT } from "../shared/events";

/** 校验结果态（⑦甲——null=未校验；valid=true 成功态文案行）。 */
type ValidateReport = { valid: boolean; errors: string[] } | null;

/** raw design.checked_units 宽容读取（constraintPicker.rawCheckedUnits 同口径）。 */
function rawCheckedUnits(raw: unknown): string[] {
  if (typeof raw !== "object" || raw === null) {
    return [];
  }
  const design = (raw as Record<string, unknown>)["design"];
  if (typeof design !== "object" || design === null) {
    return [];
  }
  const checked = (design as Record<string, unknown>)["checked_units"];
  return Array.isArray(checked) ? checked.filter((id): id is string => typeof id === "string") : [];
}

export function CanvasEditToolbar({ projectId }: { projectId: string }) {
  const editing = useEditing(projectId);
  const dirty = useDirty(projectId);
  const draft = useDraft(projectId);
  const rawQuery = useProjectQuery(projectId);
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [report, setReport] = useState<ValidateReport>(null);
  const store = useCanvasStore;

  // 草稿变更即清陈旧校验报告（报告只对当次草稿版本有效）
  useEffect(() => {
    setReport(null);
  }, [draft]);

  const validate = useValidateProjectApiProjectsProjectIdValidatePost();
  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>();
  const run = useRunCalculationApiCalcRunPost<WaterprintApiError>({
    mutation: {
      onSuccess: (outcome) => {
        // AssumptionsPanel D4 同构：?task= 回写+TASK_EVENT（六标签联动）
        const search = new URLSearchParams(window.location.search);
        search.set("task", outcome.task_id);
        window.history.replaceState(
          null,
          "",
          `${window.location.pathname}?${search.toString()}`,
        );
        window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: outcome.task_id }));
      },
    },
  });

  /** 保存/校验体：时点最新 raw+草稿四面（红线⑤ 双守口径）。 */
  const body =
    draft !== null && rawQuery.data !== undefined
      ? draftProjectRaw(rawQuery.data, draft)
      : null;

  const runCalc = async () => {
    if (body === null) {
      return;
    }
    try {
      if (dirty) {
        await save.mutateAsync({ projectId, data: body });
        store.getState().markSaved();
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
        messageApi.success("已保存");
      }
      run.mutate(
        {
          data: {
            project_id: projectId,
            // GD-N-01（A 二审）：编辑态恒用草稿受检面——删除受检单元致
            // 空清单时**不回退** raw（旧清单会算入已删单元）；只读态才读 raw
            ...(draft !== null
              ? draft.checkedUnits.length > 0
                ? { conditions: draft.checkedUnits }
                : {}
              : rawQuery.data !== undefined && rawCheckedUnits(rawQuery.data).length > 0
                ? { conditions: rawCheckedUnits(rawQuery.data) }
                : {}),
          },
        },
        {
          onError: (error: WaterprintApiError) => {
            messageApi.error(error instanceof Error ? error.message : "提交计算失败");
          },
        },
      );
    } catch {
      // GD-N-02（A 二审）：保存失败显式呈报（mutateAsync 无 per-call
      // onError——静默即用户不知未计算）
      messageApi.error("保存失败——未提交计算（请检查网络/锁冲突后重试）");
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 10px",
        borderBottom: "1px solid var(--wp-border)",
        background: "var(--wp-bg-elevated)",
        flexWrap: "wrap",
      }}
    >
      {contextHolder}
      {editing ? (
        <>
          <Popconfirm
            title="放弃未保存的修改？"
            description="退出编辑将丢弃草稿中未保存的变更。"
            okText="放弃修改"
            cancelText="继续编辑"
            disabled={!dirty}
            okButtonProps={{ danger: true }}
            onConfirm={() => store.getState().endEdit()}
          >
            <Button onClick={() => (dirty ? undefined : store.getState().endEdit())}>
              退出编辑
            </Button>
          </Popconfirm>
          <Button
            disabled={body === null}
            loading={validate.isPending}
            onClick={() => {
              if (body === null) {
                return;
              }
              validate.mutate(
                { projectId, data: body },
                {
                  onSuccess: (response) => {
                    setReport({ valid: response.valid, errors: response.errors });
                  },
                  onError: () => {
                    setReport({ valid: false, errors: ["校验请求失败（服务不可达或载荷非法）"] });
                  },
                },
              );
            }}
          >
            校验
          </Button>
          <Button
            type="primary"
            disabled={!dirty || body === null}
            loading={save.isPending}
            onClick={() => {
              if (body === null) {
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
                    messageApi.success("已保存");
                  },
                  onError: (error) => {
                    messageApi.error(
                      error instanceof Error ? error.message : "保存失败",
                    );
                  },
                },
              );
            }}
          >
            保存{dirty ? "（有修改）" : ""}
          </Button>
        </>
      ) : (
        <Button
          type="primary"
          disabled={rawQuery.data === undefined}
          onClick={() => {
            if (rawQuery.data !== undefined) {
              store.getState().beginEdit(projectId, rawQuery.data);
            }
          }}
        >
          编辑
        </Button>
      )}
      {/* 呈裁⑥ 常驻提交计算（不依赖选中/dirty——dirty 时先存后算） */}
      <Button loading={run.isPending} onClick={() => void runCalc()}>
        提交计算
      </Button>
      {editing && dirty && (
        <Typography.Text type="warning" style={{ fontSize: 12 }}>
          未保存修改
        </Typography.Text>
      )}
      {editing && !dirty && (
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          编辑中：左侧单元库可添加单元；拖拽端口连线；✕/Delete 删除
        </Typography.Text>
      )}
      {report !== null && (
        <Alert
          style={{ marginTop: 4, width: "100%" }}
          type={report.valid ? "success" : "warning"}
          showIcon
          title={report.valid ? "结构校验通过" : "结构校验发现以下问题（不阻断保存——中间态合法）"}
          description={
            report.errors.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {report.errors.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : undefined
          }
        />
      )}
    </div>
  );
}
