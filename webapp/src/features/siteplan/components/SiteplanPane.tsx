/**
 * 布置编辑器组装件：工具栏+待摆区+画布+选中侧栏+保存流（切片内组装——
 * canvasPane 壳同构；本文件是 siteplan 的唯一编排面）。
 *
 * 输入:  projectId（useSiteData 双查询：readProject 原始体+scene 足迹源）；
 *        view 态自 siteplanStore（工具/选中/开关）
 * 输出:  布置工作区（工具栏[工具/吸附/网格/复位/保存]+待摆区+SVG 画布+
 *        选中结构侧栏[ground_elevation]+折线收笔参数面板+错误呈现）
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
 *   - scene 查询失败≠致命：outline 降级示意矩形+工具栏提示（不阻断编辑）；
 *     投影失败（design 异形）=错误薄壳（不白屏）；
 *   - L4b 间距校核：GET /api/site/spacing orval hook 直用+组件层 join
 *     （预裁 9——projectSite/store 零改动；未计算=降级全量非拒不阻断）；
 *     描边色映射下放 SiteCanvas，选中侧栏列违规行（对端/净距/阈值/severity）；
 *   - ground_elevation 编辑=选中侧栏 InputNumber（米可空——纵断数据面）；
 *   - 组件只渲染零业务推导：几何/吸附/测距全在 lib/projectSite。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, InputNumber, Popover, Select, Space, Typography } from "antd";

import { useSaveProjectApiProjectsProjectIdPut } from "../../../shared/api/generated/projects/projects";
import { useGetSpacingApiSiteSpacingGet } from "../../../shared/api/generated/site/site";
import type { SpacingViolationEntry } from "../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../shared/api/http";
import { useSiteData } from "../api/useSiteData";
import {
  SiteProjectionError,
  narrowSiteDesign,
  projectSite,
  withSite,
  type SiteDesignShape,
  type SitePoint,
  type StructurePlacement,
} from "../lib/projectSite";
import { useSiteplanStore } from "../store/siteplanStore";
import { PendingPanel } from "./PendingPanel";
import { SiteCanvas } from "./SiteCanvas";

/** 409 锁冲突保守提示（AssumptionsPanel D3 先例同文——不 force 不重试）。 */
const LOCK_HINT = "项目已被他处修改，请刷新后重试（并发写锁守门——不自动覆盖）";

/** 选中结构侧栏宽度（像素——显示层常量）。 */
const SIDE_WIDTH = 220;

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

/** 深比较（键序无关——draft copy-on-write 不保插入序一致性）。 */
function sameSite(a: unknown, b: unknown): boolean {
  if (a === b) {
    return true;
  }
  if (typeof a !== "object" || typeof b !== "object" || a === null || b === null) {
    return false;
  }
  const aKeys = Object.keys(a).sort();
  const bKeys = Object.keys(b).sort();
  if (aKeys.length !== bKeys.length || aKeys.some((key, i) => key !== bKeys[i])) {
    return false;
  }
  return aKeys.every((key) =>
    sameSite((a as Record<string, unknown>)[key], (b as Record<string, unknown>)[key]),
  );
}

/** 收笔挂起面（折线已成立、宽度/kind 待补）。 */
type FinishedLine = { kind: "road" | "corridor"; points: SitePoint[] };

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
      <div style={{ padding: "4px 0", borderBottom: "1px solid #434343" }}>
        <Space size="small" wrap>
          {(
            [
              ["select", "选择/平移"],
              ["road", "道路"],
              ["corridor", "管线走廊"],
              ["boundary", "边界红线"], // L4a 第四态：≥3 点双击/Enter 闭合收笔（无参数面板）
            ] as const
          ).map(([value, label]) => (
            <Button
              key={value}
              size="small"
              type={tool === value ? "primary" : "default"}
              onClick={() => setTool(value)}
            >
              {label}
            </Button>
          ))}
          <Button size="small" onClick={toggleSnap}>
            吸附 {snapEnabled ? "开" : "关"}
          </Button>
          <Button size="small" onClick={toggleGrid}>
            坐标网 {showGrid ? "开" : "关"}
          </Button>
          <Button
            size="small"
            onClick={() => {
              setPan({ x: 0, y: 0 });
              setZoom(1);
            }}
          >
            复位视图
          </Button>
          <Popover
            open={finishedLine !== null}
            trigger={[]}
            content={lineForm}
            placement="bottomLeft"
          >
            <Button size="small" type={finishedLine !== null ? "primary" : "default"}>
              折线参数
            </Button>
          </Popover>
          <Button
            size="small"
            type="primary"
            loading={save.isPending}
            disabled={!dirty || raw === undefined}
            onClick={() => {
              if (raw === undefined || draft === null) return;
              save.mutate({ projectId, data: withSite(raw as Record<string, unknown>, draft) });
            }}
          >
            保存布置{dirty ? "（有修改）" : ""}
          </Button>
          {sceneQuery.isError || (sceneQuery.isSuccess && sceneQuery.data == null) ? (
            <Typography.Text type="warning" style={{ fontSize: 12 }}>
              场景不可得——足迹按示意矩形显示（未计算）
            </Typography.Text>
          ) : null}
        </Space>
        {save.isError ? (
          <div style={{ marginTop: 4 }}>
            <Typography.Text type="danger">
              {isLockConflict(save.error)
                ? LOCK_HINT
                : `布置保存失败：${save.error instanceof Error ? save.error.message : "未知错误"}`}
            </Typography.Text>
          </div>
        ) : null}
      </div>
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
            onPlace={handlers.onPlace}
            onMove={handlers.onMove}
            onRotate={handlers.onRotate}
            onRemove={handlers.onRemove}
            onCommitLine={handlers.onCommitLine}
          />
        </div>
        {selectedStructure !== undefined && selection !== null ? (
          <aside
            style={{
              width: SIDE_WIDTH,
              flexShrink: 0,
              padding: "8px 12px",
              borderLeft: "1px solid #434343",
              overflowY: "auto",
            }}
          >
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              选中构筑物
            </Typography.Text>
            <div style={{ fontFamily: "monospace", fontSize: 12, margin: "4px 0" }}>
              {selection.kind === "structure" ? selection.id : ""}
            </div>
            <div style={{ fontSize: 12, color: "#8c8c8c" }}>
              x {selectedStructure.x} m · y {selectedStructure.y} m · 旋转{" "}
              {selectedStructure.rotation}°
            </div>
            <div style={{ margin: "8px 0 4px", fontSize: 12 }}>
              设计地面标高 ground_elevation（m，可空）
            </div>
            <InputNumber
              size="small"
              style={{ width: 140 }}
              value={selectedStructure.ground_elevation}
              onChange={(value) => {
                if (selection !== null && selection.kind === "structure") {
                  handlers.onElev(selection.id, value);
                }
              }}
            />
            {selectedViolations.length > 0 ? (
              <div style={{ marginTop: 10 }}>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  间距校核（越限 {selectedViolations.length}）
                </Typography.Text>
                {selectedViolations.map((row) => (
                  <div key={`${row.a}:${row.b}:${row.threshold_m}`} style={{ fontSize: 12, marginTop: 4, color: row.severity === "ERROR" ? "#ff4d4f" : "#faad14" }}>
                    {row.a === selectedId ? row.b : row.a}：净距 {row.clearance_m.toFixed(1)} m ＜ 阈值 {row.threshold_m} m（{row.severity === "ERROR" ? "错误" : "警告"}）
                  </div>
                ))}
              </div>
            ) : null}
            <div style={{ marginTop: 10 }}>
              <Button
                size="small"
                danger
                onClick={() => {
                  if (selection !== null && selection.kind === "structure") {
                    handlers.onRemove(selection.id);
                  }
                }}
              >
                移出布置（回待摆区）
              </Button>
            </div>
            <div style={{ marginTop: 10, fontSize: 12, color: "#8c8c8c" }}>
              拖拽移动=坐标网吸附；旋转把手=90° 吸附（Shift 自由）；画布双击
              构筑物=移出。
            </div>
          </aside>
        ) : null}
      </div>
    </div>
  );
}
