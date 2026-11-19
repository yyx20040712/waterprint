/**
 * v4 图纸报告区（b2 壳重组批 2026-11-19——八入口「图纸报告」：图纸库/
 * 厂区总平面/计算说明三面合一入口〔稿 deliverables.html——浏览与导出
 * 合并裁决〕；沿革 B1 draftingZone〔sheets/siteplan 两子页〕+reportZone
 * 〔独立 zone〕→b2 合并〔两 zone 件逻辑零改——ReportZone 原件挂 report
 * 子页全幅〕）。
 *
 * 输入: subpage（sheets=图纸库缺省/siteplan=厂区总平面编辑面/report=
 *        计算说明——shellV4 受控）+onSubpageChange（子页切换→?tab=
 *        deliverables.<subpage>）+onGoCalc（空态「去计算」动线——
 *        shellV4 setNav process）+SiteplanPane/exports 查询族（图纸库
 *        数据源+导出工具行语境）
 * 输出: deliverables 区：左=drafting-tree（污水厂▾〔全厂总平面图→
 *        siteplan/高程纵断图/工艺图→sheets〕+计算说明书→report+管网▸
 *        规划中）+右=sheets 子页=导出语境行+图库卡栅格〔美感抛光批
 *        2026-11-20 拆件 deliverablesGallery——行数预算，空错态=
 *        EmptyState 共享配方〕；siteplan 子页全幅（SiteplanPane）；
 *        report 子页全幅（ReportZone 自持左导航与阅读卡）
 *
 * 规格说明（B1 任务书 §三.5 承袭+b2 合并裁决；回炉 R7/VB-3）：
 *   - 左树目录=交付物导航（节点点击切子页——图纸/总平面/计算说明）；
 *     管网=挂起（「规划中」Tag——G5 语义沿承，锚族在工作台条）；
 *   - 高程纵断图（DXF）=图纸交付物在本区（W2 定名消歧——分析视图的
 *     「高程纵断」在分析入口）；
 *   - siteplan 子页无左栏现状保持（全幅编辑面+返回条）；report 子页
 *     =ReportZone 全幅（返回图纸库=导航轨点「图纸报告」回缺省 sheets）；
 *   - 左树栏可拖宽（键 wp-v4-drafting-left-w 沿承——宽度记忆不丢）。
 */
import { lazy, Suspense } from "react";
import { Tag } from "antd";

import { ErrorBoundary } from "../ErrorBoundary";
import { useProjectId } from "../useProjectId";
import type { DeliverablesSubpage } from "../zoneParam";
import { SheetsGallery } from "./deliverablesGallery";
import { NavGlyph, type NavGlyphKind } from "./navGlyphs";
import { ReportZone } from "./reportZone";
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

/** 树节点（sheets 子页导航——标签+目标子页+图标；null=仅分组）。b4 稿
 *  deliverables.html .tree 形：级行图标+缩进+当前子页高亮；美感抛光批
 *  #13：几何文本字形 ▦/▥/▤/▧→NavGlyph 单线 SVG（分组 ▾/▸ 折角保持）。 */
type TreeRow = {
  key: string;
  label: string;
  subpage: DeliverablesSubpage | null;
  depth: number;
  icon: NavGlyphKind | "chevDown" | "chevRight";
  pending?: boolean;
};

const TREE_ROWS: readonly TreeRow[] = [
  { key: "plant", label: "污水厂 ▾", subpage: null, depth: 0, icon: "chevDown" },
  { key: "siteplan", label: "全厂总平面图", subpage: "siteplan", depth: 1, icon: "site" },
  { key: "profile", label: "高程纵断图", subpage: "sheets", depth: 1, icon: "profile" },
  { key: "process", label: "工艺图", subpage: "sheets", depth: 1, icon: "flow" },
  { key: "report", label: "计算说明书", subpage: "report", depth: 1, icon: "doc" },
  { key: "network", label: "管网 ▸", subpage: null, depth: 0, icon: "chevRight", pending: true },
];

/** 未选项目引导（与 parametersZone NO_PROJECT_HINT 同源白名单文案）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「工作台」打开或新建";

/** 树行图标（NavGlyph 单线形；分组折角 ▾/▸ 保持文本形——美学抛光批 #13；
 *  组行图标=单枚 span〔省略三件套测试锚 spans[0]=图标/spans[1]=标签〕）。 */
function TreeIcon({ icon }: { icon: TreeRow["icon"] }) {
  if (icon === "chevDown" || icon === "chevRight") {
    return (
      <span aria-hidden style={{ flex: "none", color: "var(--wp-text-3)", fontSize: 10 }}>
        {icon === "chevDown" ? "▾" : "▸"}
      </span>
    );
  }
  return (
    <span
      aria-hidden
      style={{
        flex: "none",
        display: "inline-flex",
        alignItems: "center",
        color: "var(--wp-text-3)",
      }}
    >
      <NavGlyph kind={icon} size={13} />
    </span>
  );
}

export function DeliverablesZone({
  subpage,
  onSubpageChange,
  onGoCalc,
}: {
  subpage: DeliverablesSubpage;
  onSubpageChange: (subpage: DeliverablesSubpage) => void;
  /** V3 D5：空态「去计算」动线（shellV4 传 setNav process——跨入口引导）。 */
  onGoCalc: () => void;
}) {
  // 左树栏宽+拖宽（v2 笔2：usePaneWidth 接入——顶层恒调，siteplan/report
  // 分支无左栏不消费〔rules-of-hooks——子页分支不卸 hook〕）
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
              color: "var(--wp-accent)",
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
  if (subpage === "report") {
    // 计算说明子页：ReportZone 全幅（自持左导航+阅读卡+导出区——B6 件
    // 零改；返回图纸库=导航轨点「图纸报告」回缺省 sheets）
    return (
      <section
        data-region="deliverables-report"
        style={{ flex: 1, minWidth: 0, display: "flex" }}
      >
        <ReportZone />
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
          交付目录
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
              <TreeIcon icon={row.icon} />
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
              data-active={row.subpage === "sheets" ? "true" : "false"}
              onClick={() => onSubpageChange(row.subpage ?? "sheets")}
              title={row.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                width: "100%",
                textAlign: "left",
                border: "none",
                borderRadius: 4,
                background: "transparent",
                color: "var(--wp-text)",
                fontSize: 12, // 回炉 R12：字号归一三档
                padding: "4px 8px",
                margin: "1px 4px",
                cursor: "pointer",
                // V4 d1-W1/N8：省略三件套（长文省略号而非静默裁切；
                // b4：flex 行+label span 承载省略——图标/标签列稳定）
                overflow: "hidden",
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
              }}
            >
              <TreeIcon icon={row.icon} />
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
            </button>
          ),
        )}
      </aside>
      <div
        data-region="drafting-gallery"
        style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
      >
        {/* b4 稿 deliverables.html 中栏 .underline-tabs：图纸库（当前）|
            计算说明书（左树同通道切子页——onSubpageChange 单源） */}
        <div
          data-testid="wp-v4-deliverables-tabs"
          style={{
            flex: "none",
            display: "flex",
            alignItems: "center",
            gap: 18,
            padding: "0 12px",
            borderBottom: "1px solid var(--wp-border-2)",
            background: "var(--wp-bg-container)",
          }}
        >
          <span
            aria-current="page"
            style={{
              position: "relative",
              padding: "8px 1px 7px",
              color: "var(--wp-accent)",
              fontSize: 12.5,
            }}
          >
            图纸库
            <span
              aria-hidden
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: -1,
                height: 2,
                background: "var(--wp-accent)",
              }}
            />
          </span>
          <button
            type="button"
            data-testid="wp-v4-deliverables-tab-report"
            onClick={() => onSubpageChange("report")}
            style={{
              border: "none",
              background: "transparent",
              padding: "8px 1px 7px",
              color: "var(--wp-text-2)",
              fontSize: 12.5,
              cursor: "pointer",
            }}
          >
            计算说明书
          </button>
        </div>
        <SheetsGallery onGoCalc={onGoCalc} />
      </div>
    </section>
  );
}
