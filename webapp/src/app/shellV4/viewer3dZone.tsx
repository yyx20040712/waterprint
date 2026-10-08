/**
 * v4 三维示意区（B1 骨架批 2026-10-09——点击直接全幅：Viewer3dPane 复用
 * 迁入〔lazy 装配——M1 槽同制，装配引用不改件本体〕；wireframe-d-v4
 * 屏 7a 形）。
 *
 * 输入: Viewer3dPane（app 件 lazy 装配——空态项目选择/Scene 懒装载由
 *        viewer3d feature 自持）
 * 输出: viewer3d 全幅区（ErrorBoundary+Suspense 薄壳）+右下角浮动视图
 *        工具簇（回炉 R6/VB-2：放大/缩小/重置视图——简笔线性图标）
 *
 * 规格说明（B1 任务书 §三.6——plan §九.5：点击直接展示=全幅视口）。
 *   - 回炉 R6（VB-2）浮动工具簇：缩放±=zone 层包裹 scale 变换；重置视图
 *     =缩放复位+场景重挂载（mountKey 换键）——微裁决 V17：真 3D 相机
 *     dolly/preset 接线随 v4 viewer3d 功能批（B1 骨架态=可见可用的
 *     zone 层最小面，不深入 Scene 内部）。
 */
import { lazy, Suspense, useState } from "react";

import { ErrorBoundary } from "../ErrorBoundary";

const Viewer3dPane = lazy(() =>
  import("../viewer3dPane").then((m) => ({ default: m.Viewer3dPane })),
);

/** 缩放步距/限界（zone 层视图变换面——B1 骨架值）。 */
const ZOOM_STEP = 0.15;
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 2.5;

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

export function Viewer3dZone() {
  // zone 层视图态（回炉 R6——缩放=包裹变换；重置=缩放复位+重挂载）
  const [zoom, setZoom] = useState(1);
  const [mountKey, setMountKey] = useState(0);

  return (
    <section
      data-region="viewer3d-full"
      style={{
        flex: 1,
        minWidth: 0,
        display: "flex",
        flexDirection: "column",
        position: "relative",
      }}
    >
      <div
        style={{
          flex: 1,
          minHeight: 0,
          // B1 R2/N1：缩放溢出防护——放大态 scale 变换不溢出邻区（包裹面
          // 裁剪，工具簇在包裹面外不受裁剪影响）
          overflow: "hidden",
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
