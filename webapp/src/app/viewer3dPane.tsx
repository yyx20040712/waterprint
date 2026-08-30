/**
 * viewer3d 标签页装配：懒加载 Scene+ErrorBoundary 包裹+projectId 空态选择。
 *
 * 输入:  URL ?project= 参数（useProjectId 共享 hook——S3 订阅面）
 *        +useListProjectsApiProjectsGet 项目列表（shared 生成 hook）
 * 输出:  三维视图标签页（空态项目选择器 / 懒加载 R3F Scene 隔离边界）
 *
 * 规格说明（FE3 批 6b 段一，D5/D8；R1/R2 补 2026-08-29；UX1 批 6b 段八
 *   S3 写方换 useProjectId hook）：
 *   - projectId 单一真相=URL：本 pane=写方（空态 Select onChange 经
 *     useProjectId setter——回写 replaceState+PROJECT_EVENT 写后派发
 *     一步收敛，S3 六 pane 订阅联动；deep-link 初值与 Select 选项共用
 *     normalizeProjectId 归一[.wp 尾缀——真服务探针实证 /api/scene/<id>.wp
 *     422；服务端根治挂账 C1]）；列表空/查询失败=指引文案（先经 CLI/API
 *     建项目——docs/user-manual.md §3 五步链「建项目→提交计算→看方案→
 *     三维场景→出审计报告」）；
 *   - 懒加载+chunk 失败重试（R1/一审 I-1）：React.lazy 的 thenable 跨挂载
 *     持久——动态 import 一旦 reject，复位边界重挂载不会重执行 import；
 *     故 lazy 持入组件 state，重试回调经 ErrorBoundary onRetry 以新 lazy
 *     实例重建 thenable（sceneLoader 模块级具名常量复用同一装载函数）；
 *     vite manualChunks three 已配——§12.6 独立 chunk 与画布互不干扰；
 *   - conditionKey 不暴露（服务端排序首键回显 R1/R2 语义）；取数/错误/
 *     加载态 Scene 自渲染（薄壳不重复做错误态）；
 *   - ErrorBoundary 逐面板隔离（label=三维视图——渲染崩溃不清空应用）。
 */
import { lazy, Suspense, useState } from "react";
import { Select, Typography } from "antd";

import { useListProjectsApiProjectsGet } from "../shared/api/generated/projects/projects";
import { ErrorBoundary } from "./ErrorBoundary";
import { normalizeProjectId } from "./projectParam";
import { useProjectId } from "./useProjectId";

/** Scene 动态 import 装载器（模块级具名常量——动态 import 表达式保持
 * check_webapp 动态 import 合法面；R1 重建 lazy 实例时复用本函数）。 */
const sceneLoader = () =>
  import("../features/viewer3d/components/Scene").then((module) => ({
    default: module.Scene,
  }));

/** 空态指引（docs/user-manual.md §3 五步链——先建项目再提交计算）。 */
const EMPTY_GUIDE =
  "暂无项目可加载：请先创建项目并提交计算（CLI 或 API：POST /api/projects → POST /api/calc/run，见 docs/user-manual.md「快速开始」五步链），完成后刷新本页。";

export function Viewer3dPane() {
  // S3 写方：hook setter 收敛回写 URL+派发（原 D5 三行 replaceState 内联退役）
  const [projectId, setProjectId] = useProjectId();
  // R1（一审 I-1）：lazy 持入 state——chunk 加载失败后以新 lazy 实例重建
  // thenable（模块级 lazy 单例的失败缓存跨挂载持久，复位重挂载无效）
  const [Scene, setScene] = useState(() => lazy(sceneLoader));
  // 空态才拉列表（projectId 已定=deep-link 直进场景，省一次列表请求）
  const projectsQuery = useListProjectsApiProjectsGet({
    query: { enabled: projectId === null },
  });

  if (projectId !== null) {
    return (
      <ErrorBoundary
        label="三维视图"
        onRetry={() => setScene(lazy(sceneLoader))}
      >
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
          // R2：与 deep-link 初值共用 normalizeProjectId（.wp 尾缀归一）
          value: normalizeProjectId(summary.project_id),
          label: normalizeProjectId(summary.project_id),
        }))}
        onChange={(value) => {
          // S3：同步回写+写后派发（useProjectId setter——不清其余参数）
          setProjectId(value);
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
