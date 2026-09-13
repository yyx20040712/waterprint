/**
 * 摆放态解释横幅（F9——C2-visual 批；Scene 抽离件——500 行预算门）。
 *
 * 输入:  RenderScene+项目详情弱类型（placementSummary 判据面）
 * 输出:  部分摆放横幅（scene 仅收已布置单元——core build_scene 诚实
 *        语义；placementSummary 判据收口=structures 非空且 placed<total
 *        [GV-01 R 轮]；兜底满场/全覆盖/详情不可达均返 null 不挂）
 */
import { semanticColor } from "../../../shared/ui/semanticColors";
import { placementSummary } from "../lib/placementSummary";
import type { RenderScene } from "../lib/projectScene";

export function PlacementBanner({
  scene,
  projectDetail,
}: {
  scene: RenderScene;
  projectDetail: unknown;
}) {
  const summary = placementSummary(scene, projectDetail);
  if (summary === null) {
    return null;
  }
  return (
    <div
      role="status"
      data-testid="placement-banner"
      style={{ padding: "4px 8px", color: semanticColor("pending"), fontSize: 12 }}
    >
      三维仅显示已在「厂区布置」标签摆放的构筑物与相关管廊（
      {summary.placed}/{summary.total}）——未摆放单元不参与三维
      场景，摆放并重新计算后可见。
    </div>
  );
}
