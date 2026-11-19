/**
 * v4 三维示意区（B1 骨架批点击直接全幅→b4 功能面重涂 II 批 2026-11-19
 * 稿 viewer3d.html 两栏重制：左=场景结构〔厂区总装单元树+场地与管线
 * 分组+取景说明〕+右=Viewer3dPane 全幅〔ErrorBoundary+Suspense 薄壳〕
 * +右下角浮动视图工具簇〔放大/缩小/重置〕；未选项目=全幅空态选择面
 * 〔Viewer3dPane 自持〕——结构栏不挂）。
 *
 * 输入:  useProjectId（结构栏挂载门）+useProjectDesign（单元清单——
 *        params 通道同键缓存共享零额外请求）+useListUnitsApiUnitsGet
 *        （unitNameIndex 中文名）+Viewer3dPane（app 件 lazy 装配）
 * 输出:  viewer3d 区：两栏〔scene-structure 结构栏/全幅视口〕+浮动缩放
 *        工具簇（回炉 R6：zone 层 scale 变换+重挂载）
 *
 * 规格说明（b4 批准稿 viewer3d.html 左栏段——信息组织重造，数据流零变）：
 *   - 结构栏=场景构成只读信息（厂区总装=设计节点单元行〔中文名+id〕；
 *     场地与管线=管廊/道路/红线静态分组行——图示语义不虚造交互）；
 *   - 未摆放或未计算单元不进入场景（稿 notice 原文——诚实呈现）；
 *   - 缩放工具簇沿承（R6/VB-2：zone 层包裹 scale 变换；重置=缩放复位
 *     +场景重挂载 mountKey 换键——真 3D 相机 dolly/preset 接线挂账）。
 */
import { lazy, Suspense, useState } from "react";

import { ErrorBoundary } from "../ErrorBoundary";
import { useProjectId } from "../useProjectId";
import { useProjectDesign } from "../../features/params/api/useProjectDesign";
import { unitNameIndex } from "../../shared/conditionLabels";
import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";

const Viewer3dPane = lazy(() =>
  import("../viewer3dPane").then((m) => ({ default: m.Viewer3dPane })),
);

/** 缩放步距/限界（zone 层视图变换面——B1 骨架值）。 */
const ZOOM_STEP = 0.15;
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 2.5;

/** 结构栏底注（稿 viewer3d.html notice——白名单：说明文案）。 */
const STRUCTURE_NOTICE =
  "未摆放或未计算单元不进入场景。取景以模型簇与红线顶点为边界。";

/** 场地与管线分组行（场景构成静态行——图示语义非交互面；域色轴标注
 *  水线/泥线两管廊）。 */
const SITE_GROUP_ROWS: ReadonlyArray<readonly [string, string, string]> = [
  ["≋", "水线管廊", "var(--wp-water)"],
  ["≋", "泥线管廊", "var(--wp-sludge)"],
  ["▦", "道路与走廊", "var(--wp-text-3)"],
  ["▭", "场地红线", "var(--wp-text-3)"],
];

/** 简笔线性图标（+／−／home——stroke currentColor，全局规则简笔线性）。 */
function ToolIcon({ kind }: { kind: "in" | "out" | "home" }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      aria-hidden
    >
      {kind === "in" ? <path d="M8 3v10M3 8h10" /> : null}
      {kind === "out" ? <path d="M3 8h10" /> : null}
      {kind === "home" ? (
        <>
          <path d="M3 8.5 8 4l5 4.5" />
          <path d="M5 7.5V12h6V7.5" />
        </>
      ) : null}
    </svg>
  );
}

/** 场景结构栏（稿 viewer3d.html 左栏：厂区总装+场地与管线两分组）。 */
function SceneStructurePane() {
  const [projectId] = useProjectId();
  const designQuery = useProjectDesign(projectId ?? "");
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};
  const unitIds = Object.keys(designQuery.data?.nodeKinds ?? {}).sort((a, b) =>
    (unitNames[a] ?? a).localeCompare(unitNames[b] ?? b, "zh-Hans-CN"),
  );
  return (
    <aside className="wp-v4-pane left" data-region="scene-structure" style={{ width: 186 }}>
      <div className="wp-v4-pane-head">
        <h3>场景结构</h3>
        <span className="wp-v4-badge">{unitIds.length} 单元</span>
      </div>
      <div className="wp-v4-pane-body">
        <div className="wp-v4-tree">
          <div className="wp-v4-tree-group">
            <span aria-hidden className="chev">▾</span>
            <strong style={{ fontWeight: 400 }}>厂区总装</strong>
          </div>
          {unitIds.length === 0 ? (
            <p style={{ padding: "2px 8px 6px 22px", color: "var(--wp-text-2)", fontSize: 11 }}>
              设计无已摆单元
            </p>
          ) : (
            unitIds.map((unitId) => (
              <div
                key={unitId}
                data-testid="wp-v4-scene-unit-row"
                className="wp-v4-tree-row"
                style={{ cursor: "default" }}
                title={unitId}
              >
                <span aria-hidden style={{ flex: "none", color: "var(--wp-text-3)", width: 13, textAlign: "center" }}>
                  ◻
                </span>
                <span
                  style={{
                    minWidth: 0,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {unitNames[unitId] ?? unitId}
                </span>
              </div>
            ))
          )}
          <div className="wp-v4-tree-group" style={{ marginTop: 8 }}>
            <span aria-hidden className="chev">▾</span>
            <strong style={{ fontWeight: 400 }}>场地与管线</strong>
          </div>
          {SITE_GROUP_ROWS.map(([icon, label, color]) => (
            <div
              key={label}
              className="wp-v4-tree-row"
              style={{ cursor: "default" }}
            >
              <span aria-hidden style={{ flex: "none", color, width: 13, textAlign: "center" }}>
                {icon}
              </span>
              <span>{label}</span>
            </div>
          ))}
        </div>
        <div className="wp-v4-pane-foot">{STRUCTURE_NOTICE}</div>
      </div>
    </aside>
  );
}

export function Viewer3dZone() {
  const [projectId] = useProjectId();
  // zone 层视图态（回炉 R6——缩放=包裹变换；重置=缩放复位+重挂载）
  const [zoom, setZoom] = useState(1);
  const [mountKey, setMountKey] = useState(0);

  return (
    <section
      data-region="viewer3d-full"
      style={{
        flex: 1,
        minWidth: 0,
        // b4 两栏：行向（结构栏+视口）——缩放包裹列态在自身样式承载
        display: "flex",
        position: "relative",
        // B1 R2/N1+门一 k1-W1：缩放溢出防护挂未缩放祖先——overflow 裁剪
        // 边界随自身 transform 一并放大（局部坐标系先于变换），挂在带
        // scale 的包裹面无法裁回其自身放大后的渲染盒；工具簇为 section
        // 子级 absolute 定位，不受此裁剪影响。
        overflow: "hidden",
      }}
    >
      {projectId !== null ? <SceneStructurePane /> : null}
      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          transform: `scale(${zoom})`,
          transformOrigin: "center center",
        }}
      >
        <ErrorBoundary label="三维示意">
          <Suspense
            fallback={
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  height: "100%",
                  color: "var(--wp-text-2)",
                }}
              >
                页面加载中…
              </div>
            }
          >
            <Viewer3dPane key={mountKey} />
          </Suspense>
        </ErrorBoundary>
      </div>
      {/* 回炉 R6（VB-2）：右下角浮动视图工具簇（wireframe 屏 7a） */}
      <div className="wp-v4-view-tools" data-testid="wp-v4-view3d-tools">
        <button
          type="button"
          title="放大"
          aria-label="放大"
          data-testid="wp-v4-view3d-zoom-in"
          onClick={() =>
            setZoom((z) => Math.min(ZOOM_MAX, +(z + ZOOM_STEP).toFixed(2)))
          }
        >
          <ToolIcon kind="in" />
        </button>
        <button
          type="button"
          title="缩小"
          aria-label="缩小"
          data-testid="wp-v4-view3d-zoom-out"
          onClick={() =>
            setZoom((z) => Math.max(ZOOM_MIN, +(z - ZOOM_STEP).toFixed(2)))
          }
        >
          <ToolIcon kind="out" />
        </button>
        <button
          type="button"
          title="重置视图"
          aria-label="重置视图"
          data-testid="wp-v4-view3d-reset"
          onClick={() => {
            setZoom(1);
            setMountKey((k) => k + 1);
          }}
        >
          <ToolIcon kind="home" />
        </button>
      </div>
    </section>
  );
}
