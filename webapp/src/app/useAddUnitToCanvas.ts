/**
 * 添加单元到画布 hook（M2 批 2026-10-08——addToCanvas 收敛单源）：编辑态
 * 守卫+store.addUnit+message 反馈实例 id/单实例约束 warning。
 *
 * 输入:  无 props（内部消费 useProjectId——projectId 守卫同 P0-3 编辑会话
 *        面；canvasStore.addUnit 经 getState 直取）
 * 输出:  { addToCanvas, editing, contextHolder }——两消费点共用（unitLibrary
 *        叶行＋钮+unitDetailPanel 主钮——Y-4「第三处复制前收敛」：两处即
 *        收敛位，逻辑逐字迁自 unitLibrary L201-217〔P0-3 呈裁② 甲案〕）
 *
 * 规格说明（M2 批预裁决 4）：
 *   - 逻辑零变（逐字迁移）：nodeId 非空=message.success（实例 id 反馈）；
 *     null+kind=unit=message.warning（引擎 v1 单实例约束——designWriter
 *     addUnit 拒绝面，装配按 node_id=注册表键精确匹配，_2 包实例 calc
 *     必败）；null+非 unit=静默（builtin 拒因不在此反馈面——原逻辑同）；
 *   - editing=useEditing(projectId)（store 会话与当前项目一致才可加）；
 *     contextHolder=message.useMessage() 实例的消费面渲染锚——两消费点
 *     各自渲染（antd message 静态方法不走 ConfigProvider 主题——useMessage
 *     先例沿袭）。
 */
import { useCallback } from "react";
import { message } from "antd";
import type { UnitMetaEntry } from "../shared/api/generated/model/unitMetaEntry";
import { useCanvasStore, useEditing } from "../features/canvas/store/canvasStore";
import { useProjectId } from "./useProjectId";

export function useAddUnitToCanvas() {
  // P0-3：编辑会话消费（projectId 守卫——store 会话与当前项目一致才可加）
  const [projectId] = useProjectId();
  const editing = useEditing(projectId);
  const [messageApi, contextHolder] = message.useMessage();
  const addToCanvas = useCallback(
    (unit: UnitMetaEntry) => {
      const nodeId = useCanvasStore.getState().addUnit(unit.unit_id, unit.kind);
      if (nodeId !== null) {
        messageApi.success(`已添加到画布：${nodeId}`);
      } else if (unit.kind === "unit") {
        // 引擎 v1 单实例约束（designWriter.addUnit 拒绝面——装配按
        // node_id=注册表键精确匹配，_2 包实例 calc 必败）
        messageApi.warning("该单元已在画布上（引擎 v1 单实例约束——多实例扩展挂账）");
      }
    },
    [messageApi],
  );
  return { addToCanvas, editing, contextHolder };
}
