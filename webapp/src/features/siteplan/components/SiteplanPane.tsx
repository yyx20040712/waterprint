/**
 * 布置编辑器组装件：工具栏+待摆区+画布+选中侧栏+保存流（切片内组装——
 * canvasPane 壳同构；本文件是 siteplan 的唯一编排面）。
 *
 * 输入:  projectId（useSiteData 双查询：readProject 原始体+scene 足迹源）；
 *        view 态自 siteplanStore（工具/选中/开关）
 * 输出:  布置工作区（工具栏 SiteplanToolbar[工具/吸附/坐标网/复位/清空
 *        红线/折线参数/保存]+待摆区+SVG 画布+选中结构侧栏[ground_
 *        elevation]+折线收笔参数面板+错误呈现）
 *
 * 规格说明（M3 批 L2b，简报 §一.5/§一.8/§三交互面）：
 *   - 本地 draft=SiteDesignShape（装载 narrowSiteDesign 归一态；copy-on-
 *     write 更新；rawQuery.data 身份变更即重置——保存 invalidate 后重装载
 *     丢弃本地态）；dirty=draft≠装载 site 深比较（sameSite 键序无关）；
 *   - 保存=withSite(raw, draft) 结构化替换 → PUT /api/projects/{id} →
 *     onSuccess invalidate（AssumptionsPanel 先例；site 不改计算面——无
 *     自动 calc/run）；409 锁/WaterprintApiError 先例呈现（失败不丢本地态）；
 *   - 折线收笔：onCommitLine(折线 ≥2 点) → finishedLine 挂起 → Popover 小面板
 *     （InputNumber 宽度+Select kind）补齐后落 draft.roads/corridors；红线
 *     工具（L4a 第四态 boundary）≥3 点闭合收笔无面板直落 draft.boundary
 *     （boundary 无宽无 kind——红线只有一个，重画=替换）；
 *   - 工具栏拆分+清空红线（ENG6）：工具栏区抽 SiteplanToolbar 纯展示子件
 *     （行预算 500 恰达腾挪）；清空=danger+Popconfirm+boundary 空时
 *     disabled，确认后 draft.boundary 置 []（copy-on-write）——dirty 派生
 *     比较自动置位（清空结果可保存），取消分支 boundary 不变；
 *   - B3 R7 侧栏拆分：选中结构侧栏抽 StructureSidebar 纯展示子件（本文件
 *     仅行预聚合并单向穿隧 props——ENG6 先例第二例；lineForm/join 两处
 *     不抽沿预裁 9）；
 *   - scene 查询失败≠致命：outline 降级示意矩形+工具栏提示（不阻断编辑）；
 *     投影失败（design 异形）=错误薄壳（不白屏）；
 *   - L4b 间距校核：GET /api/site/spacing orval hook 直用+组件层 join
 *     （预裁 9——projectSite/store 零改动；未计算=降级全量非拒不阻断）；
 *     描边色映射下放 SiteCanvas（优先级判定=siteGeometry.
 *     structureStrokeRole 口径单源——链序冻结：选中蓝>越界橙红>ERROR 红>
 *     WARN 黄），选中侧栏列违规行（对端/净距/阈值/severity）；
 *     SPC2 扩红线越界：boundary_violations 独立分组「红线越界」（越界行
 *     无净距数值不混排 D10.2）+描边集 boundaryUnitIds 下传；
 *   - ground_elevation 编辑=选中侧栏 InputNumber（米可空——纵断数据面）；
 *   - B4 笔② R2 折线删除编辑：选中 road/corridor 渲染 LineSidebar 删除
 *     侧栏（ENG6 先例第三例——行预算门禁拆文件；danger 按钮+Popconfirm
 *     确认门）与画布 Delete/Backspace 键两路汇同一 removeRequest 挂起态
 *     （仓内无 undo——删除须确认，取消=零动作）；确认=removeLineAt
 *     immutable splice+setSelection(null) 收口（索引前移选中失效）；
 *     Delete 焦点判归 canvasDisplay.lineDeleteTarget（输入框焦点不消费）；
 *   - 组件只渲染零业务推导：几何/吸附/测距全在 lib/projectSite。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, InputNumber, Select, Space, Typography } from "antd";

import { useSaveProjectApiProjectsProjectIdPut } from "../../../shared/api/generated/projects/projects";
import { useGetSpacingApiSiteSpacingGet } from "../../../shared/api/generated/site/site";
import type { BoundaryViolationEntry, SpacingViolationEntry } from "../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../shared/api/http";
import { useSiteData } from "../api/useSiteData";
import {
  SiteProjectionError,
  narrowSiteDesign,
  projectSite,
  removeLineAt,
  withSite,
  type SiteDesignShape,
  type SitePoint,
  type StructurePlacement,
} from "../lib/projectSite";
import { sameSite } from "../lib/siteDraftDiff";
import { useSiteplanStore } from "../store/siteplanStore";
import { PendingPanel } from "./PendingPanel";
import { LineSidebar } from "./LineSidebar";
import { SiteCanvas } from "./SiteCanvas";
import { StructureSidebar } from "./StructureSidebar";
import { SiteplanToolbar } from "./SiteplanToolbar";

/** 409 锁冲突保守提示（AssumptionsPanel D3 先例同文——不 force 不重试）。 */
const LOCK_HINT = "项目已被他处修改，请刷新后重试（并发写锁守门——不自动覆盖）";

/** 收笔参数面板缺省值（显示层常量：道路/走廊典型宽）。 */
const DEFAULT_ROAD_WIDTH = 4;
const DEFAULT_CORRIDOR_WIDTH = 1.5;

/** 走廊 kind 缺省（water——SiteCanvas CORRIDOR_COLORS 登记首键）。 */
const DEFAULT_CORRIDOR_KIND = "water";

/** 走廊 kind 选项（SiteCanvas CORRIDOR_COLORS 登记面——展示层映射）。 */
const CORRIDOR_KIND_OPTIONS = [
  { value: "water", label: "water（给水/中水）" }, { value: "power", label: "power（电力）" },
  { value: "gas", label: "gas（燃气/污泥气）" }, { value: "comm", label: "comm（通信）" },
];

/** 409 面=锁文件冲突（server error_type=ProjectLockedError；HTTP_409 兜底）。 */
function isLockConflict(error: unknown): boolean {
  return (
    error instanceof WaterprintApiError &&
    (error.code === "ProjectLockedError" || error.code === "HTTP_409")
  );
}

/** 收笔挂起面（折线已成立、宽度/kind 待补）。 */
type FinishedLine = { kind: "road" | "corridor"; points: SitePoint[] };

/** 删除确认门挂起面（B4 笔② R2——kind+index 随上行携带）。 */
type RemoveRequest = { kind: "road" | "corridor"; index: number };

export function SiteplanPane({ projectId }: { projectId: string }) {
  const { projectQuery, sceneQuery } = useSiteData(projectId);
  const raw = projectQuery.data;
  const queryClient = useQueryClient();

  const tool = useSiteplanStore((state) => state.tool);
  const selection = useSiteplanStore((state) => state.selection);
  const snapEnabled = useSiteplanStore((state) => state.snapEnabled);
  const showGrid = useSiteplanStore((state) => state.showGrid);
  const setTool = useSiteplanStore((state) => state.setTool);
  const toggleSnap = useSiteplanStore((state) => state.toggleSnap);
  const toggleGrid = useSiteplanStore((state) => state.toggleGrid);
  const setPan = useSiteplanStore((state) => state.setPan);
  const setZoom = useSiteplanStore((state) => state.setZoom);
  const setSelection = useSiteplanStore((state) => state.setSelection);

  // 投影围栏（CanvasFlow D6 围栏同构——fetch isError 之外第二出口）
  const projection = useMemo<{
    model: ReturnType<typeof projectSite> | null;
    error: SiteProjectionError | null;
  }>(() => {
    if (raw === undefined) {
      return { model: null, error: null };
    }
    try {
      const design = (raw as Record<string, unknown>)["design"] as Record<string, unknown>;
      return {
        model: projectSite(design, sceneQuery.data ?? null),
        error: null,
      };
    } catch (error) {
      return {
        model: null,
        error:
          error instanceof SiteProjectionError
            ? error
            : new SiteProjectionError(String(error)),
      };
    }
  }, [raw, sceneQuery.data]);

  // 装载 site（draft 基准；raw 身份变更即重置——保存 invalidate 重装载面）
  const loadedSite = useMemo<SiteDesignShape | null>(() => {
    if (raw === undefined || projection.error !== null) {
      return null;
    }
    const design = (raw as Record<string, unknown>)["design"] as Record<string, unknown>;
    return narrowSiteDesign(design["site"]);
  }, [raw, projection.error]);

  const [draft, setDraft] = useState<SiteDesignShape | null>(null);
  useEffect(() => {
    if (loadedSite !== null) {
      setDraft(loadedSite);
    }
  }, [loadedSite]);

  // 收笔挂起+参数面板态
  const [finishedLine, setFinishedLine] = useState<FinishedLine | null>(null);
  const [lineWidth, setLineWidth] = useState<number>(DEFAULT_ROAD_WIDTH);
  const [corridorKind, setCorridorKind] = useState<string>(DEFAULT_CORRIDOR_KIND);
  // 折线删除确认门挂起态（B4 笔② R2：侧栏按钮与画布 Delete 键两路汇同一
  // Popconfirm——仓内无 undo，删除须确认；取消路径=零动作）
  const [removeRequest, setRemoveRequest] = useState<RemoveRequest | null>(null);

  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>({
    mutation: {
      onSuccess: () => {
        // 仅 invalidate——refetch 后 raw 新身份经 loadedSite useEffect 同步 draft
        // （此处 setDraft 闭包旧 loadedSite=回滚闪烁；refetch 失败则已存内容丢失）
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
      },
    },
  });

  const dirty = draft !== null && loadedSite !== null && !sameSite(draft, loadedSite);

  // L4b 间距校核（GET /api/site/spacing——未计算=降级全量非拒；查询失败≠致命，
  // 无数据即无标示。组件层 join 预裁 9：projectSite/store 零改动不抽纯函数）
  const spacingQuery = useGetSpacingApiSiteSpacingGet({ project_id: projectId });
  const severityByUnit = new Map<string, "WARN" | "ERROR">();
  for (const row of spacingQuery.data?.violations ?? []) {
    for (const unitId of [row.a, row.b]) {
      if (row.severity === "ERROR" || !severityByUnit.has(unitId)) {
        severityByUnit.set(unitId, row.severity === "ERROR" ? "ERROR" : "WARN");
      }
    }
  }
  const violationsOf = (unitId: string): SpacingViolationEntry[] =>
    (spacingQuery.data?.violations ?? []).filter((row) => row.a === unitId || row.b === unitId);

  // SPC2 红线越界（boundary_violations——越界行无净距数值，侧栏独立分组
  // 渲染 D10.2；描边集下传 SiteCanvas）
  const boundaryRows = spacingQuery.data?.boundary_violations ?? [];
  const boundaryUnitIds = new Set(boundaryRows.map((row) => row.unit_id));
  const boundaryOf = (unitId: string): BoundaryViolationEntry[] =>
    boundaryRows.filter((row) => row.unit_id === unitId);

  // ── 编辑回调（copy-on-write——draft 永不原位突变） ──

  const updateStructure = (unitId: string, patch: Partial<StructurePlacement>) => {
    setDraft((prev) => {
      const current = prev === null ? undefined : prev.structures[unitId];
      if (prev === null || current === undefined) {
        return prev;
      }
      return {
        ...prev,
        structures: {
          ...prev.structures,
          [unitId]: { ...current, ...patch },
        },
      };
    });
  };

  const handlers = {
    onPlace: (unitId: string, x: number, y: number) => {
      setDraft((prev) => {
        if (prev === null) {
          return prev;
        }
        return {
          ...prev,
          structures: {
            ...prev.structures,
            [unitId]: {
              x,
              y,
              rotation: 0,
              ground_elevation: prev.structures[unitId]?.ground_elevation ?? null,
            },
          },
        };
      });
    },
    onMove: (unitId: string, x: number, y: number) => updateStructure(unitId, { x, y }),
    onRotate: (unitId: string, rotation: number) => updateStructure(unitId, { rotation }),
    onRemove: (unitId: string) => {
      setDraft((prev) => {
        if (prev === null || prev.structures[unitId] === undefined) {
          return prev;
        }
        const structures = { ...prev.structures };
        delete structures[unitId];
        return { ...prev, structures };
      });
      setSelection(null); // 选中面随移除收口
    },
    onElev: (unitId: string, elevation: number | null) =>
      updateStructure(unitId, { ground_elevation: elevation }),
    onCommitLine: (points: SitePoint[]) => {
      if (tool === "boundary") {
        // L4a 红线：无宽度/kind 面板（boundary 无宽）——≥3 点即闭合收笔
        // 直接落 draft.boundary；红线只有一个（schema 单多边形），重画=替换。
        setDraft((prev) => (prev === null ? prev : { ...prev, boundary: points }));
        return;
      }
      if (tool !== "road" && tool !== "corridor") {
        return;
      }
      setLineWidth(tool === "road" ? DEFAULT_ROAD_WIDTH : DEFAULT_CORRIDOR_WIDTH);
      setFinishedLine({ kind: tool, points });
    },
    // B4 笔② R2：immutable splice 删除+setSelection(null) 收口（索引前移
    // ——选中索引随删除失效，onRemove 先例同式）
    onRemoveLine: (kind: "road" | "corridor", index: number) => {
      setDraft((prev) => {
        if (prev === null) {
          return prev;
        }
        return kind === "road"
          ? { ...prev, roads: removeLineAt(prev.roads, index) }
          : { ...prev, corridors: removeLineAt(prev.corridors, index) };
      });
      setSelection(null);
    },
    // 画布 Delete 键上行——汇侧栏同一确认门（不直删：仓内无 undo）
    onRemoveRequest: (kind: "road" | "corridor", index: number) =>
      setRemoveRequest({ kind, index }),
  };

  // 确认门 confirm=执行删除+关闭；取消/外部点击=零动作（状态不变）
  const confirmRemoveLine = () => {
    if (removeRequest !== null) {
      handlers.onRemoveLine(removeRequest.kind, removeRequest.index);
    }
    setRemoveRequest(null);
  };

  const confirmLine = () => {
    if (finishedLine === null || !Number.isFinite(lineWidth)) {
      return;
    }
    setDraft((prev) => {
      if (prev === null) {
        return prev;
      }
      if (finishedLine.kind === "road") {
        return {
          ...prev,
          roads: [...prev.roads, { centerline: finishedLine.points, width_m: lineWidth }],
        };
      }
      return {
        ...prev,
        corridors: [
          ...prev.corridors,
          { centerline: finishedLine.points, width_m: lineWidth, kind: corridorKind },
        ],
      };
    });
    setFinishedLine(null);
  };

  // ── 工具栏回调（ENG6 拆分面：SiteplanToolbar props 消费） ──

  const resetView = () => {
    setPan({ x: 0, y: 0 });
    setZoom(1);
  };

  // 清空红线：copy-on-write 置 []——dirty 派生比较（sameSite）自动置位
  // （清空结果可保存——漏存=清空丢失坑）；boundary 空时入口已 disabled。
  const clearBoundary = () => {
    setDraft((prev) => (prev === null ? prev : { ...prev, boundary: [] }));
  };

  const saveDraft = () => {
    if (raw === undefined || draft === null) {
      return;
    }
    save.mutate({ projectId, data: withSite(raw as Record<string, unknown>, draft) });
  };

  const saveErrorText = save.isError
    ? isLockConflict(save.error)
      ? LOCK_HINT
      : `布置保存失败：${save.error instanceof Error ? save.error.message : "未知错误"}`
    : null;

  if (projectQuery.isError) {
    return (
      <div role="alert">
        项目文件加载失败：
        {projectQuery.error instanceof Error
          ? projectQuery.error.message
          : "未知错误"}
      </div>
    );
  }
  if (projection.error !== null) {
    return <div role="alert">布置投影失败：{projection.error.message}</div>;
  }
  const model = projection.model;
  if (model === null || draft === null) {
    return <div>厂区布置加载中…（{projectId.slice(0, 8)}）</div>;
  }

  const selectedStructure =
    selection !== null && selection.kind === "structure"
      ? draft.structures[selection.id]
      : undefined;
  const selectedId = selection?.kind === "structure" ? selection.id : "";
  const selectedViolations = violationsOf(selectedId);
  const selectedBoundaryViolations = boundaryOf(selectedId);

  // B4 笔② R2：选中折线面（索引失效防御——draft 竞态缩短时侧栏不渲染）
  const selectedLine =
    selection !== null && (selection.kind === "road" || selection.kind === "corridor")
      ? selection
      : null;
  const selectedLineExists =
    selectedLine !== null &&
    (selectedLine.kind === "road"
      ? selectedLine.index < draft.roads.length
      : selectedLine.index < draft.corridors.length);

  const lineForm = (
    <div style={{ display: "grid", rowGap: 6, width: 200 }}>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        {finishedLine?.kind === "corridor" ? "管线走廊" : "道路"}宽度（m）
        {finishedLine !== null ? `·${finishedLine.points.length} 点` : ""}
      </Typography.Text>
      <InputNumber
        size="small"
        min={0.1}
        value={lineWidth}
        // 清空回退按绘制工具线型二分（road=4/corridor=1.5——收笔会话 kind 即所选工具）
        onChange={(value) =>
          setLineWidth(value ?? (tool === "corridor" ? DEFAULT_CORRIDOR_WIDTH : DEFAULT_ROAD_WIDTH))
        }
      />
      {finishedLine?.kind === "corridor" ? (
        <Select
          size="small"
          value={corridorKind}
          options={CORRIDOR_KIND_OPTIONS}
          onChange={setCorridorKind}
        />
      ) : null}
      <Space size="small">
        <Button size="small" type="primary" onClick={confirmLine}>
          落笔
        </Button>
        <Button size="small" onClick={() => setFinishedLine(null)}>
          丢弃
        </Button>
      </Space>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <SiteplanToolbar
        tool={tool}
        onToolChange={setTool}
        snapEnabled={snapEnabled}
        onToggleSnap={toggleSnap}
        showGrid={showGrid}
        onToggleGrid={toggleGrid}
        onResetView={resetView}
        linePanelOpen={finishedLine !== null}
        linePanel={lineForm}
        boundaryEmpty={draft.boundary.length === 0}
        onClearBoundary={clearBoundary}
        savePending={save.isPending}
        saveDisabled={!dirty || raw === undefined}
        saveDirty={dirty}
        saveError={saveErrorText}
        sceneUnavailable={
          sceneQuery.isError || (sceneQuery.isSuccess && sceneQuery.data == null)
        }
        onSave={saveDraft}
      />
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* 待摆=nodes 全键集减 draft 编辑键集（与 placedCount 同源 draft——拖入即时消项/移除即时回挂） */}
        <PendingPanel
          pendingUnitIds={model.designUnitIds.filter((id) => !(id in draft.structures))}
          placedCount={Object.keys(draft.structures).length}
        />
        <div style={{ flex: 1, minWidth: 0 }}>
          <SiteCanvas
            model={model}
            draft={draft}
            violationSeverity={severityByUnit}
            boundaryUnitIds={boundaryUnitIds}
            onPlace={handlers.onPlace}
            onMove={handlers.onMove}
            onRotate={handlers.onRotate}
            onRemove={handlers.onRemove}
            onCommitLine={handlers.onCommitLine}
            onRemoveRequest={handlers.onRemoveRequest}
          />
        </div>
        {selectedStructure !== undefined && selection !== null ? (
          <StructureSidebar
            selection={selection}
            structure={selectedStructure}
            spacingRows={selectedViolations}
            boundaryRows={selectedBoundaryViolations}
            onElev={handlers.onElev}
            onRemove={handlers.onRemove}
          />
        ) : null}
        {/* B4 笔② R2：选中道路/走廊删除侧栏——按钮与画布 Delete 键汇同一
            Popconfirm 确认门（removeRequest 挂起态=两路回调签名汇合面） */}
        {selectedLine !== null && selectedLineExists ? (
          <LineSidebar
            selection={selectedLine}
            removeOpen={removeRequest !== null}
            onRequest={handlers.onRemoveRequest}
            onConfirmRemove={confirmRemoveLine}
            onCancelRemove={() => setRemoveRequest(null)}
          />
        ) : null}
      </div>
    </div>
  );
}
