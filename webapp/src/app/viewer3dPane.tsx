/**
 * viewer3d 标签页装配：懒加载 Scene+ErrorBoundary 包裹+projectId 空态选择。
 *
 * 输入:  URL ?project= 参数（初值 parseProjectParam 直读 location.search）
 *        +useListProjectsApiProjectsGet 项目列表（shared 生成 hook）
 * 输出:  三维视图标签页（空态项目选择器 / 懒加载 R3F Scene 隔离边界）
 *
 * 规格说明（FE3 批 6b 段一，D5/D8）：
 *   - projectId 单一真相=URL：初值经 parseProjectParam；用户经空态下拉
 *     选择后 history.replaceState 同步回 URL（withProjectParam 不清其余
 *     参数）——deep-link 可分享；
 *   - 空态=AntD Select：选项来自 GET /api/projects（app 层直用 shared
 *     生成 hook 合法）；列表 id 带 ".wp" 尾缀（服务端 path.stem 现状）
 *     而场景端点按裸 id 解析——Select 值剥尾缀归一（真服务探针实证
 *     /api/scene/<id>.wp 422；服务端根治挂账）；列表空/查询失败=指引
 *     文案（先经 CLI/API 建项目——docs/user-manual.md §3 五步链
 *     「建项目→提交计算→看方案→三维场景→出审计报告」）；
 *   - conditionKey 不暴露（服务端排序首键回显 R1/R2 语义——Scene 缺省
 *     不传）；取数/错误/加载态 Scene 自渲染（薄壳不重复做错误态）；
 *   - 懒加载：React.lazy 动态 import Scene（vite manualChunks three 已配
 *     ——§12.6 独立 chunk 与画布互不干扰）+Suspense 薄壳；
 *   - ErrorBoundary 逐面板隔离（label=三维视图——渲染崩溃不清空应用）。
 */
import { lazy, Suspense, useState } from "react";
import { Select, Typography } from "antd";

import { useListProjectsApiProjectsGet } from "../shared/api/generated/projects/projects";
import { ErrorBoundary } from "./ErrorBoundary";
import { parseProjectParam, withProjectParam } from "./projectParam";

// 懒加载：Scene（含 three/R3F）走独立异步 chunk（§12.6——不进首屏 bundle）
const Scene = lazy(() =>
  import("../features/viewer3d/components/Scene").then((module) => ({
    default: module.Scene,
  })),
);

/** 空态指引（docs/user-manual.md §3 五步链——先建项目再提交计算）。 */
const EMPTY_GUIDE =
  "暂无项目可加载：请先创建项目并提交计算（CLI 或 API：POST /api/projects → POST /api/calc/run，见 docs/user-manual.md「快速开始」五步链），完成后刷新本页。";

export function Viewer3dPane() {
  const [projectId, setProjectId] = useState<string | null>(() =>
    parseProjectParam(window.location.search),
  );
  // 空态才拉列表（projectId 已定=deep-link 直进场景，省一次列表请求）
  const projectsQuery = useListProjectsApiProjectsGet({
    query: { enabled: projectId === null },
  });

  if (projectId !== null) {
    return (
      <ErrorBoundary label="三维视图">
        <Suspense fallback={<div>三维视图加载中…</div>}>
          <Scene projectId={projectId} />
        </Suspense>
      </ErrorBoundary>
    );
  }

  const projects = projectsQuery.data ?? [];
  return (
    <div>
      <Typography.Paragraph>请选择要加载三维场景的项目：</Typography.Paragraph>
      <Select
        style={{ minWidth: 280 }}
        loading={projectsQuery.isLoading}
        status={projectsQuery.isError ? "error" : undefined}
        options={projects.map((summary) => ({
          // 列表 id 现状带 ".wp" 尾缀（服务端 path.stem 面），场景/读取
          // 端点按裸 id 解析（.wp.json 后缀服务端内部拼——探针实证
          // /api/scene/<id>.wp 422）；Select 值在此归一，服务端根治挂账
          value: summary.project_id.replace(/\.wp$/, ""),
          label: summary.project_id.replace(/\.wp$/, ""),
        }))}
        onChange={(value) => {
          setProjectId(value);
          // D5：同步回 URL（replaceState 不留历史记录、不清其余参数）
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
