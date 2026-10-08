/**
 * v4 三维示意区（B1 骨架批 2026-10-09——点击直接全幅：Viewer3dPane 复用
 * 迁入；wireframe-d-v4 屏 7a 形）。
 *
 * 输入:  Viewer3dPane（app 件复用——空态项目选择/Scene 懒装载+浮动工具面
 *        由 viewer3d feature 自持）
 * 输出:  viewer3d 全幅区（B1 装配引用——M1 件内容逻辑零改）
 *
 * 规格说明（B1 任务书 §三.6——plan §九.5：点击直接展示=全幅视口）。
 */
import { Viewer3dPane } from "../viewer3dPane";

export function Viewer3dZone() {
  return (
    <section
      data-region="viewer3d-full"
      style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
    >
      <Viewer3dPane />
    </section>
  );
}
