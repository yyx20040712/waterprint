/**
 * 项目管理 Modal（P2 生命周期治理 L3）：项目列表 Table+行级治理操作。
 *
 * 输入:  open/onClose 受控态（Header 钮+canvasPane 空态双入口同件）
 * 输出:  Modal（Table 列表+打开/重命名/复制/删除行操作+新建/刷新头部
 *        钮；POST copy/rename + DELETE /api/projects/{id}）
 *
 * 规格说明（briefs/task-p2-lifecycle-plan.md §一 L3/L4——2026-09-12）：
 *   - 治理面单源：Header「项目管理」钮（文件夹图标常驻）+canvasPane
 *     空态「管理项目」钮双入口同开本件——空态 Select 快速打开路径保留；
 *   - 行操作：打开（当前项目 disabled——projectId 上下文指示）/重命名
 *     （嵌套 Modal+normalizeProjectName 校验[P0-1 纯函数复用——红线①
 *     FE 零第二业务源，长度上限同 core ViewState.name]）/复制（服务面
 *     副本名递增制——成功后列表刷新即见新名）/删除（Popconfirm danger
 *     名称回显——不可逆双保险，服务面三守卫红线③）；
 *   - 突变后 invalidate 项目列表（getListProjects 同键缓存）；删除当前
 *     项目=useProjectId setter(null) 回空态（pane 查询随 ?project= 剥离
 *     停拉——S3 单一真相面）；
 *   - 守卫错误透传用户语（404 并发已删/409 锁或在途任务——server detail
 *     面消息直呈，禁吞错）。
 */
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  FolderOpenOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { Button, Input, Modal, Popconfirm, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";

import {
  getListProjectsApiProjectsGetQueryKey,
  useCopyProjectApiProjectsProjectIdCopyPost,
  useDeleteProjectApiProjectsProjectIdDelete,
  useListProjectsApiProjectsGet,
  useRenameProjectApiProjectsProjectIdRenamePost,
} from "../shared/api/generated/projects/projects";
import type { ProjectSummaryResponse } from "../shared/api/generated/model";
import { WaterprintApiError } from "../shared/api/http";
import { CreateProjectModal } from "./createProjectModal";
import { useProjectId } from "./useProjectId";
import { PROJECT_NAME_MAX, normalizeProjectName, projectOptionLabel } from "./projectCreate";

/** 重命名目标（null=嵌套 Modal 关态）。 */
type RenameTarget = { projectId: string; current: string };

/** 时间戳显示格式（ISO → 短式直显——PL-N-07 R2 口径注记：UTC 不做
 * 本地化换算[单用户工程工具·与后端日志同钟]，纯显示层变换；P2 测试锁）。 */
export function formatTimestamp(iso: string): string {
  return iso.length > 16 ? `${iso.slice(0, 10)} ${iso.slice(11, 16)}` : iso;
}

export function ProjectManagerModal({
  open,
  onClose,
}: {
  /** 开态（双入口写方持有）。 */
  open: boolean;
  /** 关闭回调。 */
  onClose: () => void;
}) {
  const [projectId, setProjectId] = useProjectId();
  const [renameTarget, setRenameTarget] = useState<RenameTarget | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const queryClient = useQueryClient();

  const projectsQuery = useListProjectsApiProjectsGet({
    query: { enabled: open },
  });
  const projects = projectsQuery.data ?? [];

  /** 突变后统一失效列表（行增删改名即见）。 */
  function invalidateList() {
    void queryClient.invalidateQueries({
      queryKey: getListProjectsApiProjectsGetQueryKey(),
    });
  }

  function errorMessage(error: unknown): string {
    return error instanceof Error ? error.message : "未知错误";
  }

  const copy = useCopyProjectApiProjectsProjectIdCopyPost<WaterprintApiError>({
    mutation: {
      onSuccess: () => {
        invalidateList(); // 副本名经列表刷新呈现（SaveOutcome 无 name 面）
        messageApi.success("项目已复制（副本名见列表）");
      },
      onError: (error) => messageApi.error(`复制失败：${errorMessage(error)}`),
    },
  });
  const rename = useRenameProjectApiProjectsProjectIdRenamePost<WaterprintApiError>({
    mutation: {
      onSuccess: (_outcome, variables) => {
        invalidateList();
        messageApi.success(`已重命名为「${variables.data.name}」`);
        setRenameTarget(null);
        setRenameValue("");
      },
      onError: (error) => messageApi.error(`重命名失败：${errorMessage(error)}`),
    },
  });
  const remove = useDeleteProjectApiProjectsProjectIdDelete<WaterprintApiError>({
    mutation: {
      onSuccess: (_outcome, variables) => {
        invalidateList();
        messageApi.success("项目已删除");
        if (variables.projectId === projectId) {
          setProjectId(null); // 删除当前项目→回空态（?project= 剥离）
        }
      },
      onError: (error) => messageApi.error(`删除失败：${errorMessage(error)}`),
    },
  });

  const renameCheck = normalizeProjectName(renameValue);
  const columns: ColumnsType<ProjectSummaryResponse> = [
    {
      title: "名称",
      dataIndex: "name",
      render: (_value, record) =>
        projectOptionLabel(record.name ?? "", record.project_id),
    },
    {
      title: "ID",
      dataIndex: "project_id",
      width: 110,
      render: (value: string) => (
        <span title={value} style={{ fontFamily: "var(--wp-font-mono)", fontSize: 12 }}>
          {value.slice(0, 8)}
        </span>
      ),
    },
    {
      title: "更新时间",
      dataIndex: "view_timestamp",
      width: 130,
      render: (value: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {formatTimestamp(value)}
        </Typography.Text>
      ),
    },
    {
      title: "操作",
      key: "actions",
      width: 230,
      render: (_value, record) => {
        const isCurrent = record.project_id === projectId;
        return (
          <span style={{ display: "flex", gap: 4 }}>
            <Button
              type="link"
              size="small"
              disabled={isCurrent}
              data-testid={`wp-mgr-open-${record.project_id.slice(0, 8)}`}
              onClick={() => {
                setProjectId(record.project_id);
                onClose();
              }}
            >
              {isCurrent ? "已打开" : "打开"}
            </Button>
            <Button
              type="link"
              size="small"
              data-testid={`wp-mgr-rename-${record.project_id.slice(0, 8)}`}
              onClick={() => {
                setRenameTarget({ projectId: record.project_id, current: record.name ?? "" });
                setRenameValue(record.name ?? "");
              }}
            >
              重命名
            </Button>
            <Button
              type="link"
              size="small"
              loading={copy.isPending && copy.variables?.projectId === record.project_id}
              data-testid={`wp-mgr-copy-${record.project_id.slice(0, 8)}`}
              onClick={() => copy.mutate({ projectId: record.project_id })}
            >
              复制
            </Button>
            <Popconfirm
              title="删除项目"
              description={`确认删除「${projectOptionLabel(
                record.name ?? "",
                record.project_id,
              )}」？该操作不可恢复。`}
              okText="删除"
              okButtonProps={{ danger: true }}
              cancelText="取消"
              onConfirm={() => remove.mutate({ projectId: record.project_id })}
            >
              <Button
                type="link"
                size="small"
                danger
                data-testid={`wp-mgr-delete-${record.project_id.slice(0, 8)}`}
              >
                删除
              </Button>
            </Popconfirm>
          </span>
        );
      },
    },
  ];

  return (
    <Modal
      title={
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          项目管理
          <Tag style={{ marginInlineEnd: 0 }}>{projects.length} 个项目</Tag>
        </span>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={720}
      destroyOnHidden
      data-testid="wp-project-manager"
    >
      {contextHolder}
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <Button
          type="primary"
          icon={<FolderOpenOutlined />}
          onClick={() => setCreateOpen(true)}
        >
          新建项目
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => void projectsQuery.refetch()}
          loading={projectsQuery.isFetching}
        >
          刷新
        </Button>
        {projectsQuery.isError ? (
          <Typography.Text type="danger">
            项目列表加载失败：{errorMessage(projectsQuery.error)}
          </Typography.Text>
        ) : null}
      </div>
      <Table
        size="small"
        rowKey="project_id"
        columns={columns}
        dataSource={projects}
        loading={projectsQuery.isLoading}
        pagination={false}
        scroll={{ y: 320 }}
        locale={{ emptyText: "暂无项目——点击「新建项目」创建" }}
      />
      {/* 重命名嵌套 Modal（P0-1 纯函数校验——服务面 422 兜底） */}
      <Modal
        title={`重命名项目${renameTarget === null ? "" : `（${renameTarget.current || renameTarget.projectId.slice(0, 8)}）`}`}
        open={renameTarget !== null}
        onCancel={() => {
          setRenameTarget(null);
          setRenameValue("");
          rename.reset();
        }}
        onOk={() => {
          if (renameTarget === null || !renameCheck.valid) {
            return;
          }
          rename.mutate({
            projectId: renameTarget.projectId,
            data: { name: renameCheck.name },
          });
        }}
        okText="重命名"
        confirmLoading={rename.isPending}
        okButtonProps={{ disabled: !renameCheck.valid }}
        destroyOnHidden
      >
        <Input
          value={renameValue}
          onChange={(event) => setRenameValue(event.target.value)}
          maxLength={PROJECT_NAME_MAX}
          status={renameValue.length > 0 && !renameCheck.valid ? "error" : undefined}
          data-testid="wp-rename-input"
        />
        {renameValue.length > 0 && !renameCheck.valid ? (
          <Typography.Text type="danger" style={{ fontSize: 12 }}>
            名称须 1~{PROJECT_NAME_MAX} 字符（去首尾空白后）
          </Typography.Text>
        ) : null}
      </Modal>
      {/* 新建项目复用件（P0-1 CreateProjectModal——建后本件列表经 invalidate 刷新） */}
      <CreateProjectModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(created) => {
          setCreateOpen(false);
          void created; // 建后停留管理面（列表已刷新）——打开走行钮
        }}
      />
    </Modal>
  );
}
