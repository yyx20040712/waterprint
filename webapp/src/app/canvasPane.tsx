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
 *     恒展示）；App 层 Sider=UnitLibrary 单元库树（M2 实装替换占位——
 *     单元库≠params，参数编辑面恒在本标签 ParamForm）；
 *   - D4 不 lazy 不 Suspense：canvas=默认标签首屏必渲染（App activeKey
 *     默认 canvas）——零动态 import，xyflow 进首屏入口 bundle 为预期；
 *   - ErrorBoundary label=工艺画布（渲染崩溃不清空应用 §15 细节 4；
 *     params 两件同界隔离）；不传 onRetry（无 lazy thenable 重建需求——
 *     复位复位态即重挂载，取数经 react-query 有自身重试）；
 *   - 空态=AntD Select：选项来自 GET /api/projects（P0-1/F3：label=
 *     「名称 (id 前 8)」——projectOptionLabel，无名回退全 id）+「新建项目」
 *     CTA（P0-1/F1/F4-文案面：CreateProjectModal 两态——空白新建/导入
 *     JSON；成功经 useProjectId setter 切入）；列表空=指引文案（不再教
 *     API——docs/user-manual.md §3 五步链降级为参考文档）；查询失败=
 *     错误文案（AUDIT2 I-3 纪律维持：不挂建项目引导）；
 *   - Select 不用占位文案属性（grep 门禁英文占位特征词命中该 prop
 *     名——FE3 C3 同款规避；指引由段落承担）。
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, Select, Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { CanvasFlow } from "../features/canvas/components/CanvasFlow";
import { AssumptionsPanel } from "../features/params/components/AssumptionsPanel";
import { ParamForm } from "../features/params/components/ParamForm";
import { useSceneQuery } from "../features/viewer3d/api/useSceneQuery";
import { ThumbnailStage } from "../features/viewer3d/components/ThumbnailStage";
import {
  SceneProjectionError,
  projectScene,
} from "../features/viewer3d/lib/projectScene";
import { thumbCacheKey } from "../features/viewer3d/lib/thumbnailStage";
import { useListProjectsApiProjectsGet } from "../shared/api/generated/projects/projects";
import { TASK_EVENT } from "../shared/events";
import { CreateProjectModal } from "./createProjectModal";
import { projectOptionLabel } from "./projectCreate";
import { ErrorBoundary } from "./ErrorBoundary";
import { normalizeProjectId } from "./projectParam";
import { useProjectId } from "./useProjectId";

/** 空态指引（P0-1 CTA 化——F4-文案面收口：新建/导入经 Modal，不再教 API）。 */
const EMPTY_GUIDE =
  "暂无项目：点击「新建项目」创建空白项目或导入已有项目 JSON 文件。";

/** 未选中提示（D4——ParamForm 槽位文案，假设清单恒展示）。 */
const UNSELECTED_HINT =
  "在画布中点击构筑物节点，即可在此编辑其参数并提交重算；设计假设清单始终展示于下方。";

/** 侧栏宽度：默认 280（C2-params 呈裁④——视觉稿 A 值）+拖拽可调
 * （用户裁选「边界可拉伸」Q8：240~480px clamp——下限=标签列+控件最小
 * 容宽，上限=画布区 min 宽保障）。 */
const SIDEBAR_DEFAULT = 280;
const SIDEBAR_MIN = 240;
const SIDEBAR_MAX = 480;

export function CanvasPane({
  libraryFocusId = null,
}: {
  /** 单元库定位单元（App 持态穿线——C2-lib U3：命中画布节点水蓝光环
   * wp-lib-hit；null=无定位。生命周期=单元库 Drawer 开闭[关抽屉解除]）。 */
  libraryFocusId?: string | null;
}) {
  // S3 写方：hook setter 收敛回写 URL+派发（原三行 replaceState 内联退役）
  const [projectId, setProjectId] = useProjectId();
  // P0-1：建项 Modal 开态（空态 CTA 挂点——成功后 onCreated 切入新项目）
  const [createOpen, setCreateOpen] = useState(false);
  const queryClient = useQueryClient();
  // C2-thumb V3/V5：节点 3D 缩略图（app 组合层——Viewer3d 域舞台产出；
  // sceneQuery 与 viewer3d 同键零重复请求；404[未算]/失败=静默回退象形
  // 图标——仅缩略图功能降级，禁影响画布主流程）
  const sceneQuery = useSceneQuery(projectId ?? "", undefined, {
    enabled: projectId !== null,
  });
  const [unitThumbnails, setUnitThumbnails] = useState<
    ReadonlyMap<string, string>
  >(() => new Map());
  useEffect(() => {
    setUnitThumbnails(new Map()); // 切项目清批（旧项目缩略图不跨项目残留）
  }, [projectId]);
  // C2-thumb V5+GD-01（AUDIT2 R3 DS-03 先例族第六处监听）：apply/ParamForm
  // 重算终态派发 TASK_EVENT→失效 scene 键→同键原地 refetch（GD-01 复位
  // effect 的真实触发路径——缩略图随重算刷新；viewer3d 标签同键受益）
  useEffect(() => {
    const onTaskParam = () => {
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/scene/${projectId}`],
        });
      }
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);
  const thumbScene = useMemo(() => {
    if (sceneQuery.data === undefined) {
      return null;
    }
    try {
      return projectScene(sceneQuery.data);
    } catch (error) {
      // 投影拒（版本门/未知 kind）=预期域错静默降级；非投影异常留痕
      // 可见（fail-visible——GD-03 D 一审处置：禁把代码 bug 一并吞掉）
      if (!(error instanceof SceneProjectionError)) {
        console.warn("缩略图场景投影异常（非预期域错）:", error);
      }
      return null;
    }
  }, [sceneQuery.data]);
  // D2 选中态：本组件持有（CanvasFlow 写入/ParamForm 消费——不建 store）
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  // Q8 侧栏拖拽宽度（会话内 state——纯 UI 偏好不进 URL；view 态写侧挂账）
  const [sidebarWidth, setSidebarWidth] = useState(SIDEBAR_DEFAULT);
  const dragging = useRef<{ startX: number; startWidth: number } | null>(null);
  const onHandlePointerMove = useCallback((event: PointerEvent) => {
    const drag = dragging.current;
    if (drag === null) {
      return;
    }
    const width = drag.startWidth + (event.clientX - drag.startX);
    setSidebarWidth(Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, width)));
  }, []);
  const onHandlePointerUp = useCallback(() => {
    dragging.current = null;
    document.body.style.cursor = "";
    document.removeEventListener("pointermove", onHandlePointerMove);
    document.removeEventListener("pointerup", onHandlePointerUp);
  }, [onHandlePointerMove]);
  const onHandlePointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      // GP-N-02（A 二审 R2）：仅主键启动拖拽（右/中键不触发）
      if (event.button !== 0) {
        return;
      }
      dragging.current = { startX: event.clientX, startWidth: sidebarWidth };
      document.body.style.cursor = "col-resize";
      document.addEventListener("pointermove", onHandlePointerMove);
      document.addEventListener("pointerup", onHandlePointerUp);
      // GP-N-01（A 二审 R2）：pointercancel（触摸/浏览器手势取消）路径
      // ——与 pointerup 同收口
      document.addEventListener("pointercancel", onHandlePointerUp);
    },
    [sidebarWidth, onHandlePointerMove, onHandlePointerUp],
  );
  // GP-02（D 一审 R 轮）：拖拽途中组件卸载（切项目/标签）→ document
  // 监听与 body.cursor 兜底清理（pointerup 不触达的泄漏面）
  useEffect(() => {
    return () => {
      document.removeEventListener("pointermove", onHandlePointerMove);
      document.removeEventListener("pointerup", onHandlePointerUp);
      document.removeEventListener("pointercancel", onHandlePointerUp);
      document.body.style.cursor = "";
    };
  }, [onHandlePointerMove, onHandlePointerUp]);
  // 空态才拉列表（projectId 已定=deep-link 直进画布，省一次列表请求）
  const projectsQuery = useListProjectsApiProjectsGet({
    query: { enabled: projectId === null },
  });

  if (projectId !== null) {
    return (
      <ErrorBoundary label="工艺画布">
        {/* C2-canvas P2 满高链：flex 行 height 100%（Tabs content/tabpane
            满高链配套在 global.css）；C2-params Q1：aside 改 flex 列
            （滚动下放 ParamForm body/假设清单限高面——GR-40 收敛）；
            Q8 拖拽把手（col-resize——右缘 8px 命中区） */}
        <div style={{ display: "flex", gap: 12, alignItems: "stretch", height: "100%" }}>
          <aside
            style={{
              width: sidebarWidth,
              flexShrink: 0,
              position: "relative",
              display: "flex",
              flexDirection: "column",
              minHeight: 0,
              borderRight: "1px solid #434343",
            }}
          >
            <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
              {selectedUnitId === null ? (
                <div style={{ padding: "0 12px", flex: 1, overflow: "auto" }}>
                  <Typography.Paragraph type="secondary">
                    {UNSELECTED_HINT}
                  </Typography.Paragraph>
                </div>
              ) : (
                // key=R1 修复（一审 I1）：切单元/切项目强制重挂载——草稿与
                // mutation 态不跨单元残留（消息残留+drafts 串单元双隐患）
                <ParamForm
                  key={`${projectId}:${selectedUnitId}`}
                  projectId={projectId}
                  unitId={selectedUnitId}
                />
              )}
            </div>
            {/* R 轮 R2（DS-05⑥ 跨项目草稿残留）：key=projectId 切项目强制
                重挂载；C2-params Q1：限高 42% 自滚（参数面板主面 flex 1） */}
            <div style={{ maxHeight: "42%", overflow: "auto", flex: "none", padding: "0 12px" }}>
              <AssumptionsPanel key={projectId} projectId={projectId} />
            </div>
            {/* Q8 拖拽把手（视觉稿冻结形态：8px 命中区+3px 可视条 hover 蓝） */}
            <div
              onPointerDown={onHandlePointerDown}
              title="拖拽调整面板宽度"
              style={{
                position: "absolute",
                right: -4,
                top: 0,
                bottom: 0,
                width: 8,
                cursor: "col-resize",
                zIndex: 6,
              }}
            >
              <div
                style={{
                  position: "absolute",
                  right: 3,
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: 3,
                  height: 36,
                  borderRadius: 2,
                  background: "var(--wp-border)",
                }}
              />
            </div>
          </aside>
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* C2-thumb V5：缩略图舞台挂载（离屏——场景数据就绪且投影
                通过才渲；onReady 整批 Map 一次交付——场景数据变即重渲
                [useMemo 随 sceneQuery.data 新引用重建队列]） */}
            {thumbScene !== null ? (
              // GD-N-02（A 二审）：thumbCacheKey 接线为挂载键——场景三组成
              // （项目/工况/版本）任一变强制重挂载全复位（内容级变更[同
              // 版本摆置变]由舞台内 [scene] 复位 effect 承接——两级复位）
              <ThumbnailStage
                key={thumbCacheKey(
                  projectId,
                  thumbScene.conditionKey,
                  thumbScene.sceneVersion,
                )}
                scene={thumbScene}
                onReady={setUnitThumbnails}
              />
            ) : null}
            <CanvasFlow
              projectId={projectId}
              selectedUnitId={selectedUnitId}
              libraryFocusId={libraryFocusId}
              unitThumbnails={unitThumbnails}
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
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Select
          style={{ minWidth: 280 }}
          loading={projectsQuery.isLoading}
          status={projectsQuery.isError ? "error" : undefined}
          options={projects.map((summary) => ({
            value: normalizeProjectId(summary.project_id),
            // P0-1/F3：显示名 (id 前 8)——无名回退全 id
            label: projectOptionLabel(
              summary.name ?? "",
              normalizeProjectId(summary.project_id),
            ),
          }))}
          onChange={(value) => {
            // S3：单一真相回写+写后派发（useProjectId setter——不清其余参数）
            setProjectId(value);
          }}
        />
        {/* P0-1/F1：建项入口（空白新建/导入 JSON——Modal 两态） */}
        <Button type="primary" onClick={() => setCreateOpen(true)}>
          新建项目
        </Button>
      </div>
      <CreateProjectModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(created) => setProjectId(created)}
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
