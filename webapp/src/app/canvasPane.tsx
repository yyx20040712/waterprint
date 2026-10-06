/**
 * canvas 槽装配：projectId 空态选择+画布选中态（App 受控）+ErrorBoundary
 * 隔离（M1 批 2026-10-06 析出：参数侧栏段退役——params 承载升右列 Settings
 * 窗〔App 装配〕；C2-params Q8 侧栏拖拽三 callback+两 effect+SIDEBAR 三
 * 常量随段全删——D7 析出面）。
 *
 * 输入:  URL ?project= 参数（useProjectId 共享 hook——S3 订阅面/写方）
 *        +useListProjectsApiProjectsGet 项目列表（shared 生成 hook）
 *        +画布节点点击（CanvasFlow onNodeClick→onSelectedUnitChange——
 *        App 单源受控穿线〔selectedUnitId 提升面：选中鎏金消费+Settings
 *        窗 ParamTabs unitId 消费；切项目清陈旧归 App effect〕）
 * 输出:  画布槽（空态项目选择器 / CanvasEditToolbar+CanvasFlow 只读渲染
 *        隔离边界——wp-full-bleed 满铺）
 *
 * 规格说明（FE4 D4/D5+FE5 D2/D4+UX1 S3+P0-3；M1 批 D7 析出）：
 *   - projectId 单一真相=URL：本 pane=写方（空态 Select onChange 经
 *     useProjectId setter——回写 replaceState+PROJECT_EVENT 写后派发
 *     一步收敛，S3 各槽订阅联动；.wp 尾缀归一对称面与服务端 C1 挂账
 *     同 FE3）；各槽共用 ?project= 参数（同一项目跨槽联动语义）；
 *   - FE5 选中态（D2）：M1 提升 App 受控（原本组件 useState——联动源=
 *     画布选中；树选中联动=M2）；CanvasFlow onNodeClick 写入经
 *     onSelectedUnitChange 上抛，选中鎏金消费沿现状；
 *   - D4 不 lazy 不 Suspense：canvas=默认槽首屏必渲染——零动态 import，
 *     xyflow 进首屏入口 bundle 为预期；
 *   - ErrorBoundary label=工艺画布（渲染崩溃不清空应用 §15 细节 4）；
 *     不传 onRetry（无 lazy thenable 重建需求——复位复位态即重挂载，
 *     取数经 react-query 有自身重试）；
 *   - 空态=AntD Select：选项来自 GET /api/projects（P0-1/F3：label=
 *     「名称 (id 前 8)」——projectOptionLabel，无名回退全 id）+「新建项目」
 *     CTA（P0-1/F1/F4-文案面：CreateProjectModal 两态——空白新建/导入
 *     JSON；成功经 useProjectId setter 切入）；列表空=指引文案；查询
 *     失败=错误文案（AUDIT2 I-3 纪律维持：不挂建项目引导）；
 *   - Select 不用占位文案属性（grep 门禁英文占位特征词命中该 prop
 *     名——FE3 C3 同款规避；指引由段落承担）；
 *   - P0-3+M1 解构：画布区顶部挂 CanvasEditToolbar（编辑会话开关⑤/
 *     保存 dirty/参数草稿徽标——提交计算/校验已迁顶栏 Ribbon）；画布区
 *     flex 列（工具条+画布满高链不破）。
 */
import { useEffect, useMemo, useState } from "react";
import { Button, Select, Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { CanvasFlow } from "../features/canvas/components/CanvasFlow";
import { useSceneQuery } from "../features/viewer3d/api/useSceneQuery";
import { ThumbnailStage } from "../features/viewer3d/components/ThumbnailStage";
import { resolvePngThumbs } from "../features/viewer3d/assemble/thumbSource";
import { registerProbe } from "../features/viewer3d/assemble/probe";

// 批3 主体（S9）：canvas 页也注册探针（注册位原在 Scene 模块——缩略图
// 降级计数在 canvas 页消费，两入口幂等同挂）
registerProbe();
import {
  SceneProjectionError,
  projectScene,
} from "../features/viewer3d/lib/projectScene";
import { thumbCacheKey } from "../features/viewer3d/lib/thumbnailStage";
import { useListProjectsApiProjectsGet } from "../shared/api/generated/projects/projects";
import { TASK_EVENT } from "../shared/events";
import { CanvasEditToolbar } from "./canvasEditToolbar";
import { CreateProjectModal } from "./createProjectModal";
import { ProjectManagerModal } from "./projectManagerModal";
import { projectOptionLabel } from "./projectCreate";
import { ErrorBoundary } from "./ErrorBoundary";
import { normalizeProjectId } from "./projectParam";
import { useProjectId } from "./useProjectId";

/** 空态指引（P0-1 CTA 化——F4-文案面收口：新建/导入经 Modal，不再教 API）。 */
const EMPTY_GUIDE =
  "暂无项目：点击「新建项目」创建空白项目或导入已有项目 JSON 文件。";

export function CanvasPane({
  libraryFocusId = null,
  selectedUnitId = null,
  onSelectedUnitChange,
}: {
  /** 单元库定位单元（App 持态穿线——C2-lib U3：命中画布节点水蓝光环
   * wp-lib-hit；null=无定位。生命周期=单元库 Drawer 开闭[关抽屉解除]）。 */
  libraryFocusId?: string | null;
  /** 画布选中单元（App 受控——M1 提升：选中鎏金消费+Settings 窗联动）。 */
  selectedUnitId?: string | null;
  /** 选中写入回调（CanvasFlow onNodeClick 上抛——App 单源）。 */
  onSelectedUnitChange: (unitId: string | null) => void;
}) {
  // S3 写方：hook setter 收敛回写 URL+派发（原三行 replaceState 内联退役）
  const [projectId, setProjectId] = useProjectId();
  // P0-1：建项 Modal 开态（空态 CTA 挂点——成功后 onCreated 切入新项目）
  const [createOpen, setCreateOpen] = useState(false);
  // P2 生命周期 L4：项目管理 Modal 开态（空态第二入口——Header 钮同件）
  const [managerOpen, setManagerOpen] = useState(false);
  const queryClient = useQueryClient();
  // C2-thumb V3/V5：节点 3D 缩略图（app 组合层——Viewer3d 域舞台产出；
  // sceneQuery 与 viewer3d 同键零重复请求；404[未算]/失败=静默回退象形
  // 图标——仅缩略图功能降级，禁影响画布主流程）
  const sceneQuery = useSceneQuery(projectId ?? "", undefined, {
    enabled: projectId !== null,
  });
  const [realtimeThumbnails, setRealtimeThumbnails] = useState<
    ReadonlyMap<string, string>
  >(() => new Map());
  // 批3 主体（S9 PNG-first）：registry ready 族缩略图先取静态 PNG——
  // 命中直用（省离屏渲染）；失败[404/网络]→单元入 ThumbnailStage 实时
  // 后备队列（顺序队列并发 1 ≤2 合规）；probe 计数归 thumbSource。
  const [pngThumbs, setPngThumbs] = useState<ReadonlyMap<string, string>>(
    () => new Map(),
  );
  // 合成批（PNG 命中∪实时交付——PNG 键优先[族级资产真源]）
  const mergedThumbnails = useMemo(() => {
    const merged = new Map(realtimeThumbnails);
    for (const [key, value] of pngThumbs) {
      merged.set(key, value);
    }
    return merged;
  }, [realtimeThumbnails, pngThumbs]);
  const pngSkip = useMemo(() => new Set(pngThumbs.keys()), [pngThumbs]);
  useEffect(() => {
    setRealtimeThumbnails(new Map()); // 切项目清批（旧项目缩略图不跨项目残留）
    setPngThumbs(new Map());
  }, [projectId]);
  // C2-thumb V5+GD-01（AUDIT2 R3 DS-03 先例族第六处监听）：apply/ParamForm
  // 重算终态派发 TASK_EVENT→失效 scene 键→同键原地 refetch（GD-01 复位
  // effect 的真实触发路径——缩略图随重算刷新；viewer3d 槽同键受益）
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

  useEffect(() => {
    if (thumbScene === null) {
      return;
    }
    let alive = true;
    const unitIds = new Set<string>();
    for (const node of thumbScene.solids) {
      const sep = node.id.indexOf("::");
      if (sep > 0) {
        unitIds.add(node.id.slice(0, sep));
      }
    }
    void resolvePngThumbs([...unitIds]).then((hits) => {
      if (alive) {
        setPngThumbs(hits);
      }
    });
    return () => {
      alive = false;
    };
  }, [thumbScene]);
  // 空态才拉列表（projectId 已定=deep-link 直进画布，省一次列表请求）
  const projectsQuery = useListProjectsApiProjectsGet({
    query: { enabled: projectId === null },
  });

  if (projectId !== null) {
    return (
      <ErrorBoundary label="工艺画布">
        {/* C2-canvas P2 满高链+M1 D7 析出：参数侧栏段退役（params 承载升
            App 右列 Settings 窗）——画布区独占满铺；C2-visual D2：wp-full-
            bleed 满铺回收（tabpane gutter 分策——画布编辑器面满铺，类内含
            height 补偿）；C2VD 补笔：底色=var(--wp-bg-container) 面板蓝 */}
        <div
          className="wp-full-bleed"
          style={{
            display: "flex",
            gap: 12,
            alignItems: "stretch",
            background: "var(--wp-bg-container)",
          }}
        >
          <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
            {/* 槽内工具条（M1 解构两态：编辑/退出/保存——提交计算与校验
                在顶栏 Ribbon 唯一入口） */}
            <CanvasEditToolbar projectId={projectId} />
            <div style={{ flex: 1, minHeight: 0 }}>
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
                  onReady={setRealtimeThumbnails}
                  skip={pngSkip}
                />
              ) : null}
              <CanvasFlow
                projectId={projectId}
                selectedUnitId={selectedUnitId}
                libraryFocusId={libraryFocusId}
                unitThumbnails={mergedThumbnails}
                onNodeClick={onSelectedUnitChange}
              />
            </div>
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
        {/* P2 生命周期 L4：治理入口（重命名/复制/删除——Header 钮同件） */}
        <Button onClick={() => setManagerOpen(true)} data-testid="wp-open-manager">
          管理项目
        </Button>
      </div>
      <CreateProjectModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(created) => setProjectId(created)}
      />
      <ProjectManagerModal open={managerOpen} onClose={() => setManagerOpen(false)} />
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
