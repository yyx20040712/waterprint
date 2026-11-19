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
 *     仅行预聚合并单向穿隧 props——ENG6 先例第二例；spacing join 一处不
 *     抽沿预裁 9（lineForm 已 B4 笔③抽 LineFinishForm）；
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
 *   - B4 笔③ R1+R5 红线逐点编辑：onMoveVertex/onInsertVertex/
 *     onRemoveVertex 三回调（BoundaryLayer 上行——吸附净值已归
 *     vertexEditing 层完成）copy-on-write 落 draft.boundary；删至
 *     <BOUNDARY_MIN_VERTICES 拒删=useMessage 提示+draft/selection 零变
 *     （整体清空走既有 Popconfirm 通路）；红线选中 Delete/侧栏删除=
 *     removeRequest boundary 分支汇 clearBoundary 清空通路+setSelection
 *     (null) 收口（清空后 boundary 对象不存在——selection 随清，简报 R2
 *     必改②）；顶点增删后 boundary 单例 selection 保持（身份不随顶点数变）。
 *   - B4 笔③ R6 行预算拆法：收笔参数面板抽 LineFinishForm（ENG6 第四拆
 *     ——宽度/kind 会话态随子件自持，条件渲染重挂载=缺省重置）；投影围栏
 *     try/catch 归 lib projectSiteSafe（本层 useMemo 零分支）；红线 polygon
 *     段归 SiteCanvas 挂 BoundaryLayer 子件（三新件详见各文件头）。
 *   - 组件只渲染零业务推导：几何/吸附/测距全在 lib/projectSite。
 *   - V4 P3（2026-10-15）：待摆列表/选中侧栏单元显示名中文化——
 *     useUnitDisplayNames（catalog name_zh 单源，查表键=kind ?? unitId）
 *     一处供给两子件；键集/拖拽载荷/title 悬浮原 id 零改。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { message } from "antd";

import {
  getReadProjectApiProjectsProjectIdGetQueryOptions,
  useSaveProjectApiProjectsProjectIdPut,
} from "../../../shared/api/generated/projects/projects";
import { useGetSpacingApiSiteSpacingGet } from "../../../shared/api/generated/site/site";
import type { BoundaryViolationEntry, SpacingViolationEntry } from "../../../shared/api/generated/model";
import { LOCK_HINT, WaterprintApiError, isLockConflict } from "../../../shared/api/http";
import {
  baseHashOf,
  confirmSaveConflict,
  surfaceSaveConflict,
  type SaveConflictLatest,
} from "../../../shared/ui/saveConflictModal";
import { useSiteData } from "../api/useSiteData";
import {
  narrowSiteDesign,
  projectSiteSafe,
  withSite,
  type SiteDesignShape,
} from "../lib/projectSite";
import {
  BOUNDARY_REJECT_HINT,
  buildSiteEditHandlers,
  type FinishedLine,
} from "../lib/siteEditHandlers";
import { sameSite } from "../lib/siteDraftDiff";
import { useUnitDisplayNames } from "../lib/unitDisplayNames";
import { useSiteplanStore, type RemovableSelection } from "../store/siteplanStore";
import { LineFinishForm } from "./LineFinishForm";
import { PendingPanel } from "./PendingPanel";
import { LineSidebar } from "./LineSidebar";
import { SiteCanvas } from "./SiteCanvas";
import { StructureSidebar } from "./StructureSidebar";
import { SiteplanToolbar } from "./SiteplanToolbar";
import { WindRosePanel } from "./WindRosePanel";

// 红线拒删提示文案与收笔挂起面（F2 批 2026-11-20 迁 lib/siteEditHandlers
// ——BOUNDARY_REJECT_HINT/FinishedLine 单源再导入，组件顶墙拆件 ADR-024 同构）

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

  // 投影围栏（CanvasFlow D6 围栏同构——fetch isError 之外第二出口；错误
  // 捕获归 lib projectSiteSafe——B4 笔③行预算拆法，组件层零 try/catch）
  const projection = useMemo(() => {
    if (raw === undefined) {
      return { model: null, error: null };
    }
    return projectSiteSafe(
      (raw as Record<string, unknown>)["design"] as Record<string, unknown>,
      sceneQuery.data ?? null,
    );
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

  // 收笔挂起态（宽度/kind 面板会话态随 LineFinishForm 自持——B4 笔③拆分）
  const [finishedLine, setFinishedLine] = useState<FinishedLine | null>(null);
  // 折线/红线删除确认门挂起态（B4 笔② R2+B4 笔③ 泛化：侧栏按钮与画布
  // Delete 键两路汇同一 Popconfirm——RemovableSelection 面随上行携带；
  // 仓内无 undo，删除须确认；取消路径=零动作）
  const [removeRequest, setRemoveRequest] = useState<RemovableSelection | null>(null);
  // 拒删提示（B4 笔③：useMessage+contextHolder——SheetList 先例，不用静态
  // message）；F12（P0-3 同制一并）：保存成功 toast——走查实证零反馈致
  // 「存没存上」不可知（原「成功路径零额外消息」口径就此面废止）
  const [messageApi, contextHolder] = message.useMessage();

  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>({
    mutation: {
      onSuccess: () => {
        // 仅 invalidate——refetch 后 raw 新身份经 loadedSite useEffect 同步 draft
        // （此处 setDraft 闭包旧 loadedSite=回滚闪烁；refetch 失败则已存内容丢失）
        messageApi.success("布置已保存"); // F12：保存反馈（P0-3 同制）
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
  // V4 P3：单元显示名（catalog name_zh 单源——待摆/已摆面同映射；查表键
  // =kind ?? unitId 归 lib/unitDisplayNames，title 悬浮原 id 归子件）
  const nameOf = useUnitDisplayNames(raw);
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

  // ── 编辑回调（copy-on-write——draft 永不原位突变）──
  // F2 批 2026-11-20：回调族迁 lib/siteEditHandlers 工厂（deps 注入，
  // 行为零变——组件顶墙拆件 ADR-024 同构）；拒删提示经 notify 上行。
  const handlers = buildSiteEditHandlers({
    draft,
    setDraft,
    setSelection,
    tool,
    setFinishedLine,
    setRemoveRequest,
    notifyBoundaryReject: () => messageApi.warning(BOUNDARY_REJECT_HINT),
  });

  // 确认门 confirm=执行删除/清空+关闭；取消/外部点击=零动作（状态不变）
  const confirmRemoveLine = () => {
    if (removeRequest !== null) {
      if (removeRequest.kind === "boundary") {
        // B4 笔③ R2 收口：红线整体删除=既有清空通路（clearBoundary 内含
        // setSelection(null)——清空后 boundary 对象不存在，selection 随清）
        clearBoundary();
      } else {
        handlers.onRemoveLine(removeRequest.kind, removeRequest.index);
      }
    }
    setRemoveRequest(null);
  };

  // 落笔=宽度/kind 自面板上行（B4 笔③——LineFinishForm 会话态自持，本层
  // 只收参数 copy-on-write 落 draft；宽度非有限=防御拒收零动作）
  const confirmLine = (width: number, corridorKind: string) => {
    if (finishedLine === null || !Number.isFinite(width)) {
      return;
    }
    setDraft((prev) => {
      if (prev === null) {
        return prev;
      }
      if (finishedLine.kind === "road") {
        return {
          ...prev,
          roads: [...prev.roads, { centerline: finishedLine.points, width_m: width }],
        };
      }
      return {
        ...prev,
        corridors: [
          ...prev.corridors,
          { centerline: finishedLine.points, width_m: width, kind: corridorKind },
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
  // （清空结果可保存——漏存=清空丢失坑）；boundary 空时入口已 disabled；
  // B4 笔③ R2 收口：清空后 boundary 对象不存在——boundary 选中随清
  // （工具栏/删除门两入口同收；getState 取即时选中面，SiteCanvas 先例）。
  const clearBoundary = () => {
    setDraft((prev) => (prev === null ? prev : { ...prev, boundary: [] }));
    if (useSiteplanStore.getState().selection?.kind === "boundary") {
      setSelection(null);
    }
  };

  // B5 D5/D7：风玫瑰值编辑上行——合并写回值 copy-on-write 落 draft.options.wind_rose（onMoveVertex 单行同式）
  const setWindRose = (next: Record<string, number> | null) => setDraft((prev) => (prev === null ? prev : { ...prev, options: { ...prev.options, wind_rose: next } }));

  /** F2 冲突三选（2026-11-20）：覆盖=最新 raw 重合成布置+新基线重发；放弃=重拉（draft 随 loadedSite 效应同步）。 */
  const surfaceConflict = (
    error: unknown,
    bodyDraft: SiteDesignShape,
  ): boolean =>
    surfaceSaveConflict(error, {
      confirm: confirmSaveConflict,
      refetchLatest: async () => {
        const fresh = await queryClient.fetchQuery(
          getReadProjectApiProjectsProjectIdGetQueryOptions(projectId),
        );
        const freshHash = baseHashOf(fresh);
        return freshHash !== null ? { raw: fresh, baseHash: freshHash } : null;
      },
      onOverwrite: (latest: SaveConflictLatest) => {
        save.mutate(
          {
            projectId,
            data: withSite(latest.raw, bodyDraft),
            params: { base_hash: latest.baseHash },
          },
          {
            onError: (retryError) => {
              surfaceConflict(retryError, bodyDraft); // 窗口内又他写=对话再现
            },
          },
        );
      },
      onDiscard: () => {
        // 重拉最新——draft 经 loadedSite useEffect 同步回退（onSuccess 同链注记）
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
      },
    });

  const saveDraft = () => {
    if (raw === undefined || draft === null) {
      return;
    }
    const baseHash = baseHashOf(raw as Record<string, unknown>); // F2：读时基线
    save.mutate(
      {
        projectId,
        data: withSite(raw as Record<string, unknown>, draft),
        ...(baseHash !== null ? { params: { base_hash: baseHash } } : {}),
      },
      {
        onError: (error) => {
          surfaceConflict(error, draft); // 409→三选对话；其余走 isError 行内分级
        },
      },
    );
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

  // B4 笔②/③：选中可删除面（折线索引失效防御——draft 竞态缩短时侧栏不
  // 渲染；boundary 单例无索引——存在性=boundary 非空即可选）
  const removableExists = (target: RemovableSelection): boolean =>
    target.kind === "boundary"
      ? draft.boundary.length > 0
      : target.index < (target.kind === "road" ? draft.roads : draft.corridors).length;
  const selectedRemovable =
    selection !== null && selection.kind !== "structure" ? selection : null;

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
        linePanel={finishedLine === null ? null : (
          <LineFinishForm kind={finishedLine.kind} pointsCount={finishedLine.points.length}
            onConfirm={confirmLine} onDiscard={() => setFinishedLine(null)} />
        )}
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
          nameOf={nameOf}
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
            onMoveVertex={handlers.onMoveVertex}
            onInsertVertex={handlers.onInsertVertex}
            onRemoveVertex={handlers.onRemoveVertex}
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
            nameOf={nameOf}
          />
        ) : null}
        {/* B4 笔② R2/B4 笔③：选中道路/走廊/红线删除侧栏——按钮与画布
            Delete 键汇同一 Popconfirm 确认门（removeRequest 挂起态=两路
            回调签名汇合面；boundary 分支=清空通路文案族） */}
        {selectedRemovable !== null && removableExists(selectedRemovable) ? (
          <LineSidebar
            selection={selectedRemovable}
            removeOpen={removeRequest !== null}
            onRequest={handlers.onRemoveRequest}
            onConfirmRemove={confirmRemoveLine}
            onCancelRemove={() => setRemoveRequest(null)}
          />
        ) : null}
        {selection === null ? <WindRosePanel value={draft.options.wind_rose} onChange={setWindRose} onClear={() => setWindRose(null)} /> : null}
      </div>
      {contextHolder}
    </div>
  );
}
