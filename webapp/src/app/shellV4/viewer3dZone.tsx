/**
 * v4 三维示意区（B1 骨架批 2026-10-09——点击直接全幅：Viewer3dPane 复用
 * 迁入〔lazy 装配——M1 槽同制，装配引用不改件本体〕；wireframe-d-v4
 * 屏 7a 形）。
 *
 * 输入:  Viewer3dPane（app 件 lazy 装配——空态项目选择/Scene 懒装载由
 *        viewer3d feature 自持）
 * 输出:  viewer3d 全幅区（ErrorBoundary+Suspense 薄壳）
 *
 * 规格说明（B1 任务书 §三.6——plan §九.5：点击直接展示=全幅视口）。
 */
import { lazy, Suspense } from "react";

import { ErrorBoundary } from "../ErrorBoundary";

const Viewer3dPane = lazy(() =>
  import("../viewer3dPane").then((m) => ({ default: m.Viewer3dPane })),
);

export function Viewer3dZone() {
  return (
    <section
      data-region="viewer3d-full"
      style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
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
          <Viewer3dPane />
        </Suspense>
      </ErrorBoundary>
    </section>
  );
}
