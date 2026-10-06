/**
 * 画布编辑工具条（P0-3——task-c2-edit-plan §一.4/一.5 落位件；M1 批
 * 2026-10-06 解构：提交计算/校验迁顶栏 Ribbon〔app/ribbon〕——本件=槽内
 * 工具条两态闭环维持：只读=[编辑]；编辑=[退出编辑][保存]+未保存提示）。
 *
 * 输入:  projectId+useProjectQuery raw（保存体非 design 面基座——时点
 *        最新）+canvasStore 编辑会话 selector（editing/dirty/draft）
 * 输出:  工具条两态：只读=[编辑]；编辑=[退出编辑（Popconfirm 误退护）]
 *        [保存（paramDraftCount 徽标+notifySaved 诚实口径）]+未保存提示
 *        两文案行
 *
 * 规格说明（task-c2-edit-plan 呈裁⑤+红线⑤；R2-P1-3；M1 批沿革
 *   P0-3→M1 解构——Ribbon 四命令定版后两裁量位〔编辑开关/保存〕留槽内，
 *   提交计算钮+runCalc 全链+validate 链+report Alert 迁 app/ribbon.tsx；
 *   decideRunCalc/paramDraftBlockMessage 纯函数同迁〔测试随迁 import〕）：
 *   - 呈裁⑤ 显式「编辑」钮=编辑会话开关挂点（beginEdit 快照摄入/
 *      退出带 dirty Popconfirm 二次确认——误退护）；
 *   - 红线⑤：保存体=时点最新 raw 的非 design 面+草稿 design 面
 *      （快照隔离不回流+不回写陈旧面双守）；保存成功 markSaved 基座
 *      复归+失效项目键（缩略图/参数面随 refetch 刷新）；
 *   - R2-P1-3：保存钮挂参数草稿徽标——「已保存」语义陷阱根治面（草稿
 *      正门=参数面板「提交重算」，保存只走图面；提交流程归 Ribbon 唯一
 *      入口〔dirty 先存后算链在 ribbon.runCalc〕）。
 */
import { Badge, Button, Popconfirm, Typography, message } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { useProjectQuery } from "../features/canvas/api/useProjectQuery";
import { draftProjectRaw } from "../features/canvas/lib/designWriter";
import {
  useCanvasStore,
  useDirty,
  useDraft,
  useEditing,
} from "../features/canvas/store/canvasStore";
import { useParamsStore } from "../features/params/store/paramsStore";
import {
  useSaveProjectApiProjectsProjectIdPut,
} from "../shared/api/generated/projects/projects";
import type { WaterprintApiError } from "../shared/api/http";

export function CanvasEditToolbar({ projectId }: { projectId: string }) {
  const editing = useEditing(projectId);
  const dirty = useDirty(projectId);
  const draft = useDraft(projectId);
  const rawQuery = useProjectQuery(projectId);
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const store = useCanvasStore;
  // R2-P1-3（round2 批2 扩）：参数面板未提交草稿计数（保存语义诚实化）
  const paramDraftCount = useParamsStore((s) => s.draftHint[projectId] ?? 0);
  /** 保存 toast 诚实口径：参数草稿不随图面保存走（正门=参数面板提交重算） */
  const notifySaved = () => {
    if (paramDraftCount > 0) {
      messageApi.warning(
        `图面已保存——参数草稿 ${paramDraftCount} 项未随存，请在参数面板「提交重算」`,
      );
      return;
    }
    messageApi.success("已保存");
  };

  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>();

  /** 保存体：时点最新 raw+草稿四面（红线⑤ 双守口径）。 */
  const body =
    draft !== null && rawQuery.data !== undefined
      ? draftProjectRaw(rawQuery.data, draft)
      : null;

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
          {/* R2-P1-3：参数草稿未提交时保存钮挂徽标——「已保存」语义陷阱
              根治面（草稿正门=参数面板「提交重算」，保存只走图面） */}
          <Badge
            count={paramDraftCount}
            size="small"
            offset={[-4, 0]}
            title="参数草稿不随保存提交——请在参数面板「提交重算」"
          >
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
                      notifySaved();
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
          </Badge>
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
    </div>
  );
}
