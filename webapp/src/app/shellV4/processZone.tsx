/**
 * v4 工艺区（b2 壳重组批 2026-11-19 八入口「工艺」；b3 功能面重涂批
 * 同日重制——稿 network.html 三栏形：左=工艺单元库目录树〔UnitLibraryPane
 * ——点行落画布中心〕+中=工艺画布全幅〔ThumbnailFlow——点阵底+域色
 * 节点卡〕+右=选中单元 inspector 常驻〔UnitInspector——身份/当前参数/
 * 端口/操作组〕；沿革 B1 designZone 中列画布子页→b2 独立入口全幅→
 * b3 三栏信息组织重造〔数据流零变：右键目录/拖拽连线/选中 ?node= 语义
 * 全承袭〕）。
 *
 * 输入:  selectedUnitId（?node= 对象选中真相——shellV4 受控单源）+
 *        onSelectedUnitChange（画布/inspector 删除上抛）+onOpenParameters
 *        （inspector 主钮跨入口导航——shellV4 setNav）+useProjectId
 * 输出:  工艺入口：未选项目=空态引导（白名单文案）；有项目=三栏
 * 〔wp-v4-net：单元库/画布/inspector〕+EnumerateModal（inspector
 *  重新枚举钮开态——⟳ 唯一提交入口件复挂）
 *
 * 规格说明（b3 批准稿 network.html——布局与信息组织重造）：
 *   - 左树点选=addRequest 受控通道（seq 递增门——ThumbnailFlow 画布
 *     中心 screenToFlowPosition 落点；addUnit+position=右键通道同链）；
 *   - inspector 常驻（未选=空态引导；删除=canvasStore.deleteNodes+
 *     选中清除——B2 P3 k1-N8 同语义）；
 *   - 画布选中→onSelectedUnitChange 上抛（?node= 独立键写——参数方案
 *     /分析入口跨页随动，B2 数据流沿承）。
 */
import { useState } from "react";

import { useCanvasStore } from "../../features/canvas/store/canvasStore";
import { useProjectId } from "../useProjectId";
import { EnumerateModal } from "./enumerateModal";
import { ThumbnailFlow, type CanvasAddRequest } from "./thumbnailFlow";
import { UnitInspector } from "./unitInspector";
import { UnitLibraryPane } from "./unitLibraryPane";
import type { CatalogUnitEntry } from "../catalogCategories";

/** 未选项目引导（白名单：空态引导）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「工作台」打开或新建";

export function ProcessZone({
  selectedUnitId,
  onSelectedUnitChange,
  onOpenParameters,
}: {
  /** ?node= 对象选中真相（画布选中→参数方案/分析页随动）。 */
  selectedUnitId: string | null;
  /** 选中写入回调（ThumbnailFlow onNodeClick 上抛——shellV4 单源）。 */
  onSelectedUnitChange: (unitId: string | null) => void;
  /** inspector「参数与方案」主钮（shellV4 setNav parameters）。 */
  onOpenParameters: () => void;
}) {
  const [projectId] = useProjectId();
  // 左树点选落画布请求（seq 递增门——同请求幂等）
  const [addRequest, setAddRequest] = useState<CanvasAddRequest | null>(null);
  // inspector 重新枚举 Modal 开态（EnumerateModal=⟳ 唯一提交入口件）
  const [enumOpen, setEnumOpen] = useState(false);

  /** 左树点选 → 画布中心落点请求（seq 递增——ThumbnailFlow 处理门）。 */
  const pickFromLibrary = (unit: CatalogUnitEntry) => {
    setAddRequest((prev) => ({
      unitId: unit.unit_id,
      kind: unit.kind,
      seq: (prev?.seq ?? 0) + 1,
    }));
  };

  /** inspector 删除（canvasStore.deleteNodes 通道+选中清除）。 */
  const deleteUnit = (unitId: string) => {
    useCanvasStore.getState().deleteNodes([unitId]);
    onSelectedUnitChange(unitId === selectedUnitId ? null : selectedUnitId);
  };

  return (
    <section
      data-region="process-canvas"
      style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
    >
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
        <div className="wp-v4-net">
          <UnitLibraryPane onPickUnit={pickFromLibrary} />
          <div
            className="wp-v4-canvas wp-v4-dotgrid"
            style={{ flex: 1, minHeight: 0, margin: "0 8px" }}
          >
            {/* addRequest 态不清（seq 单调递增——ThumbnailFlow 幂等门
                消费；清回 null 会使后续请求 seq 回卷与已处理序撞车） */}
            <ThumbnailFlow
              projectId={projectId}
              selectedUnitId={selectedUnitId}
              onSelectedUnitChange={onSelectedUnitChange}
              addRequest={addRequest}
            />
          </div>
          <UnitInspector
            projectId={projectId}
            unitId={selectedUnitId}
            onOpenParameters={onOpenParameters}
            onOpenEnumerate={() => setEnumOpen(true)}
            onDeleteUnit={deleteUnit}
          />
        </div>
      )}
      <EnumerateModal
        open={enumOpen}
        onClose={() => setEnumOpen(false)}
        projectId={projectId}
        unitId={selectedUnitId}
      />
    </section>
  );
}
