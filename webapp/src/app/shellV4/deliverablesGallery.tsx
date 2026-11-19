/**
 * 图纸库卡栅格（美感抛光批 2026-11-20 自 deliverablesZone 拆件〔行数
 * 预算——reportExports 先例〕：导出语境行+图库卡栅格/空错态；数据源=
 * exports 查询族；空/错态=EmptyState 共享配方居中呈现，不再缩成左上
 * 小卡+大空白）。
 *
 * 输入:  onGoCalc（空态「去计算」动线——shellV4 setNav process）+
 *        useProjectId+useExportsQuery/useConditionOptions/useUnitOptions
 *        （导出语境行数据源）+useUnitCatalog（builtin 过滤）+
 *        useListUnitsApiUnitsGet（工况列中文名）
 * 输出:  SheetsGallery：导出语境行（ExportButton 复用+空态禁用）+
 *        卡栅格（SheetGlyph 预览+kind·工况 caption+旧 Tag）；无项目/
 *        取数失败/空图纸三态=EmptyState 居中（去计算 32px 主按钮档）
 */
import { Spin, Tag } from "antd";

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
import { useProjectId } from "../useProjectId";
import { EmptyState } from "./emptyState";

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

/** 空态大图标（美感抛光批 #7——40–48px 单线档：折角图纸+两行文）。 */
function SheetGlyphLarge() {
  return (
    <svg
      width="46"
      height="46"
      viewBox="0 0 40 40"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M7 4h17l9 9v23H7z" />
      <path d="M24 4v9h9" />
      <path d="M13 21h14M13 26h14M13 31h9" />
    </svg>
  );
}

/** 栅格内空态居中壳（flex 栅格占满行高——EmptyState 三态共用容器）。 */
function GalleryCenter({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        flex: "1 1 100%",
        minHeight: 320,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {children}
    </div>
  );
}

/** 图库卡栅格（回炉 R7——导出语境行+卡片栅格/空态卡；数据源=exports 查询；
 *  V3 D5：空态卡「去计算」引导钮+空态导出钮禁用〔disabled={rows=0}〕）。 */
export function SheetsGallery({ onGoCalc }: { onGoCalc: () => void }) {
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
        <span style={{ fontSize: 12, color: "var(--wp-text-2)", letterSpacing: 1 }}>
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
          // 美感抛光批 #7：空态居中视觉配方（白名单文案拆 title/description）
          <GalleryCenter>
            <EmptyState
              icon={<SheetGlyphLarge />}
              title="尚未选择项目"
              description="在「工作台」打开或新建"
            />
          </GalleryCenter>
        ) : exportsQuery.isError ? (
          <GalleryCenter>
            <EmptyState
              icon={<SheetGlyphLarge />}
              title="图纸目录取数失败"
              detail={
                exportsQuery.error instanceof Error
                  ? exportsQuery.error.message
                  : "未知错误"
              }
            />
          </GalleryCenter>
        ) : exportsQuery.isPending ? (
          <Spin />
        ) : rows.length === 0 ? (
          // 空态（美感抛光批 #7 居中配方；V3 D5 去计算钮=工艺入口直达动线）
          <GalleryCenter>
            <EmptyState
              icon={<SheetGlyphLarge />}
              title="尚无图纸"
              description="完成计算后生成图纸交付物"
              action={
                <button
                  type="button"
                  data-testid="wp-v4-drafting-go-calc"
                  onClick={onGoCalc}
                  style={{
                    border: "1px solid var(--wp-accent)",
                    borderRadius: 4,
                    background: "var(--wp-accent)",
                    color: "var(--wp-on-accent)",
                    fontSize: 12.5,
                    padding: "6px 18px",
                    cursor: "pointer",
                  }}
                >
                  去计算
                </button>
              }
            />
          </GalleryCenter>
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
