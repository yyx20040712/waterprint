/**
 * v4 工艺区（b2 壳重组批 2026-11-19——八入口「工艺」：工艺画布全幅；
 * 沿革 B1 designZone 中列画布子页→b2 独立入口〔ThumbnailFlow 原件零改
 * 挂载——右键分级目录/拖拽连线/选中 ?node= 语义全承袭〕；稿 network
 * .html 画布段——左侧单元库目录与右侧选中 inspector=后续功能批，本批
 * 不新建面）。
 *
 * 输入:  selectedUnitId（?node= 对象选中真相——shellV4 受控单源）+
 *        onSelectedUnitChange（画布选中上抛）+useProjectId
 * 输出:  工艺画布全幅区：未选项目=空态引导（白名单文案）；有项目=
 *        ThumbnailFlow（wp-v4-canvas 容器——B1 同款边框画布槽）
 *
 * 规格说明（b2 任务书——旧 design 中列〔工艺画布｜分析表〕页签拆解）：
 *   - 画布选中→onSelectedUnitChange 上抛（?node= 独立键写——参数方案
 *     /分析入口跨页随动，B2 数据流沿承）；
 *   - 分析表=独立「分析」入口（页签退役——导航轨承载切换）。
 */
import { useProjectId } from "../useProjectId";
import { ThumbnailFlow } from "./thumbnailFlow";

/** 未选项目引导（白名单：空态引导）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「工作台」打开或新建";

export function ProcessZone({
  selectedUnitId,
  onSelectedUnitChange,
}: {
  /** ?node= 对象选中真相（画布选中→参数方案/分析页随动）。 */
  selectedUnitId: string | null;
  /** 选中写入回调（ThumbnailFlow onNodeClick 上抛——shellV4 单源）。 */
  onSelectedUnitChange: (unitId: string | null) => void;
}) {
  const [projectId] = useProjectId();
  return (
    <section
      data-region="process-canvas"
      style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
    >
      <div className="wp-v4-canvas" style={{ flex: 1, minHeight: 0, margin: 8 }}>
        {projectId === null ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "var(--wp-text-2)",
            }}
          >
            {NO_PROJECT_HINT}
          </div>
        ) : (
          <ThumbnailFlow
            projectId={projectId}
            selectedUnitId={selectedUnitId}
            onSelectedUnitChange={onSelectedUnitChange}
          />
        )}
      </div>
    </section>
  );
}
