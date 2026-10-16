/**
 * v4 工程制图区（B1 骨架批 2026-10-09——左树目录+右图库卡栅格；wireframe
 * -d-v4 屏 5 形；siteplan 编辑面随 v4-2 终裁归制图域=subpage siteplan）。
 *
 * 输入: subpage（sheets=图纸库缺省/siteplan=厂区总平面布置编辑面——shellV4
 *        受控）+onSubpageChange（子页切换→?tab= zone 级投影）
 *        +SiteplanPane（app 件复用——厂区布置编辑器）+exports 查询族
 *        （features/drawings——图库卡数据源+导出工具行语境）
 * 输出: drafting 区：左=drafting-tree（污水厂▾〔全厂总平面图→siteplan/
 *        高程纵断图/工艺图…→sheets〕+管网▸规划中）+右=drafting-gallery
 *        （sheets 子页=导出语境行+图库卡栅格；siteplan 子页全幅）
 *
 * 规格说明（B1 任务书 §三.5——plan §九.4；回炉 R7/VB-3）：
 *   - 左树目录=图纸清单导航（节点点击切子页——全厂总平面图→编辑面、
 *     其余→图库）；管网=挂起（「规划中」Tag——G5 语义沿承）；
 *   - 高程纵断图（DXF）=图纸交付物在制图域（W2 定名消歧——与 design
 *     区分析视图「高程纵断」同名异物）；
 *   - 回炉 R7（VB-3）：右区=图库卡栅格（卡片=DXF 交付物预览位+图题；
 *     数据源=useExportsQuery/buildSheetRows；空态卡=「尚无图纸——完成
 *     计算后生成」引导）；导出工具行保留为卡区上方语境行（ExportButton
 *     复用——微裁决 V18）；
 *   - 左树栏可拖宽（v2 笔2：usePaneWidth 接入——默认 190/140~420/
 *     键 wp-v4-drafting-left-w；siteplan 子页无左栏现状保持）。
 *   - V4 P2（2026-10-15）：图库卡语境行中文化——kind 显示名常量+工况
 *     conditionLabel 工程全称（""/all→全部工况；单源=shared/conditionLabels）。
 */
import { lazy, Suspense } from "react";
import { Spin, Tag, Typography } from "antd";

import { ErrorBoundary } from "../ErrorBoundary";
import { useProjectId } from "../useProjectId";
import { ExportButton } from "../../features/drawings/components/ExportButton";
import {
  useConditionOptions,
  useExportsQuery,
  useUnitOptions,
} from "../../features/drawings/api/useExportsQuery";
import { useUnitCatalog } from "../../features/drawings/api/useUnitCatalog";
import { buildSheetRows } from "../../features/drawings/lib/drawingsView";
import { conditionLabel, unitNameIndex } from "../../shared/conditionLabels";
import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";
import type { DraftingSubpage } from "../zoneParam";
import { usePaneWidth } from "./usePaneWidth";

/** 懒装载（M1 槽同制——懒件按 chunk 面隔离；装配引用不改件本体）。 */
const SiteplanPane = lazy(() =>
  import("../siteplanPane").then((m) => ({ default: m.SiteplanPane })),
);

/** 懒装载占位（薄壳——面板级 Spinner）。 */
function PaneLoading() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--wp-text-2)" }}>
      页面加载中…
    </div>
  );
}

/** 树节点（ sheets 子页导航——标签+目标子页；null=仅分组）。 */
type TreeRow = { key: string; label: string; subpage: DraftingSubpage | null; depth: number; pending?: boolean };

const TREE_ROWS: readonly TreeRow[] = [
  { key: "plant", label: "污水厂 ▾", subpage: null, depth: 0 },
  { key: "siteplan", label: "全厂总平面图", subpage: "siteplan", depth: 1 },
  { key: "profile", label: "高程纵断图", subpage: "sheets", depth: 1 },
  { key: "process", label: "工艺图", subpage: "sheets", depth: 1 },
  { key: "network", label: "管网 ▸", subpage: null, depth: 0, pending: true },
];

/** 未选项目引导（与 designZone NO_PROJECT_HINT 同源白名单文案）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「项目」区打开或新建";

/** 图库卡 kind 显示名（V4 P2 语境行中文化——值域=dxf 单值，显示层常量
 *  非查表映射；未知 kind 原样透传=dimLabels 诚实呈现同口径）。 */
const SHEET_KIND_LABELS: Record<string, string> = { dxf: "图纸" };

/** 卡片预览位简笔图纸形（折角单图——stroke currentColor 线性）。 */
function SheetGlyph() {
  return (
    <svg
      width="34"
      height="26"
      viewBox="0 0 34 26"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
      aria-hidden
    >
      <path d="M4 2h18l8 8v14H4z" />
      <path d="M22 2v8h8" />
      <path d="M9 13h16M9 17h16" />
    </svg>
  );
}

/** 图库卡栅格（回炉 R7——导出语境行+卡片栅格/空态卡；数据源=exports 查询；
 *  V3 D5：空态卡「去计算」引导钮+空态导出钮禁用〔disabled={rows=0}〕）。 */
function SheetsGallery({ onGoCalc }: { onGoCalc: () => void }) {
  const [projectId] = useProjectId();
  const exportsQuery = useExportsQuery(projectId);
  const conditionQuery = useConditionOptions(projectId);
  const unitQuery = useUnitOptions(projectId);
  // V4 P2 语境行中文化：工况工程全称（conditionLabel 单源；offline 拆段
  // 消费 unitNames——catalog 未就绪退 id 透传非阻塞）
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};
  // UX1 D3 同制：可投影面过滤（node.kind ∈ 目录 builtin 集剔除——B1 沿
  // DrawingsPane 口径重装配；catalog 未就绪不过滤全量兜底）
  const builtinIds = useUnitCatalog().data ?? null;
  const unitRefs = unitQuery.data ?? [];
  const exportableUnits =
    builtinIds === null
      ? unitRefs.map((unit) => unit.unitId)
      : unitRefs
          .filter((unit) => !builtinIds.has(unit.kind ?? ""))
          .map((unit) => unit.unitId);
  const rows = buildSheetRows(exportsQuery.data ?? []);

  return (
    <>
      {/* 导出语境行（卡区上方——ExportButton 复用；微裁决 V18） */}
      <div
        style={{
          flex: "none",
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "6px 10px",
          borderBottom: "1px solid var(--wp-border-2)",
          background: "var(--wp-bg-container)",
        }}
      >
        <span style={{ fontSize: 11, color: "var(--wp-text-2)", letterSpacing: 1 }}>
          图纸库 · DXF 交付物
        </span>
        {projectId !== null ? (
          <ExportButton
            projectId={projectId}
            units={exportableUnits}
            conditions={conditionQuery.data ?? []}
            disabled={rows.length === 0}
          />
        ) : null}
      </div>
      <div className="wp-v4-gallery" data-testid="wp-v4-sheet-grid">
        {projectId === null ? (
          <div
            className="wp-v4-sheet-card"
            style={{ width: "100%", maxWidth: 420 }}
          >
            <div className="wp-v4-sheet-thumb">
              <span>{NO_PROJECT_HINT}</span>
            </div>
          </div>
        ) : exportsQuery.isError ? (
          <Typography.Text type="danger" style={{ fontSize: 11 }}>
            图纸目录取数失败：
            {exportsQuery.error instanceof Error
              ? exportsQuery.error.message
              : "未知错误"}
          </Typography.Text>
        ) : exportsQuery.isPending ? (
          <Spin />
        ) : rows.length === 0 ? (
          // 空态卡（回炉 R7——「尚无图纸——完成计算后生成」级引导；
          // V3 D5：去计算钮=design 区直达动线）
          <div className="wp-v4-sheet-card" style={{ width: "100%", maxWidth: 420 }}>
            <div className="wp-v4-sheet-thumb">
              <SheetGlyph />
            </div>
            <div className="wp-v4-sheet-cap">尚无图纸——完成计算后生成</div>
            <button
              type="button"
              data-testid="wp-v4-drafting-go-calc"
              onClick={onGoCalc}
              style={{
                border: "1px solid var(--wpv4-ac)",
                borderRadius: 4,
                background: "var(--wp-bg-container, #ffffff)",
                color: "var(--wpv4-ac)",
                fontSize: 11,
                padding: "1px 10px",
                cursor: "pointer",
                margin: "6px auto 4px",
                display: "block",
              }}
            >
              去计算
            </button>
          </div>
        ) : (
          rows.map((row) => (
            <div
              className="wp-v4-sheet-card"
              key={row.key}
              data-testid="wp-v4-sheet-card"
              title={`${row.fileName} · digest ${row.designDigest.slice(0, 10)}`}
            >
              <div className="wp-v4-sheet-thumb">
                <SheetGlyph />
              </div>
              <div className="wp-v4-sheet-cap">
                {SHEET_KIND_LABELS[row.kind] ?? row.kind} ·{" "}
                {row.conditionKey === "" || row.conditionKey === "all"
                  ? "全部工况"
                  : conditionLabel(row.conditionKey, unitNames)}
                {row.stale ? <Tag style={{ marginInlineStart: 4 }}>旧</Tag> : null}
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}

export function DraftingZone({
  subpage,
  onSubpageChange,
  onGoCalc,
}: {
  subpage: DraftingSubpage;
  onSubpageChange: (subpage: DraftingSubpage) => void;
  /** V3 D5：空态「去计算」动线（shellV4 传 setZone design——跨区引导）。 */
  onGoCalc: () => void;
}) {
  // 左树栏宽+拖宽（v2 笔2：usePaneWidth 接入——顶层恒调，siteplan 分支
  // 无左栏不消费〔rules-of-hooks——子页分支不卸 hook〕）
  const navPane = usePaneWidth({
    key: "wp-v4-drafting-left-w",
    fallback: 190,
    min: 140,
    max: 420,
    side: "left",
  });
  if (subpage === "siteplan") {
    return (
      <section
        data-region="drafting-gallery"
        style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
      >
        {/* 返回图纸库（子页切换——左树同通道） */}
        <div
          style={{
            flex: "none",
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "4px 10px",
            borderBottom: "1px solid var(--wp-border-2)",
            background: "var(--wp-bg-container)",
          }}
        >
          <button
            type="button"
            data-testid="wp-v4-drafting-back-sheets"
            onClick={() => onSubpageChange("sheets")}
            style={{
              border: "none",
              background: "transparent",
              color: "var(--wpv4-ac)",
              fontSize: 12, // 回炉 R12：字号归一三档（12/11/10）
              cursor: "pointer",
              padding: 0,
            }}
          >
            ‹ 图纸库
          </button>
          <span style={{ fontSize: 12, color: "var(--wp-text)" }}>全厂总平面布置</span>
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <ErrorBoundary label="厂区总平面布置">
            <Suspense fallback={<PaneLoading />}>
              <SiteplanPane />
            </Suspense>
          </ErrorBoundary>
        </div>
      </section>
    );
  }

  return (
    <section style={{ flex: 1, minWidth: 0, display: "flex" }}>
      <aside
        className="wp-v4-sider"
        data-region="drafting-tree"
        style={{
          width: navPane.width,
          flex: "none",
          background: "var(--wp-bg-container)",
          borderRight: "1px solid var(--wp-border-2)",
          padding: "6px 4px",
          // 回炉 R1：overflow auto 双轴下 3px 幻影横滚（同 report 侧栏——
          // 子元素无实外溢实测在档）→ 横轴裁剪、纵滚保留
          overflowY: "auto",
          overflowX: "hidden",
        }}
      >
        <div
          className="wp-v4-drag"
          data-testid="wp-v4-drag-drafting-left"
          title="拖拽调整宽度"
          onPointerDown={navPane.onDragStart}
        >
          ⟷
        </div>
        <div
          style={{
            fontSize: 11,
            color: "var(--wp-text-2)",
            letterSpacing: 1,
            padding: "4px 8px 6px",
          }}
        >
          图纸目录
        </div>
        {TREE_ROWS.map((row) =>
          row.subpage === null ? (
            <div
              key={row.key}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "4px 8px",
                fontSize: 12, // 回炉 R12：字号归一三档
                color: "var(--wp-text-2)",
              }}
            >
              {/* V4 d1-W1/N8：省略三件套+minWidth:0/flex:1 链——flex 行内
                  span 不收缩则撑宽侧栏；长文省略号而非静默裁切（reportNav
                  条目同制） */}
              <span
                style={{
                  minWidth: 0,
                  flex: 1,
                  overflow: "hidden",
                  whiteSpace: "nowrap",
                  textOverflow: "ellipsis",
                }}
              >
                {row.label}
              </span>
              {row.pending ? <Tag style={{ marginInlineEnd: 0 }}>规划中</Tag> : null}
            </div>
          ) : (
            <button
              key={row.key}
              type="button"
              data-testid={`wp-v4-drafting-${row.key}`}
              onClick={() => onSubpageChange(row.subpage ?? "sheets")}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                border: "none",
                background: "transparent",
                color: "var(--wp-text)",
                fontSize: 12, // 回炉 R12：字号归一三档
                padding: "4px 8px 4px 22px",
                cursor: "pointer",
                // V4 d1-W1/N8：省略三件套（block 满宽条目——长文省略号
                // 而非静默裁切；reportNav 条目同制）
                overflow: "hidden",
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
              }}
            >
              {row.label}
            </button>
          ),
        )}
      </aside>
      <div
        data-region="drafting-gallery"
        style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
      >
        <SheetsGallery onGoCalc={onGoCalc} />
      </div>
    </section>
  );
}
