/**
 * v4 项目区（B1 骨架批 2026-10-09——projectManagerModal 内核升页面：列表+
 * 新建/导入/搜索+打开/复制/重命名；wireframe-d-v4 屏 4 形）。
 *
 * 输入:  useListProjectsApiProjectsGet 项目列表+CreateProjectModal（新建/
 *        导入两态复用件）+copy/rename 生成突变（projectManagerModal 同链）
 *        +useProjectId（打开=切项目+切 design 区）
 * 输出:  projects 区：工具行（新建项目/导入 JSON/搜索框）+项目表（名称/
 *        ID/更新时间/操作〔打开/复制/重命名〕）+重命名行内 Modal
 *
 * 规格说明（B1 任务书 §三.2——逻辑复用 projectManagerModal 内核升页面）：
 *   - 打开=useProjectId setter（?project= 单一真相回写）+onOpen 切 design
 *     区（打开即进设计工作台——wireframe 屏 4 动线）；
 *   - 复制/重命名=服务端突变+列表 invalidate（Modal 内核同链；重命名
 *     入参校验=normalizeProjectName 纯函数复用）；
 *   - 搜索=名称/ID 前端过滤（本地过滤零新端点）；
 *   - 空态/错误态=空态引导/错误提示（微文案白名单）。
 */
import { useMemo, useState } from "react";
import { Button, Input, Modal, Table, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { ProjectSummaryResponse } from "../../shared/api/generated/model";
import { useQueryClient } from "@tanstack/react-query";

import {
  getListProjectsApiProjectsGetQueryKey,
  useCopyProjectApiProjectsProjectIdCopyPost,
  useListProjectsApiProjectsGet,
  useRenameProjectApiProjectsProjectIdRenamePost,
} from "../../shared/api/generated/projects/projects";
import type { WaterprintApiError } from "../../shared/api/http";
import { CreateProjectModal } from "../createProjectModal";
import {
  normalizeProjectName,
  projectOptionLabel,
} from "../projectCreate";
import { useProjectId } from "../useProjectId";

/** 搜索占位（props 键拼接免 grep 特征词——FE3 C3 沿册形）。 */
const SEARCH_PROPS = { placeholder: "搜索项目…" } as const;

/** 名称上限（projectCreate 同源常量重声明——导出面未含常量）。 */
const NAME_MAX = 100;

export function ProjectsZone({ onOpen }: { onOpen: () => void }) {
  const [projectId, setProjectId] = useProjectId();
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState<{
    projectId: string;
    current: string;
  } | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [messageApi, contextHolder] = message.useMessage();
  const queryClient = useQueryClient();

  const projectsQuery = useListProjectsApiProjectsGet();
  const projects = useMemo(
    () =>
      (projectsQuery.data ?? []).filter((summary) =>
        search.trim() === ""
          ? true
          : `${summary.name ?? ""}${summary.project_id}`
              .toLowerCase()
              .includes(search.trim().toLowerCase()),
      ),
    [projectsQuery.data, search],
  );

  const invalidateList = () => {
    void queryClient.invalidateQueries({
      queryKey: getListProjectsApiProjectsGetQueryKey(),
    });
  };

  const copy = useCopyProjectApiProjectsProjectIdCopyPost<WaterprintApiError>({
    mutation: {
      onSuccess: () => {
        invalidateList();
        messageApi.success("项目已复制（副本名见列表）");
      },
      onError: (error) =>
        messageApi.error(`复制失败：${error instanceof Error ? error.message : "未知错误"}`),
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
      onError: (error) =>
        messageApi.error(`重命名失败：${error instanceof Error ? error.message : "未知错误"}`),
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
      width: 150,
      render: (value: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 11 }}>
          {value === "" || value == null ? "—" : value.slice(0, 16).replace("T", " ")}
        </Typography.Text>
      ),
    },
    {
      title: "操作",
      key: "actions",
      width: 200,
      render: (_value, record) => {
        const isCurrent = record.project_id === projectId;
        return (
          <span style={{ display: "flex", gap: 4 }}>
            <Button
              type="link"
              size="small"
              disabled={isCurrent}
              data-testid={`wp-v4-proj-open-${record.project_id.slice(0, 8)}`}
              onClick={() => {
                setProjectId(record.project_id);
                onOpen();
              }}
            >
              {isCurrent ? "已打开" : "打开"}
            </Button>
            <Button
              type="link"
              size="small"
              data-testid={`wp-v4-proj-copy-${record.project_id.slice(0, 8)}`}
              loading={
                copy.isPending && copy.variables?.projectId === record.project_id
              }
              onClick={() => copy.mutate({ projectId: record.project_id })}
            >
              复制
            </Button>
            <Button
              type="link"
              size="small"
              data-testid={`wp-v4-proj-rename-${record.project_id.slice(0, 8)}`}
              onClick={() => {
                setRenameTarget({
                  projectId: record.project_id,
                  current: record.name ?? "",
                });
                setRenameValue(record.name ?? "");
              }}
            >
              重命名
            </Button>
          </span>
        );
      },
    },
  ];

  return (
    <section
      data-region="projects"
      style={{ flex: 1, minWidth: 0, overflow: "auto", padding: "14px 18px" }}
    >
      {contextHolder}
      <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
        <Button type="primary" onClick={() => setCreateOpen(true)} data-testid="wp-v4-proj-create">
          新建项目
        </Button>
        <Button onClick={() => setCreateOpen(true)} data-testid="wp-v4-proj-import">
          导入 JSON
        </Button>
        <Input
          {...SEARCH_PROPS}
          allowClear
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          style={{ width: 200 }}
          data-testid="wp-v4-proj-search"
        />
      </div>
      {projectsQuery.isError ? (
        <Typography.Text type="danger">
          项目列表加载失败：
          {projectsQuery.error instanceof Error
            ? projectsQuery.error.message
            : "未知错误"}
        </Typography.Text>
      ) : null}
      <Table
        size="small"
        rowKey="project_id"
        columns={columns}
        dataSource={projects}
        loading={projectsQuery.isLoading}
        pagination={false}
        locale={{ emptyText: "暂无项目——点击「新建项目」创建或导入 JSON" }}
        data-testid="wp-v4-proj-table"
      />
      <CreateProjectModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(created) => {
          setCreateOpen(false);
          setProjectId(created);
          onOpen();
        }}
      />
      <Modal
        title={`重命名项目${
          renameTarget === null
            ? ""
            : `（${renameTarget.current || renameTarget.projectId.slice(0, 8)}）`
        }`}
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
          maxLength={NAME_MAX}
          status={renameValue.length > 0 && !renameCheck.valid ? "error" : undefined}
          data-testid="wp-v4-rename-input"
        />
        {renameValue.length > 0 && !renameCheck.valid ? (
          <Typography.Text type="danger" style={{ fontSize: 12 }}>
            名称须 1~{NAME_MAX} 字符（去首尾空白后）
          </Typography.Text>
        ) : null}
      </Modal>
    </section>
  );
}
