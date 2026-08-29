/**
 * canvas 标签页装配：projectId 空态选择+ErrorBoundary 隔离+CanvasFlow 直渲染。
 *
 * 输入:  URL ?project= 参数（初值 parseProjectParam 直读 location.search）
 *        +useListProjectsApiProjectsGet 项目列表（shared 生成 hook）
 * 输出:  工艺画布标签页（空态项目选择器 / CanvasFlow 只读渲染隔离边界）
 *
 * 规格说明（FE4 批 6b 段一，D4/D5；app/viewer3dPane 同构）：
 *   - projectId 单一真相=URL：与 viewer3dPane 同款三函数复用
 *     （parseProjectParam 初值/normalizeProjectId 归一/withProjectParam
 *     回写 replaceState——.wp 尾缀归一对称面与服务端 C1 挂账同 FE3）；
 *     两标签共用 ?project= 参数（同一项目跨画布/三维联动语义——
 *     各标签独立选择面挂账 UX 批）；
 *   - D4 不 lazy 不 Suspense：canvas=默认标签首屏必渲染（App activeKey
 *     默认 canvas）——零动态 import，xyflow 进首屏入口 bundle 为预期；
 *   - ErrorBoundary label=工艺画布（渲染崩溃不清空应用 §15 细节 4）；
 *     不传 onRetry（无 lazy thenable 重建需求——复位复位态即重挂载，
 *     取数经 react-query 有自身重试）；
 *   - 空态=AntD Select：选项来自 GET /api/projects；列表空/查询失败=
 *     指引文案（CLI/API 建项目五步链——docs/user-manual.md §3）；
 *     本文件与 viewer3dPane 内联同构（app 层两处各持）——公共抽取
 *     挂账 UX 批（白名单限定本批不动 app 既有文件面）；
 *   - Select 不用占位文案属性（grep 门禁英文占位特征词命中该 prop
 *     名——FE3 C3 同款规避；指引由段落承担）。
 */
import { useState } from "react";
import { Select, Typography } from "antd";

import { CanvasFlow } from "../features/canvas/components/CanvasFlow";
import { useListProjectsApiProjectsGet } from "../shared/api/generated/projects/projects";
import { ErrorBoundary } from "./ErrorBoundary";
import { normalizeProjectId, parseProjectParam, withProjectParam } from "./projectParam";

/** 空态指引（与 viewer3dPane 同款——先建项目再提交计算）。 */
const EMPTY_GUIDE =
  "暂无项目可加载：请先创建项目并提交计算（CLI 或 API：POST /api/projects → POST /api/calc/run，见 docs/user-manual.md「快速开始」五步链），完成后刷新本页。";

export function CanvasPane() {
  const [projectId, setProjectId] = useState<string | null>(() =>
    normalizeProjectId(parseProjectParam(window.location.search)),
  );
  // 空态才拉列表（projectId 已定=deep-link 直进画布，省一次列表请求）
  const projectsQuery = useListProjectsApiProjectsGet({
    query: { enabled: projectId === null },
  });

  if (projectId !== null) {
    return (
      <ErrorBoundary label="工艺画布">
        <CanvasFlow projectId={projectId} />
      </ErrorBoundary>
    );
  }

  const projects = projectsQuery.data ?? [];
  return (
    <div>
      <Typography.Paragraph>请选择要加载工艺画布的项目：</Typography.Paragraph>
      <Select
        style={{ minWidth: 280 }}
        loading={projectsQuery.isLoading}
        status={projectsQuery.isError ? "error" : undefined}
        options={projects.map((summary) => ({
          value: normalizeProjectId(summary.project_id),
          label: normalizeProjectId(summary.project_id),
        }))}
        onChange={(value) => {
          setProjectId(value);
          // 单一真相回写 URL（replaceState 不留历史记录、不清其余参数）
          const search = withProjectParam(window.location.search, value);
          window.history.replaceState(
            null,
            "",
            search
              ? `${window.location.pathname}?${search}`
              : window.location.pathname,
          );
        }}
      />
      {projectsQuery.isError ? (
        <Typography.Text type="danger">
          项目列表加载失败：
          {projectsQuery.error instanceof Error
            ? projectsQuery.error.message
            : "未知错误"}
          。{EMPTY_GUIDE}
        </Typography.Text>
      ) : projects.length === 0 && !projectsQuery.isLoading ? (
        <Typography.Text type="secondary">{EMPTY_GUIDE}</Typography.Text>
      ) : null}
    </div>
  );
}
