/**
 * canvas 标签页装配：projectId 空态选择+参数侧栏+画布选中态+ErrorBoundary 隔离。
 *
 * 输入:  URL ?project= 参数（useProjectId 共享 hook——S3 订阅面/写方）
 *        +useListProjectsApiProjectsGet 项目列表（shared 生成 hook）
 *        +画布节点点击（CanvasFlow onNodeClick→selectedUnitId）
 * 输出:  工艺画布标签页（空态项目选择器 / flex 侧栏组合：参数面板+设计
 *        假设只读清单+CanvasFlow 只读渲染隔离边界）
 *
 * 规格说明（FE4 批 6b 段一 D4/D5+FE5 批 6b 段三 D2/D4；app/viewer3dPane
 *   同构；UX1 批 6b 段八 S3 写方换 useProjectId hook）：
 *   - projectId 单一真相=URL：本 pane=写方（空态 Select onChange 经
 *     useProjectId setter——回写 replaceState+PROJECT_EVENT 写后派发
 *     一步收敛，S3 六 pane 订阅联动；.wp 尾缀归一对称面与服务端 C1
 *     挂账同 FE3）；两标签共用 ?project= 参数（同一项目跨画布/三维
 *     联动语义——各标签独立选择面挂账 UX 批）；
 *   - FE5 选中态（D2 props 提升）：selectedUnitId 本组件 useState 持有
 *     ——CanvasFlow onNodeClick 写入+ParamForm 消费；不建全局 store
 *     （最小面；§17.2 UI 态走 store 红线不阻但单面板无必要——简报 D2）；
 *   - FE5 挂载（D4 左侧固定宽侧栏）：flex 行=params 侧栏 320px+画布余宽
 *     （视觉近似 §19.2 左面板且 selectedUnitId 不跨层）；ParamsPanel=
 *     ParamForm+AssumptionsPanel 两件叠放，未选中=提示文案（假设清单
 *     恒展示）；App 层 Sider 维持单元库占位（单元库≠params——全局化挂账
 *     UX 批）；
 *   - D4 不 lazy 不 Suspense：canvas=默认标签首屏必渲染（App activeKey
 *     默认 canvas）——零动态 import，xyflow 进首屏入口 bundle 为预期；
 *   - ErrorBoundary label=工艺画布（渲染崩溃不清空应用 §15 细节 4；
 *     params 两件同界隔离）；不传 onRetry（无 lazy thenable 重建需求——
 *     复位复位态即重挂载，取数经 react-query 有自身重试）；
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
import { AssumptionsPanel } from "../features/params/components/AssumptionsPanel";
import { ParamForm } from "../features/params/components/ParamForm";
import { useListProjectsApiProjectsGet } from "../shared/api/generated/projects/projects";
import { ErrorBoundary } from "./ErrorBoundary";
import { normalizeProjectId } from "./projectParam";
import { useProjectId } from "./useProjectId";

/** 空态指引（与 viewer3dPane 同款——先建项目再提交计算）。 */
const EMPTY_GUIDE =
  "暂无项目可加载：请先创建项目并提交计算（CLI 或 API：POST /api/projects → POST /api/calc/run，见 docs/user-manual.md「快速开始」五步链），完成后刷新本页。";

/** 未选中提示（D4——ParamForm 槽位文案，假设清单恒展示）。 */
const UNSELECTED_HINT =
  "在画布中点击构筑物节点，即可在此编辑其参数并提交重算；设计假设清单始终展示于下方。";

/** 参数侧栏宽度（D4 300px 级——flexShrink 0 固定）。 */
const SIDEBAR_WIDTH = 320;

export function CanvasPane() {
  // S3 写方：hook setter 收敛回写 URL+派发（原三行 replaceState 内联退役）
  const [projectId, setProjectId] = useProjectId();
  // D2 选中态：本组件持有（CanvasFlow 写入/ParamForm 消费——不建 store）
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  // 空态才拉列表（projectId 已定=deep-link 直进画布，省一次列表请求）
  const projectsQuery = useListProjectsApiProjectsGet({
    query: { enabled: projectId === null },
  });

  if (projectId !== null) {
    return (
      <ErrorBoundary label="工艺画布">
        <div style={{ display: "flex", gap: 12, alignItems: "stretch" }}>
          <aside
            style={{
              width: SIDEBAR_WIDTH,
              flexShrink: 0,
              padding: "0 12px",
              borderRight: "1px solid #434343",
            }}
          >
            {selectedUnitId === null ? (
              <Typography.Paragraph type="secondary">
                {UNSELECTED_HINT}
              </Typography.Paragraph>
            ) : (
              // key=R1 修复（一审 I1）：切单元/切项目强制重挂载——草稿与
              // mutation 态不跨单元残留（消息残留+drafts 串单元双隐患）
              <ParamForm
                key={`${projectId}:${selectedUnitId}`}
                projectId={projectId}
                unitId={selectedUnitId}
              />
            )}
            {/* R 轮 R2（DS-05⑥ 跨项目草稿残留——FE5 I1 同族）：key=
                projectId 切项目强制重挂载——drafts/resets 编辑态不跨项目
                残留（ParamForm 上方 key 已含 projectId 面，此处单补假设面） */}
            <AssumptionsPanel key={projectId} projectId={projectId} />
          </aside>
          <div style={{ flex: 1, minWidth: 0 }}>
            <CanvasFlow
              projectId={projectId}
              selectedUnitId={selectedUnitId}
              onNodeClick={setSelectedUnitId}
            />
          </div>
        </div>
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
          // S3：单一真相回写+写后派发（useProjectId setter——不清其余参数）
          setProjectId(value);
        }}
      />
      {projectsQuery.isError ? (
        <Typography.Text type="danger">
          项目列表加载失败：
          {projectsQuery.error instanceof Error
            ? projectsQuery.error.message
            : "未知错误"}
          {/* AUDIT2 FIX2 I-3（zM-2 纪律回灌）：网络/服务错不挂「先创建
              项目」五步链引导（浏览器实录死服务+空态被误导成建项目）；
              引导仅在空列表（200 零项目）面挂——下分支。 */}
        </Typography.Text>
      ) : projects.length === 0 && !projectsQuery.isLoading ? (
        <Typography.Text type="secondary">{EMPTY_GUIDE}</Typography.Text>
      ) : null}
    </div>
  );
}
