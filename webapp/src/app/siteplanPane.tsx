/**
 * siteplan 标签页装配：projectId 空态提示+ErrorBoundary 隔离（canvasPane 同构薄壳）。
 *
 * 输入:  URL ?project= 参数（useProjectId 共享 hook——S3 订阅面/只读消费方）
 *        +feature SiteplanPane（组装件——projectId 就绪即挂载）
 * 输出:  厂区布置标签页（空态提示「先在顶栏选择项目」 / 布置编辑器隔离边界）
 *
 * 规格说明（M3 批 L2b，简报 §一.8/§二白名单）：
 *   - projectId 单一真相=URL ?project=（与 canvas 共用——canvas/viewer3d
 *     空态 Select 为写方；本 pane 只读订阅：空态=提示文案引导至画布标签
 *     选择项目，不设第二选择面——简报 §一.8 字面：先在顶栏选择项目）；
 *   - ErrorBoundary label=厂区布置（渲染崩溃不清空应用 §15 细节 4）；
 *     不传 onRetry（无 lazy thenable——零动态 import，纯 SVG 无大件）；
 *   - 不 lazy 不 Suspense（siteplan=原生 SVG 轻面——首屏直挂载可接受）。
 */
import { Typography } from "antd";

import { SiteplanPane as SiteplanEditor } from "../features/siteplan/components/SiteplanPane";
import { ErrorBoundary } from "./ErrorBoundary";
import { useProjectId } from "./useProjectId";

/** 空态提示（简报 §一.8——canvasPane UNSELECTED_HINT 同构引导面）。 */
const UNSELECTED_HINT =
  "先在顶栏选择项目：厂区布置与工艺画布共用 ?project= 参数——在「工艺画布」标签选择项目后即可在此编辑布置。";

export function SiteplanPane() {
  // S3 订阅面（只读——写方在 canvas/viewer3d 空态 Select）
  const [projectId] = useProjectId();

  if (projectId === null) {
    return (
      <div>
        <Typography.Paragraph>{UNSELECTED_HINT}</Typography.Paragraph>
      </div>
    );
  }
  return (
    <ErrorBoundary label="厂区布置">
      <div style={{ height: "100%" }}>
        <SiteplanEditor projectId={projectId} />
      </div>
    </ErrorBoundary>
  );
}
