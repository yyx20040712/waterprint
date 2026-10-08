/**
 * v4 工程制图区（B1 骨架批 2026-10-09——左树目录+右图库卡；wireframe-d-v4
 * 屏 5 形；siteplan 编辑面随 v4-2 终裁归制图域=subpage siteplan）。
 *
 * 输入:  subpage（sheets=图纸库缺省/siteplan=厂区总平面布置编辑面——shellV4
 *        受控）+onSubpageChange（子页切换→?tab= zone 级投影）
 *        +DrawingsPane（app 件复用——DXF 交付物预览）+SiteplanPane（app 件
 *        复用——厂区布置编辑器）
 * 输出:  drafting 区：左=drafting-tree（污水厂▾〔全厂总平面图→siteplan/
 *        高程纵断图/工艺图…→sheets〕+管网▸规划中）+右=drafting-gallery
 *        （sheets 子页）或 siteplan 编辑面（siteplan 子页全幅）
 *
 * 规格说明（B1 任务书 §三.5——plan §九.4）：
 *   - 左树目录=图纸清单导航（节点点击切子页——全厂总平面图→编辑面、
 *     其余→图库）；管网=挂起（「规划中」Tag——G5 语义沿承）；
 *   - 高程纵断图（DXF）=图纸交付物在制图域（W2 定名消歧——与 design
 *     区分析视图「高程纵断」同名异物）；
 *   - 图库卡=DrawingsPane 内容复用（导出发起/产物目录/预览元数据）。
 */
import { lazy, Suspense } from "react";
import { Tag } from "antd";

import { ErrorBoundary } from "../ErrorBoundary";
import type { DraftingSubpage } from "../zoneParam";

/** 懒装载（M1 槽同制——懒件按 chunk 面隔离；装配引用不改件本体）。 */
const DrawingsPane = lazy(() =>
  import("../drawingsPane").then((m) => ({ default: m.DrawingsPane })),
);
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

export function DraftingZone({
  subpage,
  onSubpageChange,
}: {
  subpage: DraftingSubpage;
  onSubpageChange: (subpage: DraftingSubpage) => void;
}) {
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
              fontSize: 11.5,
              cursor: "pointer",
              padding: 0,
            }}
          >
            ‹ 图纸库
          </button>
          <span style={{ fontSize: 11.5, color: "var(--wp-text)" }}>全厂总平面布置</span>
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
        data-region="drafting-tree"
        style={{
          width: 190,
          flex: "none",
          background: "var(--wp-bg-container)",
          borderRight: "1px solid var(--wp-border-2)",
          padding: "6px 4px",
          overflow: "auto",
        }}
      >
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
                fontSize: 11.5,
                color: "var(--wp-text-2)",
              }}
            >
              <span>{row.label}</span>
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
                fontSize: 11.5,
                padding: "4px 8px 4px 22px",
                cursor: "pointer",
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
        <ErrorBoundary label="图纸预览">
          <Suspense fallback={<PaneLoading />}>
            <DrawingsPane />
          </Suspense>
        </ErrorBoundary>
      </div>
    </section>
  );
}
